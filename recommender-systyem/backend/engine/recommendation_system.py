"""
Recommendation engine — faithful port of RecommendationEngine from recommendation_engine.py.
Uses SimilarityEngine + TrustEngine to produce trustworthy ranked recommendations.
"""
from engine.similarity_engine import SimilarityEngine
from engine.trust_engine import TrustEngine


class RecommendationEngine:
    """
    Mirrors RecommendationEngine.get_similar_trustworthy_products and
    explain_recommendation exactly.
    """

    def __init__(self):
        self.sim_engine = SimilarityEngine()
        self.trust_engine = TrustEngine()

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT (mirrors get_recommendations_with_info)
    # ------------------------------------------------------------------
    def get_recommendations(self, target_asin, all_ratings, all_products,
                             trust_map, min_trust=0.4, top_n=10,
                             collab_w=0.6, content_w=0.4):
        """
        target_asin   : str ASIN of the seed product
        all_ratings   : list of {'user_id', 'product_asin', 'rating'} dicts
        all_products  : list of product dicts with asin/title/category/price/features
        trust_map     : dict  asin -> trust result dict (pre-computed or live)
        min_trust     : float minimum final_trust_score to include in results
        top_n         : int max results to return
        Returns       : {'target_product', 'recommendations', 'total_found'}
        """
        target_info = next((p for p in all_products if p['asin'] == target_asin), None)
        if not target_info:
            return None

        candidates = self.sim_engine.calculate_hybrid_similarity(
            target_asin, all_ratings, all_products,
            top_n=100, collab_w=collab_w, content_w=content_w
        )

        results = []
        for asin, similarity, method_breakdown in candidates:
            trust_data = trust_map.get(asin)
            if trust_data is None:
                continue
            if trust_data['final_trust_score'] < min_trust:
                continue

            final_score = similarity * trust_data['final_trust_score']
            product_info = next((p for p in all_products if p['asin'] == asin), None)

            results.append({
                'asin': asin,
                'similarity': round(similarity, 4),
                'trust_data': trust_data,
                'final_score': round(final_score, 4),
                'method_breakdown': method_breakdown,
                'product_info': product_info,
                'explanation': self.explain_recommendation(
                    target_asin, asin, similarity, trust_data, method_breakdown
                )
            })

        results.sort(key=lambda x: x['final_score'], reverse=True)
        results = results[:top_n]

        target_trust = trust_map.get(target_asin, {})

        return {
            'target_product': target_info,
            'target_trust': target_trust,
            'recommendations': results,
            'total_found': len(results)
        }

    # ------------------------------------------------------------------
    # EXPLANATION  (mirrors explain_recommendation)
    # ------------------------------------------------------------------
    def explain_recommendation(self, target_asin, rec_asin, similarity,
                                trust_data, method_breakdown):
        """
        Returns human-readable explanation string, same structure as original.
        """
        parts = []
        cs = method_breakdown.get('collaborative', 0.0)
        co = method_breakdown.get('content', 0.0)

        parts.append(f"Overall similarity: {similarity:.1%}")

        if cs > 0:
            parts.append(f"  • {cs:.1%} based on user co-review patterns "
                         f"(users who rated {target_asin} also rated this)")
        if co > 0:
            parts.append(f"  • {co:.1%} based on product features "
                         f"(category, title, price, features)")

        parts.append(f"Trust score: {trust_data['final_trust_score']:.3f}")
        parts.append(f"  • Product trust: {trust_data['product_trust']:.3f}")
        parts.append(f"  • Seller trust:  {trust_data['seller_trust']:.3f}")

        details = trust_data.get('details', {})
        if details:
            parts.append(f"  • Verified purchase ratio: "
                         f"{details.get('verified_ratio', 0):.1%}")
            parts.append(f"  • Review confidence:       "
                         f"{details.get('review_confidence', 0):.3f}")

        return '\n'.join(parts)

    def invalidate_cache(self, asin=None):
        self.sim_engine.invalidate_cache(asin)