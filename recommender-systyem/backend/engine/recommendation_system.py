# backend/engine/recommendation_system.py

import numpy as np
import pandas as pd
from .similarity_engine import SimilarityEngine


class RecommendationSystem:

    def __init__(self, df_reviews, df_products, rl_env, rl_model=None):
        self.df_reviews  = df_reviews
        self.df_products = df_products
        self.rl_env      = rl_env
        self.rl_model    = rl_model
        self.sim         = SimilarityEngine(df_reviews, df_products)

    def _rl_threshold(self, asin: str) -> float:
        if self.rl_model is None:
            return 0.5

        state = self.rl_env.get_product_state(asin)
        if state is None:
            return 0.5

        try:
            action, _ = self.rl_model.predict(state, deterministic=True)
            return float(np.clip(action[0], 0.0, 1.0))
        except Exception:
            return 0.5

    def _risk_label(self, score: float) -> str:
        if score >= 0.70: return "trusted"
        if score >= 0.50: return "moderate"
        return "risky"

    def _meta(self, asin: str) -> dict:
        base = {"title": asin, "price": 0.0, "category": "Unknown",
                "store": "Unknown", "review_count": 0, "avg_rating": 0.0, "features": []}

        rev = self.df_reviews[self.df_reviews["asin"] == asin]
        if not rev.empty:
            base["review_count"] = int(len(rev))
            base["avg_rating"]   = round(float(rev["rating"].mean()), 2) if "rating" in rev.columns else 0.0

        if self.df_products.empty:
            return base

        row = self.df_products[self.df_products["asin"] == asin]
        if row.empty:
            return base

        r = row.iloc[0]

        for col in ("title", "productTitle", "name"):
            if col in r.index and pd.notna(r[col]):
                base["title"] = str(r[col])[:120]; break

        base["price"]    = float(r.get("price", 0) or 0)
        base["category"] = str(r.get("main_category", "Unknown"))

        for col in ("store", "seller", "brand", "manufacturer"):
            if col in r.index and pd.notna(r[col]):
                base["store"] = str(r[col]); break

        raw = r.get("features", [])
        if isinstance(raw, list):
            base["features"] = [str(f)[:120] for f in raw[:6] if str(f).strip()]

        if "rating_number" in r.index and pd.notna(r["rating_number"]):
            base["review_count"] = max(base["review_count"], int(r["rating_number"]))

        if "average_rating" in r.index and pd.notna(r["average_rating"]):
            base["avg_rating"] = round(float(r["average_rating"]), 2)

        return base

    def check_product(self, asin: str) -> dict:
        state      = self.rl_env.get_product_state(asin)
        trust_data = self.rl_env.get_product_trust_data(asin)

        if state is None or trust_data is None:
            return {"error": f"ASIN '{asin}' not found"}

        threshold  = self._rl_threshold(asin)
        final_sc   = trust_data["final_trust_score"]
        decision   = final_sc > threshold

        return {
            "asin": asin,
            "meta": self._meta(asin),
            "trust_data": trust_data,
            "threshold": round(threshold, 4),
            "decision": decision,
            "risk_label": self._risk_label(final_sc),
            "rl_powered": self.rl_model is not None,
        }

    def similar_products(self, target_asin: str, top_n: int = 5, min_trust: float = 0.45):

        if target_asin not in self.rl_env.product_asins:
            return None

        candidates = self.sim.hybrid(target_asin, top_n=100)
        results    = []

        for asin, sim_score, breakdown in candidates:
            trust_data = self.rl_env.get_product_trust_data(asin)
            if trust_data is None:
                continue

            threshold = self._rl_threshold(asin)
            final_sc  = trust_data["final_trust_score"]

            # ✅ FIXED CONDITION (RELAXED)
            if final_sc >= min_trust or final_sc > threshold:
                results.append({
                    "asin": asin,
                    "meta": self._meta(asin),
                    "trust_data": trust_data,
                    "similarity": round(sim_score, 4),
                    "method_breakdown": breakdown,
                    "final_score": round(sim_score * final_sc, 4),
                    "risk_label": self._risk_label(final_sc),
                    "rl_threshold": round(threshold, 4),
                })

        results.sort(key=lambda x: x["final_score"], reverse=True)

        target_trust = self.rl_env.get_product_trust_data(target_asin)
        target_meta  = self._meta(target_asin)

        # 🔥 FALLBACK
        if len(results) == 0:
            print("[WARN] No RL recommendations — using fallback")

            fallback = []
            for asin in self.rl_env.product_asins[:top_n]:
                trust_data = self.rl_env.get_product_trust_data(asin)
                if trust_data is None:
                    continue

                fallback.append({
                    "asin": asin,
                    "meta": self._meta(asin),
                    "trust_data": trust_data,
                    "similarity": 0,
                    "method_breakdown": {},
                    "final_score": trust_data["final_trust_score"],
                    "risk_label": self._risk_label(trust_data["final_trust_score"]),
                    "rl_threshold": 0.5,
                })

            return {
                "target_asin": target_asin,
                "target_product": target_meta,
                "target_trust": target_trust,
                "recommendations": fallback,
                "total_found": len(fallback),
            }

        return {
            "target_asin": target_asin,
            "target_product": target_meta,
            "target_trust": target_trust,
            "recommendations": results[:top_n],
            "total_found": len(results),
        }

    def random_products(self, n: int = 12):
        chosen = np.random.choice(
            self.rl_env.product_asins,
            size=min(n, len(self.rl_env.product_asins)),
            replace=False,
        )
        return [self.check_product(str(a)) for a in chosen]

    def search_products(self, query: str, top_n: int = 20):
        if self.df_products.empty:
            return []

        title_col = next(
            (c for c in ("title", "productTitle", "name") if c in self.df_products.columns), None
        )

        if not title_col:
            return []

        mask = self.df_products[title_col].fillna("").str.contains(query, case=False, na=False)

        results = []
        for _, row in self.df_products[mask].head(top_n).iterrows():
            asin = str(row.get("asin", ""))
            results.append(self.check_product(asin) if asin else {"error": "no asin"})

        return results

    def top_trusted(self, n: int = 20, min_trust: float = 0.60):
        cache = self.rl_env.trust_data_cache
        asins = self.rl_env.product_asins

        pairs = [
            (str(asins[i]), cache[i])
            for i in range(len(asins))
            if cache[i]["final_trust_score"] >= min_trust
        ]

        pairs.sort(key=lambda x: x[1]["final_trust_score"], reverse=True)

        results = []
        for asin, td in pairs[:n]:
            threshold = self._rl_threshold(asin)

            results.append({
                "asin": asin,
                "meta": self._meta(asin),
                "trust_data": td,
                "threshold": round(threshold, 4),
                "decision": td["final_trust_score"] > threshold,
                "risk_label": self._risk_label(td["final_trust_score"]),
                "rl_powered": self.rl_model is not None,
            })

        return results