from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd

from engine.trust_pipeline import TrustPipeline

app = Flask(__name__)
CORS(app)

app.config["REVIEWS_FILE"] = "Software.jsonl"
app.config["META_FILE"] = "meta_Software.jsonl"
app.config["MAX_ROWS"] = 5000
app.config["RL_TIMESTEPS"] = 5000

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


def extract_trust_score(trust_data):
    if not isinstance(trust_data, dict):
        return 0

    # case 1: {"final_trust_score": ...}
    if trust_data.get("final_trust_score") is not None:
        return float(trust_data.get("final_trust_score") or 0)

    # case 2: {"trust": {"final_trust_score": ...}}
    trust_obj = trust_data.get("trust")
    if isinstance(trust_obj, dict) and trust_obj.get("final_trust_score") is not None:
        return float(trust_obj.get("final_trust_score") or 0)

    # case 3: {"trust_data": {"final_trust_score": ...}}
    trust_data_obj = trust_data.get("trust_data")
    if isinstance(trust_data_obj, dict) and trust_data_obj.get("final_trust_score") is not None:
        return float(trust_data_obj.get("final_trust_score") or 0)

    # case 4: {"rl_decision": {"score": ...}}
    rl_obj = trust_data.get("rl_decision")
    if isinstance(rl_obj, dict):
        if rl_obj.get("score") is not None:
            return float(rl_obj.get("score") or 0)
        if rl_obj.get("trust_score") is not None:
            return float(rl_obj.get("trust_score") or 0)

    return 0


@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({
        "token": "dummy-token",
        "user": {"id": 1, "username": "testuser"}
    })


@app.route('/api/items/', methods=['GET'])
def get_products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    try:
        df = rec.df_products.copy()

        if df is None or df.empty:
            return jsonify([])

        if "title" not in df.columns:
            df["title"] = "Untitled Product"
        else:
            df["title"] = df["title"].fillna("Untitled Product")

        if "main_category" not in df.columns:
            df["main_category"] = "Other"
        else:
            df["main_category"] = df["main_category"].fillna("Other")

        if search:
            df = df[df["title"].astype(str).str.contains(search, case=False, na=False)]

        if category:
            df = df[df["main_category"].astype(str) == category]

        data = df.head(100).to_dict(orient="records")
        cleaned_data = []

        for item in data:
            item = clean_record(item)

            asin = item.get("asin")
            item["final_trust_score"] = 0

            if asin:
                try:
                    trust_data = rec.check_product(asin)
                    trust_data = clean_record(trust_data)

                    # debug print
                    print(f"ASIN: {asin}")
                    print("TRUST DATA:", trust_data)

                    item["final_trust_score"] = extract_trust_score(trust_data)
                except Exception as e:
                    print(f"Trust fetch failed for {asin}: {e}")
                    item["final_trust_score"] = 0

            cleaned_data.append(item)

        return jsonify(cleaned_data)

    except Exception as e:
        print("ERROR in /api/items/:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/api/items/<asin>', methods=['GET'])
def get_product(asin):
    try:
        df = rec.df_products.copy()

        if "asin" in df.columns:
            match = df[df["asin"] == asin]

            if not match.empty:
                item = match.iloc[0].to_dict()
                item = clean_record(item)
                item["final_trust_score"] = 0

                try:
                    trust_data = rec.check_product(asin)
                    trust_data = clean_record(trust_data)
                    item["final_trust_score"] = extract_trust_score(trust_data)
                    item["trust_details"] = trust_data
                except Exception as e:
                    print(f"Trust fetch failed for detail {asin}: {e}")

                return jsonify(item)

        return jsonify({"error": "Not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/recommendations/similar/<asin>', methods=['GET'])
def similar_products(asin):
    try:
        data = rec.similar_products(asin)
        if isinstance(data, list):
            enriched = []
            for item in data:
                item = clean_record(item)
                item["final_trust_score"] = item.get("final_trust_score") or 0
                enriched.append(item)
            data = enriched
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/recommendations/for-you', methods=['GET'])
def for_you():
    try:
        data = rec.top_trusted(10)
        if isinstance(data, list):
            data = [clean_record(item) for item in data]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/recommendations/trust-check/<asin>', methods=['GET'])
def trust_check(asin):
    try:
        data = rec.check_product(asin)
        data = clean_record(data)
        data["resolved_final_trust_score"] = extract_trust_score(data)
        return jsonify(data)
    except Exception:
        return jsonify({"error": "Not found"}), 404


@app.route('/api/analytics/overview', methods=['GET'])
def overview():
    try:
        return jsonify({
            "total_products": len(rec.df_products),
            "total_reviews": len(rec.df_reviews)
        })
    except Exception:
        return jsonify({"error": "failed"}), 500


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)