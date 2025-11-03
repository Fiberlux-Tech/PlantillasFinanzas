# app/services/commission_rules.py
# (This file contains all hard-coded commission calculation logic.)

def _calculate_estado_commission(data):
    """
    Handles the commission calculation for 'ESTADO' using data from a dictionary.
    All financial values (totalRevenue, MRC, etc.) are expected to be in PEN.
    """
    # --- Read values from data dict ---
    total_revenues = data.get('totalRevenue', 0.0)
    
    if total_revenues == 0:
        return 0.0

    plazo = data.get('plazoContrato', 0)
    payback = data.get('payback') # Payback is calculated *before* commission
    mrc = data.get('MRC', 0.0) # This is MRC_PEN_calc
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

def _calculate_gigalan_commission(data):
    """
    Calculates the GIGALAN commission using the data stored in a dictionary.
    All financial values (totalRevenue, MRC, etc.) are expected to be in PEN.
    """
    
    # --- 1. Map attributes from data dict ---
    region = data.get('gigalan_region')
    sale_type = data.get('gigalan_sale_type')
    
    # We assume old_mrc is always PEN as it's an internal value
    old_mrc_pen = data.get('gigalan_old_mrc') or 0.0 # Use 0.0 if None or 0.0
    # ---

    # --- 2. Access existing financial metrics from the dict (All PEN) ---
    payback = data.get('payback')
    total_revenue = data.get('totalRevenue', 1.0) # Avoid division by zero
    rentabilidad = data.get('grossMarginRatio', 0.0)
    plazo = data.get('plazoContrato', 0)
    mrc_pen = data.get('MRC', 0.0) # This is already MRC_PEN_calc
    # ---
    
    # Initialize variables
    commission_rate = 0.0
    calculated_commission = 0.0

    # --- 3. Initial Validation (Handles incomplete GIGALAN inputs) ---
    if not region or not sale_type:
        return 0.0
    
    # --- 4. Payback Period Rule ---
    if payback is not None and payback >= 2:
        return 0.0

    # --- 5. FULL GIGALAN COMMISSION LOGIC ---
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

def _calculate_corporativo_commission(data):
    """
    Placeholder logic for 'CORPORATIVO' (No rules defined yet).
    All financial values (MRC, etc.) are expected to be in PEN.
    """
    mrc_pen = data.get('MRC', 0.0) # This is already MRC_PEN_calc
    plazo = data.get('plazoContrato', 0)
    
    commission_rate = 0.06
    calculated_commission = 0
    
    limit_mrc_amount = 1.2 * mrc_pen
    
    return min(calculated_commission, limit_mrc_amount)

def _calculate_final_commission(data):
    """
    PARENT FUNCTION: Routes the commission calculation to the appropriate business unit's logic.
    """
    unit = data.get('unidadNegocio') # <-- Read from dict
    
    if unit == 'ESTADO':
        return _calculate_estado_commission(data)
    elif unit == 'GIGALAN':
        return _calculate_gigalan_commission(data)
    elif unit == 'CORPORATIVO':
        return _calculate_corporativo_commission(data)
    else:
        return 0.0