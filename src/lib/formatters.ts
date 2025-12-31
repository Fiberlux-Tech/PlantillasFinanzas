// src/lib/formatters.ts

/**
 * Interface for currency formatting options.
 */
interface CurrencyOptions {
  decimals?: number;
}

/**
 * Handles currency formatting and returns '-' for zero/null/undefined values.
 * Assumes USD locale formatting.
 * @param {number | string | null | undefined} value
 * @param {CurrencyOptions} options - Optional: { decimals: number }
 * @returns {string}
 */
export const formatCurrency = (
  value: number | string | null | undefined,
  options: CurrencyOptions = {}
): string => {
  const { decimals = 2 } = options; // Default to 2 decimals
  const numValue = parseFloat(value as string);

  if (typeof numValue !== 'number' || isNaN(numValue) || numValue === 0) {
    return '-';
  }
  
  return numValue.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

/**
 * Handles non-currency data (text and numbers) and returns '-' for zero/null/undefined/empty/N/A.
 * @param {*} value
 * @returns {string | number}
 */
export const formatCellData = (value: any): string | number => {
  if (value === null || typeof value === 'undefined' || value === '' || value === 'N/A' || value === 0) {
    return '-';
  }
  return value; // Return original value otherwise
};

/**
 * Formats an ISO string into a more readable date/time.
 * @param {string} isoString
 * @returns {string}
 */
export const formatDate = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return isoString;

    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const hh = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');

    return `${yyyy}-${mm}-${dd} | ${hh}:${min}`;
  } catch (e) {
    return isoString;
  }
};