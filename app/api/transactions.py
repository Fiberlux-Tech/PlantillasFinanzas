# app/api/transactions.py
# (This file is for all transaction related routes.)

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.utils import finance_admin_required, allowed_file, _handle_service_result

# --- IMPORT UPDATED ---
# We now import 'process_excel_file' from its new location
from app.services.excel_parser import process_excel_file

# All other services are still in the main 'transactions' service file
from app.services.transactions import (
    save_transaction,
    get_transactions,
    get_transaction_details,
    approve_transaction,
    reject_transaction,
    recalculate_commission_and_metrics,
    calculate_preview_metrics
)
# ----------------------
from app.services.fixed_costs import lookup_investment_codes, lookup_recurring_services
from app.services.kpi import (
    get_pending_mrc_sum,
    get_pending_transaction_count,
    get_pending_comisiones_sum,
    get_average_gross_margin
)

bp = Blueprint('transactions', __name__)

@bp.route('/process-excel', methods=['POST'])
@login_required 
def process_excel_route():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part in the request"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    if file and allowed_file(file.filename):
        # This call now correctly uses the imported function from excel_parser.py
        result = process_excel_file(file)
        # Service returns a tuple (dict, status) on 400 or 500 error
        return _handle_service_result(result)
    else:
        return jsonify(
            {"success": False, "error": "Invalid file type. Please upload an Excel file (.xlsx, .xls)."}), 400

@bp.route('/calculate-preview', methods=['POST'])
@login_required
def calculate_preview_route():
    """
    Receives temporary transaction data from the frontend modal,
    recalculates all KPIs, and returns the new KPIs.
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided in the request"}), 400
    
    # Call the new stateless preview service
    result = calculate_preview_metrics(data)
    
    # Service returns a tuple (dict, 400 or 500) on failure
    return _handle_service_result(result)

@bp.route('/submit-transaction', methods=['POST'])
@login_required 
def submit_transaction_route():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided in the request"}), 400
    result = save_transaction(data)
    # Service returns a tuple (dict, 500) on error
    return _handle_service_result(result)

@bp.route('/transactions', methods=['GET'])
@login_required 
def get_transactions_route():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    result = get_transactions(page=page, per_page=per_page) 
    return _handle_service_result(result)

@bp.route('/transaction/<string:transaction_id>', methods=['GET'])
@login_required 
def get_transaction_details_route(transaction_id):
    result = get_transaction_details(transaction_id) 
    # Service returns a tuple (dict, 404 or 500) on failure
    return _handle_service_result(result, default_error_status=404)


# --- SECURED STATUS CHANGE & CALCULATION ROUTES ---

@bp.route('/transaction/approve/<string:transaction_id>', methods=['POST'])
@login_required
@finance_admin_required 
def approve_transaction_route(transaction_id):
    result = approve_transaction(transaction_id)
    # Service returns a tuple (dict, 400, 404, or 500) on failure
    return _handle_service_result(result)

@bp.route('/transaction/reject/<string:transaction_id>', methods=['POST'])
@login_required
@finance_admin_required 
def reject_transaction_route(transaction_id):
    result = reject_transaction(transaction_id)
    # Service returns a tuple (dict, 400, 404, or 500) on failure
    return _handle_service_result(result)

@bp.route('/transaction/<string:transaction_id>/calculate-commission', methods=['POST'])
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

# --- NEW ROUTE FOR FIXED COST LOOKUP ---
@bp.route('/fixed-costs/lookup', methods=['POST'])
@login_required 
def lookup_fixed_costs_route():
    """
    Accepts a list of Investment Codes and returns structured FixedCost objects 
    from the external master database.
    """
    data = request.get_json()
    codes = data.get('investment_codes')

    if not codes or not isinstance(codes, list) or not all(isinstance(c, str) for c in codes):
        return jsonify({"success": False, "error": "Missing or invalid 'investment_codes' list of strings."}), 400
        
    result = lookup_investment_codes(codes) 
    # _handle_service_result handles the tuple (error_dict, status_code) on failure
    return _handle_service_result(result)

# --- NEW ROUTE FOR RECURRING SERVICE LOOKUP (dim_cotizacion_bi) ---
@bp.route('/recurring-services/lookup', methods=['POST'])
@login_required
def lookup_recurring_services_route():
    """
    Accepts a list of service codes ('quotation codes') and returns structured
    RecurringService objects from the external master database (dim_cotizacion_bi).
    """
    data = request.get_json()
    # CRITICAL: Check the key is 'service_codes' as per the frontend brief
    codes = data.get('service_codes')

    if not codes or not isinstance(codes, list) or not all(isinstance(c, str) for c in codes):
        return jsonify({"success": False, "error": "Missing or invalid 'service_codes' list of strings."}), 400

    result = lookup_recurring_services(codes)
    # _handle_service_result handles the tuple (error_dict, status_code) on failure
    return _handle_service_result(result)


# --- KPI ENDPOINTS ---
@bp.route('/kpi/pending-mrc', methods=['GET'])
@login_required
def get_pending_mrc_route():
    """
    Returns the sum of MRC for pending transactions.
    Role-based filtering:
    - SALES: Only their own transactions
    - FINANCE: All pending transactions
    - ADMIN: All pending transactions
    """
    result = get_pending_mrc_sum()
    return _handle_service_result(result)


@bp.route('/kpi/pending-count', methods=['GET'])
@login_required
def get_pending_count_route():
    """
    Returns the count of pending transactions.
    Role-based filtering:
    - SALES: Only their own transactions
    - FINANCE: All pending transactions
    - ADMIN: All pending transactions
    """
    result = get_pending_transaction_count()
    return _handle_service_result(result)


@bp.route('/kpi/pending-comisiones', methods=['GET'])
@login_required
def get_pending_comisiones_route():
    """
    Returns the sum of comisiones for pending transactions.
    Role-based filtering:
    - SALES: Only their own transactions
    - FINANCE: All pending transactions
    - ADMIN: All pending transactions
    """
    result = get_pending_comisiones_sum()
    return _handle_service_result(result)


@bp.route('/kpi/average-gross-margin', methods=['GET'])
@login_required
def get_average_gross_margin_route():
    """
    Returns the average gross margin ratio for transactions.
    Role-based filtering:
    - SALES: Only their own transactions
    - FINANCE: All transactions
    - ADMIN: All transactions

    Query parameters (optional):
    - months_back: Filter transactions from last N months (e.g., ?months_back=3)
    - status: Filter by approval status (e.g., ?status=APPROVED)
    """
    # Get optional query parameters
    months_back = request.args.get('months_back', type=int)
    status_filter = request.args.get('status', type=str)

    result = get_average_gross_margin(months_back=months_back, status_filter=status_filter)
    return _handle_service_result(result)