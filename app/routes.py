# routes.py

from flask import Blueprint, request, jsonify
# 1. NEW: Import login_required from flask_login (standard security for all routes)
from flask_login import login_required 
# 2. NEW: Import the custom RBAC decorators from the new utils.py file
from .utils import admin_required, finance_admin_required 
from .services import (
    process_excel_file, 
    save_transaction, 
    get_transactions, 
    get_transaction_details, 
    approve_transaction, 
    reject_transaction,
    # 3. NEW: Import the new Admin service functions
    get_all_users, 
    update_user_role, 
    reset_user_password
)
from . import db

# Create a Blueprint object named 'api'
api = Blueprint('api', __name__)

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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