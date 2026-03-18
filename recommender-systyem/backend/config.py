import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'trustworthy-recommender-secret-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///recommender.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-2024')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    MIN_TRUST_THRESHOLD = 0.4
    TOP_N_RECOMMENDATIONS = 10
    REVIEWS_FILE = Path(os.getenv("REVIEWS_FILE", BASE_DIR / "Software.jsonl"))
    META_FILE    = Path(os.getenv("META_FILE",    BASE_DIR / "meta_Software.jsonl"))