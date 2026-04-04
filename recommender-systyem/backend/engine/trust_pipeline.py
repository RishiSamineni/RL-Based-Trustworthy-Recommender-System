# backend/engine/trust_pipeline.py
"""
TrustPipeline — master orchestrator for the entire RL recommendation system.
"""

import json
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

from .trust_engine import TrustEngine
from .rl_engine import TrustRLEnvironment, train_ppo, RL_AVAILABLE
from .recommendation_system import RecommendationSystem

import re
import nltk


def _ensure_nltk():
    for pkg, loc in [
        ("stopwords", "corpora/stopwords"),
        ("punkt", "tokenizers/punkt"),
        ("wordnet", "corpora/wordnet"),
        ("punkt_tab", "tokenizers/punkt_tab"),
    ]:
        try:
            nltk.data.find(loc)
        except LookupError:
            nltk.download(pkg, quiet=True)


_CONTRACTIONS = {
    "ain't": "am not", "aren't": "are not", "can't": "cannot", "couldn't": "could not",
    "didn't": "did not", "doesn't": "does not", "don't": "do not", "hadn't": "had not",
    "hasn't": "has not", "haven't": "have not", "he'd": "he would", "he'll": "he will",
    "he's": "he is", "i'd": "i would", "i'll": "i will", "i'm": "i am", "i've": "i have",
    "isn't": "is not", "it's": "it is", "let's": "let us", "shouldn't": "should not",
    "that's": "that is", "there's": "there is", "they'd": "they would",
    "they'll": "they will", "they're": "they are", "they've": "they have",
    "wasn't": "was not", "we'd": "we would", "we'll": "we will", "we're": "we are",
    "we've": "we have", "weren't": "were not", "what's": "what is", "who's": "who is",
    "won't": "will not", "wouldn't": "would not", "you'd": "you would",
    "you'll": "you will", "you're": "you are", "you've": "you have",
}
_CONTRA_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in sorted(_CONTRACTIONS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE,
)
_EMOJI_RE = re.compile(
    "["
    u"\U0001F600-\U0001F64F"
    u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF"
    u"\U0001F1E0-\U0001F1FF"
    u"\U00002702-\U000027B0"
    u"\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)


def _clean_text(text: str) -> str:
    if not text or pd.isna(text):
        return ""
    text = str(text).lower()
    text = _CONTRA_RE.sub(lambda m: _CONTRACTIONS[m.group(0).lower()], text)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r'[_"\\\-;%()|+&=*%.,!?:#$@\[\]/]', " ", text)
    text = _EMOJI_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()

    try:
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        stop = set(stopwords.words("english"))
        lemma = WordNetLemmatizer()
        words = [lemma.lemmatize(w) for w in word_tokenize(text) if w not in stop and len(w) > 2]
        return " ".join(words)
    except Exception:
        return text


def _load_jsonl(path: Path, max_rows: int = 5000) -> pd.DataFrame:
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_rows:
                    break
                try:
                    rows.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"[WARN] File not found: {path}")
    return pd.DataFrame(rows)


class TrustPipeline:

    def __init__(self, config: dict = None):
        cfg = config or {}
        here = Path(__file__).resolve().parent.parent

        self.reviews_file = Path(cfg.get("REVIEWS_FILE", here / "Software.jsonl"))
        self.meta_file = Path(cfg.get("META_FILE", here / "meta_Software.jsonl"))
        self.output_dir = Path(cfg.get("OUTPUT_DIR", here / "output"))
        self.max_rows = int(cfg.get("MAX_ROWS", 5000))
        self.rl_timesteps = int(cfg.get("RL_TIMESTEPS", 10_000))

        self.df_reviews = pd.DataFrame()
        self.df_products = pd.DataFrame()
        self.trust_eng = None
        self.rl_env = None
        self.rl_model = None
        self.rec = None
        self.is_ready = False

    def run(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        _ensure_nltk()

        self._load()
        self._standardise()
        self._fix_types()
        self._clean_text()
        self._build_trust_engine()
        self._build_rl_env()
        if RL_AVAILABLE:
            self._train_rl()

        # NEW: merge precomputed trust into df_products
        self._merge_precomputed_trust()

        self._build_rec_system()

        self.is_ready = True
        print("[PIPELINE] ✓ Ready — RL-powered recommendations active.")
        return self

    def _load(self):
        print("[1/8] Loading data …")
        self.df_reviews = _load_jsonl(self.reviews_file, self.max_rows)
        self.df_products = _load_jsonl(self.meta_file, 500_000)
        if self.df_reviews.empty:
            raise RuntimeError("No reviews loaded.")
        print(f"reviews={len(self.df_reviews)} products={len(self.df_products)}")

    def _standardise(self):
        print("[2/8] Standardising column names …")
        rename = {
            "reviewerID": "user_id",
            "overall": "rating",
            "reviewText": "text",
            "unixReviewTime": "timestamp",
            "verified": "verified_purchase",
            "vote": "helpful_vote",
        }
        self.df_reviews = self.df_reviews.rename(columns=rename)

        p = self.df_products

        asin_col = next(
            (c for c in ("asin", "ASIN", "parent_asin", "product_id", "id") if c in p.columns),
            None,
        )

        if asin_col and asin_col != "asin":
            p["asin"] = p[asin_col]
        elif "asin" not in p.columns:
            p["asin"] = np.nan

        if "parent_asin" in p.columns:
            p["asin"] = p["parent_asin"]

        if "average_rating" in p.columns:
            p["rating"] = pd.to_numeric(p["average_rating"], errors="coerce").fillna(0)

    def _fix_types(self):
        print("[3/8] Fixing data types …")
        r = self.df_reviews

        r["rating"] = pd.to_numeric(r.get("rating", 5), errors="coerce").fillna(5)
        r["timestamp"] = pd.to_numeric(r.get("timestamp", 0), errors="coerce").fillna(0)
        r["verified_purchase"] = r.get("verified_purchase", False)
        r["helpful_vote"] = pd.to_numeric(r.get("helpful_vote", 0), errors="coerce").fillna(0)

    def _clean_text(self):
        print("[4/8] Cleaning text …")
        self.df_reviews["text"] = self.df_reviews["text"].apply(_clean_text)

    def _build_trust_engine(self):
        print("[5/8] Trust engine …")
        self.trust_eng = TrustEngine()

        # important setup for trust_engine internals
        if not self.df_products.empty and "price" in self.df_products.columns:
            prices = pd.to_numeric(self.df_products["price"], errors="coerce")
            self.trust_eng.mean_price = float(prices.dropna().mean()) if not prices.dropna().empty else None

        for col in ("title", "productTitle", "name"):
            if col in self.df_products.columns:
                self.trust_eng.title_col = col
                break

        for col in ("store", "seller", "brand", "manufacturer"):
            if col in self.df_products.columns:
                self.trust_eng.seller_col = col
                break

    def _build_rl_env(self):
        print("[6/8] RL env …")
        self.rl_env = TrustRLEnvironment(self.df_reviews, self.df_products, self.trust_eng)

    def _train_rl(self):
        print("[7/8] Training RL …")
        self.rl_model = train_ppo(self.rl_env, self.rl_timesteps)

    def _merge_precomputed_trust(self):
        print("[8/8] Merging precomputed trust into df_products …")

        rows = []
        for asin, td in zip(self.rl_env.product_asins, self.rl_env.trust_data_cache):
            rows.append({
                "asin": str(asin),
                "product_trust": td.get("product_trust"),
                "user_trust": td.get("user_trust"),
                "seller_trust": td.get("seller_trust"),
                "final_trust_score": td.get("final_trust_score"),
            })

        df_trust = pd.DataFrame(rows)

        if df_trust.empty:
            self.df_products["product_trust"] = np.nan
            self.df_products["user_trust"] = np.nan
            self.df_products["seller_trust"] = np.nan
            self.df_products["final_trust_score"] = np.nan
            self.df_products["has_trust_data"] = False
            return

        self.df_products["asin"] = self.df_products["asin"].astype(str)
        df_trust["asin"] = df_trust["asin"].astype(str)

        self.df_products = self.df_products.merge(
            df_trust,
            on="asin",
            how="left",
        )

        self.df_products["has_trust_data"] = self.df_products["final_trust_score"].notna()

        print(
            f"[PIPELINE] Trust merged. "
            f"products_with_trust={int(self.df_products['has_trust_data'].sum())} "
            f"total_products={len(self.df_products)}"
        )

    def _build_rec_system(self):
        print("[✓] Recommendation system …")
        self.rec = RecommendationSystem(
            self.df_reviews,
            self.df_products,
            self.rl_env,
            self.rl_model,
        )