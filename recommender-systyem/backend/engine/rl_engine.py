# backend/engine/rl_engine.py
"""
Reinforcement-learning environment (Gymnasium MDP) and PPO training.
Replaces rl_env.py.  Entirely self-contained inside engine/.

MDP formulation
───────────────
State  S  : [final_trust, avg_rating_norm, verified_ratio,
              review_confidence, text_quality]          (5-D continuous [0,1])
Action A  : learned trust threshold ∈ [0, 1]           (1-D continuous)
Reward R  : trust_accuracy + rating_reward + verified_bonus
Discount γ: 0.99

The PPO agent learns to set a *per-product* trust threshold dynamically,
which is fundamentally different from a fixed rule-based cutoff.
"""

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYM_OK = True
except ImportError:
    gym    = object
    spaces = None
    GYM_OK = False

try:
    from stable_baselines3 import PPO
    SB3_OK = True
except ImportError:
    PPO    = None
    SB3_OK = False

RL_AVAILABLE = GYM_OK and SB3_OK


# ─────────────────────────────────────────────────────────────────────────────
class TrustRLEnvironment(gym.Env if GYM_OK else object):
    """
    Gymnasium environment for RL-based trust thresholding.
    Each episode step = one product evaluation.
    """

    metadata = {"render_modes": []}

    def __init__(self, df_reviews, df_products, trust_engine):
        if not GYM_OK:
            raise ImportError("gymnasium is not installed.  pip install gymnasium")

        super().__init__()

        self.df_reviews   = df_reviews.reset_index(drop=True)
        self.df_products  = df_products
        self.trust_engine = trust_engine

        self.product_asins = df_reviews["asin"].unique()
        self.n_products    = len(self.product_asins)
        self.current_idx   = 0

        # 5-D state space, all features in [0,1]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(5,), dtype=np.float32
        )
        # 1-D action: the threshold the agent sets
        self.action_space = spaces.Box(
            low=0.0, high=1.0, shape=(1,), dtype=np.float32
        )

        # Pre-compute all product states up front (expensive but done once)
        self._precompute()

    # ── pre-computation ───────────────────────────────────────────────────────
    def _precompute(self):
        print("[RL] Pre-computing trust features for all products …")
        features   = []
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
                det.get("avg_rating_norm",   0.5),
                det.get("verified_ratio",    0.5),
                det.get("review_confidence", 0.5),
                det.get("text_quality",      0.5),
            ], dtype=np.float32)

            state = np.nan_to_num(state, nan=0.5, posinf=1.0, neginf=0.0)
            state = np.clip(state, 0.0, 1.0)

            features.append(state)
            trust_cache.append(td)

        self.product_features = np.array(features, dtype=np.float32)
        self.trust_data_cache = trust_cache
        print(f"[RL] Pre-computation done — {len(features)} products.")

    # ── Gymnasium API ─────────────────────────────────────────────────────────
    def reset(self, *, seed=None, options=None):
        if seed is not None:
            np.random.seed(seed)
        self.current_idx = int(np.random.randint(0, self.n_products))
        return self.product_features[self.current_idx].copy(), {}

    def step(self, action):
        threshold      = float(np.clip(action[0], 0.0, 1.0))
        idx            = self.current_idx
        true_trust     = float(self.product_features[idx, 0])
        true_rating    = float(self.product_features[idx, 1])
        verified_ratio = float(self.product_features[idx, 2])

        recommend = true_trust > threshold

        # ── Reward function ───────────────────────────────────────────────────
        # trust_accuracy: penalise proportionally to how far threshold is from truth
        trust_accuracy = 1.0 - abs(true_trust - threshold)
        # rating_reward: high if recommended, conservative penalty if not
        rating_reward  = true_rating if recommend else 0.2
        # verified_bonus: extra signal for high verified-purchase ratio
        verified_bonus = verified_ratio * 0.3

        reward = (
            0.50 * trust_accuracy +
            0.30 * rating_reward  +
            0.20 * verified_bonus
        )

        # Transition to a new random product (Markov property)
        self.current_idx = int(np.random.randint(0, self.n_products))
        next_obs = self.product_features[self.current_idx].copy()

        info = {
            "true_trust":  true_trust,
            "recommended": recommend,
            "threshold":   threshold,
            "reward_breakdown": {
                "trust_accuracy": trust_accuracy,
                "rating_reward":  rating_reward,
                "verified_bonus": verified_bonus,
            },
        }
        return next_obs, float(reward), False, False, info

    # ── query helpers ─────────────────────────────────────────────────────────
    def get_product_state(self, asin: str):
        idx_arr = np.where(self.product_asins == asin)[0]
        if idx_arr.size == 0:
            return None
        return self.product_features[idx_arr[0]].copy()

    def get_product_trust_data(self, asin: str):
        idx_arr = np.where(self.product_asins == asin)[0]
        if idx_arr.size == 0:
            return None
        return self.trust_data_cache[idx_arr[0]]


# ─────────────────────────────────────────────────────────────────────────────
def train_ppo(env: TrustRLEnvironment, timesteps: int = 10_000, save_path: str = None):
    """
    Train a PPO agent on the trust environment.
    Returns the trained model.
    """
    if not SB3_OK:
        raise ImportError("stable-baselines3 not installed.  pip install stable-baselines3")

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
