# app/api/admin.py
# (This file will hold all admin/user management routes.)

from flask import Blueprint, request, jsonify
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