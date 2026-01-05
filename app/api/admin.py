# app/api/admin.py
# (This file will hold all admin/user management routes.)

from flask import Blueprint, request, jsonify, g
from app.jwt_auth import require_jwt, admin_required
from app.utils import _handle_service_result
# --- IMPORT UPDATED ---
# We now import from the specific 'users' service file
from app.services.users import (
    get_all_users, 
    update_user_role, 
    reset_user_password
)
# ----------------------

bp = Blueprint('admin', __name__)

@bp.route('/admin/users', methods=['GET'])
@require_jwt 
@admin_required 
def get_all_users_route():
    """Returns a list of all users for admin dashboard."""
    result = get_all_users()
    return _handle_service_result(result)

@bp.route('/admin/users/<int:user_id>/role', methods=['POST'])
@require_jwt 
@admin_required 
def update_user_role_route(user_id):
    """Updates the role of a specified user."""
    data = request.get_json()
    new_role = data.get('role')

    if not new_role:
        return jsonify({"success": False, "error": "Role missing in request body."}), 400
        
    result = update_user_role(user_id, new_role)
    return _handle_service_result(result)

@bp.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@require_jwt
@admin_required
def reset_user_password_route(user_id):
    """Resets the password for a specified user."""
    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({"success": False, "error": "New password missing in request body."}), 400

    result = reset_user_password(user_id, new_password)
    return _handle_service_result(result)

# --- User Profile Endpoint ---
@bp.route('/me', methods=['GET'])
@require_jwt
def get_current_user_profile():
    """
    Returns the current user's profile information from JWT token.

    This endpoint is used by the frontend to verify authentication status
    and retrieve user details after Supabase login.

    Authentication:
        - Handled by Supabase on frontend
        - Backend verifies JWT token via @require_jwt decorator
        - User context extracted from token (no database lookup)

    Response:
        200: User profile with authentication status
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