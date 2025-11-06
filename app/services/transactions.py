# app/services/transactions.py
# (This file contains the core transaction services and financial calculator.)

import pandas as pd
import numpy as np
import numpy_financial as npf
from flask import current_app
from flask_login import current_user, login_required
from app import db
from app.models import Transaction, FixedCost, RecurringService, User
import json
from datetime import datetime

# --- Service Dependencies ---
from .email_service import send_new_transaction_email, send_status_update_email
# Import the newly separated commission calculator
from .commission_rules import _calculate_final_commission


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
    REFACTORED: Now calculates final MRC in original currency first,
    to correctly calculate 'Costo Carta Fianza' before PEN normalization.
    ---
    """
    
    # --- 1. INITIAL SETUP & CURRENCY ---
    tipoCambio = data.get('tipoCambio', 1) 
    # This is the currency for the 'P' values and the 'MRC' override
    mrc_currency = data.get('mrc_currency', 'PEN')
    nrc_currency = data.get('nrc_currency', 'PEN')
    
    # --- 2. DETERMINE FINAL MRC (IN ORIGINAL CURRENCY) ---
    
    # Get the user-provided override value (in original currency)
    # We assume data.get('MRC') is in the 'mrc_currency'
    user_provided_mrc_orig = data.get('MRC', 0.0) or 0.0 
    
    # Calculate MRC sum from services (in original currency)
    mrc_sum_from_services_orig = 0.0
    total_monthly_expense_pen = 0.0 # This can stay PEN
    
    for item in data.get('recurring_services', []):
        q = item.get('Q') or 0
        
        # --- Revenue side (ORIGINAL CURRENCY) ---
        p_orig = item.get('P') or 0.0
        # Store original currency income
        item['ingreso_orig'] = p_orig * q
        mrc_sum_from_services_orig += item['ingreso_orig']
        
        # --- Expense side (NORMALIZED TO PEN) ---
        cu1_pen = _normalize_to_pen(item.get('CU1'), item.get('cu_currency'), tipoCambio)
        cu2_pen = _normalize_to_pen(item.get('CU2'), item.get('cu_currency'), tipoCambio)
        item['egreso_pen'] = (cu1_pen + cu2_pen) * q
        total_monthly_expense_pen += item['egreso_pen']
            
    # --- NEW OVERRIDE LOGIC (ORIGINAL CURRENCY) ---
    final_mrc_orig = 0.0
    if user_provided_mrc_orig > 0:
        final_mrc_orig = user_provided_mrc_orig
    else:
        final_mrc_orig = mrc_sum_from_services_orig

    # --- 3. NORMALIZE VALUES TO PEN ---
    NRC_PEN = _normalize_to_pen(data.get('NRC'), nrc_currency, tipoCambio)
    final_mrc_pen = _normalize_to_pen(final_mrc_orig, mrc_currency, tipoCambio)
    
    plazoContrato = int(data.get('plazoContrato', 0))
    num_periods = plazoContrato + 1
    
    # --- 4. CALCULATE CARTA FIANZA (IN *ORIGINAL* CURRENCY) ---
    costo_carta_fianza_orig = 0.0
    costo_carta_fianza_pen = 0.0 # Default to 0
    aplicaCartaFianza = data.get('aplicaCartaFianza', False)

    tasaCartaFianza = data.get('tasaCartaFianza', 0.0) or 0.0
        
    if aplicaCartaFianza:
        # Formula = 10% * plazo * MRC_ORIG * 1.18 * tasa
        costo_carta_fianza_orig = (0.10 * plazoContrato * final_mrc_orig * 1.18 * tasaCartaFianza)
        
        # NOW NORMALIZE IT
        # The cost is in the same currency as the MRC
        costo_carta_fianza_pen = _normalize_to_pen(costo_carta_fianza_orig, mrc_currency, tipoCambio)

    # --- 5. CONTINUE WITH ALL-PEN CALCULATIONS ---
    totalRevenue = NRC_PEN + (final_mrc_pen * plazoContrato)
    
    # <-- MODIFIED: Normalize fixed costs to PEN ---
    costoInstalacion_pen = 0.0
    for item in data.get('fixed_costs', []):
        cantidad = item.get('cantidad') or 0
        costoUnitario_pen = _normalize_to_pen(item.get('costoUnitario'), item.get('costo_currency'), tipoCambio)
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
    data['MRC'] = final_mrc_pen # <-- FIX: Pass the calculated PEN version
    
    # --- THIS IS THE COMMISSION CALCULATION STEP ---
    comisiones = _calculate_final_commission(data)
    
    
    # --- 6. BUILD THE DETAILED TIMELINE (All values in PEN) ---
    
    timeline = _initialize_timeline(num_periods)
    costoCapitalAnual = data.get('costoCapitalAnual', 0)

    # A. Populate Revenues (PEN)
    timeline['revenues']['nrc'][0] = NRC_PEN
    for i in range(1, num_periods):
        timeline['revenues']['mrc'][i] = final_mrc_pen

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
        'MRC_PEN_calc': final_mrc_pen, # This is the calculated PEN MRC
        'MRC_orig_calc': final_mrc_orig, # This is the calculated Original MRC
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
        clean_financial_metrics = _convert_numpy_types(financial_metrics)

        for key, value in clean_financial_metrics.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)
        
        transaction.costoInstalacion = clean_financial_metrics.get('costoInstalacion')
        
        # --- MODIFY THIS LINE ---
        # Update the MRC field with the final *original* currency value
        transaction.MRC = clean_financial_metrics.get('MRC_orig_calc')
        # ------------------------

        # 5. Commit changes
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

# app/services/transactions.py

@login_required
def get_transaction_details(transaction_id):
    """
    Retrieves a single transaction and its full details from the database by its string ID.
    Access control: SALES can only view their own transactions.
    
    --- MODIFIED TO INCLUDE LIVE CALCULATION ---
    This function now runs the financial calculator to include the 'timeline' (Flujo)
    object in the initial response, preventing frontend lag.
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
            # --- START NEW LOGIC ---
            
            # 1. Assemble the data package from the DB model
            tx_data = transaction.to_dict()
            tx_data['fixed_costs'] = [fc.to_dict() for fc in transaction.fixed_costs]
            tx_data['recurring_services'] = [rs.to_dict() for rs in transaction.recurring_services]
            
            # Add GIGALAN fields to the dict for the commission calculator
            tx_data['gigalan_region'] = transaction.gigalan_region
            tx_data['gigalan_sale_type'] = transaction.gigalan_sale_type
            tx_data['gigalan_old_mrc'] = transaction.gigalan_old_mrc

            tx_data['tasaCartaFianza'] = transaction.tasaCartaFianza # <-- ADD THIS LINE
            tx_data['aplicaCartaFianza'] = transaction.aplicaCartaFianza
            
            # 2. Call the calculator to get fresh metrics and the timeline
            financial_metrics = _calculate_financial_metrics(tx_data)
            clean_financial_metrics = _convert_numpy_types(financial_metrics)

            # 3. Merge the fresh calculations into the main transaction details
            # This adds the 'timeline' object and ensures all KPIs are in sync.
            transaction_details = transaction.to_dict()
            transaction_details.update(clean_financial_metrics)
            
            # --- END NEW LOGIC ---

            return {
                "success": True,
                "data": {
                    # This 'transaction_details' object now contains the 'timeline'
                    "transactions": transaction_details, 
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
def save_transaction(data):
    """
    Saves a new transaction and its related costs to the database.
    NOTE: Overwrites the 'salesman' field with the currently logged-in user's username.
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
            
            # <-- FIX: Save the calculated MRC_PEN, not the (potentially wrong) Excel header MRC
            MRC=tx_data.get('MRC_orig_calc'), # Saves the final *original* currency MRC
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
                # <-- REMOVED: p_currency is no longer here
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