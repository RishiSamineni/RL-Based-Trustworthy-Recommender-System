"""
seed.py
Seeds the database from raw JSONL files — ports pipeline.py Steps 1-5
into the Flask + SQLAlchemy world.

Run once (from the backend/ directory with venv active):
    python seed.py

Environment / config variables read from config.py:
    REVIEWS_FILE  — path to reviews JSONL
    META_FILE     — path to product metadata JSONL
    MAX_ROWS      — max review rows to load (default: all)
"""
import json
import math
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

from app import app          # brings in Flask app + db
from extensions import db
from models import Product, Rating
from preprocessing import clean_text
from config import REVIEWS_FILE, META_FILE

# ── optional row cap (set in config.py or override here) ─────────────────────
try:
    from config import MAX_ROWS
except ImportError:
    MAX_ROWS = None          # load everything


# ── JSONL loader (mirrors data_loader.load_jsonl from pipeline) ───────────────

def load_jsonl(filepath: str, max_rows: int = None) -> list[dict]:
    """Read a .jsonl file into a list of dicts."""
    path = Path(filepath)
    if not path.exists():
        print(f"[ERROR] File not found: {filepath}")
        return []
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if max_rows and i >= max_rows:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    print(f"[LOAD] {len(rows):,} rows from {path.name}")
    return rows


# ── column normalisation (mirrors pipeline Step 2 + 3) ────────────────────────

def normalise_reviews(rows: list[dict]) -> list[dict]:
    """Standardise column names and coerce types — mirrors pipeline.py Step 2-3."""
    col_map = {
        'reviewerID': 'user_id',
        'asin':       'asin',
        'overall':    'rating',
        'reviewText': 'text',
        'unixReviewTime': 'timestamp',
        'verified':   'verified_purchase',
        'vote':       'helpful_votes',
        'helpful_vote': 'helpful_votes',
    }
    out = []
    for row in rows:
        r = {}
        for src, dst in col_map.items():
            if src in row:
                r[dst] = row[src]
        # Fill from already-normalised names
        for col in ('user_id', 'asin', 'rating', 'text',
                    'timestamp', 'verified_purchase', 'helpful_votes'):
            if col not in r and col in row:
                r[col] = row[col]

        # Type coercions
        try:    r['rating'] = float(r.get('rating') or 5.0)
        except: r['rating'] = 5.0

        try:    r['helpful_votes'] = int(float(r.get('helpful_votes') or 0))
        except: r['helpful_votes'] = 0

        vp = r.get('verified_purchase', False)
        if isinstance(vp, str):
            r['verified_purchase'] = vp.lower() in ('true', '1', 'yes')
        else:
            r['verified_purchase'] = bool(vp)

        # Text cleaning (mirrors pipeline Step 4)
        r['review_text'] = clean_text(str(r.get('text') or ''))

        out.append(r)
    return out


def normalise_products(rows: list[dict]) -> list[dict]:
    """Normalise product metadata columns."""
    asin_cols  = ('asin', 'ASIN', 'parent_asin', 'product_id', 'id', 'sku')
    title_cols = ('title', 'productTitle', 'name', 'product_name')
    cat_cols   = ('main_category', 'category', 'categories')

    out = []
    for row in rows:
        p = {}

        # ASIN
        for c in asin_cols:
            if c in row and row[c]:
                p['asin'] = str(row[c])
                break
        if 'asin' not in p:
            continue                         # skip rows with no ASIN

        # Title
        for c in title_cols:
            if c in row and row[c]:
                p['title'] = str(row[c])
                break
        p.setdefault('title', '')

        # Category
        for c in cat_cols:
            if c in row and row[c]:
                val = row[c]
                p['category'] = (val[0] if isinstance(val, list) else str(val))
                break
        p.setdefault('category', '')

        # Price
        try:    p['price'] = float(row.get('price') or 0.0)
        except: p['price'] = 0.0

        # Features (stored as JSON string)
        feats = row.get('features') or row.get('feature') or []
        if isinstance(feats, list):
            import json as _json
            p['features'] = _json.dumps(feats)
        else:
            p['features'] = str(feats)

        out.append(p)
    return out


# ── SEED ──────────────────────────────────────────────────────────────────────

def seed():
    with app.app_context():
        print("\n[SEED] Creating tables if they don't exist...")
        db.create_all()

        # ── products ──────────────────────────────────────────────────────────
        print(f"\n[SEED] Loading product metadata from: {META_FILE}")
        raw_products = load_jsonl(META_FILE, max_rows=500_000)
        products     = normalise_products(raw_products)

        existing_asins = {p.asin for p in Product.query.with_entities(Product.asin).all()}
        new_products = [p for p in products if p['asin'] not in existing_asins]

        print(f"[SEED] Inserting {len(new_products):,} new products "
              f"(skipping {len(products) - len(new_products):,} existing)...")

        batch = []
        for i, p in enumerate(new_products):
            batch.append(Product(
                asin     = p['asin'],
                title    = p['title'],
                category = p['category'],
                price    = p['price'],
                features = p['features'],
            ))
            if len(batch) >= 1000:
                db.session.bulk_save_objects(batch)
                db.session.commit()
                batch = []
                print(f"  ... {i+1:,} products committed")
        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()
        print(f"[DONE] Products seeded.")

        # ── reviews ───────────────────────────────────────────────────────────
        print(f"\n[SEED] Loading reviews from: {REVIEWS_FILE}")
        raw_reviews = load_jsonl(REVIEWS_FILE, max_rows=MAX_ROWS)
        reviews     = normalise_reviews(raw_reviews)

        print(f"[SEED] Inserting {len(reviews):,} ratings...")

        # Clear existing ratings so re-seeding is idempotent
        Rating.query.delete()
        db.session.commit()

        batch = []
        for i, r in enumerate(reviews):
            if not r.get('user_id') or not r.get('asin'):
                continue
            batch.append(Rating(
                user_id          = r['user_id'],
                product_asin     = r['asin'],
                rating           = r['rating'],
                review_text      = r.get('review_text', ''),
                verified_purchase= r['verified_purchase'],
                helpful_votes    = r['helpful_votes'],
            ))
            if len(batch) >= 2000:
                db.session.bulk_save_objects(batch)
                db.session.commit()
                batch = []
                print(f"  ... {i+1:,} ratings committed")
        if batch:
            db.session.bulk_save_objects(batch)
            db.session.commit()

        total_r = Rating.query.count()
        total_p = Product.query.count()
        print(f"\n[DONE] Seed complete — {total_p:,} products, {total_r:,} ratings in DB.")


if __name__ == '__main__':
    seed()
