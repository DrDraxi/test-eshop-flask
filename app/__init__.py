import os
from flask import Flask
from app.config import Config
from app.extensions import db, migrate, mail


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Register Jinja2 template filters
    from app.helpers import format_price
    app.jinja_env.filters["format_price"] = format_price

    # Register blueprints
    from app.store import bp as store_bp
    from app.admin import bp as admin_bp
    from app.api import bp as api_bp

    app.register_blueprint(store_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Import models so they are registered with SQLAlchemy
    from app import models  # noqa: F401

    # Create database tables (skip if they already exist)
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if not inspector.get_table_names():
            db.create_all()

    return app
