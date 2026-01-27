// src/config/api.ts
// API endpoints, technical configuration, and application defaults

import { TRANSACTION_STATUS, CURRENCIES } from './enums';

/**
 * API Configuration
 */
export const API_CONFIG = {
  ENDPOINTS: {
    // Transaction endpoints
    TRANSACTIONS_LIST: '/api/transactions',
    TRANSACTION_DETAIL: '/api/transaction',
    TRANSACTION_TEMPLATE: '/api/transactions/template',
    PROCESS_EXCEL: '/api/process-excel',
    SUBMIT_TRANSACTION: '/api/submit-transaction',
    CALCULATE_PREVIEW: '/api/calculate-preview',
    CALCULATE_COMMISSION: '/api/transaction/:id/calculate-commission',
    APPROVE_TRANSACTION: 'approve',
    REJECT_TRANSACTION: 'reject',

    // Master data endpoints
    MASTER_VARIABLES: '/api/master-variables',
    MASTER_VARIABLES_CATEGORIES: '/api/master-variables/categories',
    MASTER_VARIABLES_UPDATE: '/api/master-variables/update',

    // Admin endpoints
    ADMIN_USERS: '/api/admin/users',
    ADMIN_USER_ROLE: '/api/admin/users/:id/role',
    ADMIN_USER_RESET_PASSWORD: '/api/admin/users/:id/reset-password',

    // KPI endpoints
    KPI_PENDING_MRC: '/api/kpi/pending-mrc',
    KPI_PENDING_COUNT: '/api/kpi/pending-count',
    KPI_PENDING_COMISIONES: '/api/kpi/pending-comisiones',
    KPI_AVERAGE_GROSS_MARGIN: '/api/kpi/average-gross-margin',
    KPI_SUMMARY: '/api/kpi/summary',
  },

  // CSRF Configuration
  CSRF: {
    COOKIE_NAMES: ['XSRF-TOKEN', 'csrf_token', 'csrftoken'] as const,
    HEADERS: {
      XSRF: 'X-XSRF-TOKEN',
      CSRF: 'X-CSRF-Token',
    },
    METHODS_REQUIRING_CSRF: ['POST', 'PUT', 'DELETE', 'PATCH'] as const,
  },

  // HTTP Configuration
  HTTP: {
    CREDENTIALS_MODE: 'include',
    CONTENT_TYPE_HEADER: 'Content-Type',
    CONTENT_TYPE_JSON: 'application/json',
    METHOD_GET: 'GET',
    METHOD_POST: 'POST',
  },
};

/**
 * Pagination Configuration
 */
export const PAGINATION = {
  PER_PAGE: 30,
  DEFAULT_PAGE: 1,
} as const;

/**
 * Timing Configuration
 */
export const TIMING = {
  DEBOUNCE_RECALCULATION_MS: 500,
} as const;

/**
 * Validation Rules
 */
export const VALIDATION_RULES = {
  PLAZO_CONTRATO: { min: 1, step: 1 },
  CURRENCY_AMOUNT: { min: 0, step: 0.01 },
  QUANTITY: { min: 0, step: 1 },
  PERIODO_INICIO: { min: 0, step: 1 },
  DURACION_MESES: { min: 1, step: 1 },
  GIGALAN_OLD_MRC: { min: 0 },
} as const;

/**
 * Default Values
 */
export const DEFAULT_VALUES = {
  PLAZO_CONTRATO: 12,
  APPROVAL_STATUS: TRANSACTION_STATUS.PENDING,
  MRC_CURRENCY: CURRENCIES.PEN,
  NRC_CURRENCY: CURRENCIES.PEN,
  NUMERIC_ZERO: 0,
} as const;

/**
 * Format Options
 */
export const FORMAT_OPTIONS = {
  CURRENCY_DECIMALS: 2,
  EXCHANGE_RATE_DECIMALS: 4,
  PERCENTAGE_DECIMALS: 2,
  CASH_FLOW_DECIMALS: 0,
  LOCALE: 'en-US',
  DATE_PAD_LENGTH: 2,
  DATE_PAD_CHAR: '0',
} as const;

/**
 * Display Values
 */
export const DISPLAY_VALUES = {
  EMPTY: '-',
  NOT_AVAILABLE: 'N/A',
  ZERO: 0,
} as const;

/**
 * Boolean Display Labels
 */
export const BOOLEAN_LABELS = {
  TRUE: 'SI',
  FALSE: 'NO',
} as const;
