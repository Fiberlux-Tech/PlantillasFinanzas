# app/api/transactions.py
# (This file is for all transaction related routes.)

from flask import Blueprint, request, jsonify
from app.jwt_auth import require_jwt, finance_admin_required
from app.utils import allowed_file, _handle_service_result

# --- IMPORT UPDATED ---
# We now import 'process_excel_file' from its new location
from app.services.excel_parser import process_excel_file

# All other services are still in the main 'transactions' service file
from app.services.transactions import (
    save_transaction,
    get_transactions,
    get_transaction_details,
    get_transaction_template,
    approve_transaction,
    reject_transaction,
    update_transaction_content,
    recalculate_commission_and_metrics,
    calculate_preview_metrics
)
# ----------------------
from app.services.kpi import (
    get_pending_mrc_sum,
    get_pending_transaction_count,
    get_pending_comisiones_sum,
    get_average_gross_margin,
    get_kpi_summary
)

bp = Blueprint('transactions', __name__)

@bp.route('/process-excel', methods=['POST'])
@require_jwt 
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
@require_jwt
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
@require_jwt 
def create_transaction_route():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided in the request"}), 400
    result = save_transaction(data)
    # Service returns a tuple (dict, 500) on error
    return _handle_service_result(result)

@bp.route('/transactions', methods=['GET'])
@require_jwt
def get_transactions_route():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    result = get_transactions(page=page, per_page=per_page)
    return _handle_service_result(result)


@bp.route('/transactions/template', methods=['GET'])
@require_jwt
def get_transaction_template_route():
    """
    Returns an empty transaction template pre-filled with current MasterVariables.
    Used by SALES users when creating new transactions without Excel upload.
    """
    result = get_transaction_template()
    return _handle_service_result(result)


@bp.route('/transaction/<string:transaction_id>', methods=['GET'])
@require_jwt
def get_transaction_details_route(transaction_id):
    result = get_transaction_details(transaction_id)
    # Service returns a tuple (dict, 404 or 500) on failure
    return _handle_service_result(result, default_error_status=404)

@bp.route('/transaction/<string:transaction_id>', methods=['PUT'])
@require_jwt
def update_transaction_route(transaction_id):
    """
    Updates a PENDING transaction's content without changing its status or ID.
    This is the dedicated endpoint for the "Edit/Save" feature.

    Access Control:
        - SALES: Can only update their own PENDING transactions
        - FINANCE/ADMIN: Can update any PENDING transaction

    Request Body:
        {
            "transactions": {...},      # Updated transaction fields
            "fixed_costs": [...],       # New/updated fixed costs
            "recurring_services": [...] # New/updated recurring services
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided in the request"}), 400

    result = update_transaction_content(transaction_id, data)
    # Service returns a tuple (dict, 403, 404, or 500) on failure
    return _handle_service_result(result)


# --- SECURED STATUS CHANGE & CALCULATION ROUTES ---

@bp.route('/transaction/approve/<string:transaction_id>', methods=['POST'])
@require_jwt
@finance_admin_required
def approve_transaction_route(transaction_id):
    # Parse optional request body containing updated transaction data
    data = request.get_json() or {}

    # Check if data contains transaction updates (beyond just metadata)
    # If the body has 'transactions', 'fixed_costs', or 'recurring_services', treat it as an update payload
    has_update_data = any(key in data for key in ['transactions', 'fixed_costs', 'recurring_services'])

    if has_update_data:
        # Pass the data payload to the service for pre-approval updates
        result = approve_transaction(transaction_id, data_payload=data)
    else:
        # No update data, just approve with existing values
        result = approve_transaction(transaction_id)

    # Service returns a tuple (dict, 400, 404, or 500) on failure
    return _handle_service_result(result)

@bp.route('/transaction/reject/<string:transaction_id>', methods=['POST'])
@require_jwt
@finance_admin_required
def reject_transaction_route(transaction_id):
    # Extract optional rejection note and transaction updates from request body
    data = request.get_json() or {}
    rejection_note = data.get('rejection_note')

    # Validate note length if provided
    if rejection_note and len(rejection_note) > 500:
        return jsonify({
            "success": False,
            "error": "Rejection note cannot exceed 500 characters."
        }), 400

    # Check if data contains transaction updates (beyond just the rejection note)
    # If the body has 'transactions', 'fixed_costs', or 'recurring_services', treat it as an update payload
    has_update_data = any(key in data for key in ['transactions', 'fixed_costs', 'recurring_services'])

    if has_update_data:
        # Pass both the rejection note and data payload to the service
        result = reject_transaction(transaction_id, rejection_note=rejection_note, data_payload=data)
    else:
        # Only rejection note, no transaction updates
        result = reject_transaction(transaction_id, rejection_note=rejection_note)

    # Service returns a tuple (dict, 400, 404, or 500) on failure
    return _handle_service_result(result)

@bp.route('/transaction/<string:transaction_id>/calculate-commission', methods=['POST'])
@require_jwt 
@finance_admin_required 
def calculate_commission_route(transaction_id):
    """
    Triggers recalculation. Checks for ApprovalStatus == 'PENDING'
    and returns 403 Forbidden otherwise.
    """
    result = recalculate_commission_and_metrics(transaction_id)
    # Service returns a tuple (dict, 403, 404, or 500) on failure
    return _handle_service_result(result)

# --- KPI ENDPOINTS ---
@bp.route('/kpi/pending-mrc', methods=['GET'])
@require_jwt
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
@require_jwt
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
@require_jwt
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
@require_jwt
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


@bp.route('/kpi/summary', methods=['GET'])
@require_jwt
def get_kpi_summary_route():
    """
    Consolidated KPI endpoint — returns all dashboard metrics in a single response.
    Query parameters (optional):
    - months_back: Filter average margin by last N months
    - status: Filter average margin by approval status
    """
    months_back = request.args.get('months_back', type=int)
    status_filter = request.args.get('status', type=str)
    result = get_kpi_summary(months_back=months_back, status_filter=status_filter)
    return _handle_service_result(result)