# routes.py

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from .utils import admin_required, finance_admin_required, get_editable_categories # <-- get_editable_categories is new
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

# --- MASTER VARIABLE ROUTES (NEW) ---

@api.route('/master-variables', methods=['GET'])
@login_required # Everyone can view (as required)
def master_variables_route():
    """
    Returns the historical record of master variables.
    """
    category = request.args.get('category')
    result = get_all_master_variables(category)
    return jsonify(result), (200 if result["success"] else 400)

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
    
    # Return appropriate status code based on service success/failure (including 403 from RBAC)
    if result["success"]:
        return jsonify(result), 200
    else:
        # NOTE: The update_master_variable service now returns a tuple (dict, status_code) on error.
        # Check if the service returned a custom error status code (like 403)
        status_code = 400
        if isinstance(result, tuple) and len(result) == 2:
             status_code = result[1]
             result = result[0]
             
        return jsonify(result), status_code

@api.route('/master-variables/categories', methods=['GET'])
@login_required
def get_user_categories_route():
    """
    Returns a list of categories the current user is authorized to edit.
    Used for frontend UI filtering.
    """
    # 1. Call the fixed utility function
    categories = get_editable_categories()
    
    # 2. Access config for filtering (uses current_app safely)
    MASTER_VARIABLE_ROLES = current_app.config['MASTER_VARIABLE_ROLES']
    
    # Filter the full config to only include variables from categories the user can edit
    editable_variables = {}
    for name, config in MASTER_VARIABLE_ROLES.items():
        if config['category'] in categories:
            editable_variables[name] = config

    return jsonify({
        "success": True,
        "editable_categories": categories,
        "editable_variables": editable_variables,
    }), 200

@api.route('/process-excel', methods=['POST'])
@login_required # Standard security: must be logged in to upload
def process_excel_route():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    if file and allowed_file(file.filename):
        result = process_excel_file(file)
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400
    else:
        return jsonify(
            {"success": False, "error": "Invalid file type. Please upload an Excel file (.xlsx, .xls)."}), 400

@api.route('/submit-transaction', methods=['POST'])
@login_required # Standard security: must be logged in to save
def submit_transaction_route():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided in the request"}), 400
    result = save_transaction(data)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

@api.route('/transactions', methods=['GET'])
@login_required # Standard security: must be logged in to view the dashboard
def get_transactions_route():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    # Role-based data filtering is handled inside get_transactions
    result = get_transactions(page=page, per_page=per_page) 
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

@api.route('/transaction/<string:transaction_id>', methods=['GET'])
@login_required # Standard security: must be logged in to view details
def get_transaction_details_route(transaction_id):
    # Role-based data access is handled inside get_transaction_details
    result = get_transaction_details(transaction_id) 
    if result["success"]:
        return jsonify(result)
    else:
        # Returns 404 for not found OR access denied (due to service logic)
        return jsonify(result), 404

@api.route('/transaction/approve/<string:transaction_id>', methods=['POST'])
@login_required
@finance_admin_required # 4. SECURITY: Only FINANCE or ADMIN can approve
def approve_transaction_route(transaction_id):
    result = approve_transaction(transaction_id)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

@api.route('/transaction/reject/<string:transaction_id>', methods=['POST'])
@login_required
@finance_admin_required # 5. SECURITY: Only FINANCE or ADMIN can reject
def reject_transaction_route(transaction_id):
    result = reject_transaction(transaction_id)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

# -----------------------------------------------------------------------------------
# --- NEW ADMIN ROUTES FOR USER MANAGEMENT ---
# -----------------------------------------------------------------------------------

@api.route('/admin/users', methods=['GET'])
@login_required 
@admin_required # 6. SECURITY: Only ADMIN can view all users
def get_all_users_route():
    """Returns a list of all users for admin dashboard."""
    result = get_all_users()
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

@api.route('/admin/users/<int:user_id>/role', methods=['POST'])
@login_required 
@admin_required # 7. SECURITY: Only ADMIN can update roles
def update_user_role_route(user_id):
    """Updates the role of a specified user."""
    data = request.get_json()
    new_role = data.get('role')

    if not new_role:
        return jsonify({"success": False, "error": "Role missing in request body."}), 400
        
    result = update_user_role(user_id, new_role)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400 

@api.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required 
@admin_required # 8. SECURITY: Only ADMIN can reset passwords
def reset_user_password_route(user_id):
    """Resets the password for a specified user."""
    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({"success": False, "error": "New password missing in request body."}), 400
        
    result = reset_user_password(user_id, new_password)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400
    
# -----------------------------------------------------------------------------------
# --- NEW COMMISSION CALCULATION ROUTE ---
# -----------------------------------------------------------------------------------

@api.route('/transaction/<string:transaction_id>/calculate-commission', methods=['POST'])
@login_required 
@finance_admin_required # SECURITY: Only FINANCE or ADMIN can trigger calculation
def calculate_commission_route(transaction_id):
    """
    Triggers the calculation of the official commission, updates the commission 
    value in the database, and recalculates all financial metrics (VAN, TIR).
    """
    # The service function handles all logic and returns the updated transaction details.
    result = recalculate_commission_and_metrics(transaction_id)

    if result["success"]:
        # Returns the full updated data structure for frontend refresh.
        return jsonify(result)
    else:
        return jsonify(result), 400