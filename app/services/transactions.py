# app/services/transactions.py
# This file will contain all the remaining Transaction and Calculation logic.

import pandas as pd
import numpy as np
import numpy_financial as npf
from flask import current_app
from flask_login import current_user, login_required
from app import db
from app.models import Transaction, FixedCost, RecurringService, User
import json
from datetime import datetime
from .variables import get_latest_master_variables # <-- IMPORTANT: Import from sibling file
from .email_service import send_new_transaction_email, send_status_update_email # <-- NEW: IMPORT EMAIL SERVICE

# --- HELPER FUNCTIONS ---

# <-- NEW: Centralized currency normalization helper ---
def _normalize_to_pen(value, currency, exchange_rate):
    """
    Converts a value to PEN if its currency is USD.
    """
    value = value or 0.0 # Treat None as 0.0
    if currency == 'USD':
        return value * exchange_rate
    return value
# ----------------------------------------------------

def _initialize_timeline(num_periods):
    """Creates a dictionary to hold the detailed timeline components."""
    return {
        'periods': [f"t={i}" for i in range(num_periods)],
        'revenues': {
            'nrc': [0.0] * num_periods,
            'mrc': [0.0] * num_periods,
        },
        'expenses': {
            'comisiones': [0.0] * num_periods,
            'egreso': [0.0] * num_periods, # This is for recurring 'variable' costs
            'fixed_costs': [], # This will be a list of objects
        },
        'net_cash_flow': [0.0] * num_periods,
    }

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
    ---
    REFACTORED: This function now builds a detailed, itemized timeline
    and calculates KPIs based on that timeline.
    ---
    MODIFIED: All monetary inputs are now normalized to PEN at the beginning.
    ---
    """
    
    # --- 1. INITIAL SETUP & CURRENCY NORMALIZATION ---
    
    # Get the locked-in exchange rate
    tipoCambio = data.get('tipoCambio', 1) 
    
    # Normalize main transaction values to PEN
    MRC_PEN = _normalize_to_pen(data.get('MRC'), data.get('mrc_currency'), tipoCambio)
    NRC_PEN = _normalize_to_pen(data.get('NRC'), data.get('nrc_currency'), tipoCambio)

    plazoContrato = int(data.get('plazoContrato', 0))
    num_periods = plazoContrato + 1
    
    # Calculate totalRevenue in PEN
    totalRevenue = NRC_PEN + (MRC_PEN * plazoContrato)
    
    # Calculate egreso/expense *before* commission (in PEN)
    costoInstalacion = data.get('costoInstalacion', 0) # This is the old total, used for commission logic
    
    # <-- MODIFIED: Normalize recurring service costs to PEN ---
    total_monthly_expense_pen = 0.0
    for item in data.get('recurring_services', []):
        q = item.get('Q') or 0
        cu1_pen = _normalize_to_pen(item.get('CU1'), item.get('cu_currency'), tipoCambio)
        cu2_pen = _normalize_to_pen(item.get('CU2'), item.get('cu_currency'), tipoCambio)
        item['egreso_pen'] = (cu1_pen + cu2_pen) * q # Store PEN value for later
        total_monthly_expense_pen += item['egreso_pen']
    
    # <-- MODIFIED: Normalize fixed costs to PEN ---
    # We also re-calculate 'costoInstalacion' (total upfront fixed costs) in PEN
    costoInstalacion_pen = 0.0
    for item in data.get('fixed_costs', []):
        cantidad = item.get('cantidad') or 0
        costoUnitario_pen = _normalize_to_pen(item.get('costoUnitario'), item.get('costo_currency'), tipoCambio)
        item['total_pen'] = cantidad * costoUnitario_pen # Store PEN value for later
        
        # This logic is for the old commission rule
        costoInstalacion_pen += item['total_pen'] 

    # --- This logic remains based on your commission rules ---
    # We pass the old 'costoInstalacion' (not ..._pen) for now
    # unless commission logic needs to be PEN-based (which it should)
    
    # REPLACING old logic with PEN-based logic for commissions
    upfront_costs_pre_commission = costoInstalacion_pen 
    totalExpense_pre_commission = upfront_costs_pre_commission + (total_monthly_expense_pen * plazoContrato)
    
    grossMargin_pre_commission = totalRevenue - totalExpense_pre_commission
    grossMarginRatio = (grossMargin_pre_commission / totalRevenue) if totalRevenue else 0
    
    # --- Pass all required PEN values to the commission calculators ---
    data['totalRevenue'] = totalRevenue
    data['grossMargin'] = grossMargin_pre_commission
    data['grossMarginRatio'] = grossMarginRatio
    data['MRC'] = MRC_PEN # Pass the PEN version of MRC
    
    # --- THIS IS THE COMMISSION CALCULATION STEP ---
    # This remains unchanged, as commission rules are based on totals.
    comisiones = _calculate_final_commission(data) # This is now in PEN
    
    
    # --- 2. BUILD THE DETAILED TIMELINE (All values in PEN) ---
    
    timeline = _initialize_timeline(num_periods)
    costoCapitalAnual = data.get('costoCapitalAnual', 0)

    # A. Populate Revenues (PEN)
    timeline['revenues']['nrc'][0] = NRC_PEN
    for i in range(1, num_periods):
        timeline['revenues']['mrc'][i] = MRC_PEN

    # B. Populate Expenses (PEN, as negative numbers)
    timeline['expenses']['comisiones'][0] = -comisiones
    for i in range(1, num_periods):
        timeline['expenses']['egreso'][i] = -total_monthly_expense_pen

    # C. Populate Fixed Costs (PEN)
    total_fixed_costs_applied_pen = 0.0
    for cost_item in data.get('fixed_costs', []):
        # <-- MODIFIED: Use the 'total_pen' value we calculated earlier
        cost_total_pen = cost_item.get('total_pen', 0.0) 
        
        periodo_inicio = int(cost_item.get('periodo_inicio', 0) or 0)
        duracion_meses = int(cost_item.get('duracion_meses', 1) or 1)

        # Create the timeline list for this specific cost
        cost_timeline_values = [0.0] * num_periods
        distributed_cost = cost_total_pen / duracion_meses

        for i in range(duracion_meses):
            current_period = periodo_inicio + i
            if current_period < num_periods:
                cost_timeline_values[current_period] = -distributed_cost
                total_fixed_costs_applied_pen += distributed_cost

        # Add this cost's data to the main timeline object
        timeline['expenses']['fixed_costs'].append({
            "id": cost_item.get('id'),
            "categoria": cost_item.get('categoria'),
            "tipo_servicio": cost_item.get('tipo_servicio'),
            "total": cost_total_pen, # <-- Store the PEN total
            "periodo_inicio": periodo_inicio,
            "duracion_meses": duracion_meses,
            "timeline_values": cost_timeline_values
        })

    # --- 3. CALCULATE NET CASH FLOW & FINAL KPIS (All in PEN) ---
    
    net_cash_flow_list = []
    for t in range(num_periods):
        # Sum all revenues for period t
        net_t = (
            timeline['revenues']['nrc'][t] +
            timeline['revenues']['mrc'][t]
        )
        
        # Sum all expenses for period t
        net_t += (
            timeline['expenses']['comisiones'][t] +
            timeline['expenses']['egreso'][t]
        )
        
        # Sum all distributed fixed costs for period t
        for fc in timeline['expenses']['fixed_costs']:
            net_t += fc['timeline_values'][t]
            
        timeline['net_cash_flow'][t] = net_t
        net_cash_flow_list.append(net_t)

    # Calculate final KPIs using the new net_cash_flow_list (All PEN)
    totalExpense = comisiones + total_fixed_costs_applied_pen + (total_monthly_expense_pen * plazoContrato)
    grossMargin = totalRevenue - totalExpense

    try:
        monthly_discount_rate = costoCapitalAnual / 12
        van = npf.npv(monthly_discount_rate, net_cash_flow_list)
    except Exception:
        van = None

    try:
        tir = npf.irr(net_cash_flow_list)
    except Exception:
        tir = None

    cumulative_cash_flow = 0
    payback = None
    for i, flow in enumerate(net_cash_flow_list):
        cumulative_cash_flow += flow
        if cumulative_cash_flow >= 0:
            payback = i
            break

    # Return all metrics, plus the new timeline object
    return {
        'VAN': van, 'TIR': tir, 'payback': payback, 'totalRevenue': totalRevenue,
        'totalExpense': totalExpense, 
        'comisiones': comisiones,
        'comisionesRate': (comisiones / totalRevenue) if totalRevenue else 0,
        # <-- MODIFIED: This is now the PEN cost / total PEN revenue
        'costoInstalacion': total_fixed_costs_applied_pen, 
        'costoInstalacionRatio': (total_fixed_costs_applied_pen / totalRevenue) if totalRevenue else 0,
        'grossMargin': grossMargin, 
        'grossMarginRatio': (grossMargin / totalRevenue) if totalRevenue else 0,
        
        # --- THE NEW OBJECT FOR THE FRONTEND ---
        'timeline': timeline 
    }


# --- COMMISSION CALCULATION HELPERS (REFACTORED) ---
# NOTE: These functions now receive PEN-based values for totalRevenue, grossMargin, etc.

def _calculate_estado_commission(data): # <-- REFACTORED (accepts data dict)
    """
    Handles the commission calculation for 'ESTADO' using data from a dictionary.
    """
    # --- Read values from data dict ---
    total_revenues = data.get('totalRevenue', 0.0)
    
    if total_revenues == 0:
        return 0.0

    plazo = data.get('plazoContrato', 0)
    payback = data.get('payback') # Payback is calculated *before* commission, so this is OK
    mrc = data.get('MRC', 0.0) # <-- This is MRC_PEN now
    payback_ok = (payback is not None)
    rentabilidad = data.get('grossMarginRatio', 0.0) # Use pre-commission margin ratio
    # ---
    
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
            limit_mrc_amount = mrc * limit_mrc_multiplier # mrc is already PEN
            final_commission_amount = min(calculated_commission, limit_mrc_amount)

    return final_commission_amount

def _calculate_gigalan_commission(data): # <-- REFACTORED (accepts data dict)
    """
    Calculates the GIGALAN commission using the data stored in a dictionary.
    """
    
    # --- 1. Map attributes from data dict ---
    region = data.get('gigalan_region')
    sale_type = data.get('gigalan_sale_type')
    
    # <-- MODIFIED: Normalize old_mrc to PEN ---
    # We assume old_mrc is always PEN as it's an internal value, but
    # if it could be USD, we'd need to normalize it here.
    # For now, we assume it's PEN.
    old_mrc_pen = data.get('gigalan_old_mrc') or 0.0 # Use 0.0 if None or 0.0
    tipoCambio = data.get('tipoCambio', 1)
    # ---

    # --- 2. Access existing financial metrics from the dict (All PEN) ---
    payback = data.get('payback')
    total_revenue = data.get('totalRevenue', 1.0) # Avoid division by zero
    rentabilidad = data.get('grossMarginRatio', 0.0)
    plazo = data.get('plazoContrato', 0)
    mrc_pen = data.get('MRC', 0.0) # This is already PEN
    # ---
    
    # Initialize variables
    commission_rate = 0.0
    calculated_commission = 0.0

    # --- 3. Initial Validation (Handles incomplete GIGALAN inputs) ---
    if not region or not sale_type:
        # print("DIAGNOSTIC: GIGALAN inputs (region/sale_type) missing. Returning 0 commission.")
        return 0.0
    
    # --- 4. Payback Period Rule ---
    #if payback is None or payback > 2:
    if payback is not None and payback >= 2: # <-- Ensure payback is not None before comparing
        # print("\nADVERTENCIA: Payback > 2 meses. No aplica comisión.") # Optional diagnostic
        return 0.0

    # --- 5. FULL GIGALAN COMMISSION LOGIC (Refactored) ---
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

    # --- 6. FINAL CALCULATION (All PEN) ---
    if sale_type == 'NUEVO':
        calculated_commission = commission_rate * mrc_pen * plazo
    elif sale_type == 'EXISTENTE':
        calculated_commission = commission_rate * plazo * (mrc_pen - old_mrc_pen)
    else:
        calculated_commission = 0.0

    # --- 7. Return only the final commission amount (float) ---
    return calculated_commission

def _calculate_corporativo_commission(data): # <-- REFACTORED (accepts data dict)
    """
    Placeholder logic for 'CORPORATIVO' (No rules defined yet).
    """
    mrc_pen = data.get('MRC', 0.0) # This is already PEN
    plazo = data.get('plazoContrato', 0)
    
    commission_rate = 0.06
    calculated_commission = 0
    
    limit_mrc_amount = 1.2 * mrc_pen
    
    return min(calculated_commission, limit_mrc_amount)

def _calculate_final_commission(data): # <-- REFACTORED (accepts data dict)
    """
    PARENT FUNCTION: Routes the commission calculation to the appropriate business unit's logic.
    """
    unit = data.get('unidadNegocio') # <-- Read from dict
    
    if unit == 'ESTADO':
        return _calculate_estado_commission(data) # <-- Pass dict
    elif unit == 'GIGALAN':
        return _calculate_gigalan_commission(data) # <-- Pass dict
    elif unit == 'CORPORATIVO':
        return _calculate_corporativo_commission(data) # <-- Pass dict
    else:
        return 0.0

# --- MAIN SERVICE FUNCTIONS ---

@login_required
def calculate_preview_metrics(request_data):
    """
    Calculates all financial metrics based on temporary data from the frontend modal.
    This is a "stateless" calculator.
    
    --- MODIFIED ---
    This function now TRUSTS the 'tipoCambio' and 'costoCapitalAnual'
    sent in the 'request_data' packet. It NO LONGER fetches the
    latest master variables, ensuring the preview is consistent
    with the transaction's "locked-in" rates.
    """
    try:
        # 1. Extract data from the request payload
        # The frontend sends a package: {"transactions": {...}, "fixed_costs": [...], "recurring_services": [...]}
        transaction_data = request_data.get('transactions', {})
        fixed_costs_data = request_data.get('fixed_costs', [])
        recurring_services_data = request_data.get('recurring_services', [])
        
        # --- BLOCK REMOVED ---
        # We no longer fetch latest master variables here.
        # We will use the rates already present in 'transaction_data'.
        
        # 2. Build the complete data dictionary
        # This mimics the data package created in 'process_excel_file'
        
        # Start with the transaction data from the modal
        full_data_package = {**transaction_data}
        
        # --- MODIFIED VALIDATION ---
        # Instead of checking the master table, we check the data packet itself.
        if full_data_package.get('tipoCambio') is None or full_data_package.get('costoCapitalAnual') is None:
            return {"success": False, "error": "Transaction data is missing 'Tipo de Cambio' or 'Costo Capital'."}, 400
        
        # --- BLOCK REMOVED ---
        # We no longer inject/overwrite the rates. 'full_data_package'
        # already contains the correct "locked-in" rates from the client.
        
        # Add the cost/service lists
        full_data_package['fixed_costs'] = fixed_costs_data
        full_data_package['recurring_services'] = recurring_services_data
        
        # <-- MODIFIED: This 'costoInstalacion' is the *original* currency total.
        # The _calculate_financial_metrics function will handle the PEN conversion.
        full_data_package['costoInstalacion'] = sum(
            item.get('total', 0) for item in fixed_costs_data if pd.notna(item.get('total'))
        )
        
        # 4. Call the refactored, stateless calculator
        # This one function now does *everything* (commissions, VAN, TIR, etc.)
        financial_metrics = _calculate_financial_metrics(full_data_package)
        
        # 5. Clean and return the results
        clean_metrics = _convert_numpy_types(financial_metrics)
        
        # --- START FIX ---
        # Merge the original transaction inputs with the newly calculated metrics.
        # This ensures inputs like 'plazoContrato' are returned in the response.
        final_data = {**transaction_data, **clean_metrics}
        
        return {"success": True, "data": final_data}

    except Exception as e:
        import traceback
        print("--- ERROR DURING PREVIEW CALCULATION ---")
        print(traceback.format_exc())
        print("--- END ERROR ---")
        return {"success": False, "error": f"An unexpected error occurred during preview: {str(e)}"}, 500

@login_required 
def recalculate_commission_and_metrics(transaction_id):
    """
    Applies the official commission, recalculates all financial metrics,
    and saves the updated Transaction object to the database.
    
    IMMUTABILITY CHECK: Only allows modification if status is 'PENDING'.
    
    --- REFACTORED ---
    This function now uses the new stateless _calculate_financial_metrics function
    as the single source of truth for calculations.
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

        # 2. Assemble the data package
        # We convert the DB model and its relationships into a simple dictionary.
        # <-- MODIFIED: to_dict() now includes the currency fields.
        tx_data = transaction.to_dict()
        tx_data['fixed_costs'] = [fc.to_dict() for fc in transaction.fixed_costs]
        tx_data['recurring_services'] = [rs.to_dict() for rs in transaction.recurring_services]
        
        # Add GIGALAN fields to the dict for the commission calculator
        tx_data['gigalan_region'] = transaction.gigalan_region
        tx_data['gigalan_sale_type'] = transaction.gigalan_sale_type
        tx_data['gigalan_old_mrc'] = transaction.gigalan_old_mrc

        # 3. Recalculate all metrics (VAN, TIR, Commission, etc.)
        # This one function now does *everything*
        financial_metrics = _calculate_financial_metrics(tx_data) # <-- REFACTORED
        
        # 4. Update the transaction object with all new results
        clean_financial_metrics = _convert_numpy_types(financial_metrics)

        for key, value in clean_financial_metrics.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)
        
        # <-- IMPORTANT: We must also update the original, non-PEN 'costoInstalacion'
        # This value is now the total_fixed_costs_applied_pen
        transaction.costoInstalacion = clean_financial_metrics.get('costoInstalacion')

        # 5. Commit changes to the database
        db.session.commit()

        # 6. Return the full, updated transaction details
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
                # <-- MODIFIED: to_dict() now includes currency fields
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
            # <-- MODIFIED: to_dict() calls now include currency fields
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
    
    --- REFACTORED ---
    Now calculates the *real* commission during the preview step.
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
        # We removed 'unidadNegocio' from config, it won't be read here.
        for var_name, cell in config['VARIABLES_TO_EXTRACT'].items():
            df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None)
            col_idx = ord(cell[0].upper()) - ord('A')
            row_idx = int(cell[1:]) - 1
            value = df.iloc[row_idx, col_idx]

            # Apply safe_float ONLY to fields expected to be numeric
            # <-- MODIFIED: We are not reading currency fields yet from Excel
            # They will use the database defaults ('PEN', 'PEN')
            if var_name in ['MRC', 'NRC', 'plazoContrato', 'comisiones', 'companyID', 'orderID']: 
                header_data[var_name] = safe_float(value)
            else:
                # Keep as is for string fields like clientName, salesman
                header_data[var_name] = value

        # --- THIS LOGIC IS NOW OVERWRITTEN BY THE REFACTOR ---
        # We still set comisiones to 0.0 here, but _calculate_financial_metrics
        # will ignore it and calculate the real one.
        if 'comisiones' in header_data:
            header_data['comisiones'] = 0.0
        
        # --- NEW BLOCK: INJECT MASTER VARIABLES INTO HEADER DATA ---
        header_data['tipoCambio'] = latest_rates['tipoCambio']
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
                # <-- BUG FIX: Was item['cantidad'] * item['cantidad']
                item['total'] = item['cantidad'] * item['costoUnitario'] 
            
            # --- ADD THIS BLOCK TO CLEAN NEW FIELDS ---
            item['periodo_inicio'] = safe_float(item.get('periodo_inicio', 0))
            item['duracion_meses'] = safe_float(item.get('duracion_meses', 1))
            # <-- NEW: Add default currency (will be saved later)
            item['costo_currency'] = 'USD' 
            # -----------------------------------------

        for item in recurring_services_data:
            q = safe_float(item.get('Q', 0))
            p = safe_float(item.get('P', 0))
            cu1 = safe_float(item.get('CU1', 0))
            cu2 = safe_float(item.get('CU2', 0))

            item['ingreso'] = q * p
            item['egreso'] = (cu1 + cu2) * q
            
            # <-- NEW: Add default currencies (will be saved later)
            item['p_currency'] = 'PEN'
            item['cu_currency'] = 'USD'

        # <-- MODIFIED: This is the total in *original* currency, not PEN
        calculated_costoInstalacion = sum(
            item.get('total', 0) for item in fixed_costs_data if pd.notna(item.get('total')))

        # Step 4: Validate Inputs (unchanged logic)
        if pd.isna(header_data.get('clientName')) or pd.isna(header_data.get('MRC')):
            return {"success": False, "error": "Required field 'Client Name' or 'MRC' is missing from the Excel file."}

        # <-- NEW: Add default currencies for transaction
        header_data['mrc_currency'] = 'PEN'
        header_data['nrc_currency'] = 'PEN'

        # Consolidate all extracted data
        full_extracted_data = {**header_data, 'recurring_services': recurring_services_data,
                               'fixed_costs': fixed_costs_data, 'costoInstalacion': calculated_costoInstalacion}

        # Step 5: Calculate Metrics
        # --- REFACTORED ---
        # This function now calculates *all* metrics, including the *real* commission.
        # It needs the GIGALAN/Unidad fields, but they are not in the Excel file.
        # They will be None, so commission will correctly calculate as 0.0 for now.
        # This is the *correct* initial state.
        # <-- MODIFIED: This function now handles all PEN conversions internally
        financial_metrics = _calculate_financial_metrics(full_extracted_data)

        # Step 6: Assemble the Final Response
        # <-- MODIFIED: 'costoInstalacion' is now the PEN-based value from financial_metrics
        transaction_summary = {
            **header_data, 
            **financial_metrics, 
            "costoInstalacion": financial_metrics.get('costoInstalacion'), # This is now PEN
            "submissionDate": None, 
            "ApprovalStatus": "PENDING"
        }

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
        # This data now comes from the frontend modal
        gigalan_region = tx_data.get('gigalan_region')
        gigalan_sale_type = tx_data.get('gigalan_sale_type')
        gigalan_old_mrc = tx_data.get('gigalan_old_mrc') 

        # Create the main Transaction object
        new_transaction = Transaction(
            # ... (all the fields for the new transaction)
            id=unique_id, # Use the generated ID
            unidadNegocio=tx_data.get('unidadNegocio'), clientName=tx_data.get('clientName'),
            companyID=tx_data.get('companyID'), salesman=tx_data['salesman'], # Use the overwritten salesman
            orderID=tx_data.get('orderID'), tipoCambio=tx_data.get('tipoCambio'),
            
            MRC=tx_data.get('MRC'),
            mrc_currency=tx_data.get('mrc_currency', 'PEN'), # <-- NEW
            NRC=tx_data.get('NRC'),
            nrc_currency=tx_data.get('nrc_currency', 'PEN'), # <-- NEW
            
            # <-- NOTE: All these KPIs are now in PEN
            VAN=tx_data.get('VAN'),
            TIR=tx_data.get('TIR'), payback=tx_data.get('payback'),
            totalRevenue=tx_data.get('totalRevenue'), totalExpense=tx_data.get('totalExpense'),
            comisiones=tx_data.get('comisiones'), comisionesRate=tx_data.get('comisionesRate'),
            costoInstalacion=tx_data.get('costoInstalacion'),
            costoInstalacionRatio=tx_data.get('costoInstalacionRatio'),
            grossMargin=tx_data.get('grossMargin'), grossMarginRatio=tx_data.get('grossMarginRatio'),
            plazoContrato=tx_data.get('plazoContrato'), costoCapitalAnual=tx_data.get('costoCapitalAnual'),
            # <-- ADDED GIGALAN FIELDS TO SAVE ---
            gigalan_region=gigalan_region,
            gigalan_sale_type=gigalan_sale_type,
            gigalan_old_mrc=gigalan_old_mrc,
            # -------------------------------------
            ApprovalStatus='PENDING'
        )
        db.session.add(new_transaction)

        # Loop through fixed costs and add them
        for cost_item in data.get('fixed_costs', []):
            new_cost = FixedCost(
                transaction=new_transaction, categoria=cost_item.get('categoria'),
                tipo_servicio=cost_item.get('tipo_servicio'), ticket=cost_item.get('ticket'),
                ubicacion=cost_item.get('ubicacion'), cantidad=cost_item.get('cantidad'),
                costoUnitario=cost_item.get('costoUnitario'),
                costo_currency=cost_item.get('costo_currency', 'USD'), # <-- NEW
                
                # --- ADD THESE TWO LINES ---
                periodo_inicio=cost_item.get('periodo_inicio', 0),
                duracion_meses=cost_item.get('duracion_meses', 1)
                # -------------------------
            )
            db.session.add(new_cost)

        # Loop through recurring services and add them
        for service_item in data.get('recurring_services', []):
            new_service = RecurringService(
                transaction=new_transaction, tipo_servicio=service_item.get('tipo_servicio'),
                nota=service_item.get('nota'), ubicacion=service_item.get('ubicacion'),
                Q=service_item.get('Q'), 
                P=service_item.get('P'),
                p_currency=service_item.get('p_currency', 'PEN'), # <-- NEW
                CU1=service_item.get('CU1'), 
                CU2=service_item.get('CU2'),
                cu_currency=service_item.get('cu_currency', 'USD'), # <-- NEW
                proveedor=service_item.get('proveedor')
            )
            db.session.add(new_service)

        # --- DIAGNOSTIC CHANGES ---
        db.session.flush()
        new_id = new_transaction.id
        print(f"--- DIAGNOSTIC: Attempting to commit transaction with temporary ID: {new_id} by user {current_user.username} ---")

        db.session.commit()

        print(f"--- DIAGNOSTIC: Commit successful for transaction ID: {new_id} ---")

        # --- NEW: SEND SUBMISSION EMAIL ---
        try:
            send_new_transaction_email(
                salesman_name=current_user.username,
                client_name=tx_data.get('clientName', 'N/A'),
                salesman_email=current_user.email
            )
        except Exception as e:
            # We log this error but do not fail the transaction
            print(f"--- ERROR: Transaction saved, but email notification failed: {str(e)} ---")

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

        # --- NEW: SEND APPROVAL EMAIL ---
        try:
            send_status_update_email(transaction, "APPROVED")
        except Exception as e:
            print(f"--- ERROR: Transaction approved, but email notification failed: {str(e)} ---")
        # --------------------------------

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

        # --- NEW: SEND REJECTION EMAIL ---
        try:
            send_status_update_email(transaction, "REJECTED")
        except Exception as e:
            print(f"--- ERROR: Transaction rejected, but email notification failed: {str(e)} ---")
        # ---------------------------------

        return {"success": True, "message": "Transaction rejected successfully."}
    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error during transaction rejection for ID %s: %s", transaction_id, str(e), exc_info=True)
        return {"success": False, "error": f"Database error: {str(e)}"}, 500