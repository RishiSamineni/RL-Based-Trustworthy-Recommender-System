# backend/engine/evaluate_rl.py

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


def evaluate_rl_model(env, model, trusted_cutoff=0.50):
    """
    Evaluate the trained RL model as a trust-threshold decision system.

    Ground truth:
        true label = 1 if final_trust_score >= trusted_cutoff else 0

    RL prediction:
        predict threshold using PPO
        pred label = 1 if final_trust_score >= predicted_threshold else 0
    """

    if model is None:
        print("[EVAL] No RL model available. Skipping evaluation.")
        return None

    y_true = []
    y_pred = []
    thresholds = []
    rewards = []

    for i in range(env.n_products):
        state = env.product_features[i]
        true_trust = float(state[0])

        action, _ = model.predict(state, deterministic=True)
        threshold = float(action[0])

        pred = 1 if true_trust >= threshold else 0
        true = 1 if true_trust >= trusted_cutoff else 0

        y_true.append(true)
        y_pred.append(pred)
        thresholds.append(threshold)

        reward = 1.0 if pred == true else -1.0
        rewards.append(reward)

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)

    results = {
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1_score": float(f1),
        "avg_threshold": float(np.mean(thresholds)),
        "min_threshold": float(np.min(thresholds)),
        "max_threshold": float(np.max(thresholds)),
        "std_threshold": float(np.std(thresholds)),
        "avg_reward": float(np.mean(rewards)),
        "confusion_matrix": cm.tolist(),
        "total_products_evaluated": int(len(y_true)),
        "trusted_cutoff_used_for_ground_truth": float(trusted_cutoff),
    }

    print("\n========== RL MODEL EVALUATION ==========")
    print(f"Products Evaluated : {results['total_products_evaluated']}")
    print(f"Accuracy           : {results['accuracy']:.4f}")
    print(f"Precision          : {results['precision']:.4f}")
    print(f"Recall             : {results['recall']:.4f}")
    print(f"F1 Score           : {results['f1_score']:.4f}")
    print(f"Average Threshold  : {results['avg_threshold']:.4f}")
    print(f"Min Threshold      : {results['min_threshold']:.4f}")
    print(f"Max Threshold      : {results['max_threshold']:.4f}")
    print(f"Std Threshold      : {results['std_threshold']:.4f}")
    print(f"Average Reward     : {results['avg_reward']:.4f}")
    print(f"Confusion Matrix   : {results['confusion_matrix']}")
    print("========================================\n")

    return results