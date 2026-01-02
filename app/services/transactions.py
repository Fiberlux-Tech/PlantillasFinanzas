# app/services/transactions.py
# (This file contains the core transaction services and financial calculator.)

from flask import current_app, g
from app.jwt_auth import require_jwt
from app import db
from app.models import Transaction, FixedCost, RecurringService, User
import json
from datetime import datetime

# --- Service Dependencies ---
from .email_service import send_new_transaction_email, send_status_update_email
# Import the newly separated commission calculator
from .commission_rules import _calculate_final_commission
# Import pure Python financial math utilities (replaces numpy-financial)
from app.utils.math_utils import calculate_npv, calculate_irr


# --- HELPER FUNCTIONS ---

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
    year_part = now.strftime("%y")    
    datetime_micro_part = now.strftime("%m%d%H%M%S%f") 
    
    # 2. Extract the Unit Part
    unit_part = (business_unit or "XXX")[:3].upper()

    # 3. Construct the new ID
    return f"FLX{year_part}-{datetime_micro_part}"

def _convert_to_json_safe(obj):
    """
    Recursively converts values to JSON-safe types.
    Ensures floats, ints, and None values serialize correctly.

    Note: With numpy removed, this primarily validates standard Python types.
    """
    if isinstance(obj, dict):
        return {k: _convert_to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_json_safe(i) for i in obj]
    elif isinstance(obj, float):
        # Handle special float values
        if obj != obj:  # NaN check (NaN != NaN is True)
            return None
        if obj == float('inf') or obj == float('-inf'):
            return None
        return obj
    elif isinstance(obj, int):
        return obj
    elif obj is None:
        return None
    return obj

def _calculate_financial_metrics(data):
    """
    Private helper function to calculate financial metrics based on extracted data.
    ---
    REFACTORED: Now calculates final MRC in original currency first,
    to correctly calculate 'Costo Carta Fianza' before PEN normalization.
    ---
    """
    
    # --- 1. INITIAL SETUP & CURRENCY ---
    tipoCambio = data.get('tipoCambio', 1)
    MRC_currency = data.get('MRC_currency', 'PEN')
    NRC_currency = data.get('NRC_currency', 'PEN')

    # --- 2. DETERMINE FINAL MRC (IN ORIGINAL CURRENCY) ---

    # Get the user-provided override value (in original currency)
    user_provided_MRC_original = data.get('MRC_original', 0.0) or 0.0 
    
    # Calculate MRC sum from services (in original currency)
    mrc_sum_from_services_orig = 0.0
    total_monthly_expense_pen = 0.0 # This can stay PEN
    
    for item in data.get('recurring_services', []):
        q = item.get('Q') or 0

        # --- Revenue side (convert P to PEN) ---
        P_original = item.get('P_original') or 0.0
        P_currency = item.get('P_currency', 'PEN')
        P_pen = _normalize_to_pen(P_original, P_currency, tipoCambio)
        item['P_pen'] = P_pen
        item['ingreso_pen'] = P_pen * q
        mrc_sum_from_services_orig += P_original * q  # Sum in original currency

        # --- Expense side (NORMALIZED TO PEN) ---
        CU1_original = item.get('CU1_original') or 0.0
        CU2_original = item.get('CU2_original') or 0.0
        CU_currency = item.get('CU_currency', 'USD')
        CU1_pen = _normalize_to_pen(CU1_original, CU_currency, tipoCambio)
        CU2_pen = _normalize_to_pen(CU2_original, CU_currency, tipoCambio)
        item['CU1_pen'] = CU1_pen
        item['CU2_pen'] = CU2_pen
        item['egreso_pen'] = (CU1_pen + CU2_pen) * q
        total_monthly_expense_pen += item['egreso_pen']
            
    # --- OVERRIDE LOGIC (ORIGINAL CURRENCY) ---
    final_MRC_original = 0.0
    if user_provided_MRC_original > 0:
        final_MRC_original = user_provided_MRC_original
    else:
        final_MRC_original = mrc_sum_from_services_orig

    # --- 3. NORMALIZE VALUES TO PEN ---
    NRC_original = data.get('NRC_original', 0.0) or 0.0
    NRC_pen = _normalize_to_pen(NRC_original, NRC_currency, tipoCambio)
    final_MRC_pen = _normalize_to_pen(final_MRC_original, MRC_currency, tipoCambio)
    
    plazoContrato = int(data.get('plazoContrato', 0))
    num_periods = plazoContrato + 1
    
    # --- 4. CALCULATE CARTA FIANZA (IN *ORIGINAL* CURRENCY) ---
    costo_carta_fianza_orig = 0.0
    costo_carta_fianza_pen = 0.0 # Default to 0
    aplicaCartaFianza = data.get('aplicaCartaFianza', False)

    tasaCartaFianza = data.get('tasaCartaFianza', 0.0) or 0.0
        
    if aplicaCartaFianza:
        # Formula = 10% * plazo * MRC_ORIG * 1.18 * tasa
        costo_carta_fianza_orig = (0.10 * plazoContrato * final_MRC_original * 1.18 * tasaCartaFianza)

        # NOW NORMALIZE IT
        # The cost is in the same currency as the MRC
        costo_carta_fianza_pen = _normalize_to_pen(costo_carta_fianza_orig, MRC_currency, tipoCambio)

    # --- 5. CONTINUE WITH ALL-PEN CALCULATIONS ---
    totalRevenue = NRC_pen + (final_MRC_pen * plazoContrato)

    # Normalize fixed costs to PEN
    costoInstalacion_pen = 0.0
    for item in data.get('fixed_costs', []):
        cantidad = item.get('cantidad') or 0
        costoUnitario_original = item.get('costoUnitario_original') or 0.0
        costoUnitario_currency = item.get('costoUnitario_currency', 'USD')
        costoUnitario_pen = _normalize_to_pen(costoUnitario_original, costoUnitario_currency, tipoCambio)
        item['costoUnitario_pen'] = costoUnitario_pen
        item['total_pen'] = cantidad * costoUnitario_pen
        costoInstalacion_pen += item['total_pen'] 

    # --- Commission setup ---
    upfront_costs_pre_commission = costoInstalacion_pen 
    totalExpense_pre_commission = upfront_costs_pre_commission + (total_monthly_expense_pen * plazoContrato)
    
    grossMargin_pre_commission = totalRevenue - totalExpense_pre_commission
    grossMarginRatio = (grossMargin_pre_commission / totalRevenue) if totalRevenue else 0
    
    # --- Pass all required PEN values to the commission calculators ---
    data['totalRevenue'] = totalRevenue
    data['grossMargin'] = grossMargin_pre_commission
    data['grossMarginRatio'] = grossMarginRatio
    data['MRC_pen'] = final_MRC_pen  # Pass the calculated PEN version for commission
    
    # --- THIS IS THE COMMISSION CALCULATION STEP ---
    comisiones = _calculate_final_commission(data)
    
    
    # --- 6. BUILD THE DETAILED TIMELINE (All values in PEN) ---
    
    timeline = _initialize_timeline(num_periods)
    costoCapitalAnual = data.get('costoCapitalAnual', 0)

    # A. Populate Revenues (PEN)
    timeline['revenues']['nrc'][0] = NRC_pen
    for i in range(1, num_periods):
        timeline['revenues']['mrc'][i] = final_MRC_pen

    # B. Populate Expenses (PEN, as negative numbers)
    # This line is now correct, using the PEN-normalized cost
    timeline['expenses']['comisiones'][0] = -comisiones - costo_carta_fianza_pen
    for i in range(1, num_periods):
        timeline['expenses']['egreso'][i] = -total_monthly_expense_pen

    # C. Populate Fixed Costs (PEN)
    total_fixed_costs_applied_pen = 0.0
    for cost_item in data.get('fixed_costs', []):
        cost_total_pen = cost_item.get('total_pen', 0.0) 
        
        periodo_inicio = int(cost_item.get('periodo_inicio', 0) or 0)
        duracion_meses = int(cost_item.get('duracion_meses', 1) or 1)

        cost_timeline_values = [0.0] * num_periods
        distributed_cost = cost_total_pen / duracion_meses

        for i in range(duracion_meses):
            current_period = periodo_inicio + i
            if current_period < num_periods:
                cost_timeline_values[current_period] = -distributed_cost
                total_fixed_costs_applied_pen += distributed_cost

        timeline['expenses']['fixed_costs'].append({
            "id": cost_item.get('id'),
            "categoria": cost_item.get('categoria'),
            "tipo_servicio": cost_item.get('tipo_servicio'),
            "total": cost_total_pen,
            "periodo_inicio": periodo_inicio,
            "duracion_meses": duracion_meses,
            "timeline_values": cost_timeline_values
        })

    # --- 7. CALCULATE NET CASH FLOW & FINAL KPIS (All in PEN) ---
    
    net_cash_flow_list = []
    for t in range(num_periods):
        net_t = (
            timeline['revenues']['nrc'][t] +
            timeline['revenues']['mrc'][t]
        )
        
        net_t += (
            timeline['expenses']['comisiones'][t] +
            timeline['expenses']['egreso'][t]
        )
        
        for fc in timeline['expenses']['fixed_costs']:
            net_t += fc['timeline_values'][t]
            
        timeline['net_cash_flow'][t] = net_t
        net_cash_flow_list.append(net_t)

    # Calculate final KPIs using the new net_cash_flow_list (All PEN)
    # --- MODIFY TOTAL EXPENSE ---
    totalExpense = (comisiones + total_fixed_costs_applied_pen + 
                    (total_monthly_expense_pen * plazoContrato) + 
                    costo_carta_fianza_pen) # <-- Use the PEN value
    
    grossMargin = totalRevenue - totalExpense

    # Calculate VAN (NPV) and TIR (IRR) using pure Python implementations
    monthly_discount_rate = costoCapitalAnual / 12
    van = calculate_npv(monthly_discount_rate, net_cash_flow_list)
    tir = calculate_irr(net_cash_flow_list)

    cumulative_cash_flow = 0
    payback = None
    for i, flow in enumerate(net_cash_flow_list):
        cumulative_cash_flow += flow
        if cumulative_cash_flow >= 0:
            payback = i
            break

    # Return all metrics, plus the new timeline object
    return {
        'MRC_original': final_MRC_original,  # Calculated MRC in original currency
        'MRC_pen': final_MRC_pen,  # Calculated MRC in PEN
        'NRC_original': NRC_original,  # NRC in original currency
        'NRC_pen': NRC_pen,  # NRC in PEN
        'VAN': van, 'TIR': tir, 'payback': payback, 'totalRevenue': totalRevenue,
        'totalExpense': totalExpense, 
        'comisiones': comisiones,
        'comisionesRate': (comisiones / totalRevenue) if totalRevenue else 0,
        'costoInstalacion': total_fixed_costs_applied_pen, 
        'costoInstalacionRatio': (total_fixed_costs_applied_pen / totalRevenue) if totalRevenue else 0,
        'grossMargin': grossMargin, 
        'grossMarginRatio': (grossMargin / totalRevenue) if totalRevenue else 0,
        
        'costoCartaFianza': costo_carta_fianza_pen, # Store the PEN value
        'aplicaCartaFianza': aplicaCartaFianza, 
        
        'timeline': timeline 
    }



# --- MAIN SERVICE FUNCTIONS ---

def _update_transaction_data(transaction, data_payload):
    """
    Central helper function to update a transaction's scalar fields and relationships.

    This function:
    1. Updates scalar fields (MRC, Unit, Contract Term, etc.) on the transaction model
    2. Replaces FixedCost and RecurringService records by clearing and recreating them
    3. Recalculates all financial metrics (VAN, TIR, Commissions) based on new values
    4. Does NOT change the transaction status or ID

    Args:
        transaction: The Transaction object to update
        data_payload: Dictionary containing updated transaction data with structure:
            {
                'transactions': {...},  # Updated transaction fields
                'fixed_costs': [...],   # New/updated fixed costs
                'recurring_services': [...] # New/updated recurring services
            }

    Returns:
        tuple: (success_dict, None) on success, (error_dict, status_code) on failure
    """
    try:
        tx_data = data_payload.get('transactions', {})
        fixed_costs_data = data_payload.get('fixed_costs', [])
        recurring_services_data = data_payload.get('recurring_services', [])

        # 1. Update scalar fields on the transaction model
        updatable_fields = [
            'unidadNegocio', 'clientName', 'companyID', 'orderID',
            'tipoCambio', 'MRC_currency', 'NRC_currency',
            'plazoContrato', 'costoCapitalAnual',
            'tasaCartaFianza', 'aplicaCartaFianza',
            'gigalan_region', 'gigalan_sale_type', 'gigalan_old_mrc'
        ]

        for field in updatable_fields:
            if field in tx_data:
                setattr(transaction, field, tx_data[field])

        # 2. Replace FixedCost records (clear and recreate)
        # Delete all existing fixed costs for this transaction
        FixedCost.query.filter_by(transaction_id=transaction.id).delete()

        # Create new fixed costs from payload
        for cost_item in fixed_costs_data:
            new_cost = FixedCost(
                transaction=transaction,
                categoria=cost_item.get('categoria'),
                tipo_servicio=cost_item.get('tipo_servicio'),
                ticket=cost_item.get('ticket'),
                ubicacion=cost_item.get('ubicacion'),
                cantidad=cost_item.get('cantidad'),
                costoUnitario_original=cost_item.get('costoUnitario_original'),
                costoUnitario_currency=cost_item.get('costoUnitario_currency', 'USD'),
                costoUnitario_pen=cost_item.get('costoUnitario_pen'),
                periodo_inicio=cost_item.get('periodo_inicio', 0),
                duracion_meses=cost_item.get('duracion_meses', 1)
            )
            db.session.add(new_cost)

        # 3. Replace RecurringService records (clear and recreate)
        # Delete all existing recurring services for this transaction
        RecurringService.query.filter_by(transaction_id=transaction.id).delete()

        # Create new recurring services from payload
        tipoCambio = transaction.tipoCambio or 1
        for service_item in recurring_services_data:
            # Ensure _pen fields are calculated if missing
            if service_item.get('P_pen') in [0, None, '']:
                P_original = service_item.get('P_original', 0)
                P_currency = service_item.get('P_currency', 'PEN')
                service_item['P_pen'] = _normalize_to_pen(P_original, P_currency, tipoCambio)

            if service_item.get('CU1_pen') in [0, None, '']:
                CU1_original = service_item.get('CU1_original', 0)
                CU_currency = service_item.get('CU_currency', 'USD')
                service_item['CU1_pen'] = _normalize_to_pen(CU1_original, CU_currency, tipoCambio)

            if service_item.get('CU2_pen') in [0, None, '']:
                CU2_original = service_item.get('CU2_original', 0)
                CU_currency = service_item.get('CU_currency', 'USD')
                service_item['CU2_pen'] = _normalize_to_pen(CU2_original, CU_currency, tipoCambio)

            new_service = RecurringService(
                transaction=transaction,
                tipo_servicio=service_item.get('tipo_servicio'),
                nota=service_item.get('nota'),
                ubicacion=service_item.get('ubicacion'),
                Q=service_item.get('Q'),
                P_original=service_item.get('P_original'),
                P_currency=service_item.get('P_currency', 'PEN'),
                P_pen=service_item.get('P_pen'),
                CU1_original=service_item.get('CU1_original'),
                CU2_original=service_item.get('CU2_original'),
                CU_currency=service_item.get('CU_currency', 'USD'),
                CU1_pen=service_item.get('CU1_pen'),
                CU2_pen=service_item.get('CU2_pen'),
                proveedor=service_item.get('proveedor')
            )
            db.session.add(new_service)

        # 4. Flush changes to ensure relationships are updated before recalculation
        db.session.flush()

        # 5. Recalculate financial metrics based on new values
        # Assemble data package for recalculation
        recalc_data = transaction.to_dict()
        recalc_data['fixed_costs'] = [fc.to_dict() for fc in transaction.fixed_costs]
        recalc_data['recurring_services'] = [rs.to_dict() for rs in transaction.recurring_services]
        recalc_data['gigalan_region'] = transaction.gigalan_region
        recalc_data['gigalan_sale_type'] = transaction.gigalan_sale_type
        recalc_data['gigalan_old_mrc'] = transaction.gigalan_old_mrc
        recalc_data['tasaCartaFianza'] = transaction.tasaCartaFianza
        recalc_data['aplicaCartaFianza'] = transaction.aplicaCartaFianza

        # Calculate financial metrics
        financial_metrics = _calculate_financial_metrics(recalc_data)
        clean_metrics = _convert_to_json_safe(financial_metrics)

        # 6. Update transaction with fresh calculations
        for key, value in clean_metrics.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        transaction.costoInstalacion = clean_metrics.get('costoInstalacion')
        transaction.MRC_original = clean_metrics.get('MRC_original')
        transaction.MRC_pen = clean_metrics.get('MRC_pen')
        transaction.NRC_original = clean_metrics.get('NRC_original')
        transaction.NRC_pen = clean_metrics.get('NRC_pen')

        return {"success": True}, None

    except Exception as e:
        import traceback
        print("--- ERROR DURING TRANSACTION UPDATE ---")
        print(traceback.format_exc())
        print("--- END ERROR ---")
        return {"success": False, "error": f"Error updating transaction: {str(e)}"}, 500

@require_jwt
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
        if (full_data_package.get('tipoCambio') is None or 
            full_data_package.get('costoCapitalAnual') is None or
            full_data_package.get('tasaCartaFianza') is None): # Add this check
            return {"success": False, "error": "Transaction data is missing 'Tipo de Cambio', 'Costo Capital', or 'Tasa Carta Fianza'."}, 400
        
        # --- BLOCK REMOVED ---
        # We no longer inject/overwrite the rates. 'full_data_package'
        # already contains the correct "locked-in" rates from the client.
        
        # Add the cost/service lists
        full_data_package['fixed_costs'] = fixed_costs_data
        full_data_package['recurring_services'] = recurring_services_data
        
        # <-- MODIFIED: This 'costoInstalacion' is the *original* currency total.
        # The _calculate_financial_metrics function will handle the PEN conversion.
        full_data_package['costoInstalacion'] = sum(
            item.get('total', 0) for item in fixed_costs_data if item.get('total') is not None
        )
        
        # 4. Call the refactored, stateless calculator
        # This one function now does *everything* (commissions, VAN, TIR, etc.)
        financial_metrics = _calculate_financial_metrics(full_data_package)
        
        # 5. Clean and return the results
        clean_metrics = _convert_to_json_safe(financial_metrics)
        
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

@require_jwt 
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
        tx_data = transaction.to_dict()
        tx_data['fixed_costs'] = [fc.to_dict() for fc in transaction.fixed_costs]
        tx_data['recurring_services'] = [rs.to_dict() for rs in transaction.recurring_services]
        
        # Add GIGALAN fields to the dict for the commission calculator
        tx_data['gigalan_region'] = transaction.gigalan_region
        tx_data['gigalan_sale_type'] = transaction.gigalan_sale_type
        tx_data['gigalan_old_mrc'] = transaction.gigalan_old_mrc

        tx_data['tasaCartaFianza'] = transaction.tasaCartaFianza # <-- ADD THIS LINE
        tx_data['aplicaCartaFianza'] = transaction.aplicaCartaFianza

        # 3. Recalculate all metrics (VAN, TIR, Commission, etc.)
        # This one function now does *everything*
        financial_metrics = _calculate_financial_metrics(tx_data) # <-- REFACTORED
        
        # 4. Update the transaction object
        clean_financial_metrics = _convert_to_json_safe(financial_metrics)

        for key, value in clean_financial_metrics.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)
        
        transaction.costoInstalacion = clean_financial_metrics.get('costoInstalacion')

        # Update the MRC and NRC fields with calculated values
        transaction.MRC_original = clean_financial_metrics.get('MRC_original')
        transaction.MRC_pen = clean_financial_metrics.get('MRC_pen')
        transaction.NRC_original = clean_financial_metrics.get('NRC_original')
        transaction.NRC_pen = clean_financial_metrics.get('NRC_pen')

        # 5. Commit changes
        db.session.commit()

        # 6. Return the full, updated transaction details
        return get_transaction_details(transaction_id)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error during commission recalculation for ID %s: %s", transaction_id, str(e), exc_info=True)
        return {"success": False, "error": f"Error during commission recalculation: {str(e)}"}, 500

@require_jwt
def get_transactions(page=1, per_page=30):
    """
    Retrieves a paginated list of transactions from the database, filtered by user role.
    - SALES: Only sees transactions where salesman matches g.current_user.username.
    - FINANCE/ADMIN: Sees all transactions.

    PERFORMANCE FIX: Uses eager loading to prevent N+1 query problem.
    """
    try:
        from sqlalchemy.orm import joinedload

        # Start with the base query with eager loading
        # This loads fixed_costs and recurring_services in a single JOIN query
        query = Transaction.query.options(
            joinedload(Transaction.fixed_costs),
            joinedload(Transaction.recurring_services)
        )

        # --- ROLE-BASED FILTERING (NEW LOGIC) ---
        if g.current_user.role == 'SALES':
            # Filter to show only transactions uploaded by this salesman
            query = query.filter(Transaction.salesman == g.current_user.username)
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
                "user_role": g.current_user.role 
            }
        }
    except Exception as e:
        # NOTE: A failure here might mean the database filter failed or user is not logged in.
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}

# app/services/transactions.py

@require_jwt
def get_transaction_details(transaction_id):
    """
    Retrieves a single transaction and its full details from the database by its string ID.
    Access control: SALES can only view their own transactions.

    --- MODIFIED TO INCLUDE LIVE CALCULATION ---
    This function now runs the financial calculator to include the 'timeline' (Flujo)
    object in the initial response, preventing frontend lag.

    PERFORMANCE FIX: Uses eager loading to prevent N+1 query problem.
    """
    try:
        from sqlalchemy.orm import joinedload

        # Start with a base query with eager loading
        # This loads fixed_costs and recurring_services in a single JOIN query
        query = Transaction.query.options(
            joinedload(Transaction.fixed_costs),
            joinedload(Transaction.recurring_services)
        ).filter_by(id=transaction_id)

        # --- ROLE-BASED ACCESS CHECK (NEW LOGIC) ---
        if g.current_user.role == 'SALES':
            # SALES users can only load their own transactions
            query = query.filter(Transaction.salesman == g.current_user.username)

        transaction = query.first()
        # ------------------------------------------
        
        if transaction:
            # --- PERFORMANCE OPTIMIZATION: Use cache for immutable transactions ---
            # For APPROVED/REJECTED transactions, use cached metrics to avoid expensive recalculation
            # For PENDING transactions, calculate on-the-fly for live "what-if" analysis

            if transaction.ApprovalStatus in ['APPROVED', 'REJECTED'] and transaction.financial_cache:
                # Cache hit - use stored metrics (zero CPU cost)
                clean_financial_metrics = transaction.financial_cache
                transaction_details = transaction.to_dict()
                transaction_details.update(clean_financial_metrics)

            elif transaction.ApprovalStatus in ['APPROVED', 'REJECTED'] and not transaction.financial_cache:
                # Cache miss (legacy data) - recalculate and self-heal the cache
                current_app.logger.info("Cache miss for %s transaction %s - self-healing",
                                       transaction.ApprovalStatus, transaction.id)

                # 1. Assemble the data package from the DB model
                tx_data = transaction.to_dict()
                tx_data['fixed_costs'] = [fc.to_dict() for fc in transaction.fixed_costs]
                tx_data['recurring_services'] = [rs.to_dict() for rs in transaction.recurring_services]
                tx_data['gigalan_region'] = transaction.gigalan_region
                tx_data['gigalan_sale_type'] = transaction.gigalan_sale_type
                tx_data['gigalan_old_mrc'] = transaction.gigalan_old_mrc
                tx_data['tasaCartaFianza'] = transaction.tasaCartaFianza
                tx_data['aplicaCartaFianza'] = transaction.aplicaCartaFianza

                # 2. Calculate and cache the metrics
                financial_metrics = _calculate_financial_metrics(tx_data)
                clean_financial_metrics = _convert_to_json_safe(financial_metrics)

                # 3. Self-heal: Update the cache for future requests
                transaction.financial_cache = clean_financial_metrics
                db.session.commit()

                # 4. Merge into transaction details
                transaction_details = transaction.to_dict()
                transaction_details.update(clean_financial_metrics)

            else:
                # PENDING transaction - calculate on-the-fly for live editing
                # 1. Assemble the data package from the DB model
                tx_data = transaction.to_dict()
                tx_data['fixed_costs'] = [fc.to_dict() for fc in transaction.fixed_costs]
                tx_data['recurring_services'] = [rs.to_dict() for rs in transaction.recurring_services]

                # Add GIGALAN fields to the dict for the commission calculator
                tx_data['gigalan_region'] = transaction.gigalan_region
                tx_data['gigalan_sale_type'] = transaction.gigalan_sale_type
                tx_data['gigalan_old_mrc'] = transaction.gigalan_old_mrc
                tx_data['tasaCartaFianza'] = transaction.tasaCartaFianza
                tx_data['aplicaCartaFianza'] = transaction.aplicaCartaFianza

                # 2. Call the calculator to get fresh metrics and the timeline
                financial_metrics = _calculate_financial_metrics(tx_data)
                clean_financial_metrics = _convert_to_json_safe(financial_metrics)

                # 3. Merge the fresh calculations into the main transaction details
                # This adds the 'timeline' object and ensures all KPIs are in sync.
                transaction_details = transaction.to_dict()
                transaction_details.update(clean_financial_metrics)

            # --- END PERFORMANCE OPTIMIZATION ---

            # --- FIX: Recalculate _pen fields if missing (for legacy data) ---
            recurring_services_list = [rs.to_dict() for rs in transaction.recurring_services]
            tipoCambio = transaction.tipoCambio

            for service in recurring_services_list:
                # If _pen fields are missing/zero but original values exist, recalculate
                if (service.get('ingreso_pen') in [0, None] and
                    service.get('P_original') and service.get('Q')):

                    P_pen = _normalize_to_pen(
                        service['P_original'],
                        service.get('P_currency', 'PEN'),
                        tipoCambio
                    )
                    service['P_pen'] = P_pen
                    service['ingreso_pen'] = P_pen * service['Q']

                if (service.get('egreso_pen') in [0, None] and
                    service.get('Q')):

                    CU1_pen = _normalize_to_pen(
                        service.get('CU1_original', 0),
                        service.get('CU_currency', 'USD'),
                        tipoCambio
                    )
                    CU2_pen = _normalize_to_pen(
                        service.get('CU2_original', 0),
                        service.get('CU_currency', 'USD'),
                        tipoCambio
                    )
                    service['CU1_pen'] = CU1_pen
                    service['CU2_pen'] = CU2_pen
                    service['egreso_pen'] = (CU1_pen + CU2_pen) * service['Q']
            # --- END FIX ---

            return {
                "success": True,
                "data": {
                    # This 'transaction_details' object now contains the 'timeline'
                    "transactions": transaction_details,
                    "fixed_costs": [fc.to_dict() for fc in transaction.fixed_costs],
                    "recurring_services": recurring_services_list
                }
            }
        else:
            # Return Not Found if transaction ID doesn't exist OR if the user doesn't have permission
            return {"success": False, "error": "Transaction not found or access denied."}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}


@require_jwt # <-- SECURITY WRAPPER ADDED
def save_transaction(data):
    """
    Saves a new transaction and its related costs to the database.
    NOTE: Overwrites the 'salesman' field with the currently logged-in user's username.

    CRITICAL FIX: Recalculates financial metrics on the backend to ensure
    database always has correct calculated values (prevents frontend calculation errors).
    """
    try:
        tx_data = data.get('transactions', {})

        # --- ADD THIS VALIDATION BLOCK ---
        unidad_de_negocio = tx_data.get('unidadNegocio')
        if not unidad_de_negocio or unidad_de_negocio.strip() == "":
            return {"success": False, "error": "La 'Unidad de Negocio' es obligatoria. No se puede guardar la transacción."}, 400
        # -----------------------------------

        # --- SALESMAN OVERWRITE (NEW LOGIC) ---
        # Overwrite the salesman field with the current authenticated user's username
        tx_data['salesman'] = g.current_user.username
        # --------------------------------------

        # --- CRITICAL FIX: Recalculate metrics on backend ---
        # Ensure database always has correct calculated values
        # This prevents relying on potentially incorrect frontend calculations
        try:
            full_data_package = {
                **tx_data,
                'fixed_costs': data.get('fixed_costs', []),
                'recurring_services': data.get('recurring_services', [])
            }

            # Recalculate all financial metrics using backend logic
            recalculated_metrics = _calculate_financial_metrics(full_data_package)
            clean_metrics = _convert_to_json_safe(recalculated_metrics)

            # Override frontend values with backend calculations
            tx_data.update(clean_metrics)
        except Exception as calc_error:
            current_app.logger.error("Error calculating metrics during save: %s", str(calc_error), exc_info=True)
            # If calculation fails, continue with frontend values (log warning)
            current_app.logger.warning("Falling back to frontend-provided values for transaction")
        # -------------------------------------------------------

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
            
            # Save calculated MRC and NRC with all three fields
            MRC_original=tx_data.get('MRC_original'),
            MRC_currency=tx_data.get('MRC_currency', 'PEN'),
            MRC_pen=tx_data.get('MRC_pen'),
            NRC_original=tx_data.get('NRC_original'),
            NRC_currency=tx_data.get('NRC_currency', 'PEN'),
            NRC_pen=tx_data.get('NRC_pen'),
            
            # <-- NOTE: All these KPIs are now in PEN
            VAN=tx_data.get('VAN'),
            TIR=tx_data.get('TIR'), payback=tx_data.get('payback'),
            totalRevenue=tx_data.get('totalRevenue'), totalExpense=tx_data.get('totalExpense'),
            comisiones=tx_data.get('comisiones'), comisionesRate=tx_data.get('comisionesRate'),
            costoInstalacion=tx_data.get('costoInstalacion'),
            costoInstalacionRatio=tx_data.get('costoInstalacionRatio'),
            grossMargin=tx_data.get('grossMargin'), grossMarginRatio=tx_data.get('grossMarginRatio'),
            plazoContrato=tx_data.get('plazoContrato'), costoCapitalAnual=tx_data.get('costoCapitalAnual'),
            tasaCartaFianza=tx_data.get('tasaCartaFianza'),
            costoCartaFianza=tx_data.get('costoCartaFianza'),
            aplicaCartaFianza=tx_data.get('aplicaCartaFianza', False),
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
                costoUnitario_original=cost_item.get('costoUnitario_original'),
                costoUnitario_currency=cost_item.get('costoUnitario_currency', 'USD'),
                costoUnitario_pen=cost_item.get('costoUnitario_pen'),
                periodo_inicio=cost_item.get('periodo_inicio', 0),
                duracion_meses=cost_item.get('duracion_meses', 1)
            )
            db.session.add(new_cost)

        # Loop through recurring services and add them
        for service_item in data.get('recurring_services', []):
            # --- FIX: Ensure _pen fields are calculated if missing ---
            tipoCambio = tx_data.get('tipoCambio', 1)

            if service_item.get('P_pen') in [0, None, '']:
                P_original = service_item.get('P_original', 0)
                P_currency = service_item.get('P_currency', 'PEN')
                service_item['P_pen'] = _normalize_to_pen(P_original, P_currency, tipoCambio)

            if service_item.get('CU1_pen') in [0, None, '']:
                CU1_original = service_item.get('CU1_original', 0)
                CU_currency = service_item.get('CU_currency', 'USD')
                service_item['CU1_pen'] = _normalize_to_pen(CU1_original, CU_currency, tipoCambio)

            if service_item.get('CU2_pen') in [0, None, '']:
                CU2_original = service_item.get('CU2_original', 0)
                CU_currency = service_item.get('CU_currency', 'USD')
                service_item['CU2_pen'] = _normalize_to_pen(CU2_original, CU_currency, tipoCambio)
            # --- END FIX ---

            new_service = RecurringService(
                transaction=new_transaction, tipo_servicio=service_item.get('tipo_servicio'),
                nota=service_item.get('nota'), ubicacion=service_item.get('ubicacion'),
                Q=service_item.get('Q'),
                P_original=service_item.get('P_original'),
                P_currency=service_item.get('P_currency', 'PEN'),
                P_pen=service_item.get('P_pen'),
                CU1_original=service_item.get('CU1_original'),
                CU2_original=service_item.get('CU2_original'),
                CU_currency=service_item.get('CU_currency', 'USD'),
                CU1_pen=service_item.get('CU1_pen'),
                CU2_pen=service_item.get('CU2_pen'),
                proveedor=service_item.get('proveedor')
            )
            db.session.add(new_service)

        # --- DIAGNOSTIC CHANGES ---
        db.session.flush()
        new_id = new_transaction.id
        print(f"--- DIAGNOSTIC: Attempting to commit transaction with temporary ID: {new_id} by user {g.current_user.username} ---")

        db.session.commit()

        print(f"--- DIAGNOSTIC: Commit successful for transaction ID: {new_id} ---")

        # --- NEW: SEND SUBMISSION EMAIL ---
        try:
            send_new_transaction_email(
                salesman_name=g.current_user.username,
                client_name=tx_data.get('clientName', 'N/A'),
                salesman_email=g.current_user.email
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

@require_jwt
def update_transaction_content(transaction_id, data_payload):
    """
    Updates a PENDING transaction's content without changing its status or ID.
    This is the dedicated service for the "Edit" feature.

    Args:
        transaction_id: The ID of the transaction to update
        data_payload: Dictionary containing updated transaction data.
                     Structure: {'transactions': {...}, 'fixed_costs': [...], 'recurring_services': [...]}

    Returns:
        Success response with updated transaction details, or error response with status code

    Access Control:
        - SALES users can only update their own transactions
        - FINANCE/ADMIN users can update any transaction
    """
    try:
        # 1. Retrieve the transaction
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return {"success": False, "error": "Transaction not found."}, 404

        # 2. Validate transaction is PENDING
        if transaction.ApprovalStatus != 'PENDING':
            return {"success": False, "error": f"Cannot edit transaction. Only 'PENDING' transactions can be edited. Current status: '{transaction.ApprovalStatus}'."}, 403

        # 3. Access control: SALES can only edit their own transactions
        if g.current_user.role == 'SALES' and transaction.salesman != g.current_user.username:
            return {"success": False, "error": "You do not have permission to edit this transaction."}, 403

        # 4. Apply updates using the central helper
        update_result, error_status = _update_transaction_data(transaction, data_payload)
        if error_status:
            db.session.rollback()
            return update_result, error_status

        # 5. Commit the changes
        db.session.commit()

        # 6. Return the updated transaction details
        return get_transaction_details(transaction_id)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Error updating transaction content for ID %s: %s", transaction_id, str(e), exc_info=True)
        return {"success": False, "error": f"Error updating transaction: {str(e)}"}, 500

@require_jwt # <-- SECURITY WRAPPER ADDED
def approve_transaction(transaction_id, data_payload=None):
    """
    Approves a transaction by updating its status and approval date.
    Immutability Check: Only allows approval if status is 'PENDING'.

    Args:
        transaction_id: The ID of the transaction to approve
        data_payload: Optional dictionary containing updated transaction data.
                     If provided, updates the transaction before approval.
                     Structure: {'transactions': {...}, 'fixed_costs': [...], 'recurring_services': [...]}

    CRITICAL FIX: Recalculates financial metrics before approval to ensure
    database has the latest calculated values (prevents stale data).
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

        # --- NEW: Apply data updates if provided ---
        if data_payload:
            update_result, error_status = _update_transaction_data(transaction, data_payload)
            if error_status:
                db.session.rollback()
                return update_result, error_status
        # ------------------------------------------

        # --- CRITICAL FIX: Recalculate metrics before approval ---
        # This ensures the database contains the latest calculated values
        # and prevents stale data from being frozen in the approved state
        try:
            # Assemble data package for recalculation
            tx_data = transaction.to_dict()
            tx_data['fixed_costs'] = [fc.to_dict() for fc in transaction.fixed_costs]
            tx_data['recurring_services'] = [rs.to_dict() for rs in transaction.recurring_services]
            tx_data['gigalan_region'] = transaction.gigalan_region
            tx_data['gigalan_sale_type'] = transaction.gigalan_sale_type
            tx_data['gigalan_old_mrc'] = transaction.gigalan_old_mrc
            tx_data['tasaCartaFianza'] = transaction.tasaCartaFianza
            tx_data['aplicaCartaFianza'] = transaction.aplicaCartaFianza

            # Recalculate financial metrics
            financial_metrics = _calculate_financial_metrics(tx_data)
            clean_metrics = _convert_to_json_safe(financial_metrics)

            # Update transaction with fresh calculations
            for key, value in clean_metrics.items():
                if hasattr(transaction, key):
                    setattr(transaction, key, value)

            transaction.costoInstalacion = clean_metrics.get('costoInstalacion')
            transaction.MRC_original = clean_metrics.get('MRC_original')
            transaction.MRC_pen = clean_metrics.get('MRC_pen')
            transaction.NRC_original = clean_metrics.get('NRC_original')
            transaction.NRC_pen = clean_metrics.get('NRC_pen')

            # --- PERFORMANCE OPTIMIZATION: Cache financial metrics ---
            # Store the complete calculated metrics in financial_cache
            # This prevents expensive recalculations when viewing approved transactions
            transaction.financial_cache = clean_metrics
            # --------------------------------------------------------
        except Exception as calc_error:
            current_app.logger.error("Error recalculating metrics before approval for ID %s: %s", transaction_id, str(calc_error), exc_info=True)
            # Continue with approval even if recalculation fails (log the error but don't block)
        # ---------------------------------------------------------

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

@require_jwt
def reject_transaction(transaction_id, rejection_note=None, data_payload=None):
    """
    Rejects a transaction by updating its status and approval date.
    Immutability Check: Only allows rejection if status is 'PENDING'.

    Args:
        transaction_id: The ID of the transaction to reject
        rejection_note: Optional note explaining the rejection reason
        data_payload: Optional dictionary containing updated transaction data.
                     If provided, updates the transaction before rejection.
                     Structure: {'transactions': {...}, 'fixed_costs': [...], 'recurring_services': [...]}

    CRITICAL FIX: Recalculates financial metrics before rejection to ensure
    database has the latest calculated values (prevents stale data).
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

        # --- NEW: Apply data updates if provided ---
        if data_payload:
            update_result, error_status = _update_transaction_data(transaction, data_payload)
            if error_status:
                db.session.rollback()
                return update_result, error_status
        # ------------------------------------------

        # --- CRITICAL FIX: Recalculate metrics before rejection ---
        # This ensures the database contains the latest calculated values
        # and prevents stale data from being frozen in the rejected state
        try:
            # Assemble data package for recalculation
            tx_data = transaction.to_dict()
            tx_data['fixed_costs'] = [fc.to_dict() for fc in transaction.fixed_costs]
            tx_data['recurring_services'] = [rs.to_dict() for rs in transaction.recurring_services]
            tx_data['gigalan_region'] = transaction.gigalan_region
            tx_data['gigalan_sale_type'] = transaction.gigalan_sale_type
            tx_data['gigalan_old_mrc'] = transaction.gigalan_old_mrc
            tx_data['tasaCartaFianza'] = transaction.tasaCartaFianza
            tx_data['aplicaCartaFianza'] = transaction.aplicaCartaFianza

            # Recalculate financial metrics
            financial_metrics = _calculate_financial_metrics(tx_data)
            clean_metrics = _convert_to_json_safe(financial_metrics)

            # Update transaction with fresh calculations
            for key, value in clean_metrics.items():
                if hasattr(transaction, key):
                    setattr(transaction, key, value)

            transaction.costoInstalacion = clean_metrics.get('costoInstalacion')
            transaction.MRC_original = clean_metrics.get('MRC_original')
            transaction.MRC_pen = clean_metrics.get('MRC_pen')
            transaction.NRC_original = clean_metrics.get('NRC_original')
            transaction.NRC_pen = clean_metrics.get('NRC_pen')

            # --- PERFORMANCE OPTIMIZATION: Cache financial metrics ---
            # Store the complete calculated metrics in financial_cache
            # This prevents expensive recalculations when viewing rejected transactions
            transaction.financial_cache = clean_metrics
            # --------------------------------------------------------
        except Exception as calc_error:
            current_app.logger.error("Error recalculating metrics before rejection for ID %s: %s", transaction_id, str(calc_error), exc_info=True)
            # Continue with rejection even if recalculation fails (log the error but don't block)
        # ---------------------------------------------------------

        transaction.ApprovalStatus = 'REJECTED'
        transaction.approvalDate = datetime.utcnow()

        # Store rejection note if provided
        if rejection_note:
            transaction.rejection_note = rejection_note.strip()

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