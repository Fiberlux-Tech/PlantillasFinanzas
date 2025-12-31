// src/config/constants.ts
// Master Configuration File - All application constants centralized here

/**
 * Currency Configuration
 * Defines all currency codes used throughout the application
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
 * Defines all possible transaction approval statuses
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
 * Defines the business units (Unidades de Negocio)
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
 * Defines the geographical regions for service deployment
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
 * Defines the types of sales (new customer vs existing customer)
 */
export const SALE_TYPES = {
  NUEVO: 'NUEVO' as const,
  EXISTENTE: 'EXISTENTE' as const,
  LIST: ['NUEVO', 'EXISTENTE'] as const,
} as const;

export type SaleType = typeof SALE_TYPES.NUEVO | typeof SALE_TYPES.EXISTENTE;

/**
 * User Role Configuration
 * Defines all user roles in the system
 */
export const USER_ROLES = {
  ADMIN: 'ADMIN' as const,
  SALES: 'SALES' as const,
  FINANCE: 'FINANCE' as const,
  USER: 'USER' as const,
  LIST: ['ADMIN', 'SALES', 'FINANCE', 'USER'] as const,
} as const;

export type UserRole = typeof USER_ROLES.ADMIN | typeof USER_ROLES.SALES | typeof USER_ROLES.FINANCE | typeof USER_ROLES.USER;

/**
 * API Configuration
 * Centralized API endpoints and related configuration
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

    // Lookup endpoints
    FIXED_COSTS_LOOKUP: '/api/fixed-costs/lookup',
    RECURRING_SERVICES_LOOKUP: '/api/recurring-services/lookup',

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
 * Default pagination settings for list views
 */
export const PAGINATION = {
  PER_PAGE: 30,
  DEFAULT_PAGE: 1,
} as const;

/**
 * Timing Configuration
 * Timeouts, debounce delays, and other timing-related values
 */
export const TIMING = {
  DEBOUNCE_RECALCULATION_MS: 500,
} as const;

/**
 * Validation Rules
 * Min/max values and step increments for form inputs
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
 * Default values for form fields and initialization
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
 * Number and date formatting configuration
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
 * Special values used for display purposes
 */
export const DISPLAY_VALUES = {
  EMPTY: '-',
  NOT_AVAILABLE: 'N/A',
  ZERO: 0,
} as const;

/**
 * Boolean Display Labels
 * Spanish labels for boolean values
 */
export const BOOLEAN_LABELS = {
  TRUE: 'SI',
  FALSE: 'NO',
} as const;

/**
 * UI Labels
 * All user-facing text labels (Spanish)
 */
export const UI_LABELS = {
  // Transaction Overview
  TRANSACTION_OVERVIEW: 'Transaction Overview',
  TIPO_CAMBIO: 'Tipo de Cambio',
  COSTO_CAPITAL: 'Costo Capital',
  TASA_CARTA_FIANZA: 'Tasa Carta Fianza',
  COSTO_CARTA_FIANZA: 'Costo Carta Fianza',
  UNIDAD_NEGOCIO: 'Unidad de Negocio',
  RUC_DNI: 'RUC/DNI',
  NOMBRE_CLIENTE: 'Nombre Cliente',
  PLAZO_CONTRATO: 'Plazo de Contrato',
  MRC_RECURRENTE: 'MRC (Recurrente Mensual)',
  NRC_PAGO_UNICO: 'NRC (Pago Único)',
  COMISION_VENTAS: 'Comisión de Ventas',
  APLICA_CARTA_FIANZA: 'Aplica Carta Fianza',
  REGION: 'Región',
  TIPO_VENTA: 'Tipo de Venta',
  MRC_PREVIO: 'MRC PREVIO',

  // KPIs
  INGRESOS_TOTALES: 'Ingresos Totales',
  GASTOS_TOTALES: 'Gastos Totales',
  UTILIDAD_BRUTA: 'Utilidad Bruta',
  MARGEN_BRUTO: 'Margen Bruto (%)',
  PERIODO_PAYBACK: 'Periodo de Payback',
  TIR: 'TIR',
  VAN: 'VAN',
  COSTO_INSTALACION: 'Costo Instalación (%)',

  // Table Headers - Fixed Costs
  CATEGORIA: 'Categoría',
  TIPO_SERVICIO: 'Tipo Servicio',
  TICKET: 'Ticket',
  UBICACION: 'Ubicación',
  CANTIDAD: 'Cantidad',
  COSTO_UNITARIO: 'Costo Unitario',
  INICIO_MES: 'Inicio (Mes)',
  DURACION_MESES: 'Duración (Meses)',
  MONEDA: 'Moneda',
  TOTAL: 'Total',

  // Table Headers - Finance Transaction List
  ID: 'ID',
  ID_TRANSACCION: 'ID Transacción',
  CLIENTE: 'Cliente',
  VENDEDOR: 'Vendedor',
  MRC: 'MRC',
  PLAZO: 'Plazo',
  MARGEN_PERCENT: 'Margen %',
  PAYBACK_MESES: 'Payback (Meses)',
  FECHA: 'Fecha',
  FECHA_APROBACION: 'Fecha Aprobación',
  STATUS: 'Status',

  // Error Messages Display
  ERROR_LABEL: 'Error: ',

  // Table Headers - Recurring Services
  Q: 'Q',
  P: 'P',
  INGRESO: 'Ingreso',
  EGRESO: 'Egreso',
  CU1: 'CU1',
  CU2: 'CU2',
  PROVEEDOR: 'Proveedor',

  // New labels for redesigned tables
  MRR: 'MRC (Ingreso)',
  COSTO_RECURRENTE: 'Costo Recurrente',
  ACCIONES: 'Acciones',
  TOTAL_USD: 'Total (USD)',
  INICIO: 'Inicio (Mes)',
  DURACION: 'Duración (Meses)',

  // Cash Flow
  FLUJO_CAJA: 'Flujo de Caja',
  INGRESO_NRC: 'Ingreso (NRC)',
  INGRESO_MRC: 'Ingreso (MRC)',
  EGRESO_COMISIONES: 'Egreso (Comisiones)',
  EGRESO_RECURRENTE: 'Egreso (Recurrente)',
  NET_CASH_FLOW: 'Net Cash Flow',
  COSTO_FIJO_ID: 'Costo Fijo (ID {id})',
  ITEMS: 'items',
  VALORES_POR_PERIODO: 'Valores por periodo',

  // Service Details
  DETALLE_SERVICIOS: 'Detalle de Servicios',
  SERVICIOS_RECURRENTES: 'Servicios Recurrentes',
  INVERSION_COSTOS_FIJOS: 'Inversión (Costos Fijos)',

  // Units
  MESES: 'meses',
  PERCENTAGE: '%',

  // Page Titles
  PAGE_TITLE_SALES: 'Plantillas Economicas',
  PAGE_TITLE_FINANCE: 'Aprobación de Plantillas Economicas',
  PAGE_TITLE_ADMIN_USERS: 'Manejo de Permisos',
  PAGE_TITLE_ADMIN_MASTER_DATA: 'Maestro de Variables',
  PAGE_TITLE_MAIN_MENU: 'Menu Principal',

  // Navigation
  BACK: 'Atrás',
  LOGOUT: 'Logout',
  CREATE_TEMPLATE: 'Crear Plantilla',

  // Transaction Dashboard
  NUEVA_PLANTILLA: 'Nueva Plantilla',
  UPLOAD_NOT_AVAILABLE: 'Upload not yet available',
  FILTRA_POR_CLIENTE: 'Filtra por nombre de cliente...',
  FILTER_BY_CLIENT: 'Filter by client name...',
  PREVIEW_LABEL: 'Preview: {fileName}',
  CARGAR_EXCEL: 'Cargar Excel',
  TRANSACTION_ID_LABEL: 'Transaction ID: {id}',
  ERROR_PREFIX: 'Error: ',

  // Admin Panel
  USER_MANAGEMENT: 'User Management',
  VIEW_ALL_USERS: 'View all users and manage their roles',
  USERNAME: 'Username',
  EMAIL: 'Email',
  CURRENT_ROLE: 'Current Role',
  CHANGE_ROLE: 'Change Role',
  NO_USERS_FOUND: 'No users found',
  LOADING: 'Loading...',
  LOADING_USER_DATA: 'Loading user data...',
  RESET_USER_PASSWORD: 'Reset User Password',
  SELECT_USER_PASSWORD: 'Select a user and set a new password',
  NEW_PASSWORD: 'New Password',
  CONFIRM_PASSWORD: 'Confirm Password',
  SELECTED: 'Selected',
  TYPE_USERNAME: 'Type username...',
  ENTER_NEW_PASSWORD: 'Enter new password',
  CONFIRM_NEW_PASSWORD: 'Confirm new password',

  // Master Data
  UPDATE_VARIABLE: 'Update Variable',
  VARIABLE: 'Variable',
  VALUE: 'Value',
  COMENTARIO: 'Comentario',
  UPDATE_HISTORY: 'Update History',
  RECENT_UPDATES: 'Recent variable updates and changes',
  CATEGORY: 'Category',
  DATE_UPDATED: 'Date Updated',
  USER_UPDATER: 'User Updater',
  COMMENT: 'Comment',
  LOADING_HISTORY: 'Loading history...',
  NO_HISTORY: 'No update history available.',
  VIEWING_ACCESS_ONLY: 'Viewing Access Only',
  ROLE_NO_UPDATE_PERMISSION: 'Your role ({role}) does not permit updating Master Variables.',

  // Auth & Landing Page
  WELCOME_BACK: 'Welcome Back',
  CREATE_ACCOUNT: 'Create Account',
  USUARIO: 'Usuario',
  CONTRASENA: 'Contraseña',
  PROCESSING: 'Processing...',
  LOGIN: 'Login',
  SIGN_UP: 'Sign Up',
  NEED_ACCOUNT: 'Need an account? Sign Up',
  ALREADY_HAVE_ACCOUNT: 'Already have an account? Login',
  NO_MODULES_AVAILABLE: 'No hay modulos disponible para ti ({role})',

  // Module Descriptions
  MODULE_SALES_NAME: 'Plantillas Economicas',
  MODULE_SALES_DESC: 'Ingresa y revisa el estado de tus plantillas.',
  MODULE_FINANCE_NAME: 'Aprobación de Plantillas Economicas',
  MODULE_FINANCE_DESC: 'Aprueba las plantillas economicas.',
  MODULE_ADMIN_NAME: 'Manejo de Permisos',
  MODULE_ADMIN_DESC: 'Maneja usuarios, roles y asignación de modulos.',
  MODULE_MASTER_DATA_NAME: 'Maestro de Variables',
  MODULE_MASTER_DATA_DESC: 'Visualiza y actualizar variables clave.',

  // Fixed Cost Code Manager
  CODIGO_INVERSION: 'Código de Inversión',
  IR: 'Ir',
  CODIGOS_CARGADOS: 'Códigos Cargados:',
  REMOVE_CODE: 'Remove code {code}',
  NO_DATOS_INVERSION: 'No hay datos de inversión cargados.',
  USE_CARGAR_BUTTON_HINT: 'Use el botón \'Cargar\' para agregar datos por código.',

  // Recurring Service Code Manager
  CODIGO_SERVICIO_RECURRENTE: 'Código de Servicio Recurrente',
  NO_SERVICIOS_RECURRENTES: 'No hay servicios recurrentes cargados.',
  USE_CARGAR_BUTTON_SERVICIOS: 'Use el botón \'Cargar\' para agregar servicios por código.',

  // Section Headings
  KEY_PERFORMANCE_INDICATORS: 'Key Performance Indicators',

  // Pagination
  PREVIO: 'Previo',
  SIGUIENTE: 'Siguiente',
  PAGINA_DE: 'Pagina {current} de {total}',

  // Loading States
  LOADING_TRANSACTIONS: 'Loading transactions...',
} as const;

/**
 * Button Labels
 * All button text labels (Spanish)
 */
export const BUTTON_LABELS = {
  COMISIONES: 'Comisiones',
  RECHAZAR: 'Rechazar',
  APROBAR: 'Aprobar',
  CANCELAR: 'Cancelar',
  CONFIRMAR: 'Confirmar',
  CARGAR: 'Cargar',
  RESET_PASSWORD: 'Reset Password',
  UPDATE_VARIABLE: 'Update Variable',
  CLEAR: 'Clear',
  TODAY: 'Today',
} as const;

/**
 * Aria Labels
 * Accessibility labels for screen readers
 */
export const ARIA_LABELS = {
  CONFIRM: 'Confirm',
  CANCEL: 'Cancel',
  EDIT_VALUE: 'Edit value',
  CONFIRM_FIELD: 'Confirm {field}',
  CANCEL_FIELD: 'Cancel {field}',
} as const;

/**
 * Finance Stats Labels
 * Labels for finance statistics cards
 */
export const FINANCE_STATS_LABELS = {
  VALOR_TOTAL_APROBADO: 'Valor Total Aprobado',
  MARGEN_PROMEDIO: 'Margen Promedio',
  HIGH_RISK_DEALS: 'High-Risk Deals',
  DEALS_THIS_MONTH: 'Deals This Month',
} as const;

/**
 * Sales Stats Labels
 * Labels for sales statistics cards
 */
export const SALES_STATS_LABELS = {
  PENDING_APPROVALS: 'Aprobaciones Pendiente',
  PENDING_MRC: 'MRC Pendiente',
  PENDING_COMISIONES: 'Comisiones Pendientes',
  AVG_GROSS_MARGIN: 'Margen Bruto Promedio',
} as const;

/**
 * Date Picker Labels
 * Day abbreviations and date picker labels
 */
export const DATE_PICKER = {
  DAYS: ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'] as const,
} as const;

/**
 * Validation Messages
 * Error and validation messages for form fields
 */
export const VALIDATION_MESSAGES = {
  PLAZO_INVALID: 'Please enter a valid whole number greater than 0 for Plazo Contrato.',
  UNIDAD_REQUIRED: 'Selección obligatoria: Por favor, selecciona una Unidad de Negocio válida.',
  REGION_REQUIRED: 'Selección obligatoria: Por favor, selecciona una Región válida.',
  TIPO_VENTA_REQUIRED: 'Selección obligatoria: Por favor, selecciona un Tipo de Venta válido.',
  MRC_INVALID: 'Please enter a valid non-negative number for MRC.',
  NRC_INVALID: 'Please enter a valid non-negative number for NRC.',
  CODE_EMPTY: 'Por favor, ingresa un código.',
  CODE_ALREADY_LOADED: 'Code {code} is already loaded.',
  NO_SERVICE_RETURNED: 'Error: El código no devolvió ningún servicio.',
  NO_CLIENT_DATA: 'Error: Los datos del cliente (RUC/Razón Social) no vinieron en la respuesta. Contactar a backend.',
  CLIENT_MISMATCH_TITLE: 'Error: No puedes agregar servicios de un cliente diferente.',
  CLIENT_MISMATCH_CURRENT: 'Cliente Actual: {name} (RUC: {ruc})',
  CLIENT_MISMATCH_NEW: 'Nuevo Cliente: {name} (RUC: {ruc})',
  CLIENT_MISMATCH_FOOTER: 'Todos los servicios deben pertenecer al mismo cliente.',

  // Admin Panel Validation
  SELECT_USER_REQUIRED: 'Please select a user',
  PASSWORD_REQUIRED: 'Please enter a new password',
  PASSWORDS_DO_NOT_MATCH: 'Passwords do not match',

  // Master Data Validation
  VARIABLE_AND_VALUE_REQUIRED: 'Please select a variable and enter a value.',
  VALUE_MUST_BE_POSITIVE: 'Please enter a valid numeric value greater than zero.',

  // Fixed Cost Code Manager Validation
  CODIGO_NO_VALIDO: 'Código no válido.',

  // Rejection Note Validation
  REJECTION_NOTE_MAX_LENGTH: 500,
} as const;

/**
 * Error Messages
 * Service and API error messages
 */
export const ERROR_MESSAGES = {
  // Admin Service Errors
  FAILED_LOAD_USER_DATA: 'Failed to load user data.',
  FAILED_UPDATE_ROLE: 'Failed to update role.',
  FAILED_RESET_PASSWORD: 'Failed to reset password.',

  // Master Data Service Errors
  FAILED_FETCH_HISTORY: 'Failed to fetch history.',
  FAILED_CONNECT_SERVER: 'Failed to connect to server.',
  FAILED_FETCH_EDITABLE_VARIABLES: 'Failed to fetch editable variables.',
  FAILED_FETCH_VARIABLE_CONFIG: 'Failed to fetch editable variable configuration.',
  FAILED_UPDATE_VARIABLE: 'Failed to update variable.',
  SERVER_ERROR_VARIABLE_UPDATE: 'Server error during variable update.',

  // Transaction Service Errors
  FAILED_FETCH_TRANSACTIONS: 'Failed to fetch transactions.',
  FAILED_FETCH_TRANSACTION_DETAILS: 'Failed to fetch transaction details.',
  FAILED_ACTION_TRANSACTION: 'Failed to {action} transaction.',
  FAILED_CALCULATE_COMMISSION: 'Failed to calculate commission.',
  FAILED_CONNECT_SERVER_COMMISSION: 'Failed to connect to the server for commission calculation.',
  FAILED_PROCESS_EXCEL: 'An unknown error occurred during processing.',
  FAILED_CONNECT_SERVER_UPLOAD: 'Failed to connect to the server for upload.',
  FAILED_SUBMIT_TRANSACTION: 'An unknown error occurred during submission.',
  FAILED_CONNECT_SERVER_SUBMISSION: 'Failed to connect to the server for submission.',
  FAILED_CALCULATE_PREVIEW: 'Failed to calculate preview.',
  FAILED_CONNECT_SERVER_PREVIEW: 'Failed to connect to the server for preview calculation.',
  FAILED_FETCH_FIXED_COSTS: 'Failed to fetch fixed costs.',
  FAILED_FETCH_RECURRING_SERVICES: 'Failed to fetch recurring services.',
  NETWORK_ERROR_CODE_LOOKUP: 'Network error during code lookup.',
  UNKNOWN_UPLOAD_ERROR: 'Unknown upload error',
  UNKNOWN_SUBMISSION_ERROR: 'Unknown submission error',

  // Generic Errors
  UNKNOWN_ERROR: 'Unknown error',
} as const;

/**
 * Master Data Variable Labels
 * Labels for master data variables
 */
export const VARIABLE_LABELS = {
  COSTO_CAPITAL: 'Costo Capital',
  TIPO_CAMBIO: 'Tipo de Cambio',
  TASA_CARTA_FIANZA: 'Tasa Carta Fianza (%)',
} as const;

/**
 * Confirmation Messages
 * Confirmation dialog messages
 */
export const CONFIRMATION_MESSAGES = {
  APPROVE_TRANSACTION: '¿Estás seguro/a de aprobar esta transacción?',
  REJECT_TRANSACTION: '¿Estás seguro/a de rechazar esta transacción?',
  CALCULATE_COMMISSION: '¿Estás seguro/a de realizar el cálculo de comisión? Esto actualizará la base de datos.',
} as const;

/**
 * Placeholder Text
 * Placeholder text for input fields
 */
export const PLACEHOLDERS = {
  SELECT_FIELD: 'Selecciona {field}...',
  ENTER_AMOUNT: 'Enter amount',
  INVESTMENT_CODE: 'E.G., WIN-001',
  SERVICE_CODE: 'E.G., Q-12345',
  SELECT_VARIABLE: 'Selecciona una variable',
  ENTER_VALUE: 'Ingresa el valor',
  OPTIONAL_COMMENT: 'Comentario opcional (máximo 50 caracteres)',
} as const;

/**
 * Empty State Messages
 * Messages shown when data is not available
 */
export const EMPTY_STATE_MESSAGES = {
  NO_FIXED_COSTS: 'No fixed cost data available.',
  NO_RECURRING_SERVICES: 'No recurring services data available.',
  NO_CASH_FLOW: 'No cash flow data available.',
  NO_INVESTMENT_DATA: 'No hay datos de inversión cargados.',
  NO_RECURRING_SERVICES_LOADED: 'No hay servicios recurrentes cargados.',
  USE_CARGAR_BUTTON: 'Use el botón \'Cargar\' para agregar {type} por código.',
  NO_TRANSACTIONS_FOUND: 'No transactions found matching your criteria.',
  NO_DATA_AVAILABLE: 'No data available.',
} as const;

/**
 * Status Messages
 * Banner and status-related messages
 */
export const STATUS_MESSAGES = {
  FINANCE_EDIT_MODE: 'Finance Edit Mode Active',
  FINANCE_EDIT_INFO: 'Puedes modificar los valores clave (Unidad, Plazo, MRC, NRC, Gigalan, Periodos) antes de aprobar/rechazar.',
  APPROVED_TITLE: 'Plantilla Aprobada!',
  APPROVED_MESSAGE: 'Esta plantilla ya fue aprobada. Felicidades',
  REJECTED_TITLE: 'Plantilla Rechazada!',
  REJECTED_MESSAGE: 'No se logro aprobar. Comunicate con mesadeprecios@fiberlux.pe para indagar porque.',
  DATA_FROM_EXCEL: 'Toda la data es inicialmente extraida del excel',
  TRANSACTION_STATUS: 'Transaction Status: {status}',
  MODIFICATION_NOT_ALLOWED: 'Modification of key inputs is not allowed once a transaction has been reviewed.',
  REVIEW_DATA_CAREFULLY: 'Por favor revisar la data cargada de manera minuciosa',
  REVIEW_DATA_MESSAGE: 'Asegúrate que toda la información sea correcta antes de confirmarla.',
} as const;

/**
 * Success Messages
 * Success notifications and confirmations
 */
export const SUCCESS_MESSAGES = {
  ROLE_UPDATED: 'Role updated successfully to {role}',
  PASSWORD_RESET: 'Password reset successful for {username}',
  VARIABLE_UPDATED: 'Variable "{variable}" updated successfully to {value}.',
} as const;

// Legacy exports for backwards compatibility
// TODO: Remove these after migration is complete
export const UNIDADES_NEGOCIO = BUSINESS_UNITS.LIST;
export const REGIONS_LEGACY = REGIONS.LIST;
export const SALE_TYPES_LEGACY = SALE_TYPES.LIST;
