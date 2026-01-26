// src/features/transactions/services/shared.service.ts
import { api } from '@/lib/api';
import type { KpiCalculationResponse } from '@/types';
import { API_CONFIG, ERROR_MESSAGES } from '@/config';

// --- Types ---

type CalculatePreviewResult = {
    success: true;
    data: KpiCalculationResponse['data'];
} | {
    success: false;
    error: string;
    data?: undefined;
};

// --- Functions ---

/**
 * Sends modified data to the backend for KPI recalculation (PREVIEW ONLY).
 */
export async function calculatePreview(payload: any): Promise<CalculatePreviewResult> {
    try {
        const result = await api.post<KpiCalculationResponse>(API_CONFIG.ENDPOINTS.CALCULATE_PREVIEW, payload); 

        if (result && result.success) {
            return { success: true, data: result.data };
        } else {
             return { success: false, error: (result as any).error || ERROR_MESSAGES.FAILED_CALCULATE_PREVIEW };
        }

    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER_PREVIEW };
    }
}