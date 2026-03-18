from flask import Blueprint, jsonify
from models import Product, Rating, User
from extensions import db
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/overview', methods=['GET'])
def overview():
    total_products = Product.query.count()
    total_users = User.query.count()
    total_ratings = Rating.query.count()

    avg_trust = db.session.query(func.avg(Product.final_trust_score)).scalar() or 0
    avg_rating = db.session.query(func.avg(Product.avg_rating)).scalar() or 0

    trustworthy = Product.query.filter(Product.final_trust_score >= 0.5).count()
    risky = total_products - trustworthy

    return jsonify({
        'total_products': total_products,
        'total_users': total_users,
        'total_ratings': total_ratings,
        'avg_trust_score': round(float(avg_trust), 3),
        'avg_product_rating': round(float(avg_rating), 2),
        'trustworthy_products': trustworthy,
        'risky_products': risky,
        'trust_rate': round(trustworthy / total_products * 100, 1) if total_products else 0
    })


@analytics_bp.route('/trust-distribution', methods=['GET'])
def trust_distribution():
    buckets = {'0.0-0.2': 0, '0.2-0.4': 0, '0.4-0.6': 0, '0.6-0.8': 0, '0.8-1.0': 0}
    for p in Product.query.all():
        s = p.final_trust_score
        if s < 0.2:   buckets['0.0-0.2'] += 1
        elif s < 0.4: buckets['0.2-0.4'] += 1
        elif s < 0.6: buckets['0.4-0.6'] += 1
        elif s < 0.8: buckets['0.6-0.8'] += 1
        else:         buckets['0.8-1.0'] += 1
    return jsonify(buckets)


@analytics_bp.route('/top-trusted', methods=['GET'])
def top_trusted():
    products = (Product.query
                .filter(Product.rating_count > 0)
                .order_by(Product.final_trust_score.desc())
                .limit(5).all())
    return jsonify([{
        'asin': p.asin, 'title': p.title[:60],
        'final_trust_score': p.final_trust_score,
        'category': p.category
    } for p in products])


@analytics_bp.route('/category-stats', methods=['GET'])
def category_stats():
    from sqlalchemy import distinct
    cats = db.session.query(distinct(Product.category)).all()
    result = []
    for (cat,) in cats:
        if not cat:
            continue
        ps = Product.query.filter_by(category=cat).all()
        if ps:
            avg_t = sum(p.final_trust_score for p in ps) / len(ps)
            avg_r = sum(p.avg_rating for p in ps) / len(ps)
            result.append({
                'category': cat,
                'product_count': len(ps),
                'avg_trust': round(avg_t, 3),
                'avg_rating': round(avg_r, 2)
            })
    result.sort(key=lambda x: x['avg_trust'], reverse=True)
    return jsonify(result)