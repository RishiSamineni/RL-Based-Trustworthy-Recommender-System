"""
Trust scoring engine — faithful port of TrustworthyRecommender from trust_model.py.
Works on the SQLAlchemy models instead of raw DataFrames so the web API can use it.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TrustEngine:
    """
    Computes product_trust, user_trust, seller_trust and final_trust_score
    exactly as defined in the original TrustworthyRecommender class.
    """

    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=500, stop_words='english')

    # ------------------------------------------------------------------
    # USER TRUST  (mirrors user_trust_score)
    # ------------------------------------------------------------------
    def user_trust_score(self, ratings_qs):
        """
        ratings_qs : list of Rating ORM objects for one user
        Returns float in [0, 1]
        """
        if not ratings_qs:
            return 0.5

        verified_flags = [r.verified_purchase for r in ratings_qs]
        v_ratio = sum(verified_flags) / len(verified_flags)

        helpful = [r.helpful_votes for r in ratings_qs]
        h_mean = np.mean(helpful) if helpful else 0.0
        h_ratio = h_mean / max(h_mean + 1, 1)

        raw_ratings = [r.rating for r in ratings_qs]
        rating_std = float(np.std(raw_ratings)) if len(raw_ratings) > 1 else 0.0
        c_rating = 1 - (rating_std / 2.0)

        text_lens = [len(r.review_text or '') for r in ratings_qs]
        median_len = float(np.median(text_lens)) if text_lens else 1.0
        mean_len = float(np.mean(text_lens)) if text_lens else 0.0
        q_text = float(np.clip(mean_len / max(median_len, 10), 0, 1))

        score = 0.30 * v_ratio + 0.25 * h_ratio + 0.20 * c_rating + 0.25 * q_text
        return float(np.clip(score, 0.0, 1.0))

    # ------------------------------------------------------------------
    # PRODUCT TRUST  (mirrors product_trust_score with return_details=True)
    # ------------------------------------------------------------------
    def product_trust_score(self, product, ratings_qs, mean_price=None):
        """
        product     : Product ORM object
        ratings_qs  : list of Rating ORM objects for this product
        mean_price  : float, dataset-level mean price (optional)
        Returns dict with product_trust + intermediate features
        """
        if not ratings_qs:
            return {
                'product_trust': 0.0,
                'avg_rating_norm': 0.0,
                'verified_ratio': 0.0,
                'review_confidence': 0.0,
                'text_quality': 0.0,
                'price_factor': 1.0,
                'title_similarity': 0.0,
            }

        raw_ratings = [r.rating for r in ratings_qs]
        avg_rating = float(np.mean(raw_ratings))
        n = len(ratings_qs)

        verified_flags = [r.verified_purchase for r in ratings_qs]
        v_share = sum(verified_flags) / n

        rn_conf = 1 - np.exp(-n / 1000.0)

        text_lens = [len(r.review_text or '') for r in ratings_qs]
        text_quality = float(np.clip(np.mean(text_lens) / 500.0, 0, 1))

        # Price abnormality
        price_factor = 1.0
        try:
            if mean_price and product.price and product.price > 0:
                diff = abs(product.price - mean_price) / float(mean_price)
                price_factor = 1.0 - min(diff, 1.0)
        except Exception:
            price_factor = 1.0

        # Title ↔ review TF-IDF similarity
        title_sim = 0.0
        try:
            title = product.title or ''
            texts = [title] + [r.review_text or '' for r in ratings_qs if r.review_text]
            if len(texts) > 1:
                mat = self.tfidf.fit_transform(texts)
                sims = cosine_similarity(mat[0:1], mat[1:])
                title_sim = float(sims.mean())
        except Exception:
            title_sim = 0.0

        p_trust = (
            0.35 * (avg_rating / 5.0) +
            0.20 * rn_conf +
            0.15 * v_share +
            0.15 * price_factor +
            0.15 * title_sim
        )
        p_trust = float(np.clip(p_trust, 0, 1))

        return {
            'product_trust': p_trust,
            'avg_rating_norm': avg_rating / 5.0,
            'verified_ratio': v_share,
            'review_confidence': rn_conf,
            'text_quality': text_quality,
            'price_factor': price_factor,
            'title_similarity': title_sim,
        }

    # ------------------------------------------------------------------
    # SELLER TRUST  (mirrors seller_trust_score)
    # ------------------------------------------------------------------
    def seller_trust_score(self, category_products_ratings, mean_price=None):
        """
        category_products_ratings : list of (Product, [Rating, ...]) for
                                    all products in the same category/seller
        """
        if not category_products_ratings:
            return 0.5
        scores = []
        for prod, ratings in category_products_ratings:
            d = self.product_trust_score(prod, ratings, mean_price)
            scores.append(d['product_trust'])
        return float(np.nanmean(scores)) if scores else 0.5

    # ------------------------------------------------------------------
    # FINAL COMBINED SCORE  (mirrors final_product_score)
    # ------------------------------------------------------------------
    def final_product_score(self, product, ratings_qs, user_ratings_qs=None,
                             seller_products_ratings=None, mean_price=None):
        """
        Returns dict: product_trust, user_trust, seller_trust, final_trust_score, details
        Weights: 0.55 * product + 0.35 * user + 0.10 * seller  (same as original)
        """
        p_details = self.product_trust_score(product, ratings_qs, mean_price)
        p_trust = p_details['product_trust']

        u_trust = self.user_trust_score(user_ratings_qs) if user_ratings_qs else 0.5
        s_trust = self.seller_trust_score(seller_products_ratings or [], mean_price)

        final = 0.55 * p_trust + 0.35 * u_trust + 0.10 * s_trust

        return {
            'product_trust': round(p_trust, 3),
            'user_trust': round(u_trust, 3),
            'seller_trust': round(s_trust, 3),
            'final_trust_score': round(float(final), 3),
            'details': {k: round(v, 3) for k, v in p_details.items() if k != 'product_trust'}
        }