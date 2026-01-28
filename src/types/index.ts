// src/types/index.ts

// 1. User and Auth
export type UserRole = "ADMIN" | "SALES" | "FINANCE";

export interface User {
  id: string;  // Supabase UUID
  email: string;
  username: string;
  role: UserRole;
  is_authenticated?: boolean;  // Added for Pure JWT authentication
}

export interface AuthResponse {
  success: boolean;
  username: string;
  role: UserRole;
}

// 1b. Master Data Types
export interface EditableConfigItem {
  name: string;
  label: string;
  category: string;
}

export interface HistoryItem {
  id: number | string;
  variable_name: string;
  category: string;
  variable_value: number | string;
  date_recorded: string;
  recorder_username: string;
  comment: string | null;
}

export interface FormInputState {
  variable_name: string;
  variable_value: string;
  comment: string;
}

// 2. Core Data Models
export interface Transaction {
  id: number;
  transactionID?: string; // From Excel
  clientName: string;
  companyID?: string;
  orderID?: string;
  salesman: string;
  submissionDate: string;
  approvalDate?: string;
  ApprovalStatus: "PENDING" | "APPROVED" | "REJECTED";

  // Financials
  MRC_original: number;
  MRC_currency: "PEN" | "USD";
  MRC_pen: number;
  NRC_original: number;
  NRC_currency: "PEN" | "USD";
  NRC_pen: number;
  plazoContrato: number;
  tipoCambio: number;
  costoCapitalAnual: number;
  costoInstalacion: number;

  // KPIs
  VAN: number;
  TIR: number;
  payback: number;
  totalRevenue: number;
  totalExpense: number;
  grossMargin: number;
  grossMarginRatio: number;
  costoInstalacionRatio: number;
  comisiones: number;

  // Gigalan Specific
  unidadNegocio: string;
  gigalan_region?: string;
  gigalan_sale_type?: "NUEVO" | "EXISTENTE";
  gigalan_old_mrc?: number | null;

  timeline?: CashFlowTimeline; // <-- ADD THIS LINE

  // --- ADD THESE THREE LINES ---
  aplicaCartaFianza?: boolean;
  tasaCartaFianza?: number;
  costoCartaFianza?: number;

  // Rejection note
  rejection_note?: string;

  // Read-only field metadata from backend
  _readonly?: string[];
}

export interface FixedCost {
  id: number | string;
  categoria: string;
  tipo_servicio: string;
  ticket: string;
  ubicacion: string;
  cantidad: number;
  costoUnitario_original: number;
  costoUnitario_currency: "PEN" | "USD";
  costoUnitario_pen: number;
  periodo_inicio: number;
  duracion_meses: number;
  total_pen: number;
}

export interface RecurringService {
  id: number | string;
  tipo_servicio: string;
  ubicacion: string;
  Q: number;
  P_original: number;
  P_currency: "PEN" | "USD";
  P_pen: number;
  ingreso_pen: number;
  CU1_original: number;
  CU2_original: number;
  CU_currency: "PEN" | "USD";
  CU1_pen: number;
  CU2_pen: number;
  proveedor: string;
  egreso_pen: number;
}

export interface CashFlowTimeline {
  periods: string[];
  revenues: {
    nrc: number[];
    mrc: number[];
  };
  expenses: {
    comisiones: number[];
    egreso: number[];
    fixed_costs: Array<{
      id: number;
      tipo_servicio?: string;
      categoria?: string;
      timeline_values: number[];
    }>;
  };
  net_cash_flow: number[];
}

// 2b. API Payload Types
export interface TransactionSubmitPayload {
  transactions: Transaction;
  fixed_costs: FixedCost[];
  recurring_services: RecurringService[];
  fileName?: string;
}

export interface TransactionUpdatePayload {
  transactions: Partial<Transaction>;
  fixed_costs?: FixedCost[];
  recurring_services?: RecurringService[];
}

export interface PreviewPayload {
  transactions: Partial<Transaction>;
  fixed_costs: FixedCost[];
  recurring_services: RecurringService[];
}

// 3. API Response Payloads
// Note: We use generics for list responses

interface ApiListResponse<T> {
  success: boolean;
  data: {
    transactions: T[];
    pages: number;
  };
  error?: string;
}

export type SalesTransactionListResponse = ApiListResponse<Transaction>;
export type FinanceTransactionListResponse = ApiListResponse<Transaction>;

// For single transaction details
export interface TransactionDetailResponse {
  success: boolean;
  data: {
    transactions: Transaction;
    fixed_costs: FixedCost[];
    recurring_services: RecurringService[];
    timeline: CashFlowTimeline;
    fileName?: string; // From Excel upload
  };
  error?: string;
}

// KPI data shape returned by calculation endpoints
export interface KpiData extends Partial<Transaction> {
  timeline: CashFlowTimeline;
}

// For KPI calculation
export interface KpiCalculationResponse {
  success: boolean;
  data: KpiData;
  error?: string;
}

// Generic API envelope for all backend responses
export interface ApiResponse<T = void> {
  success: boolean;
  data?: T;
  error?: string;
  error_code?: number;  // Numeric HTTP-like code from backend (e.g., 400, 404, 500)
  message?: string;
}