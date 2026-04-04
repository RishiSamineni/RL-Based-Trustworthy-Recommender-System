
Each product is evaluated using multiple trust dimensions:

#### Product Trust
- Normalized rating
- Review volume (log-scaled)
- Verified purchase ratio
- Price consistency
- Title relevance

#### User Trust
- Reviewer consistency
- Helpful vote behavior
- Verified purchase behavior
- Review text quality

#### Seller Trust
- Category-level reliability proxy

#### Final Trust Score
A weighted combination:


final_trust = 0.55 * product_trust
+ 0.35 * user_trust
+ 0.10 * seller_trust


---

### 2. Hybrid Recommendation Engine

The system combines:

#### Collaborative Filtering
- User-item interaction overlap
- Co-rating similarity

#### Content-Based Filtering
- TF-IDF similarity (title)
- Category match
- Price similarity
- Feature similarity

Final similarity is a weighted combination of both.

---

### 3. Reinforcement Learning (PPO)

Instead of using a fixed trust threshold, the system learns a **dynamic decision policy**.

#### State Space

[final_trust, avg_rating_norm, verified_ratio, review_confidence, text_quality]


#### Action Space
- Continuous value ∈ [0,1] representing trust threshold

#### Reward Function
Encourages:
- Alignment with actual trustworthiness
- Higher ratings
- Verified purchase confidence

#### Outcome
The agent learns:
> "How strict should the system be for this product?"

---

## ⚙️ System Architecture


Raw Data (JSONL)
↓
Preprocessing (NLTK cleaning, normalization)
↓
Trust Engine (feature extraction + scoring)
↓
RL Environment (Gym-style simulation)
↓
PPO Training (policy learning)
↓
Recommendation Engine
↓
Flask API Layer
↓
React Frontend


---

## 📁 Project Structure


recommender-system/
│
├── backend/
│ ├── app.py # Flask API (pipeline-based)
│ ├── preprocessing.py # Text cleaning (NLTK)
│ ├── Software.jsonl # Reviews dataset
│ ├── meta_Software.jsonl # Product metadata
│ │
│ ├── engine/
│ │ ├── trust_pipeline.py # End-to-end pipeline
│ │ ├── trust_engine.py # Trust computation
│ │ ├── similarity_engine.py # Hybrid similarity
│ │ ├── rl_engine.py # PPO + environment
│ │ └── recommendation_system.py
│ │
│ └── output/
│ └── trust_rl_policy.zip # (optional) saved RL model
│
├── frontend/
│ ├── src/
│ │ ├── App.js # Routing
│ │ ├── utils/api.js # API calls
│ │ ├── components/ # UI components
│ │ ├── pages/ # Pages (Home, Products, etc.)
│ │ └── context/ # Auth & Toast state
│
└── README.md


---

## 🔍 Pipeline Execution

### Step 1: Data Loading
- Load `.jsonl` datasets into Pandas
- Normalize column names and formats

### Step 2: Preprocessing
- Remove noise (URLs, emojis, HTML)
- Tokenization + lemmatization (NLTK)

### Step 3: Trust Computation
- Compute user-level trust metrics
- Compute product-level trust features
- Aggregate into final trust score

### Step 4: RL Training
- Construct environment (`TrustEnv`)
- Train PPO agent (if dependencies available)
- Learn threshold policy

### Step 5: Recommendation
- Generate candidate products via similarity
- Filter using RL threshold
- Rank using:


score = similarity × final_trust_score


---

## 🌐 API Endpoints

| Endpoint | Description |
|--------|------------|
| `/api/items/` | List products |
| `/api/items/<asin>` | Get product details |
| `/api/recommendations/similar/<asin>` | Similar + trust-filtered |
| `/api/recommendations/for-you` | Personalized recommendations |
| `/api/recommendations/trust-check/<asin>` | Trust breakdown |
| `/api/analytics/overview` | System analytics |

---

## 💻 Frontend Features

- 🔍 Product search & browsing
- 📊 Trust visualization (badges, bars)
- 📦 Product detail with trust breakdown
- 🤖 Personalized recommendations
- 📈 Analytics dashboard
- 🔐 Auth UI (currently demo-level)

---

## 📦 Dependencies

### Backend
- Flask
- Pandas
- NumPy
- scikit-learn
- NLTK
- gymnasium
- stable-baselines3

### Frontend
- React
- Axios
- React Router
- Recharts
- Lucide Icons

---

## 👍 Strengths

- Multi-dimensional trust modeling
- Hybrid recommendation approach
- RL-based adaptive filtering
- Explainable recommendations
- Modular pipeline architecture

---

## 👎 Limitations

- RL training is computationally expensive
- No persistent storage of processed features
- Model saving not fully integrated
- Frontend/backend API mismatches
- Authentication not fully implemented

---

## 🚀 Future Work

- Persist trained RL model and features
- Full user-based personalization
- Online learning (continuous RL updates)
- Replace dummy auth with real JWT integration
- Deploy as scalable microservice

---

## 📊 Expected Outcomes

- Improved recommendation reliability
- Reduced exposure to low-quality products
- Transparent decision-making
- Adaptive system behavior

---

## 🧾 Conclusion

TrustRec demonstrates how **trust modeling + reinforcement learning** can enhance traditional recommender systems by making them:

- More reliable  
- More adaptive  
- More explainable  

This makes it suitable for real-world platforms where **trust is critical** (e.g., software marketplaces, e-commerce, review platforms).

---
