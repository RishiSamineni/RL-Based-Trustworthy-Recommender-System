"""
Seed the DB by loading ALL products from meta_Software.jsonl and Software.jsonl.
Mirrors the exact pipeline.py steps:
  Step 1: Load files
  Step 2: Standardize columns
  Step 3: Fix data types
  Step 4: Text cleaning
  Step 5: Trust scoring
"""
import json
import re
import math
import statistics
from pathlib import Path
from extensions import db
from models import User, Product, Rating
from engine.trust_engine import TrustEngine

# ── Paths (same as original config.py) ───────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent
REVIEWS_FILE = BASE_DIR / "Software.jsonl"
META_FILE    = BASE_DIR / "meta_Software.jsonl"
MAX_ROWS     = int(__import__('os').environ.get('MAX_ROWS', '50000'))

# ── Default demo users ────────────────────────────────────────────────────────
DEMO_USERS = [
    {"username": "alice_dev",     "email": "alice@example.com",  "password": "password123"},
    {"username": "bob_tech",      "email": "bob@example.com",    "password": "password123"},
    {"username": "carol_pm",      "email": "carol@example.com",  "password": "password123"},
    {"username": "dave_design",   "email": "dave@example.com",   "password": "password123"},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_jsonl(file_path, max_rows=MAX_ROWS):
    """Load JSONL file into a list of dicts."""
    print(f"[LOAD] {file_path}")
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= max_rows:
                    print(f"[WARN] Stopped at {max_rows} rows")
                    break
                try:
                    data.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        print(f"[DONE] Loaded {len(data)} rows")
        return data
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        return []
    except Exception as e:
        print(f"[ERROR] {e}")
        return []


def clean_text(text):
    """Basic text cleaning."""
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[_"\\\-;%()|+&=*%.,!?:#$@\[\]/]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _detect_col(candidates):
    """Return first candidate column name that exists in df, else None."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _detect_col_dict(row, candidates):
    """Return first candidate key that exists in row dict."""
    for c in candidates:
        if c in row:
            return c
    return None


def _detect_col_list(data, candidates):
    """Return first candidate key that exists in any row."""
    for c in candidates:
        for row in data[:10]:  # check first 10
            if c in row:
                return c
    return None


# ── Main seed function ────────────────────────────────────────────────────────

def seed_data(db_instance):
    print("Starting seed_data")
    """Load datasets, compute trust scores, and populate the DB."""

    # ── Column mappings ───────────────────────────────────────────────────────────
    review_col_map = {
        'reviewerID': 'user_id', 'asin': 'asin', 'overall': 'rating',
        'reviewText': 'text',    'unixReviewTime': 'timestamp',
        'verified':   'verified_purchase', 'vote': 'helpful_vote'
    }

    # Skip if already seeded
    current_count = Product.query.count()
    print(f"[DEBUG] Current product count: {current_count}")
    if current_count > 0:
        print("[SEED] Database already seeded. Skipping.")
        return

    print("\n[SEED] ══════════════════════════════════════════")
    print("[SEED] Starting dataset-driven seeding pipeline")
    print("[SEED] ══════════════════════════════════════════")

    # ── STEP 1: Load files ────────────────────────────────────────────────────
    print("\n[STEP 1] LOADING DATA")
    reviews_data = load_jsonl(REVIEWS_FILE)
    products_data = load_jsonl(META_FILE, max_rows=500000)

    if not reviews_data:
        print("[ERROR] No reviews loaded. Check that Software.jsonl exists in backend/data/")
        print("[INFO]  Falling back to built-in demo data...")
        _seed_demo_fallback(db_instance)
        return

    # ── STEP 2: Standardize columns (mirrors pipeline.py Step 2) ─────────────
    print("\n[STEP 2] STANDARDISING COLUMNS")
    # For reviews, map keys
    standardized_reviews = []
    for row in reviews_data:
        new_row = {}
        for k, v in review_col_map.items():
            if k in row:
                new_row[v] = row[k]
        # Ensure asin
        if 'asin' not in new_row and 'ASIN' in row:
            new_row['asin'] = row['ASIN']
        elif 'asin' not in new_row and 'product_id' in row:
            new_row['asin'] = row['product_id']
        elif 'asin' not in new_row and 'parent_asin' in row:
            new_row['asin'] = row['parent_asin']
        if 'asin' not in new_row:
            new_row['asin'] = 'unknown'
        standardized_reviews.append(new_row)

    # For products, similar
    standardized_products = []
    for row in products_data:
        new_row = row.copy()  # dict
        if 'asin' not in new_row and 'ASIN' in row:
            new_row['asin'] = row['ASIN']
        elif 'asin' not in new_row and 'parent_asin' in row:
            new_row['asin'] = row['parent_asin']
        elif 'asin' not in new_row and 'product_id' in row:
            new_row['asin'] = row['product_id']
        if 'asin' not in new_row:
            new_row['asin'] = None
        standardized_products.append(new_row)

    # ── STEP 3: Fix data types (mirrors pipeline.py Step 3) ──────────────────
    print("\n[STEP 3] FIXING DATA TYPES")

    for row in standardized_reviews:
        # Rating
        if 'rating' not in row and 'overall' in row:
            try:
                row['rating'] = float(row['overall'])
            except:
                row['rating'] = 5.0
        elif 'rating' in row:
            try:
                row['rating'] = float(row['rating'])
            except:
                row['rating'] = 5.0
        else:
            row['rating'] = 5.0

        # Text
        if 'text' not in row:
            text_col = _detect_col_dict(row, ['reviewText', 'review_text', 'body', 'content'])
            row['text'] = str(row.get(text_col, '')) if text_col else ''

        # Timestamp
        if 'timestamp' not in row:
            ts_col = _detect_col_dict(row, ['unixReviewTime', 'unix_time', 'timestamp'])
            try:
                row['timestamp'] = int(row.get(ts_col, 0)) if ts_col else 0
            except:
                row['timestamp'] = 0

        # Verified purchase
        if 'verified_purchase' not in row:
            vp_col = _detect_col_dict(row, ['verified', 'verifiedPurchase', 'verified_purchase'])
            row['verified_purchase'] = bool(row.get(vp_col, False)) if vp_col else False
        else:
            row['verified_purchase'] = bool(row['verified_purchase'])

        # Helpful votes
        if 'helpful_vote' not in row:
            hv_col = _detect_col_dict(row, ['vote', 'helpful', 'helpful_vote', 'helpfulVotes'])
            try:
                row['helpful_vote'] = int(row.get(hv_col, 0)) if hv_col else 0
            except:
                row['helpful_vote'] = 0
        else:
            try:
                row['helpful_vote'] = int(row['helpful_vote'])
            except:
                row['helpful_vote'] = 0

        # User ID
        if 'user_id' not in row:
            uid_col = _detect_col_dict(row, ['reviewerID', 'user_id', 'reviewer_id', 'userId'])
            row['user_id'] = str(row.get(uid_col, 'unknown')) if uid_col else 'unknown'

    # For products
    for row in standardized_products:
        price_col = _detect_col_dict(row, ['price', 'Price', 'price_usd'])
        if price_col:
            try:
                row['price'] = float(row.get(price_col, 0) or 0)
            except:
                row['price'] = 0.0
        else:
            row['price'] = 0.0

    # Detect title, category, etc.
    title_col = _detect_col_list(standardized_products, ['title', 'productTitle', 'name', 'product_name'])
    category_col = _detect_col_list(standardized_products, ['main_category', 'category', 'categories', 'main_cat'])
    desc_col = _detect_col_list(standardized_products, ['description', 'details', 'feature', 'features'])
    features_col = _detect_col_list(standardized_products, ['features', 'feature', 'details'])

    print(f"[INFO] title={title_col}, category={category_col}, price=price")

    # ── STEP 4: Text cleaning (mirrors pipeline.py Step 4) ───────────────────
    print("\n[STEP 4] TEXT CLEANING")
    for row in standardized_reviews:
        row['text'] = clean_text(row['text'])

    # ── STEP 5: Build product records ─────────────────────────────────────────
    print("\n[STEP 5] BUILDING PRODUCT RECORDS")

    # Create a products lookup
    prod_lookup = {}
    for row in standardized_products:
        asin = str(row.get('asin', '')).strip()
        if asin and asin != 'nan' and asin != 'None':
            prod_lookup[asin] = row

    # Determine unique ASINs that appear in reviews
    unique_asins = set()
    for row in standardized_reviews:
        asin = str(row.get('asin', '')).strip()
        if asin:
            unique_asins.add(asin)
    unique_asins = list(unique_asins)
    print(f"[INFO] {len(unique_asins)} unique products in reviews")

    mean_price = 0.0
    prices = []
    for asin in unique_asins:
        if asin in prod_lookup:
            p = prod_lookup[asin].get('price', 0)
            if p > 0:
                prices.append(p)
    if prices:
        mean_price = sum(prices) / len(prices)

    # ── STEP 6: Create DB records ─────────────────────────────────────────────
    print("\n[STEP 6] CREATING DATABASE RECORDS")

    trust_engine = TrustEngine()

    # Create demo users
    user_map = {}
    for ud in DEMO_USERS:
        u = User(username=ud['username'], email=ud['email'])
        u.set_password(ud['password'])
        db_instance.session.add(u)
        db_instance.session.flush()
        user_map[ud['username']] = u

    # Map reviewer IDs to DB users
    all_reviewer_ids = list(set(row['user_id'] for row in standardized_reviews))
    demo_user_list = list(user_map.values())
    reviewer_to_user = {}
    for i, rid in enumerate(all_reviewer_ids):
        reviewer_to_user[rid] = demo_user_list[i % len(demo_user_list)]

    # Insert products
    product_map = {}
    total = len(unique_asins)
    print(f"[INFO] Inserting {total} products...")

    for idx, asin in enumerate(unique_asins):
        if idx % 500 == 0:
            print(f"  Progress: {idx}/{total}")

        meta = prod_lookup.get(asin)

        # Build title
        title = ''
        if meta and title_col:
            title = str(meta.get(title_col, '') or '').strip()
        if not title:
            title = f"Software Product {asin}"

        # Category
        category = 'Software'
        if meta and category_col:
            raw_cat = meta.get(category_col, '')
            if isinstance(raw_cat, list):
                category = str(raw_cat[0]) if raw_cat else 'Software'
            else:
                category = str(raw_cat or 'Software').strip()

        # Price
        price = 0.0
        if meta:
            try:
                price = float(meta.get('price', 0) or 0)
            except:
                price = 0.0

        # Description
        description = ''
        if meta and desc_col:
            raw_desc = meta.get(desc_col, '')
            if isinstance(raw_desc, list):
                description = ' '.join(str(x) for x in raw_desc[:3])
            else:
                description = str(raw_desc or '')
            description = description[:1000]

        # Features
        features_list = []
        if meta and features_col:
            raw_feat = meta.get(features_col, [])
            if isinstance(raw_feat, list):
                features_list = [str(f) for f in raw_feat[:10] if f]
            elif isinstance(raw_feat, str):
                features_list = [raw_feat[:200]]

        # Image
        image_url = ''
        if meta:
            imgs = meta.get('images', meta.get('image', meta.get('imageURL', [])))
            if isinstance(imgs, list) and imgs:
                first = imgs[0]
                if isinstance(first, dict):
                    image_url = first.get('large', first.get('thumb', ''))
                else:
                    image_url = str(first)
            elif isinstance(imgs, str):
                image_url = imgs
        if not image_url:
            image_url = f"https://picsum.photos/seed/{asin}/300/200"

        p = Product(
            asin=str(asin),
            title=title[:300],
            description=description,
            category=category[:100],
            price=price,
            image_url=image_url[:500],
            features=json.dumps(features_list),
        )
        db_instance.session.add(p)
        db_instance.session.flush()
        product_map[str(asin)] = p

    print(f"[DONE] {len(product_map)} products inserted")

    # Insert ratings
    print(f"\n[INFO] Inserting ratings...")
    seen_pairs = set()
    rating_count = 0

    for row in standardized_reviews:
        asin = str(row.get('asin', '')).strip()
        user_id = str(row.get('user_id', '')).strip()

        p = product_map.get(asin)
        if not p:
            continue

        u = reviewer_to_user.get(user_id)
        if not u:
            continue

        pair = (u.id, p.id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        r = Rating(
            user_id=u.id,
            product_id=p.id,
            rating=float(row.get('rating', 5.0)),
            review_text=str(row.get('text', ''))[:2000],
            verified_purchase=bool(row.get('verified_purchase', False)),
            helpful_votes=int(row.get('helpful_vote', 0)),
        )
        db_instance.session.add(r)
        rating_count += 1

    db_instance.session.commit()
    print(f"[DONE] {rating_count} ratings inserted")

    # ── STEP 7: Compute trust scores (mirrors pipeline.py Step 5) ────────────
    print("\n[STEP 7] COMPUTING TRUST SCORES")
    total = len(product_map)

    for idx, (asin, prod_obj) in enumerate(product_map.items()):
        if idx % 200 == 0:
            print(f"  Trust scoring: {idx}/{total}")

        ratings_qs = Rating.query.filter_by(product_id=prod_obj.id).all()
        if not ratings_qs:
            continue

        raw = [r.rating for r in ratings_qs]
        prod_obj.avg_rating = sum(raw) / len(raw)
        prod_obj.rating_count = len(raw)

        p_details = trust_engine.product_trust_score(prod_obj, ratings_qs, mean_price)

        # User trust
        user_trusts = []
        for r in ratings_qs:
            u_ratings = Rating.query.filter_by(user_id=r.user_id).all()
            user_trusts.append(trust_engine.user_trust_score(u_ratings))
        u_trust = sum(user_trusts) / len(user_trusts) if user_trusts else 0.5

        # Seller trust
        same_cat = Product.query.filter(
            Product.category == prod_obj.category,
            Product.id != prod_obj.id
        ).limit(20).all()
        seller_pairs = []
        for sp in same_cat:
            sp_r = Rating.query.filter_by(product_id=sp.id).all()
            if sp_r:
                seller_pairs.append((sp, sp_r))
        s_trust = trust_engine.seller_trust_score(seller_pairs, mean_price)

        final = 0.55 * p_details['product_trust'] + 0.35 * u_trust + 0.10 * s_trust

        prod_obj.product_trust = round(p_details['product_trust'], 3)
        prod_obj.seller_trust = round(s_trust, 3)
        prod_obj.final_trust_score = round(final, 3)
        prod_obj.avg_rating_norm = round(p_details['avg_rating_norm'], 3)
        prod_obj.verified_ratio = round(p_details['verified_ratio'], 3)
        prod_obj.review_confidence = round(p_details['review_confidence'], 3)
        prod_obj.text_quality = round(p_details['text_quality'], 3)
        prod_obj.price_factor = round(p_details['price_factor'], 3)
        prod_obj.title_similarity = round(p_details['title_similarity'], 3)

        # Commit in batches
        if idx % 500 == 0:
            db_instance.session.commit()

    db_instance.session.commit()
    print(f"\n[SEED] ✓ Complete: {len(product_map)} products, {rating_count} ratings seeded from real dataset.")

    # ── STEP 2: Standardize columns (mirrors pipeline.py Step 2) ─────────────
    print("\n[STEP 2] STANDARDISING COLUMNS")
    review_col_map = {
        'reviewerID': 'user_id', 'asin': 'asin', 'overall': 'rating',
        'reviewText': 'text',    'unixReviewTime': 'timestamp',
        'verified':   'verified_purchase', 'vote': 'helpful_vote'
    }
    df_reviews = df_reviews.rename(columns={k: v for k, v in review_col_map.items() if k in df_reviews.columns})

    # Ensure 'asin' exists in reviews
    asin_col = _detect_col(df_reviews, ['asin', 'ASIN', 'product_id', 'parent_asin'])
    if asin_col and asin_col != 'asin':
        df_reviews['asin'] = df_reviews[asin_col]

    # Ensure 'asin' exists in products
    prod_asin_col = _detect_col(df_products, ['asin', 'ASIN', 'parent_asin', 'product_id', 'id'])
    if prod_asin_col and prod_asin_col != 'asin':
        df_products['asin'] = df_products[prod_asin_col]
    elif 'asin' not in df_products.columns:
        df_products['asin'] = np.nan

    # ── STEP 3: Fix data types (mirrors pipeline.py Step 3) ──────────────────
    print("\n[STEP 3] FIXING DATA TYPES")

    # Rating
    if 'rating' not in df_reviews.columns and 'overall' in df_reviews.columns:
        df_reviews['rating'] = pd.to_numeric(df_reviews['overall'], errors='coerce').fillna(5.0)
    elif 'rating' in df_reviews.columns:
        df_reviews['rating'] = pd.to_numeric(df_reviews['rating'], errors='coerce').fillna(5.0)
    else:
        df_reviews['rating'] = 5.0

    # Text
    if 'text' not in df_reviews.columns:
        text_col = _detect_col(df_reviews, ['reviewText', 'review_text', 'body', 'content'])
        df_reviews['text'] = df_reviews[text_col].fillna('') if text_col else ''

    # Timestamp
    if 'timestamp' not in df_reviews.columns:
        ts_col = _detect_col(df_reviews, ['unixReviewTime', 'unix_time', 'timestamp'])
        df_reviews['timestamp'] = pd.to_numeric(df_reviews[ts_col], errors='coerce').fillna(0) if ts_col else 0

    # Verified purchase
    if 'verified_purchase' not in df_reviews.columns:
        vp_col = _detect_col(df_reviews, ['verified', 'verifiedPurchase', 'verified_purchase'])
        df_reviews['verified_purchase'] = df_reviews[vp_col].astype(bool) if vp_col else False
    else:
        df_reviews['verified_purchase'] = df_reviews['verified_purchase'].astype(bool)

    # Helpful votes
    if 'helpful_vote' not in df_reviews.columns:
        hv_col = _detect_col(df_reviews, ['vote', 'helpful', 'helpful_vote', 'helpfulVotes'])
        df_reviews['helpful_vote'] = pd.to_numeric(df_reviews[hv_col], errors='coerce').fillna(0) if hv_col else 0
    else:
        df_reviews['helpful_vote'] = pd.to_numeric(df_reviews['helpful_vote'], errors='coerce').fillna(0)

    # User ID
    if 'user_id' not in df_reviews.columns:
        uid_col = _detect_col(df_reviews, ['reviewerID', 'user_id', 'reviewer_id', 'userId'])
        df_reviews['user_id'] = df_reviews[uid_col] if uid_col else 'unknown'

    # Product price
    price_col = _detect_col(df_products, ['price', 'Price', 'price_usd'])
    if price_col:
        df_products['price'] = pd.to_numeric(df_products[price_col], errors='coerce').fillna(0.0)
    else:
        df_products['price'] = 0.0

    # Detect title and category columns
    title_col    = _detect_col(df_products, ['title', 'productTitle', 'name', 'product_name'])
    category_col = _detect_col(df_products, ['main_category', 'category', 'categories', 'main_cat'])
    desc_col     = _detect_col(df_products, ['description', 'details', 'feature', 'features'])
    features_col = _detect_col(df_products, ['features', 'feature', 'details'])

    print(f"[INFO] title={title_col}, category={category_col}, price={price_col}")

    # ── STEP 4: Text cleaning (mirrors pipeline.py Step 4) ───────────────────
    print("\n[STEP 4] TEXT CLEANING")
    df_reviews['text'] = df_reviews['text'].fillna('').apply(clean_text)

    # ── STEP 5: Build product records ─────────────────────────────────────────
    print("\n[STEP 5] BUILDING PRODUCT RECORDS")

    # Create a products lookup from meta
    prod_lookup = {}
    if not df_products.empty and 'asin' in df_products.columns:
        for _, row in df_products.iterrows():
            asin = str(row.get('asin', '')).strip()
            if asin and asin != 'nan':
                prod_lookup[asin] = row

    # Determine unique ASINs that appear in reviews
    unique_asins = df_reviews['asin'].dropna().unique()
    print(f"[INFO] {len(unique_asins)} unique products in reviews")

    mean_price = 0.0
    if prod_lookup:
        prices = [float(prod_lookup[a].get('price', 0) or 0)
                  for a in unique_asins if a in prod_lookup]
        prices = [p for p in prices if p > 0]
        mean_price = float(sum(prices) / len(prices)) if prices else 0.0

    # ── STEP 6: Create DB records ─────────────────────────────────────────────
    print("\n[STEP 6] CREATING DATABASE RECORDS")

    trust_engine = TrustEngine()

    # Create demo users
    user_map = {}
    for ud in DEMO_USERS:
        u = User(username=ud['username'], email=ud['email'])
        u.set_password(ud['password'])
        db_instance.session.add(u)
        db_instance.session.flush()
        user_map[ud['username']] = u

    # Map reviewer IDs to DB users (round-robin assignment for real reviewer IDs)
    all_reviewer_ids = df_reviews['user_id'].unique().tolist()
    demo_user_list   = list(user_map.values())
    reviewer_to_user = {}
    for i, rid in enumerate(all_reviewer_ids):
        reviewer_to_user[rid] = demo_user_list[i % len(demo_user_list)]

    # Insert products
    product_map = {}   # asin -> Product ORM object
    total = len(unique_asins)
    print(f"[INFO] Inserting {total} products...")

    for idx, asin in enumerate(unique_asins):
        if idx % 500 == 0:
            print(f"  Progress: {idx}/{total}")

        meta = prod_lookup.get(str(asin))

        # Build title
        title = ''
        if meta is not None and title_col:
            title = str(meta.get(title_col, '') or '').strip()
        if not title:
            title = f"Software Product {asin}"

        # Category
        category = 'Software'
        if meta is not None and category_col:
            raw_cat = meta.get(category_col, '')
            if isinstance(raw_cat, list):
                category = str(raw_cat[0]) if raw_cat else 'Software'
            else:
                category = str(raw_cat or 'Software').strip()

        # Price
        price = 0.0
        if meta is not None:
            try:
                price = float(meta.get('price', 0) or 0)
            except Exception:
                price = 0.0

        # Description
        description = ''
        if meta is not None and desc_col:
            raw_desc = meta.get(desc_col, '')
            if isinstance(raw_desc, list):
                description = ' '.join(str(x) for x in raw_desc[:3])
            else:
                description = str(raw_desc or '')
            description = description[:1000]

        # Features
        features_list = []
        if meta is not None and features_col:
            raw_feat = meta.get(features_col, [])
            if isinstance(raw_feat, list):
                features_list = [str(f) for f in raw_feat[:10] if f]
            elif isinstance(raw_feat, str):
                features_list = [raw_feat[:200]]

        # Image
        image_url = ''
        if meta is not None:
            imgs = meta.get('images', meta.get('image', meta.get('imageURL', [])))
            if isinstance(imgs, list) and imgs:
                first = imgs[0]
                if isinstance(first, dict):
                    image_url = first.get('large', first.get('thumb', ''))
                else:
                    image_url = str(first)
            elif isinstance(imgs, str):
                image_url = imgs
        if not image_url:
            image_url = f"https://picsum.photos/seed/{asin}/300/200"

        p = Product(
            asin=str(asin),
            title=title[:300],
            description=description,
            category=category[:100],
            price=price,
            image_url=image_url[:500],
            features=json.dumps(features_list),
        )
        db_instance.session.add(p)
        db_instance.session.flush()
        product_map[str(asin)] = p

    print(f"[DONE] {len(product_map)} products inserted")

    # Insert ratings
    print(f"\n[INFO] Inserting ratings...")
    seen_pairs = set()
    rating_count = 0

    for _, row in df_reviews.iterrows():
        asin    = str(row.get('asin', '')).strip()
        user_id = str(row.get('user_id', '')).strip()

        p = product_map.get(asin)
        if not p:
            continue

        u = reviewer_to_user.get(user_id)
        if not u:
            continue

        pair = (u.id, p.id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        r = Rating(
            user_id=u.id,
            product_id=p.id,
            rating=float(row.get('rating', 5.0)),
            review_text=str(row.get('text', ''))[:2000],
            verified_purchase=bool(row.get('verified_purchase', False)),
            helpful_votes=int(row.get('helpful_vote', 0)),
        )
        db_instance.session.add(r)
        rating_count += 1

    db_instance.session.commit()
    print(f"[DONE] {rating_count} ratings inserted")

    # ── STEP 7: Compute trust scores (mirrors pipeline.py Step 5) ────────────
    print("\n[STEP 7] COMPUTING TRUST SCORES")
    total = len(product_map)

    for idx, (asin, prod_obj) in enumerate(product_map.items()):
        if idx % 200 == 0:
            print(f"  Trust scoring: {idx}/{total}")

        ratings_qs = Rating.query.filter_by(product_id=prod_obj.id).all()
        if not ratings_qs:
            continue

        raw = [r.rating for r in ratings_qs]
        prod_obj.avg_rating   = float(np.mean(raw))
        prod_obj.rating_count = len(raw)

        p_details = trust_engine.product_trust_score(prod_obj, ratings_qs, mean_price)

        # User trust: average across all reviewers of this product
        user_trusts = []
        for r in ratings_qs:
            u_ratings = Rating.query.filter_by(user_id=r.user_id).all()
            user_trusts.append(trust_engine.user_trust_score(u_ratings))
        u_trust = float(sum(user_trusts) / len(user_trusts)) if user_trusts else 0.5

        # Seller trust: same category products
        same_cat = Product.query.filter(
            Product.category == prod_obj.category,
            Product.id != prod_obj.id
        ).limit(20).all()
        seller_pairs = []
        for sp in same_cat:
            sp_r = Rating.query.filter_by(product_id=sp.id).all()
            if sp_r:
                seller_pairs.append((sp, sp_r))
        s_trust = trust_engine.seller_trust_score(seller_pairs, mean_price)

        final = 0.55 * p_details['product_trust'] + 0.35 * u_trust + 0.10 * s_trust

        prod_obj.product_trust     = round(p_details['product_trust'], 3)
        prod_obj.seller_trust      = round(s_trust, 3)
        prod_obj.final_trust_score = round(final, 3)
        prod_obj.avg_rating_norm   = round(p_details['avg_rating_norm'], 3)
        prod_obj.verified_ratio    = round(p_details['verified_ratio'], 3)
        prod_obj.review_confidence = round(p_details['review_confidence'], 3)
        prod_obj.text_quality      = round(p_details['text_quality'], 3)
        prod_obj.price_factor      = round(p_details['price_factor'], 3)
        prod_obj.title_similarity  = round(p_details['title_similarity'], 3)

        # Commit in batches of 500 to avoid memory issues
        if idx % 500 == 0:
            db_instance.session.commit()

    db_instance.session.commit()
    print(f"\n[SEED] ✓ Complete: {len(product_map)} products, {rating_count} ratings seeded from real dataset.")


# ── Fallback if no dataset files found ───────────────────────────────────────

def _seed_demo_fallback(db_instance):
    """Insert a small set of demo products if no JSONL files are present."""
    print("[SEED] Running demo fallback (no dataset files found)")
    from seed_demo import seed_demo_data
    seed_demo_data(db_instance)