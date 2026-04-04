# 🛡️ TrustRec — Trust-Aware Reinforcement Learning Recommender System

## 📌 Overview

TrustRec is a hybrid recommender system that integrates trust modeling and reinforcement learning (RL) to generate reliable recommendations.

Unlike traditional recommender systems that rely only on similarity or ratings, this system evaluates a trust ecosystem consisting of:
- Product-level signals
- User (reviewer) credibility
- Seller/category reliability
- Review quality and consistency

A Proximal Policy Optimization (PPO) agent is used to dynamically learn decision thresholds for filtering recommendations.

---

## 🎯 Problem Statement

Traditional recommender systems suffer from:
- Fake or biased reviews
- Rating manipulation
- Lack of explainability
- Static decision thresholds

Goal:
Design a system that produces relevant AND trustworthy recommendations using:
- Multi-dimensional trust scoring
- Hybrid similarity modeling
- Reinforcement learning-based decision policies

---

## 🧠 Core Concepts

### 1. Trust Modeling

Final Trust Score:

final_trust = 0.55 * product_trust
            + 0.35 * user_trust
            + 0.10 * seller_trust

---

### 2. Hybrid Recommendation

- Collaborative Filtering (user overlap)
- Content-Based Filtering (title, category, price, features)

---

### 3. Reinforcement Learning (PPO)

State:
[final_trust, avg_rating_norm, verified_ratio, review_confidence, text_quality]

Action:
Threshold ∈ [0,1]

Reward:
Encourages trust alignment + rating quality

---

## ⚙️ Architecture

Raw Data → Preprocessing → Trust Engine → RL → Recommendation → API → Frontend

---

## 📁 Structure

backend/
  app.py
  preprocessing.py
  engine/
frontend/
  src/

---

## 🔍 Pipeline

1. Load data
2. Clean text
3. Compute trust
4. Train RL
5. Recommend

---

## 🌐 API

- /api/items/
- /api/recommendations/similar/<asin>
- /api/recommendations/trust-check/<asin>

---

## 👍 Strengths

- Trust-aware recommendations
- RL-based dynamic filtering
- Explainable system

---

## 👎 Limitations

- No persistent storage yet
- RL expensive
- API mismatches

---

## 🚀 Future Work

- Save model + features
- Improve personalization
- Deploy system

---

## 🧾 Conclusion

TrustRec combines trust modeling + RL to build reliable, adaptive, explainable recommender systems.
