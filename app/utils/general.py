# app/utils/general.py
"""
General-purpose utility functions.

This module contains helper functions for file validation, service result handling,
and role-based authorization helpers (re-exported from jwt_auth for backward compatibility).
"""

from functools import wraps
from flask import jsonify, current_app, g
from app.jwt_auth import admin_required, finance_admin_required

# --- NEW: Helper variables/functions moved from routes.py ---
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _handle_service_result(result, default_error_status=500):
    """
    Parses the result from a service function. 
    If it's a tuple (error_dict, status_code), it uses the custom status code.
    Otherwise, it assumes success (status 200) or uses the default error status.
    """
    # Check if the result is a tuple (error_dict, status_code)
    if isinstance(result, tuple) and len(result) == 2:
        error_dict, status_code = result
        return jsonify(error_dict), status_code
    
    # If not a tuple, check the 'success' key in the dictionary
    if result.get("success"):
        return jsonify(result), 200
    else:
        # Fallback for general errors (e.g., from an older service method)
        return jsonify(result), default_error_status
# -----------------------------------------------------------


# admin_required and finance_admin_required are now imported from jwt_auth
# They are re-exported here for backwards compatibility

def get_editable_categories():
    """
    Returns a list of unique categories the current user's role is authorized to edit.
    """
    user = getattr(g, 'current_user', None)

    if not user or not g.get('is_authenticated', False):
        return []

    MASTER_VARIABLE_ROLES = current_app.config['MASTER_VARIABLE_ROLES']

    editable_categories = set()
    user_role = user.role

    # CRITICAL FIX: Explicitly check for 'category' using safe iteration
    if user_role == 'ADMIN':
        # Retrieve all unique category names for the ADMIN role
        return list(set(config_item.get('category') for config_item in MASTER_VARIABLE_ROLES.values() if config_item.get('category')))

    # Logic for other roles (FINANCE, SALES, etc.)
    for config_item in MASTER_VARIABLE_ROLES.values():
        if config_item.get('write_role') == user_role:
            editable_categories.add(config_item.get('category'))

    return list(editable_categories)