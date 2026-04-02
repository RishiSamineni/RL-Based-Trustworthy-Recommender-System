from flask import Flask, jsonify, request
from flask_cors import CORS

# 🔥 IMPORT YOUR PIPELINE
from engine.trust_pipeline import TrustPipeline

app = Flask(__name__)
CORS(app)

# ---------------- CONFIG ----------------
app.config["REVIEWS_FILE"] = "Software.jsonl"
app.config["META_FILE"] = "meta_Software.jsonl"
app.config["MAX_ROWS"] = 5000
app.config["RL_TIMESTEPS"] = 5000

# ---------------- INIT PIPELINE ----------------
print("🚀 Starting Trust Pipeline... (this may take time)")
pipeline = TrustPipeline(app.config)
pipeline.run()
rec = pipeline.rec
print("✅ Pipeline Ready!")

# ---------------- AUTH (DUMMY) ----------------
@app.route('/api/auth/login', methods=['POST'])
def login():
    return jsonify({"token": "dummy-token", "user": {"id": 1, "username": "testuser"}})

# ---------------- PRODUCTS ----------------
@app.route('/api/items/', methods=['GET'])
def get_products():
    search = request.args.get("search", "")
    category = request.args.get("category", "")

    try:
        df = rec.df_products.copy()

        # normalize
        df["title"] = df.get("title", "").fillna("")
        df["category"] = df.get("main_category", "Other")

        if search:
            df = df[df["title"].str.contains(search, case=False, na=False)]

        if category:
            df = df[df["category"] == category]

        data = df.head(100).to_dict(orient="records")
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/items/<asin>', methods=['GET'])
def get_product(asin):
    try:
        product = rec.check_product(asin)
        return jsonify(product)
    except:
        return jsonify({"error": "Not found"}), 404


# ---------------- RECOMMENDATIONS ----------------

# ✅ SIMILAR PRODUCTS (REAL RL / TRUST)
@app.route('/api/recommendations/similar/<asin>', methods=['GET'])
def similar_products(asin):
    try:
        data = rec.similar_products(asin)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ TOP TRUSTED
@app.route('/api/recommendations/for-you', methods=['GET'])
def for_you():
    try:
        data = rec.top_trusted(10)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ TRUST CHECK
@app.route('/api/recommendations/trust-check/<asin>', methods=['GET'])
def trust_check(asin):
    try:
        data = rec.check_product(asin)
        return jsonify(data)
    except:
        return jsonify({"error": "Not found"}), 404


# ---------------- ANALYTICS ----------------
@app.route('/api/analytics/overview')
def overview():
    try:
        return jsonify({
            "total_products": len(rec.df_products),
            "total_reviews": len(rec.df_reviews)
        })
    except:
        return jsonify({"error": "failed"}), 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)