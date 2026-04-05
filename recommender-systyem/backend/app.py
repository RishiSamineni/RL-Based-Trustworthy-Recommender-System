from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd

from engine.trust_pipeline import TrustPipeline

app = Flask(__name__)
CORS(app)

# CONFIG
app.config["REVIEWS_FILE"] = "Software.jsonl"
app.config["META_FILE"] = "meta_Software.jsonl"
app.config["MAX_ROWS"] = 20000
app.config["RL_TIMESTEPS"] = 25000

print("🚀 Starting Trust Pipeline... (this may take time)")
pipeline = TrustPipeline(app.config)
pipeline.run()
rec = pipeline.rec
print("✅ Pipeline Ready!")


def clean_json_value(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, dict):
        return {k: clean_json_value(v) for k, v in value.items()}

    if isinstance(value, list):
        return [clean_json_value(v) for v in value]

    return value


def clean_record(record):
    if not isinstance(record, dict):
        return record
    return {k: clean_json_value(v) for k, v in record.items()}


# AUTH
@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({
        "token": "dummy-token",
        "user": {"id": 1, "username": "testuser"}
    })


# PRODUCTS (FIXED)
@app.route('/api/items/', methods=['GET'])
def get_products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    try:
        df = rec.df_products.copy()

        if df is None or df.empty:
            return jsonify([])

        df["asin"] = df["asin"].astype(str)

        df["title"] = df.get("title", "").fillna("Untitled Product")
        df["main_category"] = df.get("main_category", "Other").fillna("Other")

        # 🔥 ONLY TRUSTED PRODUCTS
        df = df[df["final_trust_score"].notna()]

        # 🔥 SORT BY TRUST
        df = df.sort_values("final_trust_score", ascending=False)

        # FILTERS
        if search:
            df = df[df["title"].str.contains(search, case=False, na=False)]

        if category:
            df = df[df["main_category"] == category]

        data = df.to_dict(orient="records")
        data = [clean_record(item) for item in data]

        return jsonify(data)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# PRODUCT DETAIL
@app.route('/api/items/<asin>', methods=['GET'])
def get_product(asin):
    try:
        df = rec.df_products.copy()
        match = df[df["asin"].astype(str) == str(asin)]

        if match.empty:
            return jsonify({"error": "Not found"}), 404

        return jsonify(clean_record(match.iloc[0].to_dict()))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# RECOMMENDATIONS
@app.route('/api/recommendations/similar/<asin>')
def similar_products(asin):
    try:
        data = rec.similar_products(asin)
        return jsonify(clean_record(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/recommendations/for-you')
def for_you():
    try:
        data = rec.top_trusted(20)
        return jsonify([clean_record(x) for x in data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/recommendations/trust-check/<asin>')
def trust_check(asin):
    try:
        data = rec.check_product(asin)
        return jsonify(clean_record(data))
    except Exception:
        return jsonify({"error": "Not found"}), 404


# ANALYTICS
@app.route('/api/analytics/overview')
def overview():
    try:
        return jsonify({
            "total_products": len(rec.df_products),
            "total_reviews": len(rec.df_reviews),
            "products_with_trust": int(rec.df_products["final_trust_score"].notna().sum())
        })
    except:
        return jsonify({"error": "failed"}), 500


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)