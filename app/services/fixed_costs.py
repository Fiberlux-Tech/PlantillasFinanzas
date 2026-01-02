# In app/services/fixed_costs.py

import psycopg2
from flask import current_app, g
import urllib.parse


# --- HELPER FUNCTION ---
def _normalize_to_pen(value, currency, exchange_rate):
    """
    Converts a value to PEN if its currency is USD.
    """
    value = value or 0.0  # Treat None as 0.0
    if currency == 'USD':
        return value * exchange_rate
    return value


# New Service Function to look up costs
def lookup_investment_codes(investment_codes, tipo_cambio=1):
    """
    Connects to the external Data Warehouse and retrieves FixedCost data
    based on a list of ticket IDs (Investment Codes).

    Args:
        investment_codes: List of ticket IDs to lookup
        tipo_cambio: Exchange rate for USD to PEN conversion (default: 1)
    """
    if not investment_codes:
        return {"success": True, "data": {"fixed_costs": []}}

    # The external DB URI is stored in app.config
    db_uri = current_app.config['DATAWAREHOUSE_URI']

    # We must parse the connection string to get psycopg2 arguments
    import urllib.parse
    url = urllib.parse.urlparse(db_uri)

    conn = None
    try:
        # 1. Connect to the external database
        conn = psycopg2.connect(
            dbname=url.path[1:], 
            user=url.username, 
            password=url.password, 
            host=url.hostname, 
            port=url.port
        )
        cursor = conn.cursor()

        # 2. Construct the dynamic SQL query
        # Use placeholders (%s) for the list of codes for security against SQL injection.
        # We also need to map DB columns to our model's column names.
        placeholders = ', '.join(['%s'] * len(investment_codes))
        
        # NOTE: producto is mapped to tipo_servicio
        # NOTE: moneda is mapped to costo_currency
        sql_query = f"""
            SELECT ticket, producto, cantidad, moneda, costo_unitario 
            FROM dim_ticket_interno_producto_bi 
            WHERE ticket IN ({placeholders});
        """

        cursor.execute(sql_query, investment_codes)
        records = cursor.fetchall()
        
        # 3. Map the raw records to the FixedCost model structure
        mapped_costs = []
        for record in records:
            # DB columns: ticket, producto, cantidad, moneda, costo_unitario
            ticket, tipo_servicio, cantidad_raw, costo_currency_raw, costoUnitario_raw = record
            
            periodo_inicio = 0
            duracion_meses = 1 
            costo_currency_clean = (costo_currency_raw or "USD").upper().strip()
            if costo_currency_clean not in ["PEN", "USD"]:
                costo_currency_clean = "USD"
            
            # Ensure numeric types are valid floats, defaulting to 0.0
            clean_cantidad = float(cantidad_raw) if cantidad_raw is not None else 0.0
            clean_costoUnitario = float(costoUnitario_raw) if costoUnitario_raw is not None else 0.0
            
            
            # --- FIX: Calculate PEN values for frontend display ---
            costoUnitario_pen = _normalize_to_pen(clean_costoUnitario, costo_currency_clean, tipo_cambio)
            total_pen = clean_cantidad * costoUnitario_pen

            cost = {
                "id": ticket,
                "categoria": "Inversión",  # Placeholder category
                "tipo_servicio": tipo_servicio,
                "ticket": ticket,
                "ubicacion": "N/A",  # Placeholder location
                "cantidad": clean_cantidad,
                "costoUnitario_original": clean_costoUnitario,
                "costoUnitario_currency": costo_currency_clean,
                "costoUnitario_pen": costoUnitario_pen,  # PEN value for frontend
                "periodo_inicio": periodo_inicio,
                "duracion_meses": duracion_meses
            }

            # 4. Calculate the required 'total' field for preview (in original currency)
            total = cost['cantidad'] * cost['costoUnitario_original']
            cost['total'] = total
            cost['total_pen'] = total_pen  # PEN value for frontend display
            
            mapped_costs.append(cost)

        return {"success": True, "data": {"fixed_costs": mapped_costs}}

    except psycopg2.Error as e:
        current_app.logger.error("Data Warehouse connection/query error: %s", str(e), exc_info=True)
        return {"success": False, "error": f"Database query failed. Error: {str(e)}"}, 500
    except Exception as e:
        current_app.logger.error("Unexpected error during Fixed Cost lookup: %s", str(e), exc_info=True)
        return {"success": False, "error": f"An unexpected error occurred during lookup: {str(e)}"}, 500
    finally:
        if conn:
            conn.close()

def lookup_recurring_services(service_codes, tipo_cambio=1):
    """
    Connects to the external Data Warehouse and retrieves RecurringService data
    from the dim_cotizacion_bi table based on a list of service codes (Cotizacion).

    --- MODIFIED ---
    This function also enriches the data by looking up the 'cliente_id'
    in the 'dim_cliente_bi' table to add 'ruc' and 'razon_social'.

    Args:
        service_codes: List of service codes to lookup
        tipo_cambio: Exchange rate for USD to PEN conversion (default: 1)
    """
    if not service_codes:
        return {"success": True, "data": {"recurring_services": []}}

    # The external DB URI is stored in app.config
    db_uri = current_app.config['DATAWAREHOUSE_URI']

    # We must parse the connection string to get psycopg2 arguments
    import urllib.parse
    url = urllib.parse.urlparse(db_uri)

    conn = None
    try:
        # 1. Connect to the external database
        conn = psycopg2.connect(
            dbname=url.path[1:], 
            user=url.username, 
            password=url.password, 
            host=url.hostname, 
            port=url.port
        )
        cursor = conn.cursor()

        # 2. Construct the dynamic SQL query for services
        # --- MODIFIED: Added "cliente_id" and fixed "linea" case
        placeholders = ', '.join(['%s'] * len(service_codes))
        
        sql_query = f"""
            SELECT 
                "servicio", 
                "destino_direccion", 
                "cantidad", 
                "precio_unitario_new", 
                "moneda", 
                "id_servicio",
                "cotizacion",
                "cliente_id" 
            FROM dim_cotizacion_bi 
            WHERE "cotizacion" IN ({placeholders});
        """

        cursor.execute(sql_query, service_codes)
        records = cursor.fetchall()
        
        # --- NEW: Step 3 - Collect client_ids for enrichment ---
        client_ids = set()
        for record in records:
            cliente_id = record[7] # Get the 8th item (cliente_id)
            if cliente_id:
                client_ids.add(cliente_id)

        # --- NEW: Step 4 - Query client table and build lookup map ---
        client_lookup_map = {}
        if client_ids:
            client_placeholders = ', '.join(['%s'] * len(client_ids))
            client_query = f"""
                SELECT cliente_id, ruc, razon_social
                FROM dim_cliente_bi
                WHERE cliente_id IN ({client_placeholders});
            """
            # Use list(client_ids) to pass the set as a list
            cursor.execute(client_query, list(client_ids)) 
            client_records = cursor.fetchall()
            
            # Build a fast-access map
            for client_rec in client_records:
                c_id, c_ruc, c_razon = client_rec
                client_lookup_map[c_id] = {
                    "ruc": c_ruc,
                    "razon_social": c_razon
                }
        
        # --- MODIFIED: Step 5 - Map records and merge client data ---
        mapped_services = []
        
        for record in records:
            # DB columns: linea, destino_direccion, cantidad, precio_unitario_new, moneda, id_servicio, Cotizacion, cliente_id
            servicio, destino, cantidad_raw, precio_raw, moneda_raw, id_servicio, cotizacion_code, cliente_id = record
            
            # Ensure numeric types are valid floats, defaulting to 0.0
            clean_q = float(cantidad_raw) if cantidad_raw is not None else 0.0
            clean_p = float(precio_raw) if precio_raw is not None else 0.0
            
            # Clean currency (defaults to PEN if missing)
            moneda_clean = (moneda_raw or "PEN").upper().strip()
            if moneda_clean not in ["PEN", "USD"]:
                moneda_clean = "PEN"

            # Placeholder values for cost fields
            cu1 = 0.0
            cu2 = 0.0
            cu_currency = 'USD'
            proveedor = None # <-- Set to None as requested

            # --- NEW: Get enriched client data from the map ---
            # Use .get(cliente_id, {}) to safely handle cases where
            # the client_id is None or not found in the map
            client_data = client_lookup_map.get(cliente_id, {})
            ruc = client_data.get("ruc")
            razon_social = client_data.get("razon_social")
            
            # --- FIX: Calculate _pen fields for frontend display ---
            P_pen = _normalize_to_pen(clean_p, moneda_clean, tipo_cambio)
            CU1_pen = _normalize_to_pen(cu1, cu_currency, tipo_cambio)
            CU2_pen = _normalize_to_pen(cu2, cu_currency, tipo_cambio)

            service = {
                "id": cotizacion_code,
                "tipo_servicio": servicio,
                "ubicacion": destino,
                "Q": clean_q,
                "P_original": clean_p,
                "P_currency": moneda_clean,
                "P_pen": P_pen,

                # Preview calculation in original currency
                "ingreso": clean_q * clean_p,
                # Calculated values in PEN for frontend display
                "ingreso_pen": clean_q * P_pen,

                # Placeholder fields for costs
                "CU1_original": cu1,
                "CU2_original": cu2,
                "CU_currency": cu_currency,
                "CU1_pen": CU1_pen,
                "CU2_pen": CU2_pen,
                "proveedor": proveedor,
                "egreso": (cu1 + cu2) * clean_q,
                # Calculated cost in PEN for frontend display
                "egreso_pen": (CU1_pen + CU2_pen) * clean_q,

                # Original IDs retained for context
                "id_servicio_lookup": id_servicio,
                "cotizacion_code_lookup": cotizacion_code,

                # --- NEW ENRICHED FIELDS ---
                "ruc": ruc,
                "razon_social": razon_social
            }
            
            mapped_services.append(service)

        return {"success": True, "data": {"recurring_services": mapped_services}}

    except psycopg2.Error as e:
        current_app.logger.error("Data Warehouse connection/query error: %s", str(e), exc_info=True)
        return {"success": False, "error": f"Database query failed. Error: {str(e)}"}, 500
    except Exception as e:
        current_app.logger.error("Unexpected error during Recurring Service lookup: %s", str(e), exc_info=True)
        return {"success": False, "error": f"An unexpected error occurred during lookup: {str(e)}"}, 500
    finally:
        if conn:
            conn.close()