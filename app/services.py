import pandas as pd
import numpy as np
import numpy_financial as npf
from flask import current_app
from flask_login import current_user, login_required # <-- NEW IMPORTS
from sqlalchemy import or_ # <-- NEW IMPORT for complex filtering
from . import db
from .models import Transaction, FixedCost, RecurringService, User
import json
from datetime import datetime

# --- HELPER FUNCTIONS ---

def _generate_unique_id(customer_name, business_unit):
    """
    Generates a unique transaction ID based on the specified format.
    FLX(YYYY)-MMDDHHSS-(3 first letters from customer name)-(3 first letters from unidadNegocio)
    """
    now = datetime.now()
    date_part = now.strftime("%Y-%m%d%H%M%S")

    # Safely get the first 3 letters, even if the strings are short
    customer_part = (customer_name or "XXX")[:3].upper()
    unit_part = (business_unit or "XXX")[:3].upper()

    return f"FLX{date_part}-{customer_part}-{unit_part}"


def _convert_numpy_types(obj):
    """
    Recursively converts numpy numeric types in a dictionary or list to standard Python types
    to ensure proper JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(i) for i in obj]
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32)):
        if np.isnan(obj):
            return None
        return float(obj)
    elif pd.isna(obj):
        return None
    return obj


def _calculate_financial_metrics(data):
    """
    Private helper function to calculate financial metrics based on extracted data.
    """
    # NOTE: Assuming safe_float conversion was applied to header_data before this call
    costoCapitalAnual = data.get('costoCapitalAnual', 0)
    plazoContrato = int(data.get('plazoContrato', 0))
    MRC = data.get('MRC', 0)
    NRC = data.get('NRC', 0)
    comisiones = data.get('comisiones', 0)
    costoInstalacion = data.get('costoInstalacion', 0)
    tipoCambio = data.get('tipoCambio', 1)

    total_monthly_expense = sum(item.get('egreso', 0) for item in data.get('recurring_services', []))

    totalRevenue = NRC + (MRC * plazoContrato)
    upfront_costs = (costoInstalacion * tipoCambio) + comisiones
    total_monthly_expense_converted = total_monthly_expense * tipoCambio
    totalExpense = upfront_costs + (total_monthly_expense_converted * plazoContrato)
    grossMargin = totalRevenue - totalExpense

    initial_cash_flow = NRC - upfront_costs
    cash_flows = [initial_cash_flow]
    monthly_net_cash_flow = MRC - total_monthly_expense_converted
    cash_flows.extend([monthly_net_cash_flow] * plazoContrato)

    try:
        monthly_discount_rate = costoCapitalAnual / 12
        van = npf.npv(monthly_discount_rate, cash_flows)
    except Exception:
        van = None

    try:
        tir = npf.irr(cash_flows)
    except Exception:
        tir = None

    cumulative_cash_flow = 0
    payback = None
    for i, flow in enumerate(cash_flows):
        cumulative_cash_flow += flow
        if cumulative_cash_flow >= 0:
            payback = i
            break

    return {
        'VAN': van, 'TIR': tir, 'payback': payback, 'totalRevenue': totalRevenue,
        'totalExpense': totalExpense, 'comisionesRate': (comisiones / totalRevenue) if totalRevenue else 0,
        'costoInstalacionRatio': (costoInstalacion * tipoCambio / totalRevenue) if totalRevenue else 0,
        'grossMargin': grossMargin, 'grossMarginRatio': (grossMargin / totalRevenue) if totalRevenue else 0,
    }


# --- MAIN SERVICE FUNCTIONS ---

@login_required # <-- SECURITY WRAPPER ADDED
def get_transactions(page=1, per_page=30):
    """
    Retrieves a paginated list of transactions from the database, filtered by user role.
    - SALES: Only sees transactions where salesman matches current_user.username.
    - FINANCE/ADMIN: Sees all transactions.
    """
    try:
        # Start with the base query
        query = Transaction.query

        # --- ROLE-BASED FILTERING (NEW LOGIC) ---
        if current_user.role == 'SALES':
            # Filter to show only transactions uploaded by this salesman
            query = query.filter(Transaction.salesman == current_user.username)
        # ADMIN and FINANCE roles see all transactions, so no filter is needed.
        
        # Apply ordering and pagination
        transactions = query.order_by(Transaction.submissionDate.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        # ------------------------------------------

        return {
            "success": True,
            "data": {
                "transactions": [tx.to_dict() for tx in transactions.items],
                "total": transactions.total,
                "pages": transactions.pages,
                "current_page": transactions.page,
                # Optional: return user role for frontend context
                "user_role": current_user.role 
            }
        }
    except Exception as e:
        # NOTE: A failure here might mean the database filter failed or user is not logged in.
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

@login_required # <-- SECURITY WRAPPER ADDED
def get_transaction_details(transaction_id):
    """
    Retrieves a single transaction and its full details from the database by its string ID.
    Access control: SALES can only view their own transactions.
    """
    try:
        # Start with a base query
        query = Transaction.query.filter_by(id=transaction_id)
        
        # --- ROLE-BASED ACCESS CHECK (NEW LOGIC) ---
        if current_user.role == 'SALES':
            # SALES users can only load their own transactions
            query = query.filter(Transaction.salesman == current_user.username)
        
        transaction = query.first()
        # ------------------------------------------
        
        if transaction:
            return {
                "success": True,
                "data": {
                    "transactions": transaction.to_dict(),
                    "fixed_costs": [fc.to_dict() for fc in transaction.fixed_costs],
                    "recurring_services": [rs.to_dict() for rs in transaction.recurring_services]
                }
            }
        else:
            # Return Not Found if transaction ID doesn't exist OR if the user doesn't have permission
            return {"success": False, "error": "Transaction not found or access denied."}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

@login_required # <-- SECURITY WRAPPER ADDED
def process_excel_file(excel_file):
    """
    Orchestrates the entire process of reading, validating, and calculating data from the uploaded Excel file.
    """
    try:
        # Access config variables from the current Flask app context
        config = current_app.config
        
        # =========================================================
        # FIX: Define the local helper function here
        # =========================================================
        def safe_float(val):
            """Converts value to float, treating non-numeric/NaN values as 0.0."""
            if pd.notna(val):
                try:
                    # Attempt to convert to float
                    return float(val)
                except (ValueError, TypeError):
                    # Catch cases like unexpected strings
                    return 0.0
            return 0.0
        # =========================================================

        # Step 3: Read & Extract Data
        header_data = {}
        for var_name, cell in config['VARIABLES_TO_EXTRACT'].items():
            # NOTE: Re-reading the entire Excel file for every cell is inefficient. 
            # Ideally, read once outside the loop. Left as-is for now based on your previous code.
            df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None)
            col_idx = ord(cell[0].upper()) - ord('A')
            row_idx = int(cell[1:]) - 1
            value = df.iloc[row_idx, col_idx]

            # Apply safe_float ONLY to fields expected to be numeric
            if var_name in ['MRC', 'NRC', 'costoCapitalAnual', 'plazoContrato', 'comisiones', 'tipoCambio', 'companyID', 'orderID']: 
                header_data[var_name] = safe_float(value)
            else:
                # Keep as is for string fields like clientName, salesman
                header_data[var_name] = value

        # ... (rest of extraction and calculation logic) ...
        
        services_col_indices = [ord(c.upper()) - ord('A') for c in config['RECURRING_SERVICES_COLUMNS'].values()]
        services_df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None, skiprows=config['RECURRING_SERVICES_START_ROW'], usecols=services_col_indices)
        services_df.columns = config['RECURRING_SERVICES_COLUMNS'].keys()
        recurring_services_data = services_df.dropna(how='all').to_dict('records')

        fixed_costs_col_indices = [ord(c.upper()) - ord('A') for c in config['FIXED_COSTS_COLUMNS'].values()]
        fixed_costs_df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None, skiprows=config['FIXED_COSTS_START_ROW'], usecols=fixed_costs_col_indices)
        fixed_costs_df.columns = config['FIXED_COSTS_COLUMNS'].keys()
        fixed_costs_data = fixed_costs_df.dropna(how='all').to_dict('records')

        # Calculate totals for preview
        for item in fixed_costs_data:
            if pd.notna(item.get('cantidad')) and pd.notna(item.get('costoUnitario')):
                item['total'] = item['cantidad'] * item['costoUnitario']

        for item in recurring_services_data:
            q = safe_float(item.get('Q', 0))
            p = safe_float(item.get('P', 0))
            cu1 = safe_float(item.get('CU1', 0))
            cu2 = safe_float(item.get('CU2', 0))

            item['ingreso'] = q * p
            item['egreso'] = (cu1 + cu2) * q

        calculated_costoInstalacion = sum(
            item.get('total', 0) for item in fixed_costs_data if pd.notna(item.get('total')))

        # Step 4: Validate Inputs
        if pd.isna(header_data.get('clientName')) or pd.isna(header_data.get('MRC')):
            return {"success": False, "error": "Required field 'Client Name' or 'MRC' is missing from the Excel file."}

        # Consolidate all extracted data
        full_extracted_data = {**header_data, 'recurring_services': recurring_services_data,
                               'fixed_costs': fixed_costs_data, 'costoInstalacion': calculated_costoInstalacion}

        # Step 5: Calculate Metrics
        financial_metrics = _calculate_financial_metrics(full_extracted_data)

        # Step 6: Assemble the Final Response
        transaction_summary = {**header_data, **financial_metrics, "costoInstalacion": calculated_costoInstalacion,
                               "submissionDate": None, "ApprovalStatus": "PENDING"}

        final_data_package = {"transactions": transaction_summary, "fixed_costs": fixed_costs_data,
                              "recurring_services": recurring_services_data}

        clean_data = _convert_numpy_types(final_data_package)

        return {"success": True, "data": clean_data}

    except Exception as e:
        import traceback
        print("--- ERROR DURING EXCEL PROCESSING ---")
        print(traceback.format_exc())
        print("--- END ERROR ---")
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}


@login_required # <-- SECURITY WRAPPER ADDED
def save_transaction(data):
    """
    Saves a new transaction and its related costs to the database.
    NOTE: Overwrites the 'salesman' field with the currently logged-in user's username.
    """
    try:
        tx_data = data.get('transactions', {})
        
        # --- SALESMAN OVERWRITE (NEW LOGIC) ---
        # Overwrite the salesman field with the current authenticated user's username
        tx_data['salesman'] = current_user.username 
        # --------------------------------------

        unique_id = _generate_unique_id(tx_data.get('clientName'), tx_data.get('unidadNegocio'))

        # Create the main Transaction object
        new_transaction = Transaction(
            # ... (all the fields for the new transaction)
            id=unique_id, # Use the generated ID
            unidadNegocio=tx_data.get('unidadNegocio'), clientName=tx_data.get('clientName'),
            companyID=tx_data.get('companyID'), salesman=tx_data['salesman'], # Use the overwritten salesman
            orderID=tx_data.get('orderID'), tipoCambio=tx_data.get('tipoCambio'),
            MRC=tx_data.get('MRC'), NRC=tx_data.get('NRC'), VAN=tx_data.get('VAN'),
            TIR=tx_data.get('TIR'), payback=tx_data.get('payback'),
            totalRevenue=tx_data.get('totalRevenue'), totalExpense=tx_data.get('totalExpense'),
            comisiones=tx_data.get('comisiones'), comisionesRate=tx_data.get('comisionesRate'),
            costoInstalacion=tx_data.get('costoInstalacion'),
            costoInstalacionRatio=tx_data.get('costoInstalacionRatio'),
            grossMargin=tx_data.get('grossMargin'), grossMarginRatio=tx_data.get('grossMarginRatio'),
            plazoContrato=tx_data.get('plazoContrato'), costoCapitalAnual=tx_data.get('costoCapitalAnual'),
            ApprovalStatus='PENDING'
        )
        db.session.add(new_transaction)

        # Loop through fixed costs and add them
        for cost_item in data.get('fixed_costs', []):
            new_cost = FixedCost(
                transaction=new_transaction, categoria=cost_item.get('categoria'),
                tipo_servicio=cost_item.get('tipo_servicio'), ticket=cost_item.get('ticket'),
                ubicacion=cost_item.get('ubicacion'), cantidad=cost_item.get('cantidad'),
                costoUnitario=cost_item.get('costoUnitario')
            )
            db.session.add(new_cost)

        # Loop through recurring services and add them
        for service_item in data.get('recurring_services', []):
            new_service = RecurringService(
                transaction=new_transaction, tipo_servicio=service_item.get('tipo_servicio'),
                nota=service_item.get('nota'), ubicacion=service_item.get('ubicacion'),
                Q=service_item.get('Q'), P=service_item.get('P'),
                CU1=service_item.get('CU1'), CU2=service_item.get('CU2'),
                proveedor=service_item.get('proveedor')
            )
            db.session.add(new_service)

        # --- DIAGNOSTIC CHANGES ---
        db.session.flush()
        new_id = new_transaction.id
        print(f"--- DIAGNOSTIC: Attempting to commit transaction with temporary ID: {new_id} by user {current_user.username} ---")

        db.session.commit()

        print(f"--- DIAGNOSTIC: Commit successful for transaction ID: {new_id} ---")

        return {"success": True, "message": "Transaction saved successfully.", "transaction_id": new_id}

    except Exception as e:
        db.session.rollback() # Roll back the transaction if any error occurs
        import traceback
        print("--- ERROR DURING SAVE ---")
        print(traceback.format_exc())
        print("--- END ERROR ---")
        return {"success": False, "error": f"Database error: {str(e)}"}

@login_required # <-- SECURITY WRAPPER ADDED
def approve_transaction(transaction_id):
    """
    Approves a transaction by updating its status and approval date.
    """
    try:
        # NOTE: Approval should likely be restricted to FINANCE or ADMIN roles
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction not found."}

        transaction.ApprovalStatus = 'APPROVED'
        transaction.approvalDate = datetime.utcnow()
        db.session.commit()
        return {"success": True, "message": "Transaction approved successfully."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Database error: {str(e)}"}

@login_required # <-- SECURITY WRAPPER ADDED
def reject_transaction(transaction_id):
    """
    Rejects a transaction by updating its status and approval date.
    """
    try:
        # NOTE: Rejection should likely be restricted to FINANCE or ADMIN roles
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction not found."}

        transaction.ApprovalStatus = 'REJECTED'
        transaction.approvalDate = datetime.utcnow()
        db.session.commit()
        return {"success": True, "message": "Transaction rejected successfully."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Database error: {str(e)}"}
    
# ---------------------------------------------------------------------------------------
# --- NEW ADMIN USER MANAGEMENT SERVICES ---

@login_required 
def get_all_users():
    """Fetches all users, excluding sensitive data like password_hash, for the Admin dashboard."""
    # This function relies on admin_required decorator in routes.py for security.
    try:
        users = User.query.all()
        # Explicitly select fields to ensure password_hash is not returned
        user_list = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            } 
            for user in users
        ]
        return {"success": True, "users": user_list}
    except Exception as e:
        return {"success": False, "error": f"Database error fetching users: {str(e)}"}


@login_required 
def update_user_role(user_id, new_role):
    """Updates the role of a specified user."""
    try:
        # 1. Input validation
        if new_role not in ['SALES', 'FINANCE', 'ADMIN']:
            return {"success": False, "error": "Invalid role specified."}
        
        # 2. Check for user existence
        user = db.session.get(User, user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        # 3. Update and commit
        user.role = new_role
        db.session.commit()
        return {"success": True, "message": f"Role for user {user.username} updated to {new_role}."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Could not update role: {str(e)}"}


@login_required 
def reset_user_password(user_id, new_password):
    """Sets a new temporary password for a specified user."""
    try:
        # 1. Check for user existence
        user = db.session.get(User, user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        # 2. Set new password (uses the secure hashing method from models.py)
        user.set_password(new_password) 
        db.session.commit()
        return {"success": True, "message": f"Password for user {user.username} successfully reset."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Could not reset password: {str(e)}"}