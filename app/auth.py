# auth.py

from flask import Blueprint, jsonify, g
from app.jwt_auth import require_jwt

# Define the Blueprint
bp = Blueprint('auth', __name__)


@bp.route('/me', methods=['GET'])
@require_jwt
def get_current_user():
    """
    Returns the current user's profile information from the JWT token.

    This endpoint is used by the frontend to verify authentication status
    and retrieve user details after Supabase login.

    Authentication:
        - Handled by Supabase on the frontend
        - Backend verifies JWT token via @require_jwt decorator

    Response:
        200: User details with authentication status
        401: Invalid or missing token
    """
    user = g.current_user

    return jsonify({
        "is_authenticated": True,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "user_id": user.id
    }), 200


# REMOVED: /register endpoint (handled by Supabase)
# REMOVED: /login endpoint (handled by Supabase)
# REMOVED: /logout endpoint (handled by Supabase frontend - just delete token)
# REMOVED: /setup/create_default_users (no longer needed)

# NOTE FOR DEVELOPERS:
# User registration and login are now handled entirely by Supabase:
# - Frontend uses Supabase client library for signup/signin
# - Supabase returns JWT token to frontend
# - Frontend includes token in Authorization header for all API requests
# - Backend verifies token using @require_jwt decorator
