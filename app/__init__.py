import os 
from flask import Flask, jsonify # <-- Make sure jsonify is imported
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
    # This replaces your old 'login_manager.login_view'
    @login_manager.unauthorized_handler
    def unauthorized():
        # Send a 401 error, which React will catch
        return jsonify({"message": "Authentication required."}), 401
    
    # --- 2. REGISTER BLUEPRINTS (No change from your original) ---
    from .routes import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from .auth import bp as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth') 

    with app.app_context():
        from . import models
                
        @login_manager.user_loader
        def load_user(user_id):
            from .models import User
            return db.session.get(User, int(user_id))

    return app