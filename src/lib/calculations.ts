/**
 * Currency conversion and calculation utilities for transaction modals
 */

/**
 * Converts a value from its original currency to PEN
 * @param value - The value to convert
 * @param currency - The currency of the value ("PEN" or "USD")
 * @param tipoCambio - The exchange rate (USD to PEN)
 * @returns The value in PEN
 */
export function convertToPEN(
  value: number,
  currency: "PEN" | "USD",
  tipoCambio: number
): number {
  return currency === "USD" ? value * tipoCambio : value;
}

/**
 * Calculates recurring service totals
 * @param Q - Quantity
 * @param P_pen - Unit price in PEN
 * @param CU1_pen - Unit cost 1 in PEN
 * @param CU2_pen - Unit cost 2 in PEN
 * @returns Object with ingreso_pen and egreso_pen
 */
export function calculateRecurringServiceTotals(
  Q: number,
  P_pen: number,
  CU1_pen: number,
  CU2_pen: number
): { ingreso_pen: number; egreso_pen: number } {
  return {
    ingreso_pen: Q * P_pen,
    egreso_pen: Q * (CU1_pen + CU2_pen),
  };
}

/**
 * Calculates fixed cost total
 * @param cantidad - Quantity
 * @param costoUnitario_pen - Unit cost in PEN
 * @returns The total cost in PEN
 */
export function calculateFixedCostTotal(
  cantidad: number,
  costoUnitario_pen: number
): number {
  return cantidad * costoUnitario_pen;
}
