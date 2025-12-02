# app/services/excel_parser.py
# (This file is responsible for all Excel file ingestion and parsing.)

import pandas as pd
import traceback
from flask import current_app
from flask_login import login_required

# --- Service Dependencies ---
from .variables import get_latest_master_variables
from .transactions import _calculate_financial_metrics, _convert_numpy_types


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
        required_master_variables = ['tipoCambio', 'costoCapital', 'tasaCartaFianza']
        latest_rates = get_latest_master_variables(required_master_variables)
        
        # Check if the necessary rates were found in the DB (CRITICAL VALIDATION)
        if (latest_rates.get('tipoCambio') is None or 
            latest_rates.get('costoCapital') is None or
            latest_rates.get('tasaCartaFianza') is None):
             return {"success": False, "error": "Cannot calculate financial metrics. System rates (Tipo de Cambio, Costo Capital, or Tasa Carta Fianza) are missing. Please ensure they have been set by the Finance department."}, 400
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
        header_data['tasaCartaFianza'] = latest_rates['tasaCartaFianza'] # <-- ADD THIS LINE
        header_data['aplicaCartaFianza'] = False # Default to NO
        # --- END INJECTION ---
        
        services_col_indices = [ord(c.upper()) - ord('A') for c in config['RECURRING_SERVICES_COLUMNS'].values()]
        services_df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None, skiprows=config['RECURRING_SERVICES_START_ROW'], usecols=services_col_indices)

        # Debug logging
        current_app.logger.info(f"--- DEBUG: Recurring Services DataFrame ---")
        current_app.logger.info(f"Shape: {services_df.shape}")
        current_app.logger.info(f"Columns: {len(services_df.columns)} (expected: {len(config['RECURRING_SERVICES_COLUMNS'])})")
        current_app.logger.info(f"Empty: {services_df.empty}")
        current_app.logger.info(f"Column indices: {services_col_indices}")
        if not services_df.empty:
            current_app.logger.info(f"First 3 rows:\n{services_df.head(3)}")

        # Handle empty DataFrame case with detailed feedback
        if services_df.empty:
            current_app.logger.warning("WARNING: Recurring Services DataFrame is empty (no rows)")
            recurring_services_data = []
        elif len(services_df.columns) != len(config['RECURRING_SERVICES_COLUMNS']):
            current_app.logger.error(f"ERROR: Recurring Services column mismatch - got {len(services_df.columns)}, expected {len(config['RECURRING_SERVICES_COLUMNS'])}")
            recurring_services_data = []
        else:
            services_df.columns = config['RECURRING_SERVICES_COLUMNS'].keys()
            recurring_services_data = services_df.dropna(how='all').to_dict('records')
            current_app.logger.info(f"SUCCESS: Read {len(recurring_services_data)} recurring service records")
            current_app.logger.info(f"--- END DEBUG ---\n")

        fixed_costs_col_indices = [ord(c.upper()) - ord('A') for c in config['FIXED_COSTS_COLUMNS'].values()]
        fixed_costs_df = pd.read_excel(excel_file, sheet_name=config['PLANTILLA_SHEET_NAME'], header=None, skiprows=config['FIXED_COSTS_START_ROW'], usecols=fixed_costs_col_indices)

        # Debug logging
        current_app.logger.info(f"--- DEBUG: Fixed Costs DataFrame ---")
        current_app.logger.info(f"Shape: {fixed_costs_df.shape}")
        current_app.logger.info(f"Columns: {len(fixed_costs_df.columns)} (expected: {len(config['FIXED_COSTS_COLUMNS'])})")
        current_app.logger.info(f"Empty: {fixed_costs_df.empty}")
        current_app.logger.info(f"Column indices: {fixed_costs_col_indices}")
        if not fixed_costs_df.empty:
            current_app.logger.info(f"First 3 rows:\n{fixed_costs_df.head(3)}")

        # Handle empty DataFrame case with detailed feedback
        if fixed_costs_df.empty:
            current_app.logger.warning("WARNING: Fixed Costs DataFrame is empty (no rows)")
            fixed_costs_data = []
        elif len(fixed_costs_df.columns) != len(config['FIXED_COSTS_COLUMNS']):
            current_app.logger.error(f"ERROR: Fixed Costs column mismatch - got {len(fixed_costs_df.columns)}, expected {len(config['FIXED_COSTS_COLUMNS'])}")
            fixed_costs_data = []
        else:
            fixed_costs_df.columns = config['FIXED_COSTS_COLUMNS'].keys()
            fixed_costs_data = fixed_costs_df.dropna(how='all').to_dict('records')
            current_app.logger.info(f"SUCCESS: Read {len(fixed_costs_data)} fixed cost records")
            current_app.logger.info(f"--- END DEBUG ---\n")

        # Calculate totals for preview
        for item in fixed_costs_data:
            # Rename to _original pattern
            item['costoUnitario_original'] = safe_float(item.get('costoUnitario', 0))
            item['costoUnitario_currency'] = 'USD'

            # Calculate total for preview (in original currency)
            if pd.notna(item.get('cantidad')) and pd.notna(item.get('costoUnitario_original')):
                item['total'] = item['cantidad'] * item['costoUnitario_original']

            item['periodo_inicio'] = safe_float(item.get('periodo_inicio', 0))
            item['duracion_meses'] = safe_float(item.get('duracion_meses', 1))

        for item in recurring_services_data:
            q = safe_float(item.get('Q', 0))
            p_original = safe_float(item.get('P', 0))
            cu1_original = safe_float(item.get('CU1', 0))
            cu2_original = safe_float(item.get('CU2', 0))

            # Rename to _original pattern
            item['P_original'] = p_original
            item['P_currency'] = 'PEN'
            item['CU1_original'] = cu1_original
            item['CU2_original'] = cu2_original
            item['CU_currency'] = 'USD'

            # Calculate preview values in original currency
            item['ingreso'] = q * p_original
            item['egreso'] = (cu1_original + cu2_original) * q

        # <-- MODIFIED: This is the total in *original* currency, not PEN
        calculated_costoInstalacion = sum(
            item.get('total', 0) for item in fixed_costs_data if pd.notna(item.get('total')))

        # Step 4: Validate Inputs (unchanged logic)
        if pd.isna(header_data.get('clientName')) or pd.isna(header_data.get('MRC')):
            return {"success": False, "error": "Required field 'Client Name' or 'MRC' is missing from the Excel file."}

        # Rename to _original pattern for transaction
        header_data['MRC_original'] = header_data.get('MRC')
        header_data['MRC_currency'] = 'PEN'
        header_data['NRC_original'] = header_data.get('NRC')
        header_data['NRC_currency'] = 'PEN'

        # Consolidate all extracted data
        full_extracted_data = {**header_data, 'recurring_services': recurring_services_data,
                               'fixed_costs': fixed_costs_data, 'costoInstalacion': calculated_costoInstalacion}

        # Step 5: Calculate Metrics
        # This function now calculates *all* metrics, including the *real* commission.
        # It needs the GIGALAN/Unidad fields, but they are not in the Excel file.
        # They will be None, so commission will correctly calculate as 0.0 for now.
        # This is the *correct* initial state.
        # <-- This function now handles all PEN conversions internally
        financial_metrics = _calculate_financial_metrics(full_extracted_data)

        # Step 6: Assemble the Final Response
        # <-- MODIFIED: 'costoInstalacion' is now the PEN-based value from financial_metrics
        transaction_summary = {
            **header_data, 
            **financial_metrics, 
            "costoInstalacion": financial_metrics.get('costoInstalacion'), # This is now PEN
            "submissionDate": None, 
            "ApprovalStatus": "BORRADOR"
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