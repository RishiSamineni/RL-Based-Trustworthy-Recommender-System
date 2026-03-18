from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from models import Product, Rating
from engine.recommendation_system import RecommendationEngine

rec_bp = Blueprint('recommendations', __name__)
_engine = RecommendationEngine()


def _build_data_structures():
    """Build the flat lists needed by the engine from the DB."""
    all_products = []
    for p in Product.query.all():
        import json
        try:
            features = json.loads(p.features) if p.features else []
        except Exception:
            features = []
        all_products.append({
            'asin': p.asin, 'title': p.title, 'category': p.category,
            'price': p.price, 'features': features,
            'avg_rating': p.avg_rating, 'rating_count': p.rating_count
        })

    all_ratings = []
    for r in Rating.query.all():
        p = Product.query.get(r.product_id)
        if p:
            all_ratings.append({
                'user_id': r.user_id,
                'product_asin': p.asin,
                'rating': r.rating
            })

    trust_map = {}
    for p in Product.query.all():
        trust_map[p.asin] = {
            'product_trust': p.product_trust,
            'user_trust': 0.5,
            'seller_trust': p.seller_trust,
            'final_trust_score': p.final_trust_score,
            'details': {
                'avg_rating_norm': p.avg_rating_norm,
                'verified_ratio': p.verified_ratio,
                'review_confidence': p.review_confidence,
                'text_quality': p.text_quality,
                'price_factor': p.price_factor,
                'title_similarity': p.title_similarity,
            }
        }
    return all_products, all_ratings, trust_map


@rec_bp.route('/similar/<string:asin>', methods=['GET'])
def similar_products(asin):
    """
    GET /api/recommendations/similar/<asin>
    Returns hybrid (collaborative + content) trustworthy recommendations.
    Mirrors RecommendationEngine.get_recommendations_with_info.
    """
    min_trust = float(request.args.get('min_trust', 0.4))
    top_n = int(request.args.get('top_n', 10))
    collab_w = float(request.args.get('collab_w', 0.6))
    content_w = float(request.args.get('content_w', 0.4))

    all_products, all_ratings, trust_map = _build_data_structures()

    result = _engine.get_recommendations(
        asin, all_ratings, all_products, trust_map,
        min_trust=min_trust, top_n=top_n,
        collab_w=collab_w, content_w=content_w
    )
    if result is None:
        return jsonify({'error': f'Product {asin} not found'}), 404

    # Enrich recommendations with DB product data
    enriched_recs = []
    for rec in result['recommendations']:
        p = Product.query.filter_by(asin=rec['asin']).first()
        if p:
            enriched_recs.append({
                'product': p.to_dict(),
                'similarity': rec['similarity'],
                'final_score': rec['final_score'],
                'method_breakdown': rec['method_breakdown'],
                'explanation': rec['explanation']
            })

    target_p = Product.query.filter_by(asin=asin).first()
    return jsonify({
        'target_product': target_p.to_dict() if target_p else result['target_product'],
        'target_trust': result['target_trust'],
        'recommendations': enriched_recs,
        'total_found': len(enriched_recs),
        'algorithm_config': {'collab_weight': collab_w, 'content_weight': content_w, 'min_trust': min_trust}
    })


@rec_bp.route('/for-you', methods=['GET'])
@jwt_required()
def for_you():
    """
    Personalised recommendations for the logged-in user.
    Uses the user's highest-rated product as seed, then applies hybrid filtering.
    """
    user_id = int(get_jwt_identity())
    top_n = int(request.args.get('top_n', 10))
    min_trust = float(request.args.get('min_trust', 0.4))

    # Find user's best-rated product as seed
    user_ratings = (Rating.query
                    .filter_by(user_id=user_id)
                    .order_by(Rating.rating.desc())
                    .limit(3).all())

    if not user_ratings:
        # Fall back to globally trusted products
        products = (Product.query
                    .filter(Product.final_trust_score >= min_trust)
                    .order_by(Product.final_trust_score.desc())
                    .limit(top_n).all())
        return jsonify({
            'recommendations': [{'product': p.to_dict(), 'final_score': p.final_trust_score,
                                  'similarity': 1.0, 'method_breakdown': {'collaborative': 0, 'content': 0},
                                  'explanation': 'Top trusted product in our catalogue'} for p in products],
            'seed_asin': None,
            'total_found': len(products)
        })

    all_products, all_ratings, trust_map = _build_data_structures()

    # Aggregate recommendations from top 3 rated products
    seen_asins = {Product.query.get(r.product_id).asin for r in user_ratings if Product.query.get(r.product_id)}
    aggregated = {}

    for ur in user_ratings:
        seed_p = Product.query.get(ur.product_id)
        if not seed_p:
            continue
        result = _engine.get_recommendations(
            seed_p.asin, all_ratings, all_products, trust_map,
            min_trust=min_trust, top_n=top_n * 2
        )
        if result:
            for rec in result['recommendations']:
                a = rec['asin']
                if a not in seen_asins:
                    if a not in aggregated or rec['final_score'] > aggregated[a]['final_score']:
                        aggregated[a] = rec

    final = sorted(aggregated.values(), key=lambda x: x['final_score'], reverse=True)[:top_n]

    enriched = []
    for rec in final:
        p = Product.query.filter_by(asin=rec['asin']).first()
        if p:
            enriched.append({
                'product': p.to_dict(),
                'similarity': rec['similarity'],
                'final_score': rec['final_score'],
                'method_breakdown': rec['method_breakdown'],
                'explanation': rec['explanation']
            })

    seed_asin = Product.query.get(user_ratings[0].product_id).asin if user_ratings else None
    return jsonify({
        'recommendations': enriched,
        'seed_asin': seed_asin,
        'total_found': len(enriched)
    })


@rec_bp.route('/trust-check/<string:asin>', methods=['GET'])
def trust_check(asin):
    """
    Returns full trust breakdown for a single product.
    Mirrors display_product_recommendation from recommendation_display.py.
    """
    p = Product.query.filter_by(asin=asin).first_or_404()
    threshold = float(request.args.get('threshold', 0.5))
    trust_score = p.final_trust_score
    is_trustworthy = trust_score > threshold

    return jsonify({
        'asin': asin,
        'product': p.to_dict(),
        'trust_breakdown': {
            'product_trust': p.product_trust,
            'seller_trust': p.seller_trust,
            'final_trust_score': p.final_trust_score,
            'details': {
                'avg_rating_norm': p.avg_rating_norm,
                'verified_ratio': p.verified_ratio,
                'review_confidence': p.review_confidence,
                'text_quality': p.text_quality,
                'price_factor': p.price_factor,
                'title_similarity': p.title_similarity,
            }
        },
        'rl_decision': {
            'threshold': threshold,
            'is_trustworthy': is_trustworthy,
            'verdict': 'TRUSTWORTHY' if is_trustworthy else 'RISKY',
            'reason': (
                f"Trust score ({trust_score:.3f}) {'exceeds' if is_trustworthy else 'is below'} "
                f"threshold ({threshold:.3f})"
            )
        }
    })


@rec_bp.route('/batch-check', methods=['POST'])
def batch_check():
    """
    Mirrors display_batch_recommendations.
    Body: { "asins": [...], "threshold": 0.5 }
    """
    data = request.get_json()
    asins = data.get('asins', [])
    threshold = float(data.get('threshold', 0.5))

    results = []
    for asin in asins:
        p = Product.query.filter_by(asin=asin).first()
        if not p:
            continue
        is_trustworthy = p.final_trust_score > threshold
        results.append({
            'asin': asin,
            'title': p.title,
            'trust_data': {
                'product_trust': p.product_trust,
                'seller_trust': p.seller_trust,
                'final_trust_score': p.final_trust_score,
            },
            'threshold': threshold,
            'decision': is_trustworthy,
            'verdict': 'TRUSTWORTHY' if is_trustworthy else 'RISKY'
        })

    trustworthy_count = sum(1 for r in results if r['decision'])
    avg_trust = sum(r['trust_data']['final_trust_score'] for r in results) / len(results) if results else 0

    return jsonify({
        'results': results,
        'summary': {
            'total': len(results),
            'trustworthy': trustworthy_count,
            'risky': len(results) - trustworthy_count,
            'avg_trust': round(avg_trust, 3),
            'threshold': threshold
        }
    })