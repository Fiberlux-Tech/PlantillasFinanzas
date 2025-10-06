from flask import current_app as app, request, jsonify
from .services import process_excel_file, save_transaction, get_transactions
from . import db

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/process-excel', methods=['POST'])
def process_excel_route():
    """
    API endpoint to handle the initial Excel file upload and processing.
    It receives the file, passes it to the service layer for processing,
    and returns the structured data for the frontend preview.
    """
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


@app.route('/api/submit-transaction', methods=['POST'])
def submit_transaction_route():
    """
    API endpoint to handle the final submission of the transaction data.
    It receives the complete JSON package from the frontend preview,
    passes it to the service layer to be saved in the database,
    and returns a success response.
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided in the request"}), 400

    result = save_transaction(data)

    if result["success"]:
        return jsonify(result)
    else:
        # Use a 500 status code for a server-side database error
        return jsonify(result), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions_route():
    """
    API endpoint to retrieve a paginated list of transactions.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    result = get_transactions(page=page, per_page=per_page)
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500