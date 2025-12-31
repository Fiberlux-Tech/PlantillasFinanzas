// src/features/transactions/services/kpi.service.ts
import { api } from '@/lib/api';
import { API_CONFIG, ERROR_MESSAGES } from '@/config';

// --- Types ---

interface PendingMrcResponse {
  success: boolean;
  total_pending_mrc: number;
  user_role: string;
  username: string;
}

interface PendingCountResponse {
  success: boolean;
  pending_count: number;
  user_role: string;
  username: string;
}

interface PendingComisionesResponse {
  success: boolean;
  total_pending_comisiones: number;
  user_role: string;
  username: string;
}

interface AverageGrossMarginResponse {
  success: boolean;
  average_gross_margin_ratio: number;
  user_role: string;
  username: string;
  filters?: {
    months_back: number | null;
    status_filter: string | null;
  };
}

export interface KpiData {
  pendingMrc: number;
  pendingCount: number;
  pendingComisiones: number;
  averageGrossMargin: number;
}

interface FetchKpiResult {
  success: boolean;
  data?: KpiData;
  error?: string;
}

// --- Query Parameter Types ---

interface AverageGrossMarginParams {
  months_back?: number;
  status?: 'PENDING' | 'APPROVED' | 'REJECTED';
}

// --- Functions ---

/**
 * Fetches the total sum of MRC for all pending transactions
 */
export async function getPendingMrc(): Promise<{ success: boolean; data?: number; error?: string }> {
  try {
    const result = await api.get<PendingMrcResponse>(API_CONFIG.ENDPOINTS.KPI_PENDING_MRC);

    if (result.success) {
      return { success: true, data: result.total_pending_mrc };
    }

    return { success: false, error: ERROR_MESSAGES.FAILED_FETCH_TRANSACTIONS };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : ERROR_MESSAGES.FAILED_CONNECT_SERVER,
    };
  }
}

/**
 * Fetches the count of pending transactions
 */
export async function getPendingCount(): Promise<{ success: boolean; data?: number; error?: string }> {
  try {
    const result = await api.get<PendingCountResponse>(API_CONFIG.ENDPOINTS.KPI_PENDING_COUNT);

    if (result.success) {
      return { success: true, data: result.pending_count };
    }

    return { success: false, error: ERROR_MESSAGES.FAILED_FETCH_TRANSACTIONS };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : ERROR_MESSAGES.FAILED_CONNECT_SERVER,
    };
  }
}

/**
 * Fetches the total sum of comisiones (commissions) for all pending transactions
 */
export async function getPendingComisiones(): Promise<{ success: boolean; data?: number; error?: string }> {
  try {
    const result = await api.get<PendingComisionesResponse>(API_CONFIG.ENDPOINTS.KPI_PENDING_COMISIONES);

    if (result.success) {
      return { success: true, data: result.total_pending_comisiones };
    }

    return { success: false, error: ERROR_MESSAGES.FAILED_FETCH_TRANSACTIONS };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : ERROR_MESSAGES.FAILED_CONNECT_SERVER,
    };
  }
}

/**
 * Fetches the average gross margin ratio for transactions
 * @param params - Optional filters (months_back, status)
 */
export async function getAverageGrossMargin(
  params?: AverageGrossMarginParams
): Promise<{ success: boolean; data?: number; error?: string }> {
  try {
    let url = API_CONFIG.ENDPOINTS.KPI_AVERAGE_GROSS_MARGIN;

    // Build query string if params are provided
    if (params) {
      const queryParams = new URLSearchParams();
      if (params.months_back !== undefined) {
        queryParams.append('months_back', params.months_back.toString());
      }
      if (params.status) {
        queryParams.append('status', params.status);
      }
      const queryString = queryParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    const result = await api.get<AverageGrossMarginResponse>(url);

    if (result.success) {
      return { success: true, data: result.average_gross_margin_ratio };
    }

    return { success: false, error: ERROR_MESSAGES.FAILED_FETCH_TRANSACTIONS };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : ERROR_MESSAGES.FAILED_CONNECT_SERVER,
    };
  }
}

/**
 * Fetches all KPIs in parallel
 * This is the recommended method to use in components
 */
export async function getAllKpis(
  averageMarginParams?: AverageGrossMarginParams
): Promise<FetchKpiResult> {
  try {
    const [mrcResult, countResult, comisionesResult, marginResult] = await Promise.all([
      getPendingMrc(),
      getPendingCount(),
      getPendingComisiones(),
      getAverageGrossMargin(averageMarginParams),
    ]);

    // Check if any request failed
    if (!mrcResult.success || !countResult.success || !comisionesResult.success || !marginResult.success) {
      const errors = [
        mrcResult.error,
        countResult.error,
        comisionesResult.error,
        marginResult.error,
      ].filter(Boolean);

      return {
        success: false,
        error: errors[0] || ERROR_MESSAGES.FAILED_FETCH_TRANSACTIONS,
      };
    }

    return {
      success: true,
      data: {
        pendingMrc: mrcResult.data ?? 0,
        pendingCount: countResult.data ?? 0,
        pendingComisiones: comisionesResult.data ?? 0,
        averageGrossMargin: marginResult.data ?? 0,
      },
    };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : ERROR_MESSAGES.FAILED_CONNECT_SERVER,
    };
  }
}
