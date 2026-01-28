// src/config/enums.ts
// Domain enums and their associated TypeScript types

/**
 * Currency Configuration
 */
export const CURRENCIES = {
  PEN: 'PEN' as const,
  USD: 'USD' as const,
  LIST: ['PEN', 'USD'] as const,
  DEFAULT: 'PEN' as const,
  DEFAULT_FIXED_COST: 'USD' as const,
  DEFAULT_RECURRING_P: 'PEN' as const,
  DEFAULT_RECURRING_CU: 'USD' as const,
} as const;

export type Currency = typeof CURRENCIES.PEN | typeof CURRENCIES.USD;

/**
 * Transaction Status Configuration
 */
export const TRANSACTION_STATUS = {
  PENDING: 'PENDING' as const,
  APPROVED: 'APPROVED' as const,
  REJECTED: 'REJECTED' as const,
  LIST: ['PENDING', 'APPROVED', 'REJECTED'] as const,
} as const;

export type TransactionStatus = typeof TRANSACTION_STATUS.PENDING | typeof TRANSACTION_STATUS.APPROVED | typeof TRANSACTION_STATUS.REJECTED;

/**
 * Business Unit Configuration
 */
export const BUSINESS_UNITS = {
  GIGALAN: 'GIGALAN' as const,
  CORPORATIVO: 'CORPORATIVO' as const,
  ESTADO: 'ESTADO' as const,
  LIST: ['GIGALAN', 'CORPORATIVO', 'ESTADO'] as const,
} as const;

export type BusinessUnit = typeof BUSINESS_UNITS.GIGALAN | typeof BUSINESS_UNITS.CORPORATIVO | typeof BUSINESS_UNITS.ESTADO;

/**
 * Region Configuration
 */
export const REGIONS = {
  LIMA: 'LIMA' as const,
  PROVINCIAS_CACHING: 'PROVINCIAS CON CACHING' as const,
  PROVINCIAS_INTERNEXA: 'PROVINCIAS CON INTERNEXA' as const,
  PROVINCIAS_TDP: 'PROVINCIAS CON TDP' as const,
  LIST: ['LIMA', 'PROVINCIAS CON CACHING', 'PROVINCIAS CON INTERNEXA', 'PROVINCIAS CON TDP'] as const,
} as const;

/**
 * Sale Type Configuration
 */
export const SALE_TYPES = {
  NUEVO: 'NUEVO' as const,
  EXISTENTE: 'EXISTENTE' as const,
  LIST: ['NUEVO', 'EXISTENTE'] as const,
} as const;

export type SaleType = typeof SALE_TYPES.NUEVO | typeof SALE_TYPES.EXISTENTE;

/**
 * User Role Configuration
 */
export const USER_ROLES = {
  ADMIN: 'ADMIN' as const,
  SALES: 'SALES' as const,
  FINANCE: 'FINANCE' as const,
  LIST: ['ADMIN', 'SALES', 'FINANCE'] as const,
} as const;

export type UserRole = typeof USER_ROLES.ADMIN | typeof USER_ROLES.SALES | typeof USER_ROLES.FINANCE;

/**
 * Category Configuration
 */
export const CATEGORIES = {
  FINANCE: 'Finance' as const,
  SALES: 'Sales' as const,
  MAYORISTA: 'Mayorista' as const,
  ADMIN: 'Admin' as const,
} as const;

export type Category = (typeof CATEGORIES)[keyof typeof CATEGORIES];

/** Maps each category to its Badge variant name */
export const CATEGORY_VARIANT: Record<Category, string> = {
  [CATEGORIES.FINANCE]: 'categoryFinance',
  [CATEGORIES.SALES]: 'categorySales',
  [CATEGORIES.MAYORISTA]: 'categoryMayorista',
  [CATEGORIES.ADMIN]: 'categoryAdmin',
};

export const CATEGORY_DEFAULT_VARIANT = 'categoryUser';

// Legacy exports for backwards compatibility
// TODO: Remove these after migration is complete
export const UNIDADES_NEGOCIO = BUSINESS_UNITS.LIST;
export const REGIONS_LEGACY = REGIONS.LIST;
export const SALE_TYPES_LEGACY = SALE_TYPES.LIST;
