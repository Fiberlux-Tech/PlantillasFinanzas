// src/lib/formatters.ts
import { FORMAT_OPTIONS } from '@/config';

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
  const { decimals = FORMAT_OPTIONS.CURRENCY_DECIMALS } = options;
  const numValue = parseFloat(value as string);

  if (typeof numValue !== 'number' || isNaN(numValue) || numValue === 0) {
    return '-';
  }
  
  return numValue.toLocaleString(FORMAT_OPTIONS.LOCALE, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

/**
 * Handles non-currency data (text and numbers) and returns '-' for zero/null/undefined/empty/N/A.
 * @param {*} value
 * @returns {string | number}
 */
export const formatCellData = (value: string | number | null | undefined): string | number => {
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
    const mm = String(date.getMonth() + 1).padStart(FORMAT_OPTIONS.DATE_PAD_LENGTH, FORMAT_OPTIONS.DATE_PAD_CHAR);
    const dd = String(date.getDate()).padStart(FORMAT_OPTIONS.DATE_PAD_LENGTH, FORMAT_OPTIONS.DATE_PAD_CHAR);
    const hh = String(date.getHours()).padStart(FORMAT_OPTIONS.DATE_PAD_LENGTH, FORMAT_OPTIONS.DATE_PAD_CHAR);
    const min = String(date.getMinutes()).padStart(FORMAT_OPTIONS.DATE_PAD_LENGTH, FORMAT_OPTIONS.DATE_PAD_CHAR);

    return `${yyyy}-${mm}-${dd} | ${hh}:${min}`;
  } catch (e) {
    return isoString;
  }
};