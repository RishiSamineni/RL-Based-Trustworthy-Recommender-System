from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from models import Product, Rating
from extensions import db
import json

items_bp = Blueprint('items', __name__)


def _product_with_user_rating(product, user_id=None):
    d = product.to_dict()
    if user_id:
        ur = Rating.query.filter_by(user_id=user_id, product_id=product.id).first()
        d['user_rating'] = ur.rating if ur else None
    return d


@items_bp.route('/', methods=['GET'])
def list_products():
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        from flask_jwt_extended import get_jwt_identity
        uid = get_jwt_identity()
        user_id = int(uid) if uid else None
    except Exception:
        pass

    category = request.args.get('category')
    search = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'trust')         # trust | rating | price
    min_trust = float(request.args.get('min_trust', 0))
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 12))

    q = Product.query
    if category:
        q = q.filter_by(category=category)
    if search:
        q = q.filter(Product.title.ilike(f'%{search}%'))
    if min_trust > 0:
        q = q.filter(Product.final_trust_score >= min_trust)

    if sort == 'trust':
        q = q.order_by(Product.final_trust_score.desc())
    elif sort == 'rating':
        q = q.order_by(Product.avg_rating.desc())
    elif sort == 'price_asc':
        q = q.order_by(Product.price.asc())
    elif sort == 'price_desc':
        q = q.order_by(Product.price.desc())

    paginated = q.paginate(page=page, per_page=per_page, error_out=False)
    items = [_product_with_user_rating(p, user_id) for p in paginated.items]

    return jsonify({
        'products': items,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'categories': _get_categories()
    })


@items_bp.route('/<int:pid>', methods=['GET'])
def get_product(pid):
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        from flask_jwt_extended import get_jwt_identity
        uid = get_jwt_identity()
        user_id = int(uid) if uid else None
    except Exception:
        pass

    p = Product.query.get_or_404(pid)
    d = _product_with_user_rating(p, user_id)

    # Add parsed features list
    try:
        d['features_list'] = json.loads(p.features) if p.features else []
    except Exception:
        d['features_list'] = []

    # Add recent reviews
    reviews = Rating.query.filter_by(product_id=pid).order_by(Rating.timestamp.desc()).limit(5).all()
    d['reviews'] = []
    for r in reviews:
        from models import User
        u = User.query.get(r.user_id)
        d['reviews'].append({
            'username': u.username if u else 'Unknown',
            'rating': r.rating,
            'text': r.review_text,
            'verified': r.verified_purchase,
            'helpful_votes': r.helpful_votes,
            'timestamp': r.timestamp.isoformat()
        })
    return jsonify(d)


@items_bp.route('/<int:pid>/asin', methods=['GET'])
def get_by_asin(pid):
    """Get product by ASIN (pid is actually string asin here)"""
    pass


@items_bp.route('/asin/<string:asin>', methods=['GET'])
def get_product_by_asin(asin):
    p = Product.query.filter_by(asin=asin).first_or_404()
    return jsonify(p.to_dict())


def _get_categories():
    from sqlalchemy import distinct
    cats = db.session.query(distinct(Product.category)).all()
    return sorted([c[0] for c in cats if c[0]])