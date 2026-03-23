from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Product, Rating
import math

ratings_bp = Blueprint('ratings', __name__)


def _recompute_trust(product):
    """Recompute product trust scores after a new rating using TrustEngine."""
    from engine.trust_engine import TrustEngine
    from seed import PRODUCTS_DATA

    trust_engine = TrustEngine()
    ratings_qs = Rating.query.filter_by(product_id=product.id).all()
    if not ratings_qs:
        return

    mean_price = float(np.mean([p['price'] for p in PRODUCTS_DATA]))
    p_details = trust_engine.product_trust_score(product, ratings_qs, mean_price)

    user_trusts = []
    for r in ratings_qs:
        u_ratings = Rating.query.filter_by(user_id=r.user_id).all()
        user_trusts.append(trust_engine.user_trust_score(u_ratings))
    u_trust = float(np.mean(user_trusts)) if user_trusts else 0.5

    # Seller trust: same category
    same_cat = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).all()
    seller_pairs = []
    for sp in same_cat:
        sp_r = Rating.query.filter_by(product_id=sp.id).all()
        if sp_r:
            seller_pairs.append((sp, sp_r))
    s_trust = trust_engine.seller_trust_score(seller_pairs, mean_price)

    final = 0.55 * p_details['product_trust'] + 0.35 * u_trust + 0.10 * s_trust

    raw = [r.rating for r in ratings_qs]
    product.avg_rating = float(np.mean(raw))
    product.rating_count = len(raw)
    product.product_trust     = round(p_details['product_trust'], 3)
    product.seller_trust      = round(s_trust, 3)
    product.final_trust_score = round(final, 3)
    product.avg_rating_norm   = round(p_details['avg_rating_norm'], 3)
    product.verified_ratio    = round(p_details['verified_ratio'], 3)
    product.review_confidence = round(p_details['review_confidence'], 3)
    product.text_quality      = round(p_details['text_quality'], 3)
    product.price_factor      = round(p_details['price_factor'], 3)
    product.title_similarity  = round(p_details['title_similarity'], 3)


@ratings_bp.route('/', methods=['POST'])
@jwt_required()
def submit_rating():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    product_id = data.get('product_id')
    rating_val = float(data.get('rating', 0))
    review_text = data.get('review_text', '')

    if not product_id or not (1.0 <= rating_val <= 5.0):
        return jsonify({'error': 'Invalid data'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    existing = Rating.query.filter_by(user_id=user_id, product_id=product_id).first()
    if existing:
        existing.rating = rating_val
        existing.review_text = review_text
        existing.verified_purchase = True
    else:
        r = Rating(
            user_id=user_id, product_id=product_id,
            rating=rating_val, review_text=review_text,
            verified_purchase=True, helpful_votes=0
        )
        db.session.add(r)

    db.session.flush()
    _recompute_trust(product)
    db.session.commit()

    # Invalidate similarity cache
    from engine.similarity_engine import SimilarityEngine
    SimilarityEngine().invalidate_cache()

    return jsonify({'message': 'Rating saved', 'product': product.to_dict()})


@ratings_bp.route('/my', methods=['GET'])
@jwt_required()
def my_ratings():
    user_id = int(get_jwt_identity())
    ratings = Rating.query.filter_by(user_id=user_id).all()
    result = []
    for r in ratings:
        d = r.to_dict()
        p = Product.query.get(r.product_id)
        if p:
            d['product_title'] = p.title
            d['product_asin'] = p.asin
        result.append(d)
    return jsonify(result)