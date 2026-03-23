"""
Product similarity engine — faithful port of ProductSimilarity from product_similarity.py.
Implements collaborative filtering, content-based filtering, and hybrid combination.
"""
import math
from collections import defaultdict


def _mean(arr):
    return float(sum(arr) / len(arr)) if arr else 0.0


def _jaccard_similarity(a, b):
    set_a = set(str(a).lower().split())
    set_b = set(str(b).lower().split())
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return float(inter / union) if union else 0.0


class SimilarityEngine:
    """
    Mirrors ProductSimilarity:
      - calculate_collaborative_similarity  (co-review patterns)
      - calculate_content_similarity        (TF-IDF on title/category/price/features)
      - calculate_hybrid_similarity         (weighted combination)
    All methods operate on plain Python dicts so they work with both
    the seeded in-memory data and live DB queries.
    """

    def __init__(self):
        self._collab_cache = {}
        self._content_cache = {}

    # ------------------------------------------------------------------
    # COLLABORATIVE FILTERING  (co-review patterns)
    # ------------------------------------------------------------------
    def calculate_collaborative_similarity(self, target_asin, all_ratings, top_n=50):
        """
        all_ratings : list of dicts  {'user_id', 'product_asin', 'rating'}
        Returns list of (asin, score) sorted desc.
        Mirrors original algorithm exactly.
        """
        if target_asin in self._collab_cache:
            return self._collab_cache[target_asin][:top_n]

        target_users = {r['user_id'] for r in all_ratings if r['product_asin'] == target_asin}
        if not target_users:
            return []

        target_ratings = [r for r in all_ratings if r['product_asin'] == target_asin]
        target_avg = np.mean([r['rating'] for r in target_ratings])

        product_data = defaultdict(lambda: {'count': 0, 'ratings': []})
        for r in all_ratings:
            if r['user_id'] in target_users and r['product_asin'] != target_asin:
                product_data[r['product_asin']]['count'] += 1
                product_data[r['product_asin']]['ratings'].append(r['rating'])

        similarities = []
        for asin, data in product_data.items():
            if data['count'] < 1:
                continue
            freq_score = min(data['count'] / len(target_users), 1.0)
            avg_r = _mean(data['ratings'])

            rating_sim = 1 - abs(target_avg - avg_r) / 5.0
            sim = 0.7 * freq_score + 0.3 * rating_sim
            similarities.append((asin, float(sim)))

        similarities.sort(key=lambda x: x[1], reverse=True)
        self._collab_cache[target_asin] = similarities
        return similarities[:top_n]

    # ------------------------------------------------------------------
    # CONTENT-BASED FILTERING
    # ------------------------------------------------------------------
    def calculate_content_similarity(self, target_asin, all_products, top_n=50):
        """
        all_products : list of dicts with keys: asin, title, category, price, features
        Returns list of (asin, score) sorted desc.
        Mirrors original _calculate_* helpers.
        """
        if target_asin in self._content_cache:
            return self._content_cache[target_asin][:top_n]

        target = next((p for p in all_products if p['asin'] == target_asin), None)
        if not target:
            return []

        similarities = []
        for p in all_products:
            if p['asin'] == target_asin:
                continue

            cat_sim   = self._category_similarity(target, p)
            title_sim = self._title_similarity(target, p)
            price_sim = self._price_similarity(target, p)
            feat_sim  = self._feature_similarity(target, p)

            score = 0.40 * cat_sim + 0.30 * title_sim + 0.20 * price_sim + 0.10 * feat_sim
            similarities.append((p['asin'], float(score)))

        similarities.sort(key=lambda x: x[1], reverse=True)
        self._content_cache[target_asin] = similarities
        return similarities[:top_n]

    def _category_similarity(self, p1, p2):
        c1, c2 = str(p1.get('category', '') or ''), str(p2.get('category', '') or '')
        if not c1 or not c2:
            return 0.5
        if c1 == c2:
            return 1.0
        if c1.lower() in c2.lower() or c2.lower() in c1.lower():
            return 0.7
        return 0.0

    def _title_similarity(self, p1, p2):
        t1, t2 = str(p1.get('title', '') or ''), str(p2.get('title', '') or '')
        if not t1 or not t2:
            return 0.0
        try:
            return _jaccard_similarity(t1, t2)
        except Exception:
            return 0.0

    def _price_similarity(self, p1, p2):
        try:
            pr1, pr2 = float(p1.get('price', 0) or 0), float(p2.get('price', 0) or 0)
            if pr1 == 0 or pr2 == 0:
                return 0.5
            diff = abs(pr1 - pr2) / max(pr1, pr2)
            return 1.0 - min(diff, 1.0)
        except Exception:
            return 0.5

    def _feature_similarity(self, p1, p2):
        try:
            f1 = set(str(x).lower() for x in (p1.get('features') or []))
            f2 = set(str(x).lower() for x in (p2.get('features') or []))
            if not f1 or not f2:
                return 0.5
            inter = len(f1 & f2)
            union = len(f1 | f2)
            return inter / union if union > 0 else 0.0
        except Exception:
            return 0.5

    # ------------------------------------------------------------------
    # HYBRID  (mirrors calculate_hybrid_similarity)
    # ------------------------------------------------------------------
    def calculate_hybrid_similarity(self, target_asin, all_ratings, all_products,
                                     top_n=50, collab_w=0.6, content_w=0.4):
        """
        Returns list of (asin, hybrid_score, {'collaborative': ..., 'content': ...})
        Mirrors original exactly.
        """
        collab = dict(self.calculate_collaborative_similarity(target_asin, all_ratings, 100))
        content = dict(self.calculate_content_similarity(target_asin, all_products, 100))

        all_asins = set(collab) | set(content)
        results = []
        for asin in all_asins:
            cs = collab.get(asin, 0.0)
            co = content.get(asin, 0.0)
            hybrid = collab_w * cs + content_w * co
            results.append((asin, float(hybrid), {'collaborative': cs, 'content': co}))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def invalidate_cache(self, asin=None):
        if asin:
            self._collab_cache.pop(asin, None)
            self._content_cache.pop(asin, None)
        else:
            self._collab_cache.clear()
            self._content_cache.clear()