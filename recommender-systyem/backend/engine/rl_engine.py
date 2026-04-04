# backend/engine/rl_engine.py
"""
Reinforcement-learning environment (Gymnasium MDP) and PPO training.

State S  : [final_trust, avg_rating_norm, verified_ratio,
            review_confidence, text_quality]      (5-D continuous [0,1])

Action A : learned trust threshold ∈ [0.2, 0.75] (1-D continuous)
Reward R : balanced objective that discourages:
           - trivial threshold = 0 collapse
           - overly high threshold collapse
           - accepting low-trust products
           - rejecting genuinely good products

The PPO agent learns a per-product trust threshold dynamically.
"""

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYM_OK = True
except ImportError:
    gym = object
    spaces = None
    GYM_OK = False

try:
    from stable_baselines3 import PPO
    SB3_OK = True
except ImportError:
    PPO = None
    SB3_OK = False

RL_AVAILABLE = GYM_OK and SB3_OK


class TrustRLEnvironment(gym.Env if GYM_OK else object):
    """
    Gymnasium environment for RL-based trust thresholding.
    Each episode step = one product evaluation.
    """

    metadata = {"render_modes": []}

    def __init__(self, df_reviews, df_products, trust_engine):
        if not GYM_OK:
            raise ImportError("gymnasium is not installed. pip install gymnasium")

        super().__init__()

        self.df_reviews = df_reviews.reset_index(drop=True)
        self.df_products = df_products
        self.trust_engine = trust_engine

        self.product_asins = df_reviews["asin"].astype(str).unique()
        self.n_products = len(self.product_asins)
        self.current_idx = 0

        # narrower action range to prevent meaningless extreme thresholds
        self.min_threshold = 0.20
        self.max_threshold = 0.75

        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(5,), dtype=np.float32
        )

        self.action_space = spaces.Box(
            low=np.array([self.min_threshold], dtype=np.float32),
            high=np.array([self.max_threshold], dtype=np.float32),
            shape=(1,),
            dtype=np.float32,
        )

        self._precompute()

    def _precompute(self):
        print("[RL] Pre-computing trust features for all products …")
        features = []
        trust_cache = []

        for i, asin in enumerate(self.product_asins):
            if i % 100 == 0:
                print(f"    {i}/{self.n_products}")

            td = self.trust_engine.final_product_score(
                self.df_reviews, self.df_products, asin, include_details=True
            )
            det = td.get("details", {})

            state = np.array([
                td["final_trust_score"],
                det.get("avg_rating_norm", 0.5),
                det.get("verified_ratio", 0.5),
                det.get("review_confidence", 0.5),
                det.get("text_quality", 0.5),
            ], dtype=np.float32)

            state = np.nan_to_num(state, nan=0.5, posinf=1.0, neginf=0.0)
            state = np.clip(state, 0.0, 1.0)

            features.append(state)
            trust_cache.append(td)

        self.product_features = np.array(features, dtype=np.float32)
        self.trust_data_cache = trust_cache
        print(f"[RL] Pre-computation done — {len(features)} products.")

    def reset(self, *, seed=None, options=None):
        if seed is not None:
            np.random.seed(seed)
        self.current_idx = int(np.random.randint(0, self.n_products))
        return self.product_features[self.current_idx].copy(), {}

    def step(self, action):
        threshold = float(np.clip(action[0], self.min_threshold, self.max_threshold))

        idx = self.current_idx
        true_trust = float(self.product_features[idx, 0])
        true_rating = float(self.product_features[idx, 1])
        verified_ratio = float(self.product_features[idx, 2])
        review_confidence = float(self.product_features[idx, 3])
        text_quality = float(self.product_features[idx, 4])

        recommend = true_trust >= threshold

        # slightly relaxed target to avoid making the policy too strict
        target_accept = true_trust >= 0.50

        # 1) Classification reward
        classification_reward = 1.0 if recommend == target_accept else -1.0

        # 2) Threshold calibration reward
        calibration_reward = 1.0 - abs(true_trust - threshold)

        # 3) Penalize too-low threshold
        low_threshold_penalty = 0.0
        if threshold < 0.30:
            low_threshold_penalty = -(0.30 - threshold) * 1.2

        # 4) Penalize too-high threshold
        high_threshold_penalty = 0.0
        if threshold > 0.65:
            high_threshold_penalty = -(threshold - 0.65) * 1.6

        # 5) Penalize accepting low-trust products, but less aggressively than before
        false_positive_penalty = 0.0
        if recommend and true_trust < 0.45:
            false_positive_penalty = -(0.45 - true_trust) * 0.5

        # 6) Penalize rejecting strong products
        false_negative_penalty = 0.0
        if (not recommend) and true_trust > 0.70:
            false_negative_penalty = -(true_trust - 0.70) * 1.3

        # 7) Bonus for correctly accepting genuinely good products
        good_accept_bonus = 0.0
        if recommend and true_trust > 0.65:
            good_accept_bonus = (true_trust - 0.65) * 0.8

        # 8) Quality support bonus
        support_bonus = (
            0.25 * true_rating +
            0.25 * verified_ratio +
            0.25 * review_confidence +
            0.25 * text_quality
        )

        reward = (
            0.35 * classification_reward +
            0.25 * calibration_reward +
            0.20 * support_bonus +
            good_accept_bonus +
            low_threshold_penalty +
            high_threshold_penalty +
            false_positive_penalty +
            false_negative_penalty
        )

        self.current_idx = int(np.random.randint(0, self.n_products))
        next_obs = self.product_features[self.current_idx].copy()

        info = {
            "true_trust": true_trust,
            "recommended": recommend,
            "threshold": threshold,
            "target_accept": target_accept,
            "reward_breakdown": {
                "classification_reward": classification_reward,
                "calibration_reward": calibration_reward,
                "support_bonus": support_bonus,
                "good_accept_bonus": good_accept_bonus,
                "low_threshold_penalty": low_threshold_penalty,
                "high_threshold_penalty": high_threshold_penalty,
                "false_positive_penalty": false_positive_penalty,
                "false_negative_penalty": false_negative_penalty,
            },
        }

        return next_obs, float(reward), False, False, info

    def get_product_state(self, asin: str):
        idx_arr = np.where(self.product_asins == str(asin))[0]
        if idx_arr.size == 0:
            return None
        return self.product_features[idx_arr[0]].copy()

    def get_product_trust_data(self, asin: str):
        idx_arr = np.where(self.product_asins == str(asin))[0]
        if idx_arr.size == 0:
            return None
        return self.trust_data_cache[idx_arr[0]]


def train_ppo(env: TrustRLEnvironment, timesteps: int = 10_000, save_path: str = None):
    """
    Train a PPO agent on the trust environment.
    Returns the trained model.
    """
    if not SB3_OK:
        raise ImportError("stable-baselines3 not installed. pip install stable-baselines3")

    print(f"[RL] Training PPO for {timesteps:,} timesteps …")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=0,
    )
    model.learn(total_timesteps=timesteps)

    if save_path:
        model.save(save_path)
        print(f"[RL] Model saved → {save_path}")

    return model


def load_ppo(path: str):
    """Load a previously saved PPO model."""
    if not SB3_OK:
        raise ImportError("stable-baselines3 not installed.")
    return PPO.load(path)