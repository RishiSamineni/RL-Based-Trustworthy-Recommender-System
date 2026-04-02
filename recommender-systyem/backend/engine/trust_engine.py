# backend/engine/trust_engine.py
"""
Trust scoring engine.
Computes product, user and seller trust scores from review + metadata DataFrames.
This is a cleaned-up, self-contained copy of trust_model.py that lives inside
the engine/ package so imports never need to go outside the package.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TrustEngine:
    """
    Multi-dimensional trust scoring for products, users and sellers.

    Weights (product trust):
        avg_rating      35 %
        review_volume   20 %
        verified_ratio  15 %
        price_normalcy  15 %
        title_relevance 15 %

    Final score:
        product_trust  55 %
        user_trust     35 %
        seller_trust   10 %
    """

    def __init__(self):
        self.tfidf       = TfidfVectorizer(max_features=1000, stop_words="english")
        self.mean_price  = None   # set by pipeline after loading data
        self.title_col   = None   # e.g. "title"
        self.seller_col  = None   # e.g. "store"

    # ── user trust ────────────────────────────────────────────────────────────
    def user_trust_score(self, df_reviews: pd.DataFrame, user_id) -> float:
        uid_col = (
            "user_id"    if "user_id"    in df_reviews.columns else
            "reviewerID" if "reviewerID" in df_reviews.columns else None
        )
        if not uid_col:
            return 0.5

        ur = df_reviews[df_reviews[uid_col] == user_id]
        if ur.empty:
            return 0.5

        v_ratio = ur["verified_purchase"].mean() if "verified_purchase" in ur.columns else 0.5

        h_col = next((c for c in ("helpful_vote", "vote") if c in ur.columns), None)
        if h_col:
            h = pd.to_numeric(ur[h_col], errors="coerce").fillna(0)
            h_ratio = h.mean() / max((h + 1).mean(), 1)
        else:
            h_ratio = 0.0

        r_col = next((c for c in ("rating", "overall") if c in ur.columns), None)
        if r_col:
            ratings    = pd.to_numeric(ur[r_col], errors="coerce")
            rating_std = ratings.std()
            c_rating   = 1 - (rating_std / 2.0) if pd.notna(rating_std) else 1.0
        else:
            c_rating = 1.0

        text_len = ur.get("text", pd.Series(dtype=str)).fillna("").str.len()
        q_text   = float(np.clip(text_len.mean() / max(float(text_len.median()), 10), 0, 1))

        score = 0.30 * v_ratio + 0.25 * h_ratio + 0.20 * c_rating + 0.25 * q_text
        return float(np.clip(score, 0.0, 1.0))

    # ── product trust ─────────────────────────────────────────────────────────
    def product_trust_score(
        self,
        df_reviews: pd.DataFrame,
        df_products: pd.DataFrame,
        asin: str,
        return_details: bool = False,
    ):
        pr = df_reviews[df_reviews["asin"] == asin]
        if pr.empty:
            empty = {
                "product_trust":    0.0,
                "avg_rating_norm":  0.0,
                "verified_ratio":   0.0,
                "review_confidence":0.0,
                "text_quality":     0.0,
                "price_factor":     1.0,
                "title_similarity": 0.0,
            }
            return empty if return_details else 0.0

        r_col = next((c for c in ("rating", "overall") if c in pr.columns), None)
        ratings    = pd.to_numeric(pr[r_col], errors="coerce") if r_col else pd.Series([5.0] * len(pr))
        avg_rating = float(ratings.mean())
        rn_conf    = float(1 - np.exp(-len(pr) / 1000))

        v_share     = float(pr["verified_purchase"].mean()) if "verified_purchase" in pr.columns else 0.0
        text_quality = float(np.clip(pr["text"].fillna("").str.len().mean() / 500, 0, 1)) if "text" in pr.columns else 0.0

        # price normalcy
        price_factor = 1.0
        try:
            if self.mean_price and not df_products.empty:
                row = df_products[df_products["asin"] == asin]
                if not row.empty:
                    price = float(pd.to_numeric(row["price"].iloc[0], errors="coerce"))
                    if not np.isnan(self.mean_price) and self.mean_price > 0:
                        price_factor = float(1.0 - min(abs(price - self.mean_price) / self.mean_price, 1.0))
        except Exception:
            price_factor = 1.0

        # title-review cosine similarity
        title_sim = 0.0
        try:
            if self.title_col and self.title_col in df_products.columns:
                row = df_products[df_products["asin"] == asin]
                if not row.empty:
                    title = str(row[self.title_col].iloc[0])
                    texts = [title] + pr["text"].fillna("").astype(str).tolist()
                    if len(texts) > 1 and any(t.strip() for t in texts[1:]):
                        mat      = self.tfidf.fit_transform(texts)
                        title_sim = float(cosine_similarity(mat[0:1], mat[1:]).mean())
        except Exception:
            title_sim = 0.0

        p_trust = float(np.clip(
            0.35 * (avg_rating / 5.0) +
            0.20 * rn_conf +
            0.15 * v_share +
            0.15 * price_factor +
            0.15 * title_sim,
            0, 1,
        ))

        if return_details:
            return {
                "product_trust":    p_trust,
                "avg_rating_norm":  avg_rating / 5.0,
                "verified_ratio":   v_share,
                "review_confidence":rn_conf,
                "text_quality":     text_quality,
                "price_factor":     price_factor,
                "title_similarity": title_sim,
            }
        return p_trust

    # ── seller trust ──────────────────────────────────────────────────────────
    def seller_trust_score(
        self,
        df_reviews: pd.DataFrame,
        df_products: pd.DataFrame,
        asin: str,
    ) -> float:
        try:
            if not self.seller_col or self.seller_col not in df_products.columns:
                return 0.5
            row = df_products[df_products["asin"] == asin]
            if row.empty:
                return 0.5
            seller_id       = row[self.seller_col].iloc[0]
            seller_products = df_products[df_products[self.seller_col] == seller_id]["asin"].unique()
            scores = [
                self.product_trust_score(df_reviews, df_products, a)
                for a in seller_products
            ]
            return float(np.nanmean(scores)) if scores else 0.5
        except Exception:
            return 0.5

    # ── combined final score ──────────────────────────────────────────────────
    def final_product_score(
        self,
        df_reviews: pd.DataFrame,
        df_products: pd.DataFrame,
        asin: str,
        user_id=None,
        include_details: bool = False,
    ) -> dict:
        details_raw = self.product_trust_score(df_reviews, df_products, asin, return_details=True)
        p_trust     = details_raw["product_trust"]
        s_trust     = self.seller_trust_score(df_reviews, df_products, asin)
        u_trust     = self.user_trust_score(df_reviews, user_id) if user_id else 0.5

        final = round(0.55 * p_trust + 0.35 * u_trust + 0.10 * s_trust, 3)

        result = {
            "asin":              asin,
            "product_trust":     round(p_trust, 3),
            "user_trust":        round(u_trust, 3),
            "seller_trust":      round(s_trust, 3),
            "final_trust_score": final,
        }
        if include_details:
            result["details"] = {k: round(float(v), 3) for k, v in details_raw.items() if k != "product_trust"}

        return result
