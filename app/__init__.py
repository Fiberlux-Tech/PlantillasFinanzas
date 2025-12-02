# app/__init__.py

import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    # We are NOT setting static_folder or static_url_path
    # Nginx will handle serving the frontend files.
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure logging to show INFO level messages
    app.logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    db.init_app(app)
    migrate.init_app(app, db)
    
    # CORS is now CRITICAL because your frontend and backend
    # are on the same domain but served by different processes.
    CORS(app, supports_credentials=True, origins=[
        "http://10.100.23.164", # Your specific frontend IP
        "http://127.0.0.1:5000",  # Allow localhost access
        "http://localhost:5000",  # Allow localhost access
        "http://127.0.0.1",
        "http://localhost"
    ])
    
    login_manager.init_app(app) 
    
    # --- 1. SET THE CORRECT 401 HANDLER FOR A SPA ---
    @login_manager.unauthorized_handler
    def unauthorized():
        # Send a 401 error, which React will catch
        return jsonify({"message": "Authentication required."}), 401
    
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

    # Register the existing auth blueprint
    from .auth import bp as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth') 

    with app.app_context():
        from . import models
                
        @login_manager.user_loader
        def load_user(user_id):
            from .models import User
            return db.session.get(User, int(user_id))

    return app