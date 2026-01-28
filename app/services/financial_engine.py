# app/services/financial_engine.py
# Modular Financial Engine — decomposed from _calculate_financial_metrics
# This module is a pure logic library with NO imports from transactions.py.

from .commission_rules import _calculate_final_commission
from app.utils.math_utils import calculate_npv, calculate_irr


# --- 1. CurrencyConverter ---

class CurrencyConverter:
    """Holds exchange rate state and converts values to PEN."""

    def __init__(self, tipo_cambio=1):
        self.tipo_cambio = tipo_cambio or 1

    def to_pen(self, value, currency):
        value = value or 0.0
        if currency == 'USD':
            return value * self.tipo_cambio
        return value


# --- 2. RecurringServiceProcessor ---

def process_recurring_services(services, converter):
    """
    Enriches each service with PEN fields and returns aggregates.

    Returns:
        (enriched_services, total_monthly_expense_pen, mrc_sum_from_services_orig)
    """
    mrc_sum_orig = 0.0
    total_monthly_expense_pen = 0.0

    for item in services:
        q = item.get('Q') or 0

        P_original = item.get('P_original') or 0.0
        P_currency = item.get('P_currency', 'PEN')
        P_pen = converter.to_pen(P_original, P_currency)
        item['P_pen'] = P_pen
        item['ingreso_pen'] = P_pen * q
        mrc_sum_orig += P_original * q

        CU1_original = item.get('CU1_original') or 0.0
        CU2_original = item.get('CU2_original') or 0.0
        CU_currency = item.get('CU_currency', 'USD')
        CU1_pen = converter.to_pen(CU1_original, CU_currency)
        CU2_pen = converter.to_pen(CU2_original, CU_currency)
        item['CU1_pen'] = CU1_pen
        item['CU2_pen'] = CU2_pen
        item['egreso_pen'] = (CU1_pen + CU2_pen) * q
        total_monthly_expense_pen += item['egreso_pen']

    return services, total_monthly_expense_pen, mrc_sum_orig


# --- 3. MRCResolver ---

def resolve_mrc(user_provided_mrc_original, mrc_sum_from_services_orig, mrc_currency, converter):
    """
    Determines final MRC using override logic.

    Returns:
        (final_mrc_original, final_mrc_pen)
    """
    user_provided = user_provided_mrc_original or 0.0
    if user_provided > 0:
        final_mrc_original = user_provided
    else:
        final_mrc_original = mrc_sum_from_services_orig

    final_mrc_pen = converter.to_pen(final_mrc_original, mrc_currency)
    return final_mrc_original, final_mrc_pen


# --- 4. FixedCostProcessor ---

def process_fixed_costs(fixed_costs, converter):
    """
    Normalizes fixed costs to PEN and calculates total.

    Returns:
        (enriched_costs, total_installation_pen)
    """
    total_installation_pen = 0.0

    for item in fixed_costs:
        cantidad = item.get('cantidad') or 0
        costoUnitario_original = item.get('costoUnitario_original') or 0.0
        costoUnitario_currency = item.get('costoUnitario_currency', 'USD')
        costoUnitario_pen = converter.to_pen(costoUnitario_original, costoUnitario_currency)
        item['costoUnitario_pen'] = costoUnitario_pen
        item['total_pen'] = cantidad * costoUnitario_pen
        total_installation_pen += item['total_pen']

    return fixed_costs, total_installation_pen


# --- 5. CartaFianzaCalculator ---

def calculate_carta_fianza(aplica, tasa, plazo, mrc_original, mrc_currency, converter):
    """
    Calculates Carta Fianza cost in original currency and PEN.
    Formula: 10% * plazo * MRC_ORIG * 1.18 * tasa

    Returns:
        (costo_orig, costo_pen)
    """
    if not aplica:
        return 0.0, 0.0

    tasa = tasa or 0.0
    costo_orig = 0.10 * plazo * mrc_original * 1.18 * tasa
    costo_pen = converter.to_pen(costo_orig, mrc_currency)
    return costo_orig, costo_pen


# --- 6. CommissionCoordinator ---

def calculate_commission(data, total_revenue, gross_margin_pre, gross_margin_ratio, mrc_pen):
    """
    Prepares data and delegates to _calculate_final_commission.

    Returns:
        float: commission amount in PEN
    """
    data['totalRevenue'] = total_revenue
    data['grossMargin'] = gross_margin_pre
    data['grossMarginRatio'] = gross_margin_ratio
    data['MRC_pen'] = mrc_pen
    return _calculate_final_commission(data)


# --- 7. TimelineGenerator ---

def initialize_timeline(num_periods):
    """Creates a dictionary to hold the detailed timeline components."""
    return {
        'periods': [f"t={i}" for i in range(num_periods)],
        'revenues': {
            'nrc': [0.0] * num_periods,
            'mrc': [0.0] * num_periods,
        },
        'expenses': {
            'comisiones': [0.0] * num_periods,
            'egreso': [0.0] * num_periods,
            'fixed_costs': [],
        },
        'net_cash_flow': [0.0] * num_periods,
    }


def build_timeline(num_periods, nrc_pen, mrc_pen, comisiones, carta_fianza_pen,
                   monthly_expense_pen, fixed_costs):
    """
    Builds period-by-period cash flow timeline.

    Returns:
        (timeline_dict, total_fixed_costs_applied_pen, net_cash_flow_list)
    """
    timeline = initialize_timeline(num_periods)

    # A. Revenues
    timeline['revenues']['nrc'][0] = nrc_pen
    for i in range(1, num_periods):
        timeline['revenues']['mrc'][i] = mrc_pen

    # B. Expenses
    timeline['expenses']['comisiones'][0] = -comisiones - carta_fianza_pen
    for i in range(1, num_periods):
        timeline['expenses']['egreso'][i] = -monthly_expense_pen

    # C. Fixed costs distribution
    total_fixed_costs_applied_pen = 0.0
    for cost_item in fixed_costs:
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

    # D. Net cash flow
    net_cash_flow_list = []
    for t in range(num_periods):
        net_t = (
            timeline['revenues']['nrc'][t] +
            timeline['revenues']['mrc'][t] +
            timeline['expenses']['comisiones'][t] +
            timeline['expenses']['egreso'][t]
        )
        for fc in timeline['expenses']['fixed_costs']:
            net_t += fc['timeline_values'][t]

        timeline['net_cash_flow'][t] = net_t
        net_cash_flow_list.append(net_t)

    return timeline, total_fixed_costs_applied_pen, net_cash_flow_list


# --- 8. KPICalculator ---

def calculate_kpis(net_cash_flow_list, total_revenue, total_expense, costo_capital_anual):
    """
    Calculates VAN, TIR, payback, grossMargin, and grossMarginRatio.

    Returns:
        dict with keys: VAN, TIR, payback, totalRevenue, totalExpense,
                        grossMargin, grossMarginRatio
    """
    monthly_discount_rate = costo_capital_anual / 12
    van = calculate_npv(monthly_discount_rate, net_cash_flow_list)
    tir = calculate_irr(net_cash_flow_list)

    cumulative_cash_flow = 0
    payback = None
    for i, flow in enumerate(net_cash_flow_list):
        cumulative_cash_flow += flow
        if cumulative_cash_flow >= 0:
            payback = i
            break

    gross_margin = total_revenue - total_expense

    return {
        'VAN': van,
        'TIR': tir,
        'payback': payback,
        'totalRevenue': total_revenue,
        'totalExpense': total_expense,
        'grossMargin': gross_margin,
        'grossMarginRatio': (gross_margin / total_revenue) if total_revenue else 0,
    }


# --- 9. Main Orchestrator ---

def calculate_financial_metrics(data):
    """
    Orchestrator: coordinates all modular financial engine components.
    This is the main entry point for financial calculations.

    Args:
        data: Dictionary containing transaction data with keys:
            - tipoCambio: Exchange rate (USD to PEN)
            - plazoContrato: Contract term in months
            - recurring_services: List of recurring service items
            - MRC_original, MRC_currency: Monthly Recurring Charge
            - NRC_original, NRC_currency: Non-Recurring Charge
            - fixed_costs: List of fixed cost items
            - aplicaCartaFianza, tasaCartaFianza: Carta Fianza settings
            - costoCapitalAnual: Annual cost of capital for NPV calculation

    Returns:
        Dictionary with calculated financial metrics including VAN, TIR, timeline, etc.
    """
    converter = CurrencyConverter(data.get('tipoCambio', 1))
    plazo = int(data.get('plazoContrato', 0))

    # 1. Process recurring services
    services, monthly_expense_pen, mrc_sum_orig = process_recurring_services(
        data.get('recurring_services', []), converter)

    # 2. Resolve MRC (override vs. sum from services)
    mrc_orig, mrc_pen = resolve_mrc(
        data.get('MRC_original', 0.0), mrc_sum_orig,
        data.get('MRC_currency', 'PEN'), converter)

    # 3. NRC normalization
    nrc_orig = data.get('NRC_original', 0.0) or 0.0
    nrc_pen = converter.to_pen(nrc_orig, data.get('NRC_currency', 'PEN'))

    # 4. Fixed costs
    costs, installation_pen = process_fixed_costs(
        data.get('fixed_costs', []), converter)

    # 5. Carta Fianza
    cf_orig, cf_pen = calculate_carta_fianza(
        data.get('aplicaCartaFianza', False), data.get('tasaCartaFianza', 0.0),
        plazo, mrc_orig, data.get('MRC_currency', 'PEN'), converter)

    # 6. Revenue & pre-commission margin
    total_revenue = nrc_pen + (mrc_pen * plazo)
    total_expense_pre = installation_pen + (monthly_expense_pen * plazo)
    gm_pre = total_revenue - total_expense_pre
    gm_ratio = (gm_pre / total_revenue) if total_revenue else 0

    # 7. Commission
    comisiones = calculate_commission(data, total_revenue, gm_pre, gm_ratio, mrc_pen)

    # 8. Timeline
    timeline, fixed_applied, ncf_list = build_timeline(
        plazo + 1, nrc_pen, mrc_pen, comisiones, cf_pen,
        monthly_expense_pen, data.get('fixed_costs', []))

    # 9. KPIs
    total_expense = comisiones + fixed_applied + (monthly_expense_pen * plazo) + cf_pen
    kpis = calculate_kpis(ncf_list, total_revenue, total_expense,
                          data.get('costoCapitalAnual', 0))

    return {
        'MRC_original': mrc_orig,
        'MRC_pen': mrc_pen,
        'NRC_original': nrc_orig,
        'NRC_pen': nrc_pen,
        **kpis,
        'comisiones': comisiones,
        'comisionesRate': (comisiones / total_revenue) if total_revenue else 0,
        'costoInstalacion': fixed_applied,
        'costoInstalacionRatio': (fixed_applied / total_revenue) if total_revenue else 0,
        'costoCartaFianza': cf_pen,
        'aplicaCartaFianza': data.get('aplicaCartaFianza', False),
        'timeline': timeline
    }
