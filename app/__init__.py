# app/__init__.py

import os
import sys
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # We are NOT setting static_folder or static_url_path
    # Nginx will handle serving the frontend files.
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure logging to show INFO level messages (MOVED UP)
    # This must happen BEFORE validate_config() so validation warnings appear in logs
    app.logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # --- COLD START OPTIMIZED: Validate ONLY critical configuration ---
    # This ensures the app FAILS FAST if critical settings are missing
    # while deferring validation of non-critical settings (email, data warehouse)
    # to their respective services for faster serverless cold starts.
    try:
        Config.validate_critical_config()
    except ValueError as e:
        # Log the error and re-raise to prevent app startup
        print(str(e), file=sys.stderr)
        raise
    # ----------------------------------------------------------

    db.init_app(app)

    # IMPORTANT: Initialize Flask-Migrate for CLI commands ONLY
    # DO NOT run migrations here (db.upgrade(), alembic upgrade, etc.)
    # Migrations MUST be run in CI/CD pipeline before deployment
    # See: .github/workflows/deploy-*.yml and docs/DATABASE_MIGRATIONS.md
    migrate.init_app(app, db)

    # CORS is now CRITICAL because your frontend and backend
    # are on the same domain but served by different processes.
    # Origins are configured via environment variables for flexibility.
    CORS(app, supports_credentials=True, origins=app.config['CORS_ALLOWED_ORIGINS'])
    
    # --- 2. REGISTER BLUEPRINTS (REFACTORED) ---
    
    # Import the new blueprints from the app.api package
    from .api.transactions import bp as transactions_bp
    from .api.admin import bp as admin_bp
    from .api.variables import bp as variables_bp
    
    # Register them all with the original '/api' prefix
    # This ensures no frontend URLs need to change.
    app.register_blueprint(transactions_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')
    app.register_blueprint(variables_bp, url_prefix='/api')

    with app.app_context():
        from . import models

    return app