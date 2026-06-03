import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base

DEFAULT_SQLITE = "sqlite:///./payments.db"

def init_db(app):
    database_url = os.environ.get("DATABASE_URL", DEFAULT_SQLITE)
    engine = create_engine(database_url, connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {})
    SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
    # Create tables if they don't exist (safe for initial dev)
    Base.metadata.create_all(bind=engine)
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['db_engine'] = engine
    app.extensions['db_session'] = SessionLocal

def get_db_session(app):
    """Return a SQLAlchemy session from the Flask `app`."""
    return app.extensions['db_session']()

from flask import Flask, jsonify


def create_app():
    app = Flask(__name__)
    init_db(app)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'healthy'}), 200

    from .main import bp as payment_bp
    app.register_blueprint(payment_bp, url_prefix='/payments')

    return app
