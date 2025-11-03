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
            ticket, tipo_servicio, cantidad, costo_currency, costoUnitario = record
            
            # Use default/placeholder values for fields not in the external DB
            # The frontend can modify these (e.g., ubicacion, periodo_inicio, duracion_meses)
            periodo_inicio = 1
            duracion_meses = 60 # Default to 5 years
            
            cost = {
                # We use the ticket as the unique ID for the lookup result
                "id": ticket, 
                "categoria": "Inversión", # Placeholder category
                "tipo_servicio": tipo_servicio, 
                "ticket": ticket, 
                "ubicacion": "N/A", # Placeholder location
                "cantidad": float(cantidad) if cantidad is not None else 0.0,
                "costoUnitario": float(costoUnitario) if costoUnitario is not None else 0.0,
                "costo_currency": costo_currency.upper(),
                "periodo_inicio": periodo_inicio,
                "duracion_meses": duracion_meses
            }
            
            # 4. Calculate the required 'total' field for preview
            total = cost['cantidad'] * cost['costoUnitario'] * cost['duracion_meses']
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