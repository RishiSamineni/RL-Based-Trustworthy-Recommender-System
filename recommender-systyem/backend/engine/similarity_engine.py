# backend/engine/similarity_engine.py
"""
Hybrid product similarity (collaborative + content-based).
Replaces product_similarity.py — self-contained inside engine/.
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimilarityEngine:
    """
    Computes hybrid product similarity combining:
      • Collaborative filtering — co-review patterns ("users who reviewed X also Y")
      • Content-based          — category, title TF-IDF, price proximity, features
    """

    def __init__(self, df_reviews: pd.DataFrame, df_products: pd.DataFrame):
        self.df_reviews  = df_reviews
        self.df_products = df_products
        self.tfidf       = TfidfVectorizer(max_features=500, stop_words="english")
        self._collab_cache  = {}
        self._content_cache = {}

    # ── collaborative ─────────────────────────────────────────────────────────
    def collaborative(self, target_asin: str, top_n: int = 50) -> list:
        if target_asin in self._collab_cache:
            return self._collab_cache[target_asin][:top_n]

        target_rev = self.df_reviews[self.df_reviews["asin"] == target_asin]
        if target_rev.empty:
            return []

        uid_col = "user_id" if "user_id" in self.df_reviews.columns else "reviewerID"
        target_users = set(target_rev[uid_col].unique())
        peer_rev     = self.df_reviews[self.df_reviews[uid_col].isin(target_users)]

        scores: dict = defaultdict(lambda: {"count": 0, "ratings": []})
        for _, row in peer_rev.iterrows():
            a = row["asin"]
            if a != target_asin:
                scores[a]["count"] += 1
                scores[a]["ratings"].append(row.get("rating", 5.0))

        target_avg = float(target_rev["rating"].mean()) if "rating" in target_rev.columns else 5.0
        sims = []
        for asin, data in scores.items():
            if data["count"] < 1:
                continue
            freq_score   = min(data["count"] / max(len(target_users), 1), 1.0)
            avg_r        = float(np.mean(data["ratings"]))
            rating_sim   = 1.0 - abs(target_avg - avg_r) / 5.0
            sims.append((asin, 0.7 * freq_score + 0.3 * rating_sim))

        sims.sort(key=lambda x: x[1], reverse=True)
        self._collab_cache[target_asin] = sims
        return sims[:top_n]

    # ── content-based ─────────────────────────────────────────────────────────
    def content(self, target_asin: str, top_n: int = 50) -> list:
        if target_asin in self._content_cache:
            return self._content_cache[target_asin][:top_n]

        tgt_rows = self.df_products[self.df_products["asin"] == target_asin]
        if tgt_rows.empty:
            return []
        tgt = tgt_rows.iloc[0]

        sims = []
        for _, prod in self.df_products.iterrows():
            if prod["asin"] == target_asin:
                continue
            cat_s  = self._cat_sim(tgt, prod)
            title_s = self._title_sim(tgt, prod)
            price_s = self._price_sim(tgt, prod)
            feat_s  = self._feat_sim(tgt, prod)
            total   = 0.40*cat_s + 0.30*title_s + 0.20*price_s + 0.10*feat_s
            sims.append((prod["asin"], total))

        sims.sort(key=lambda x: x[1], reverse=True)
        self._content_cache[target_asin] = sims
        return sims[:top_n]

    def _cat_sim(self, p1, p2) -> float:
        c1, c2 = str(p1.get("main_category","")).lower(), str(p2.get("main_category","")).lower()
        if not c1 or not c2 or c1 == "nan" or c2 == "nan":
            return 0.5
        if c1 == c2:      return 1.0
        if c1 in c2 or c2 in c1: return 0.7
        return 0.0

    def _title_sim(self, p1, p2) -> float:
        t1, t2 = str(p1.get("title","")), str(p2.get("title",""))
        if not t1 or not t2:
            return 0.0
        try:
            mat = self.tfidf.fit_transform([t1, t2])
            return float(cosine_similarity(mat[0:1], mat[1:2])[0][0])
        except Exception:
            return 0.0

    def _price_sim(self, p1, p2) -> float:
        try:
            v1 = float(pd.to_numeric(p1.get("price", 0), errors="coerce") or 0)
            v2 = float(pd.to_numeric(p2.get("price", 0), errors="coerce") or 0)
            if v1 == 0 or v2 == 0:
                return 0.5
            return float(1.0 - min(abs(v1 - v2) / max(v1, v2), 1.0))
        except Exception:
            return 0.5

    def _feat_sim(self, p1, p2) -> float:
        try:
            f1 = set(str(x).lower() for x in (p1.get("features") or []) if pd.notna(x))
            f2 = set(str(x).lower() for x in (p2.get("features") or []) if pd.notna(x))
            if not f1 or not f2:
                return 0.5
            return len(f1 & f2) / len(f1 | f2)
        except Exception:
            return 0.5

    # ── hybrid ────────────────────────────────────────────────────────────────
    def hybrid(
        self,
        target_asin: str,
        top_n: int = 50,
        collab_w: float = 0.6,
        content_w: float = 0.4,
    ) -> list:
        """
        Returns list of (asin, hybrid_score, {collaborative, content}) tuples.
        """
        collab_dict  = dict(self.collaborative(target_asin, top_n=100))
        content_dict = dict(self.content(target_asin, top_n=100))
        all_asins    = set(collab_dict) | set(content_dict)

        results = []
        for asin in all_asins:
            cs = collab_dict.get(asin, 0.0)
            ct = content_dict.get(asin, 0.0)
            results.append((
                asin,
                collab_w * cs + content_w * ct,
                {"collaborative": cs, "content": ct},
            ))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]
