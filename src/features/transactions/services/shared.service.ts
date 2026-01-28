// src/features/transactions/services/shared.service.ts
import { api } from '@/lib/api';
import type { KpiCalculationResponse, PreviewPayload } from '@/types';
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
export async function calculatePreview(payload: PreviewPayload): Promise<CalculatePreviewResult> {
    try {
        const result = await api.post<KpiCalculationResponse>(API_CONFIG.ENDPOINTS.CALCULATE_PREVIEW, payload);

        if (result && result.success) {
            return { success: true, data: result.data };
        } else {
            const errorResult = result as KpiCalculationResponse & { error?: string };
            return { success: false, error: errorResult.error || ERROR_MESSAGES.FAILED_CALCULATE_PREVIEW };
        }

    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : ERROR_MESSAGES.FAILED_CONNECT_SERVER_PREVIEW;
        return { success: false, error: message };
    }
}