// src/features/transactions/services/kpi.service.ts
import { api } from '@/lib/api';
import { API_CONFIG, ERROR_MESSAGES } from '@/config';

// --- Types ---

interface KpiSummaryResponse {
  success: boolean;
  data: {
    total_pending_mrc: number;
    pending_count: number;
    total_pending_comisiones: number;
    average_gross_margin_ratio: number;
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
 * Fetches all KPI metrics in a single request.
 * This is the recommended method to use in components.
 */
export async function getAllKpis(
  averageMarginParams?: AverageGrossMarginParams
): Promise<FetchKpiResult> {
  try {
    let url = API_CONFIG.ENDPOINTS.KPI_SUMMARY;

    if (averageMarginParams) {
      const queryParams = new URLSearchParams();
      if (averageMarginParams.months_back !== undefined) {
        queryParams.append('months_back', averageMarginParams.months_back.toString());
      }
      if (averageMarginParams.status) {
        queryParams.append('status', averageMarginParams.status);
      }
      const queryString = queryParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }

    const result = await api.get<KpiSummaryResponse>(url);

    if (result.success && result.data) {
      return {
        success: true,
        data: {
          pendingMrc: result.data.total_pending_mrc,
          pendingCount: result.data.pending_count,
          pendingComisiones: result.data.total_pending_comisiones,
          averageGrossMargin: result.data.average_gross_margin_ratio,
        },
      };
    }

    return { success: false, error: ERROR_MESSAGES.FAILED_FETCH_TRANSACTIONS };
  } catch (err) {
    return {
      success: false,
      error: err instanceof Error ? err.message : ERROR_MESSAGES.FAILED_CONNECT_SERVER,
    };
  }
}
