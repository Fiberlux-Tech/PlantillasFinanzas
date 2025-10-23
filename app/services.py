# services.py

import pandas as pd
import numpy as np
import numpy_financial as npf
from flask import current_app
from flask_login import current_user, login_required
from sqlalchemy import or_, desc, func 
from . import db
from .models import Transaction, FixedCost, RecurringService, User, MasterVariable
import json
from datetime import datetime

# --- HELPER FUNCTIONS ---

def _generate_unique_id(customer_name, business_unit):
    """
    Generates a unique transaction ID using microseconds for maximum granularity.
    
    Format: FLXYYYY(UNIT PART)-MMDDHHMMSSFFFFFF
    """
    now = datetime.now()
    
    # 1. Extract the Date/Time Components
    year_part = now.strftime("%Y")    
    datetime_micro_part = now.strftime("%m%d%H%M%S%f") 
    
    # 2. Extract the Unit Part
    unit_part = (business_unit or "XXX")[:3].upper()

    # 3. Construct the new ID
    return f"FLX{year_part}{unit_part}-{datetime_micro_part}"

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

# --- COMMISSION CALCULATION HELPERS (Adapted to Transaction Model) ---

def _calculate_estado_commission(transaction):
    """
    Handles the commission calculation for 'ESTADO' using Transaction model attributes.
    ---
    NOTE: Logic now uses transaction.grossMarginRatio and checks plazoContrato 
    for Pago Unico deals, as suggested.
    ---
    """
    total_revenues = transaction.totalRevenue or 0
    
    if total_revenues == 0:
        return 0.0

    plazo = transaction.plazoContrato or 0
    payback = transaction.payback
    mrc = transaction.MRC or 0
    payback_ok = (payback is not None)
    rentabilidad = transaction.grossMarginRatio or 0.0
    final_commission_amount = 0.0
    commission_rate = 0.0

    # Pago Unico is defined as a contract term of 1 month or less.
    is_pago_unico = (plazo <= 1)

    if is_pago_unico:
        # PAGO UNICO LOGIC
        limit_pen = 0.0
        if 0.30 <= rentabilidad <= 0.35:
            commission_rate, limit_pen = 0.01, 11000
        elif 0.35 < rentabilidad <= 0.39:
            commission_rate, limit_pen = 0.02, 12000
        elif 0.39 < rentabilidad <= 0.49:
            commission_rate, limit_pen = 0.03, 13000
        elif 0.49 < rentabilidad <= 0.59:
            commission_rate, limit_pen = 0.04, 14000
        elif rentabilidad > 0.59:
            commission_rate, limit_pen = 0.05, 15000

        if commission_rate > 0:
            calculated_commission = total_revenues * commission_rate
            final_commission_amount = min(calculated_commission, limit_pen)
    else:
        # RECURRENT DEAL LOGIC (Plazo dependent)
        limit_mrc_multiplier = 0.0

        if plazo == 12:
            if 0.30 <= rentabilidad <= 0.35 and payback_ok and payback <= 7:
                commission_rate, limit_mrc_multiplier = 0.025, 0.8
            elif 0.35 < rentabilidad <= 0.39 and payback_ok and payback <= 7:
                commission_rate, limit_mrc_multiplier = 0.03, 0.9
            elif rentabilidad > 0.39 and payback_ok and payback <= 6:
                commission_rate, limit_mrc_multiplier = 0.035, 1.0
        elif plazo == 24:
            if 0.30 <= rentabilidad <= 0.35 and payback_ok and payback <= 11:
                commission_rate, limit_mrc_multiplier = 0.025, 0.8
            elif 0.35 < rentabilidad <= 0.39 and payback_ok and payback <= 11:
                commission_rate, limit_mrc_multiplier = 0.03, 0.9
            elif rentabilidad > 0.39 and payback_ok and payback <= 10:
                commission_rate, limit_mrc_multiplier = 0.035, 1.0
        elif plazo == 36:
            if 0.30 <= rentabilidad <= 0.35 and payback_ok and payback <= 19:
                commission_rate, limit_mrc_multiplier = 0.025, 0.8
            elif 0.35 < rentabilidad <= 0.39 and payback_ok and payback <= 19:
                commission_rate, limit_mrc_multiplier = 0.03, 0.9
            elif rentabilidad > 0.39 and payback_ok and payback <= 18:
                commission_rate, limit_mrc_multiplier = 0.035, 1.0
        elif plazo == 48:
            if 0.30 <= rentabilidad <= 0.35 and payback_ok and payback <= 26:
                commission_rate, limit_mrc_multiplier = 0.02, 0.8
            elif 0.35 < rentabilidad <= 0.39 and payback_ok and payback <= 26:
                commission_rate, limit_mrc_multiplier = 0.025, 0.9
            elif rentabilidad > 0.39 and payback_ok and payback <= 25:
                commission_rate, limit_mrc_multiplier = 0.03, 1.0
        
        # All other plazo values (e.g., 60 months) default to 0 commission rate

        if commission_rate > 0.0:
            calculated_commission = total_revenues * commission_rate
            limit_mrc_amount = mrc * limit_mrc_multiplier
            final_commission_amount = min(calculated_commission, limit_mrc_amount)

    return final_commission_amount

def _calculate_gigalan_commission(transaction):
    """
    Calculates the GIGALAN commission using the data stored in the transaction model
    (gigalan_region, gigalan_sale_type, gigalan_old_mrc).
    """
    
    # --- 1. Map new model attributes to local variables ---
    region = transaction.gigalan_region
    sale_type = transaction.gigalan_sale_type
    old_mrc = transaction.gigalan_old_mrc or 0.0 # Use 0.0 if None
    # ---

    # --- 2. Access existing financial metrics from the model ---
    payback = transaction.payback
    total_revenue = transaction.totalRevenue or 1 # Avoid division by zero
    gross_margin = transaction.grossMargin or 0
    rentabilidad = gross_margin / total_revenue
    
    plazo = transaction.plazoContrato or 0
    mrc = transaction.MRC or 0
    # ---
    
    # Initialize variables
    commission_rate = 0.0
    calculated_commission = 0.0

    # --- 3. Initial Validation (Handles incomplete GIGALAN inputs) ---
    if not region or not sale_type:
        print("DIAGNOSTIC: GIGALAN inputs (region/sale_type) missing. Returning 0 commission.")
        return 0.0
    
    # --- 4. Payback Period Rule ---
    # NOTE: The existing logic already uses the correct model attribute: transaction.payback
    #if payback is None or payback > 2:
    if payback >= 2:
        # print("\nADVERTENCIA: Payback > 2 meses. No aplica comisión.") # Optional diagnostic
        return 0.0

    # --- 5. FULL GIGALAN COMMISSION LOGIC (Refactored) ---
    # The 'project_type' from your old code is now 'sale_type'
    if region == 'LIMA':
        if sale_type == 'NUEVO':
            if 0.40 <= rentabilidad < 0.50:
                commission_rate = 0.009
            elif 0.50 <= rentabilidad < 0.60:
                commission_rate = 0.014
            elif 0.60 <= rentabilidad < 0.70:
                commission_rate = 0.019
            elif rentabilidad >= 0.70:
                commission_rate = 0.024
        elif sale_type == 'EXISTENTE':
            # NOTE: Your logic uses 'UPGRADE' as the type for existing sales.
            if 0.40 <= rentabilidad < 0.50:
                commission_rate = 0.01
            elif 0.50 <= rentabilidad < 0.60:
                commission_rate = 0.015
            elif 0.60 <= rentabilidad < 0.70:
                commission_rate = 0.02
            elif rentabilidad >= 0.70:
                commission_rate = 0.025

    elif region == 'PROVINCIAS CON CACHING':
        if 0.40 <= rentabilidad < 0.45:
            commission_rate = 0.03
        elif rentabilidad >= 0.45:
            commission_rate = 0.035

    elif region == 'PROVINCIAS CON INTERNEXA':
        if 0.17 <= rentabilidad < 0.20:
            commission_rate = 0.02
        elif rentabilidad >= 0.20:
            commission_rate = 0.03

    elif region == 'PROVINCIAS CON TDP':
        if 0.17 <= rentabilidad < 0.20:
            commission_rate = 0.02
        elif rentabilidad >= 0.20:
            commission_rate = 0.03

    # --- 6. FINAL CALCULATION ---
    # Use the 'sale_type' (which corresponds to your old 'project_type')
    if sale_type == 'NUEVO':
        calculated_commission = commission_rate * mrc * plazo
    elif sale_type == 'EXISTENTE':
        # If sale_type is UPGRADE, the commission is calculated on the MRC difference.
        calculated_commission = commission_rate * plazo * (mrc - old_mrc)
    else:
        # Should be caught by the initial validation, but included for robustness
        calculated_commission = 0.0

    # --- 7. Return only the final commission amount (float) ---
    return calculated_commission

def _calculate_corporativo_commission(transaction):
    """
    Placeholder logic for 'CORPORATIVO' (No rules defined yet).
    """
    mrc = transaction.MRC or 0
    plazo = transaction.plazoContrato or 0
    
    commission_rate = 0.06
    calculated_commission = 0
    
    limit_mrc_amount = 1.2 * mrc
    
    return min(calculated_commission, limit_mrc_amount)

def _calculate_final_commission(transaction):
    """
    PARENT FUNCTION: Routes the commission calculation to the appropriate business unit's logic.
    """
    unit = transaction.unidadNegocio
    
    if unit == 'ESTADO':
        return _calculate_estado_commission(transaction)
    elif unit == 'GIGALAN':
        return _calculate_gigalan_commission(transaction)
    elif unit == 'CORPORATIVO':
        return _calculate_corporativo_commission(transaction)
    else:
        return 0.0

# --- NEW: MASTER VARIABLE SERVICES ---

@login_required
def get_all_master_variables(category=None):
    """
    Retrieves all records for master variables, filtered by category if provided.
    (Supports the "EVERYONE CAN VIEW" requirement)
    """
    try:
        query = MasterVariable.query.order_by(MasterVariable.date_recorded.desc())
        
        if category:
            query = query.filter_by(category=category.upper())

        variables = query.all()
        
        return {
            "success": True,
            "data": [v.to_dict() for v in variables]
        }
    except Exception as e:
        return {"success": False, "error": f"Database error fetching master variables: {str(e)}"}

@login_required
def update_master_variable(variable_name, value, comment):
    """
    Inserts a new record for a master variable, enforcing RBAC based on config.
    """
    config = current_app.config
    variable_config = config['MASTER_VARIABLE_ROLES'].get(variable_name)

    # 1. Input Validation (checks if the variable is registered)
    if not variable_config:
        return {"success": False, "error": f"Variable name '{variable_name}' is not a registered master variable."}, 400
    
    try:
        value = float(value)
    except (TypeError, ValueError):
        return {"success": False, "error": "Variable value must be a valid number."}, 400

    # 2. RBAC Enforcement (Security Check)
    required_role = variable_config['write_role']
    variable_category = variable_config['category']
    
    # ADMIN is always authorized. Other roles must match the required role.
    if current_user.role != 'ADMIN' and current_user.role != required_role:
        return {"success": False, "error": f"Permission denied. Only {required_role} can update the {variable_category} category."}, 403

    try:
        # 3. Create a new record (historical audit)
        new_variable = MasterVariable(
            variable_name=variable_name,
            variable_value=value,
            category=variable_category,
            user_id=current_user.id,
            comment=comment 
        )
        
        db.session.add(new_variable)
        db.session.commit()

        return {"success": True, "message": f"Successfully updated {variable_name} to {value}."}

    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Database error saving variable: {str(e)}"}, 500

def get_latest_master_variables(variable_names):
    """
    Retrieves the single most recent value for a list of required variables.
    Returns a dictionary: {variable_name: latest_value, ...}
    """
    if not variable_names:
        return {}
        
    # 1. Find the latest date for each unique variable name
    subquery = db.session.query(
        MasterVariable.variable_name,
        func.max(MasterVariable.date_recorded).label('latest_date')
    ).filter(
        MasterVariable.variable_name.in_(variable_names)
    ).group_by(
        MasterVariable.variable_name
    ).subquery()
    
    # 2. Use the latest dates to select the full records
    latest_records = db.session.query(MasterVariable).join(
        subquery,
        (MasterVariable.variable_name == subquery.c.variable_name) & 
        (MasterVariable.date_recorded == subquery.c.latest_date)
    ).all()
    
    # 3. Map to a clean dictionary
    latest_values = {
        record.variable_name: record.variable_value
        for record in latest_records
    }
    
    # 4. Fill in missing variables with None/Default if no history exists
    final_result = {name: latest_values.get(name) for name in variable_names}
    
    return final_result

# --- MAIN SERVICE FUNCTIONS ---

@login_required 
def recalculate_commission_and_metrics(transaction_id):
    """
    Applies the official commission, recalculates all financial metrics,
    and saves the updated Transaction object to the database.
    
    IMMUTABILITY CHECK: Only allows modification if status is 'PENDING'.
    """
    try:
        # 1. Retrieve the transaction object
        transaction = db.session.get(Transaction, transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction not found."}, 404

        # --- IMMUTABILITY CHECK (CRITICAL NEW LOGIC) ---
        if transaction.ApprovalStatus != 'PENDING':
            return {"success": False, "error": f"Transaction is already {transaction.ApprovalStatus}. Financial metrics can only be modified for 'PENDING' transactions."}, 403
        # ---------------------------------------------

        # 2. Calculate new commission using the official logic
        new_commission = _calculate_final_commission(transaction)

        # 3. Update the commission field on the database object
        transaction.comisiones = new_commission

        # 4. Fetch related data for financial recalculation
        fixed_costs_data = [fc.to_dict() for fc in transaction.fixed_costs]
        recurring_services_data = [rs.to_dict() for rs in transaction.recurring_services]

        # 5. Assemble the data package expected by _calculate_financial_metrics
        tx_data = transaction.to_dict()
        tx_data['comisiones'] = new_commission # CRITICAL: Pass the new commission
        tx_data['fixed_costs'] = fixed_costs_data
        tx_data['recurring_services'] = recurring_services_data

        # 6. Recalculate all metrics (VAN, TIR, etc.)
        financial_metrics = _calculate_financial_metrics(tx_data)

        # 7. Update the transaction object with all new result
        clean_financial_metrics = _convert_numpy_types(financial_metrics)

        for key, value in clean_financial_metrics.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        # 8. Commit changes to the database
        db.session.commit()

        # 9. Return the full, updated transaction details
        # NOTE: get_transaction_details returns a dict on success
        return get_transaction_details(transaction_id)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error during commission recalculation for ID %s: %s", transaction_id, str(e), exc_info=True)
        return {"success": False, "error": f"Error during commission recalculation: {str(e)}"}, 500

@login_required
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

@login_required
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

@login_required 
def process_excel_file(excel_file):
    """
    Orchestrates the entire process of reading, validating, and calculating data 
    from the uploaded Excel file, using master variables for key financial rates.
    """
    try:
        # Access config variables from the current Flask app context
        config = current_app.config
        
        # FIX: Define the local helper function here
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

        # --- NEW BLOCK: FETCH LATEST MASTER VARIABLES (Decoupling) ---
        required_master_variables = ['tipoCambio', 'costoCapital']
        latest_rates = get_latest_master_variables(required_master_variables)
        
        # Check if the necessary rates were found in the DB (CRITICAL VALIDATION)
        if latest_rates.get('tipoCambio') is None or latest_rates.get('costoCapital') is None:
             return {"success": False, "error": "Cannot calculate financial metrics. System rates (Tipo de Cambio or Costo Capital) are missing. Please ensure they have been set by the Finance department."}, 400
        # --- END NEW BLOCK ---


        # Step 3: Read & Extract Data
        header_data = {}
        for var_name, cell in config['VARIABLES_TO_EXTRACT'].items():
            # NOTE: The config no longer contains 'tipoCambio' and 'costoCapitalAnual'
            df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None)
            col_idx = ord(cell[0].upper()) - ord('A')
            row_idx = int(cell[1:]) - 1
            value = df.iloc[row_idx, col_idx]

            # Apply safe_float ONLY to fields expected to be numeric
            if var_name in ['MRC', 'NRC', 'plazoContrato', 'comisiones', 'companyID', 'orderID']: 
                header_data[var_name] = safe_float(value)
            else:
                # Keep as is for string fields like clientName, salesman
                header_data[var_name] = value

        # FORCE INITIAL COMMISSION TO ZERO (unchanged logic)
        if 'comisiones' in header_data:
            header_data['comisiones'] = 0.0
        
        # --- NEW BLOCK: INJECT MASTER VARIABLES INTO HEADER DATA ---
        header_data['tipoCambio'] = latest_rates['tipoCambio']
        # Map the Master Variable name 'costoCapital' to the Transaction Model name 'costoCapitalAnual'
        header_data['costoCapitalAnual'] = latest_rates['costoCapital'] 
        # --- END INJECTION ---
        
        services_col_indices = [ord(c.upper()) - ord('A') for c in config['RECURRING_SERVICES_COLUMNS'].values()]
        services_df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None, skiprows=config['RECURRING_SERVICES_START_ROW'], usecols=services_col_indices)
        services_df.columns = config['RECURRING_SERVICES_COLUMNS'].keys()
        recurring_services_data = services_df.dropna(how='all').to_dict('records')

        fixed_costs_col_indices = [ord(c.upper()) - ord('A') for c in config['FIXED_COSTS_COLUMNS'].values()]
        fixed_costs_df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None, skiprows=config['FIXED_COSTS_START_ROW'], usecols=fixed_costs_col_indices)
        fixed_costs_df.columns = config['FIXED_COSTS_COLUMNS'].keys()
        fixed_costs_data = fixed_costs_df.dropna(how='all').to_dict('records')

        # Calculate totals for preview (unchanged logic)
        for item in fixed_costs_data:
            if pd.notna(item.get('cantidad')) and pd.notna(item.get('costoUnitario')):
                item['total'] = item['cantidad'] * item['cantidad']

        for item in recurring_services_data:
            q = safe_float(item.get('Q', 0))
            p = safe_float(item.get('P', 0))
            cu1 = safe_float(item.get('CU1', 0))
            cu2 = safe_float(item.get('CU2', 0))

            item['ingreso'] = q * p
            item['egreso'] = (cu1 + cu2) * q

        calculated_costoInstalacion = sum(
            item.get('total', 0) for item in fixed_costs_data if pd.notna(item.get('total')))

        # Step 4: Validate Inputs (unchanged logic)
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

        # --- NEW STEP: Extract GIGALAN Data ---
        gigalan_region = tx_data.get('gigalan_region')
        gigalan_sale_type = tx_data.get('gigalan_sale_type')
        # Use safe_float or just get the value. It is best to stick to .get() 
        # as the frontend should send a number or None/null.
        gigalan_old_mrc = tx_data.get('gigalan_old_mrc') 

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
            gigalan_region=gigalan_region,
            gigalan_sale_type=gigalan_sale_type,
            gigalan_old_mrc=gigalan_old_mrc,
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
    Immutability Check: Only allows approval if status is 'PENDING'.
    """
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction not found."}, 404

        # --- STATE CONSISTENCY CHECK ---
        if transaction.ApprovalStatus != 'PENDING':
            # Block approval if not pending
            return {"success": False, "error": f"Cannot approve transaction. Current status is '{transaction.ApprovalStatus}'. Only 'PENDING' transactions can be approved."}, 400
        # -------------------------------

        transaction.ApprovalStatus = 'APPROVED'
        transaction.approvalDate = datetime.utcnow()
        db.session.commit()
        return {"success": True, "message": "Transaction approved successfully."}
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error during transaction approval for ID %s: %s", transaction_id, str(e), exc_info=True)
        return {"success": False, "error": f"Database error: {str(e)}"}, 500

@login_required 
def reject_transaction(transaction_id):
    """
    Rejects a transaction by updating its status and approval date.
    Immutability Check: Only allows rejection if status is 'PENDING'.
    """
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction not found."}, 404

        # --- STATE CONSISTENCY CHECK ---
        if transaction.ApprovalStatus != 'PENDING':
            # Block rejection if not pending
            return {"success": False, "error": f"Cannot reject transaction. Current status is '{transaction.ApprovalStatus}'. Only 'PENDING' transactions can be rejected."}, 400
        # -------------------------------

        transaction.ApprovalStatus = 'REJECTED'
        transaction.approvalDate = datetime.utcnow()
        db.session.commit()
        return {"success": True, "message": "Transaction rejected successfully."}
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error during transaction rejection for ID %s: %s", transaction_id, str(e), exc_info=True)
        return {"success": False, "error": f"Database error: {str(e)}"}, 500

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
    

