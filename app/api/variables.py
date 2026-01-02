# app/api/variables.py
# (This file will hold all master variable routes.)

from flask import Blueprint, request, jsonify, current_app
from app.jwt_auth import require_jwt
from app.utils import get_editable_categories, _handle_service_result
# --- IMPORT UPDATED ---
# We now import from the specific 'variables' service file
from app.services.variables import get_all_master_variables, update_master_variable
# ----------------------

bp = Blueprint('variables', __name__)

@bp.route('/master-variables', methods=['GET'])
@require_jwt 
def master_variables_route():
    """
    Returns the historical record of master variables.
    """
    category = request.args.get('category')
    result = get_all_master_variables(category)
    
    # get_all_master_variables now returns a tuple (dict, 500) on error.
    return _handle_service_result(result)

@bp.route('/master-variables/update', methods=['POST'])
@require_jwt 
def update_master_variable_route():
    """
    Updates a master variable, with dynamic RBAC enforced in the service layer.
    """
    data = request.get_json()
    variable_name = data.get('variable_name')
    value = data.get('variable_value')
    comment = data.get('comment')

    if not variable_name or value is None:
        return jsonify({"success": False, "error": "Missing variable_name or variable_value."}), 400

    result = update_master_variable(variable_name, value, comment)
    
    # The service returns a tuple (dict, status_code) on 400, 403, or 500 error, or a dict on success.
    return _handle_service_result(result)


@bp.route('/master-variables/categories', methods=['GET'])
@require_jwt
def get_user_categories_route():
    """
    Returns a list of categories the current user is authorized to edit.
    """
    categories = get_editable_categories()
    MASTER_VARIABLE_ROLES = current_app.config['MASTER_VARIABLE_ROLES']
    
    editable_variables = {}
    for name, config in MASTER_VARIABLE_ROLES.items():
        if config['category'] in categories:
            editable_variables[name] = config

    return jsonify({
        "success": True,
        "editable_categories": categories,
        "editable_variables": editable_variables,
    }), 200