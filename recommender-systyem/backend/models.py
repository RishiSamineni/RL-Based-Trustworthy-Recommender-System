from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ratings = db.relationship('Rating', backref='user', lazy=True)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'rating_count': len(self.ratings)
        }


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    asin = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    price = db.Column(db.Float, default=0.0)
    image_url = db.Column(db.String(500))
    features = db.Column(db.Text)          # JSON string
    avg_rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    # Trust score fields (from TrustworthyRecommender)
    product_trust = db.Column(db.Float, default=0.5)
    seller_trust = db.Column(db.Float, default=0.5)
    final_trust_score = db.Column(db.Float, default=0.5)
    avg_rating_norm = db.Column(db.Float, default=0.5)
    verified_ratio = db.Column(db.Float, default=0.5)
    review_confidence = db.Column(db.Float, default=0.5)
    text_quality = db.Column(db.Float, default=0.5)
    price_factor = db.Column(db.Float, default=1.0)
    title_similarity = db.Column(db.Float, default=0.5)
    ratings = db.relationship('Rating', backref='product', lazy=True)

    def to_dict(self, include_trust=True):
        d = {
            'id': self.id,
            'asin': self.asin,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'image_url': self.image_url,
            'avg_rating': round(self.avg_rating, 2),
            'rating_count': self.rating_count,
        }
        if include_trust:
            d['trust'] = {
                'product_trust': round(self.product_trust, 3),
                'seller_trust': round(self.seller_trust, 3),
                'final_trust_score': round(self.final_trust_score, 3),
                'details': {
                    'avg_rating_norm': round(self.avg_rating_norm, 3),
                    'verified_ratio': round(self.verified_ratio, 3),
                    'review_confidence': round(self.review_confidence, 3),
                    'text_quality': round(self.text_quality, 3),
                    'price_factor': round(self.price_factor, 3),
                    'title_similarity': round(self.title_similarity, 3),
                }
            }
        return d


class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review_text = db.Column(db.Text)
    verified_purchase = db.Column(db.Boolean, default=False)
    helpful_votes = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='uq_user_product'),)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'rating': self.rating,
            'review_text': self.review_text,
            'verified_purchase': self.verified_purchase,
            'helpful_votes': self.helpful_votes,
            'timestamp': self.timestamp.isoformat()
        }


class RecommendationLog(db.Model):
    __tablename__ = 'recommendation_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    algorithm = db.Column(db.String(50))
    score = db.Column(db.Float)
    clicked = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)