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
from .financial_engine import CurrencyConverter, initialize_timeline, calculate_financial_metrics
from app.utils.general import convert_to_json_safe


# --- HELPER FUNCTIONS ---

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
        # NOTE: tipoCambio, costoCapitalAnual, tasaCartaFianza are EXCLUDED
        # These rates are frozen at transaction creation and cannot be modified.
        # See: master_variables_snapshot for audit trail.
        updatable_fields = [
            'unidadNegocio', 'clientName', 'companyID', 'orderID',
            'MRC_currency', 'NRC_currency',
            'plazoContrato', 'aplicaCartaFianza',
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
        converter = CurrencyConverter(transaction.tipoCambio or 1)
        for service_item in recurring_services_data:
            # Ensure _pen fields are calculated if missing
            if service_item.get('P_pen') in [0, None, '']:
                P_original = service_item.get('P_original', 0)
                P_currency = service_item.get('P_currency', 'PEN')
                service_item['P_pen'] = converter.to_pen(P_original, P_currency)

            if service_item.get('CU1_pen') in [0, None, '']:
                CU1_original = service_item.get('CU1_original', 0)
                CU_currency = service_item.get('CU_currency', 'USD')
                service_item['CU1_pen'] = converter.to_pen(CU1_original, CU_currency)

            if service_item.get('CU2_pen') in [0, None, '']:
                CU2_original = service_item.get('CU2_original', 0)
                CU_currency = service_item.get('CU_currency', 'USD')
                service_item['CU2_pen'] = converter.to_pen(CU2_original, CU_currency)

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
        financial_metrics = calculate_financial_metrics(recalc_data)
        clean_metrics = convert_to_json_safe(financial_metrics)

        # 6. Update transaction with fresh calculations
        for key, value in clean_metrics.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        transaction.costoInstalacion = clean_metrics.get('costoInstalacion')
        transaction.MRC_original = clean_metrics.get('MRC_original')
        transaction.MRC_pen = clean_metrics.get('MRC_pen')
        transaction.NRC_original = clean_metrics.get('NRC_original')
        transaction.NRC_pen = clean_metrics.get('NRC_pen')

        # <-- CACHE: Update cached metrics so reads are zero-CPU ---
        transaction.financial_cache = clean_metrics
        # ----------------------------------------------------------

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
        # The calculate_financial_metrics function will handle the PEN conversion.
        full_data_package['costoInstalacion'] = sum(
            item.get('total', 0) for item in fixed_costs_data if item.get('total') is not None
        )
        
        # 4. Call the refactored, stateless calculator
        # This one function now does *everything* (commissions, VAN, TIR, etc.)
        financial_metrics = calculate_financial_metrics(full_data_package)
        
        # 5. Clean and return the results
        clean_metrics = convert_to_json_safe(financial_metrics)
        
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
    This function now uses the new stateless calculate_financial_metrics function
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
        financial_metrics = calculate_financial_metrics(tx_data) # <-- REFACTORED
        
        # 4. Update the transaction object
        clean_financial_metrics = convert_to_json_safe(financial_metrics)

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
def get_transactions(page=1, per_page=30, search=None, start_date=None, end_date=None):
    """
    Retrieves a paginated list of transactions from the database, filtered by user role.
    - SALES: Only sees transactions where salesman matches g.current_user.username.
    - FINANCE/ADMIN: Sees all transactions.
    - search: Optional ILIKE filter on clientName or salesman columns.
    - start_date/end_date: Optional date range filter on submissionDate.

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

        # --- SERVER-SIDE SEARCH FILTER ---
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Transaction.clientName.ilike(search_pattern),
                    Transaction.salesman.ilike(search_pattern)
                )
            )

        # --- DATE RANGE FILTER ---
        if start_date:
            query = query.filter(Transaction.submissionDate >= start_date)
        if end_date:
            query = query.filter(Transaction.submissionDate <= end_date)

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

            if transaction.financial_cache:
                # Cache hit - use stored metrics (zero CPU cost for ALL statuses)
                clean_financial_metrics = transaction.financial_cache
                transaction_details = transaction.to_dict()
                transaction_details.update(clean_financial_metrics)

            else:
                # Cache miss (legacy data or failed cache write) - recalculate and self-heal
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
                financial_metrics = calculate_financial_metrics(tx_data)
                clean_financial_metrics = convert_to_json_safe(financial_metrics)

                # 3. Self-heal: Update the cache for future requests
                transaction.financial_cache = clean_financial_metrics
                db.session.commit()

                # 4. Merge into transaction details
                transaction_details = transaction.to_dict()
                transaction_details.update(clean_financial_metrics)

            # --- END PERFORMANCE OPTIMIZATION ---

            # --- FIX: Recalculate _pen fields if missing (for legacy data) ---
            recurring_services_list = [rs.to_dict() for rs in transaction.recurring_services]
            converter = CurrencyConverter(transaction.tipoCambio)

            for service in recurring_services_list:
                # If _pen fields are missing/zero but original values exist, recalculate
                if (service.get('ingreso_pen') in [0, None] and
                    service.get('P_original') and service.get('Q')):

                    P_pen = converter.to_pen(
                        service['P_original'],
                        service.get('P_currency', 'PEN')
                    )
                    service['P_pen'] = P_pen
                    service['ingreso_pen'] = P_pen * service['Q']

                if (service.get('egreso_pen') in [0, None] and
                    service.get('Q')):

                    CU1_pen = converter.to_pen(
                        service.get('CU1_original', 0),
                        service.get('CU_currency', 'USD')
                    )
                    CU2_pen = converter.to_pen(
                        service.get('CU2_original', 0),
                        service.get('CU_currency', 'USD')
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
            recalculated_metrics = calculate_financial_metrics(full_data_package)
            clean_metrics = convert_to_json_safe(recalculated_metrics)

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
            # <-- MASTER VARIABLES SNAPSHOT: Frozen at creation ---
            master_variables_snapshot=tx_data.get('master_variables_snapshot'),
            # -----------------------------------------------------
            ApprovalStatus='PENDING',
            # <-- CACHE: Store calculated metrics at creation for zero-CPU reads ---
            financial_cache=clean_metrics
            # ----------------------------------------------------------------------
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
        save_converter = CurrencyConverter(tx_data.get('tipoCambio', 1))
        for service_item in data.get('recurring_services', []):
            # --- FIX: Ensure _pen fields are calculated if missing ---
            if service_item.get('P_pen') in [0, None, '']:
                P_original = service_item.get('P_original', 0)
                P_currency = service_item.get('P_currency', 'PEN')
                service_item['P_pen'] = save_converter.to_pen(P_original, P_currency)

            if service_item.get('CU1_pen') in [0, None, '']:
                CU1_original = service_item.get('CU1_original', 0)
                CU_currency = service_item.get('CU_currency', 'USD')
                service_item['CU1_pen'] = save_converter.to_pen(CU1_original, CU_currency)

            if service_item.get('CU2_pen') in [0, None, '']:
                CU2_original = service_item.get('CU2_original', 0)
                CU_currency = service_item.get('CU_currency', 'USD')
                service_item['CU2_pen'] = save_converter.to_pen(CU2_original, CU_currency)
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
            financial_metrics = calculate_financial_metrics(tx_data)
            clean_metrics = convert_to_json_safe(financial_metrics)

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
            financial_metrics = calculate_financial_metrics(tx_data)
            clean_metrics = convert_to_json_safe(financial_metrics)

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


# --- TRANSACTION TEMPLATE SERVICE ---

@require_jwt
def get_transaction_template():
    """
    Returns an empty transaction template pre-filled with current MasterVariables.

    This allows SALES users to create new transactions with the current system rates
    (tipoCambio, costoCapitalAnual, tasaCartaFianza) without requiring an Excel upload.

    Returns:
        dict: Success response with template data, or error if MasterVariables missing
    """
    from app.services.variables import get_latest_master_variables

    try:
        # 1. Fetch current MasterVariables
        required_vars = ['tipoCambio', 'costoCapital', 'tasaCartaFianza']
        master_vars = get_latest_master_variables(required_vars)

        # 2. Validate all required variables exist
        missing_vars = [var for var in required_vars if master_vars.get(var) is None]
        if missing_vars:
            return {
                "success": False,
                "error": f"System rates ({', '.join(missing_vars)}) are not configured. Please contact Finance."
            }, 400

        # 3. Build the default transaction template
        default_plazo = 36  # Default contract term in months

        template_transaction = {
            "id": None,
            "unidadNegocio": "",
            "clientName": "",
            "companyID": "",
            "salesman": g.current_user.username,
            "orderID": "",
            "tipoCambio": master_vars['tipoCambio'],
            "MRC_original": 0,
            "MRC_currency": "PEN",
            "MRC_pen": 0,
            "NRC_original": 0,
            "NRC_currency": "PEN",
            "NRC_pen": 0,
            "VAN": 0,
            "TIR": 0,
            "payback": 0,
            "totalRevenue": 0,
            "totalExpense": 0,
            "comisiones": 0,
            "comisionesRate": 0,
            "costoInstalacion": 0,
            "costoInstalacionRatio": 0,
            "grossMargin": 0,
            "grossMarginRatio": 0,
            "plazoContrato": default_plazo,
            "costoCapitalAnual": master_vars['costoCapital'],
            "tasaCartaFianza": master_vars['tasaCartaFianza'],
            "costoCartaFianza": 0,
            "aplicaCartaFianza": True,
            "gigalan_region": None,
            "gigalan_sale_type": None,
            "gigalan_old_mrc": None,
            "ApprovalStatus": "PENDING",
            "submissionDate": None,
            "approvalDate": None,
            "rejection_note": None,
            # Include empty timeline for frontend compatibility
            "timeline": initialize_timeline(default_plazo)
        }

        return {
            "success": True,
            "data": {
                "transactions": template_transaction,
                "fixed_costs": [],
                "recurring_services": []
            }
        }

    except Exception as e:
        current_app.logger.error(f"Error generating transaction template: {str(e)}", exc_info=True)
        return {"success": False, "error": f"An unexpected error occurred: {str(e)}"}, 500