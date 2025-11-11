# In app/services/fixed_costs.py

import psycopg2
from flask import current_app 
# <<<
from flask_login import current_user
import urllib.parse 


# New Service Function to look up costs
def lookup_investment_codes(investment_codes):
    """
    Connects to the external Data Warehouse and retrieves FixedCost data 
    based on a list of ticket IDs (Investment Codes).
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
            
            
            cost = {
                "id": ticket, 
                "categoria": "Inversión", # Placeholder category
                "tipo_servicio": tipo_servicio, 
                "ticket": ticket, 
                "ubicacion": "N/A", # Placeholder location
                "cantidad": clean_cantidad,
                "costoUnitario": clean_costoUnitario,
                "costo_currency": costo_currency_clean, # <-- FIXED
                "periodo_inicio": periodo_inicio,       # <-- FIXED
                "duracion_meses": duracion_meses        # <-- FIXED
            }
            
            # 4. Calculate the required 'total' field for preview
            total = cost['cantidad'] * cost['costoUnitario']
            cost['total'] = total
            
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

def lookup_recurring_services(service_codes):
    """
    Connects to the external Data Warehouse and retrieves RecurringService data 
    from the dim_cotizacion_bi table based on a list of service codes (Cotizacion).
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

        # 2. Construct the dynamic SQL query
        # CRITICAL FIX: Targeting the "Cotizacion" column for filtering
        placeholders = ', '.join(['%s'] * len(service_codes))
        
        sql_query = f"""
            SELECT 
                "linea", 
                "destino_direccion", 
                "cantidad", 
                "precio_unitario_new", 
                "moneda", 
                "id_servicio",
                "cotizacion"
            FROM dim_cotizacion_bi 
            WHERE "cotizacion" IN ({placeholders});
        """

        cursor.execute(sql_query, service_codes)
        records = cursor.fetchall()
        
        # 3. Map the raw records to the required RecurringService structure
        mapped_services = []
        
        for record in records:
            # DB columns: Linea, destino_direccion, cantidad, precio_unitario_new, moneda, id_servicio, Cotizacion
            linea, destino, cantidad_raw, precio_raw, moneda_raw, id_servicio, cotizacion_code = record
            
            # Ensure numeric types are valid floats, defaulting to 0.0
            clean_q = float(cantidad_raw) if cantidad_raw is not None else 0.0
            clean_p = float(precio_raw) if precio_raw is not None else 0.0
            
            # Clean currency (defaults to PEN if missing)
            moneda_clean = (moneda_raw or "PEN").upper().strip()
            if moneda_clean not in ["PEN", "USD"]:
                moneda_clean = "PEN"

            # Placeholder values for cost fields as requested
            cu1 = 0.0
            cu2 = 0.0
            cu_currency = 'USD'
            
            service = {
                "id": cotizacion_code, # <--- FIXED: Using the Cotizacion code as the unique ID
                "tipo_servicio": linea,
                "ubicacion": destino,
                "Q": clean_q,
                "P": clean_p,
                
                # Mapped fields
                "p_currency": moneda_clean, 
                "ingreso": clean_q * clean_p,
                
                # Placeholder/Calculated fields
                "CU1": cu1,
                "CU2": cu2,
                "proveedor": f"ID_SERV:{id_servicio}",
                "cu_currency": cu_currency,
                "egreso": (cu1 + cu2) * clean_q,
                
                # Original IDs retained for context
                "id_servicio_lookup": id_servicio,
                "cotizacion_code_lookup": cotizacion_code,
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