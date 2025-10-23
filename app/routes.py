# routes.py

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from .utils import admin_required, finance_admin_required, get_editable_categories 
from .services import (
    process_excel_file, 
    save_transaction, 
    get_transactions, 
    get_transaction_details, 
    approve_transaction, 
    reject_transaction,
    recalculate_commission_and_metrics,
    get_all_users, 
    update_user_role, 
    reset_user_password,
    get_all_master_variables,
    update_master_variable
)
from . import db

# Create a Blueprint object named 'api'
api = Blueprint('api', __name__)

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper to handle service results that might return a tuple (dict, status_code) on error ---
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
# ----------------------------------------------------------------------------------------------


# --- MASTER VARIABLE ROUTES ---

@api.route('/master-variables', methods=['GET'])
@login_required 
def master_variables_route():
    """
    Returns the historical record of master variables.
    """
    category = request.args.get('category')
    result = get_all_master_variables(category)
    
    # get_all_master_variables now returns a tuple (dict, 500) on error.
    return _handle_service_result(result)

@api.route('/master-variables/update', methods=['POST'])
@login_required 
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


@api.route('/master-variables/categories', methods=['GET'])
@login_required
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

# --- TRANSACTION ROUTES ---

@api.route('/process-excel', methods=['POST'])
@login_required 
def process_excel_route():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    if file and allowed_file(file.filename):
        result = process_excel_file(file)
        # Service returns a tuple (dict, status) on 400 or 500 error
        return _handle_service_result(result)
    else:
        return jsonify(
            {"success": False, "error": "Invalid file type. Please upload an Excel file (.xlsx, .xls)."}), 400

@api.route('/submit-transaction', methods=['POST'])
@login_required 
def submit_transaction_route():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided in the request"}), 400
    result = save_transaction(data)
    # Service returns a tuple (dict, 500) on error
    return _handle_service_result(result)

@api.route('/transactions', methods=['GET'])
@login_required 
def get_transactions_route():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    result = get_transactions(page=page, per_page=per_page) 
    return _handle_service_result(result)

@api.route('/transaction/<string:transaction_id>', methods=['GET'])
@login_required 
def get_transaction_details_route(transaction_id):
    result = get_transaction_details(transaction_id) 
    # Service returns a tuple (dict, 404 or 500) on failure
    return _handle_service_result(result, default_error_status=404)


# -----------------------------------------------------------------------------------
# --- SECURED STATUS CHANGE & CALCULATION ROUTES ---
# -----------------------------------------------------------------------------------

@api.route('/transaction/approve/<string:transaction_id>', methods=['POST'])
@login_required
@finance_admin_required 
def approve_transaction_route(transaction_id):
    result = approve_transaction(transaction_id)
    # Service returns a tuple (dict, 400, 404, or 500) on failure
    return _handle_service_result(result)

@api.route('/transaction/reject/<string:transaction_id>', methods=['POST'])
@login_required
@finance_admin_required 
def reject_transaction_route(transaction_id):
    result = reject_transaction(transaction_id)
    # Service returns a tuple (dict, 400, 404, or 500) on failure
    return _handle_service_result(result)

@api.route('/transaction/<string:transaction_id>/calculate-commission', methods=['POST'])
@login_required 
@finance_admin_required 
def calculate_commission_route(transaction_id):
    """
    Triggers recalculation. Now strictly checks for ApprovalStatus='PENDING' 
    and returns 403 Forbidden otherwise.
    """
    result = recalculate_commission_and_metrics(transaction_id)
    # Service returns a tuple (dict, 403, 404, or 500) on failure
    return _handle_service_result(result)
    
# -----------------------------------------------------------------------------------
# --- ADMIN USER MANAGEMENT ROUTES ---
# -----------------------------------------------------------------------------------

@api.route('/admin/users', methods=['GET'])
@login_required 
@admin_required 
def get_all_users_route():
    """Returns a list of all users for admin dashboard."""
    result = get_all_users()
    return _handle_service_result(result)

@api.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required 
@admin_required 
def update_user_role_route(user_id):
    """Updates the role of a specified user."""
    data = request.get_json()
    new_role = data.get('role')

    if not new_role:
        return jsonify({"success": False, "error": "Role missing in request body."}), 400
        
    result = update_user_role(user_id, new_role)
    return _handle_service_result(result)

@api.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required 
@admin_required 
def reset_user_password_route(user_id):
    """Resets the password for a specified user."""
    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({"success": False, "error": "New password missing in request body."}), 400
        
    result = reset_user_password(user_id, new_password)
    return _handle_service_result(result)