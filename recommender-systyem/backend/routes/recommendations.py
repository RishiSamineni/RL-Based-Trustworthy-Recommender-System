"""
routes/recommendations.py
Flask Blueprint that exposes the recommendation + trust engine via REST API.

Endpoints
---------
GET  /api/recommendations/<asin>          — get top-N similar trustworthy products
GET  /api/trust/<asin>                    — get trust breakdown for one product
GET  /api/products                        — list all products (paginated)
POST /api/recommendations/batch           — trust-check a list of ASINs

All heavy logic lives in engine/; this file only handles HTTP + ORM queries.
"""
from flask import Blueprint, jsonify, request, current_app
from extensions import db
from models import Product, Rating

from engine.recommendation_system import RecommendationEngine
from engine.trust_engine import TrustEngine

recommendations_bp = Blueprint('recommendations', __name__)

# Module-level singletons (created once per worker process)
_rec_engine   = RecommendationEngine()
_trust_engine = TrustEngine()


# ── helpers ───────────────────────────────────────────────────────────────────

def _product_to_dict(p: Product) -> dict:
    """Convert a Product ORM object to the dict format the engine expects."""
    features = []
    if p.features:
        try:
            import json
            features = json.loads(p.features) if isinstance(p.features, str) else p.features
        except Exception:
            features = []
    return {
        'asin':     p.asin,
        'title':    p.title     or '',
        'category': p.category  or '',
        'price':    float(p.price or 0.0),
        'features': features,
    }


def _rating_to_dict(r: Rating) -> dict:
    """Convert a Rating ORM object to the dict format the engine expects."""
    return {
        'user_id':      r.user_id,
        'product_asin': r.product_asin,
        'rating':       float(r.rating or 0.0),
    }


def _build_trust_map(product_asins: list, mean_price: float = None) -> dict:
    """
    Pre-compute trust scores for a list of ASINs.
    Returns dict: asin -> trust result dict.
    Mirrors the pipeline's Step 5 trust loop.
    """
    trust_map = {}
    for asin in product_asins:
        product = Product.query.filter_by(asin=asin).first()
        if not product:
            continue
        ratings_qs = Rating.query.filter_by(product_asin=asin).all()

        # User trust: use the first reviewer as representative sample
        user_ratings_qs = None
        if ratings_qs:
            sample_user     = ratings_qs[0].user_id
            user_ratings_qs = Rating.query.filter_by(user_id=sample_user).all()

        # Seller trust: all products in same category
        seller_products_ratings = []
        if product.category:
            peer_products = Product.query.filter_by(category=product.category).limit(50).all()
            for peer in peer_products:
                peer_ratings = Rating.query.filter_by(product_asin=peer.asin).all()
                seller_products_ratings.append((peer, peer_ratings))

        trust_map[asin] = _trust_engine.final_product_score(
            product,
            ratings_qs,
            user_ratings_qs=user_ratings_qs,
            seller_products_ratings=seller_products_ratings,
            mean_price=mean_price,
        )
    return trust_map


def _get_mean_price() -> float:
    """Dataset-level mean price (cached on app context to avoid recompute)."""
    if not hasattr(current_app, '_mean_price_cache'):
        from sqlalchemy import func
        result = db.session.query(func.avg(Product.price)).scalar()
        current_app._mean_price_cache = float(result) if result else None
    return current_app._mean_price_cache


# ── ROUTES ────────────────────────────────────────────────────────────────────

@recommendations_bp.route('/api/recommendations/<string:asin>', methods=['GET'])
def get_recommendations(asin: str):
    """
    GET /api/recommendations/<asin>?min_trust=0.4&top_n=10&collab_w=0.6&content_w=0.4

    Returns top-N similar trustworthy products for the given seed ASIN.
    """
    min_trust = float(request.args.get('min_trust',  0.4))
    top_n     = int(  request.args.get('top_n',      10))
    collab_w  = float(request.args.get('collab_w',   0.6))
    content_w = float(request.args.get('content_w',  0.4))

    # Validate seed product
    target_product = Product.query.filter_by(asin=asin).first()
    if not target_product:
        return jsonify({'error': f'Product {asin} not found'}), 404

    mean_price = _get_mean_price()

    # Load all products + ratings as plain dicts for the engine
    all_products = [_product_to_dict(p) for p in Product.query.all()]
    all_ratings  = [_rating_to_dict(r)  for r in Rating.query.all()]

    # Build trust map for all candidate ASINs
    all_asins = [p['asin'] for p in all_products]
    trust_map = _build_trust_map(all_asins, mean_price)

    result = _rec_engine.get_recommendations(
        target_asin  = asin,
        all_ratings  = all_ratings,
        all_products = all_products,
        trust_map    = trust_map,
        min_trust    = min_trust,
        top_n        = top_n,
        collab_w     = collab_w,
        content_w    = content_w,
    )

    if result is None:
        return jsonify({'error': f'Could not generate recommendations for {asin}'}), 404

    return jsonify(result)


@recommendations_bp.route('/api/trust/<string:asin>', methods=['GET'])
def get_trust(asin: str):
    """
    GET /api/trust/<asin>

    Returns full trust breakdown for a single product.
    """
    product = Product.query.filter_by(asin=asin).first()
    if not product:
        return jsonify({'error': f'Product {asin} not found'}), 404

    ratings_qs = Rating.query.filter_by(product_asin=asin).all()

    user_ratings_qs = None
    if ratings_qs:
        sample_user     = ratings_qs[0].user_id
        user_ratings_qs = Rating.query.filter_by(user_id=sample_user).all()

    seller_products_ratings = []
    if product.category:
        peer_products = Product.query.filter_by(category=product.category).limit(50).all()
        for peer in peer_products:
            peer_ratings = Rating.query.filter_by(product_asin=peer.asin).all()
            seller_products_ratings.append((peer, peer_ratings))

    mean_price = _get_mean_price()

    trust_data = _trust_engine.final_product_score(
        product,
        ratings_qs,
        user_ratings_qs=user_ratings_qs,
        seller_products_ratings=seller_products_ratings,
        mean_price=mean_price,
    )
    trust_data['asin'] = asin
    return jsonify(trust_data)


@recommendations_bp.route('/api/products', methods=['GET'])
def list_products():
    """
    GET /api/products?page=1&per_page=20

    Returns a paginated list of products with their trust scores.
    """
    page     = int(request.args.get('page',     1))
    per_page = int(request.args.get('per_page', 20))

    paginated = Product.query.paginate(page=page, per_page=per_page, error_out=False)
    mean_price = _get_mean_price()

    items = []
    for product in paginated.items:
        ratings_qs = Rating.query.filter_by(product_asin=product.asin).all()
        trust_data = _trust_engine.final_product_score(
            product, ratings_qs, mean_price=mean_price
        )
        items.append({
            **_product_to_dict(product),
            'trust': trust_data,
        })

    return jsonify({
        'products':   items,
        'total':      paginated.total,
        'page':       page,
        'per_page':   per_page,
        'pages':      paginated.pages,
    })


@recommendations_bp.route('/api/recommendations/batch', methods=['POST'])
def batch_trust_check():
    """
    POST /api/recommendations/batch
    Body: {"asins": ["B001", "B002", ...], "threshold": 0.5}

    Returns trust verdict for each ASIN — mirrors display_batch_recommendations().
    """
    body      = request.get_json(force=True) or {}
    asins     = body.get('asins', [])
    threshold = float(body.get('threshold', 0.5))

    if not asins:
        return jsonify({'error': 'No ASINs provided'}), 400

    mean_price = _get_mean_price()
    results    = []

    for asin in asins:
        product = Product.query.filter_by(asin=asin).first()
        if not product:
            results.append({'asin': asin, 'error': 'Not found'})
            continue

        ratings_qs = Rating.query.filter_by(product_asin=asin).all()
        trust_data = _trust_engine.final_product_score(
            product, ratings_qs, mean_price=mean_price
        )
        decision = trust_data['final_trust_score'] >= threshold

        results.append({
            'asin':       asin,
            'trust_data': trust_data,
            'threshold':  threshold,
            'decision':   decision,
            'verdict':    'TRUSTWORTHY' if decision else 'RISKY',
        })

    # Summary stats (mirrors display_batch_recommendations)
    decided   = [r for r in results if 'decision' in r]
    n         = len(decided)
    n_trust   = sum(1 for r in decided if r['decision'])
    avg_trust = (
        sum(r['trust_data']['final_trust_score'] for r in decided) / n
        if n else 0.0
    )

    return jsonify({
        'results': results,
        'summary': {
            'total':            len(results),
            'trustworthy':      n_trust,
            'risky':            n - n_trust,
            'avg_trust_score':  round(avg_trust, 3),
        }
    })
