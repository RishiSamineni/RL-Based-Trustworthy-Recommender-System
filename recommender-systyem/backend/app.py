from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    jwt.init_app(app)

    from routes.auth import auth_bp
    from routes.items import items_bp
    from routes.recommendations import rec_bp
    from routes.ratings import ratings_bp
    from routes.analytics import analytics_bp

    app.register_blueprint(auth_bp,      url_prefix='/api/auth')
    app.register_blueprint(items_bp,     url_prefix='/api/items')
    app.register_blueprint(rec_bp,       url_prefix='/api/recommendations')
    app.register_blueprint(ratings_bp,   url_prefix='/api/ratings')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    with app.app_context():
        db.create_all()
        from seed import seed_data
        seed_data(db)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)