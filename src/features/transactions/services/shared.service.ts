// src/features/transactions/services/shared.service.ts
import { api } from '@/lib/api';
import type {
    KpiCalculationResponse,
    FixedCost,
    RecurringService
} from '@/types';
import { API_CONFIG, ERROR_MESSAGES } from '@/config';

// --- Types ---

// 1. Define the structure the API is ACTUALLY sending in its 'data' key
//    (Based on your lookup, it's an object containing the array)
interface RecurringServiceLookupResponse {
    recurring_services: RecurringService[];
    // We no longer expect a separate 'client_data' key
}

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

export async function getFixedCostsByCodes(codes: string[]): Promise<{ success: true; data: FixedCost[] } | { success: false; error: string; data?: undefined }> {
    try {
        const payload = { investment_codes: codes };
        const result = await api.post<{ success: boolean, data: { fixed_costs: FixedCost[] }, error?: string }>(
            API_CONFIG.ENDPOINTS.FIXED_COSTS_LOOKUP,
            payload
        );
        if (result.success) {
            const fixedCosts = result.data?.fixed_costs || [];
            return { success: true, data: fixedCosts };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_FETCH_FIXED_COSTS };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.NETWORK_ERROR_CODE_LOOKUP };
    }
}

//
// --- 2. THIS FUNCTION IS NOW CORRECTED ---
//
export async function getRecurringServicesByCodes(codes: string[]): Promise<{ 
    success: true; 
    data: RecurringServiceLookupResponse // Return the object: { recurring_services: [...] }
} | { 
    success: false; 
    error: string; 
    data?: undefined 
}> {
    try {
        const payload = { service_codes: codes }; 
        // We expect the API to return { success: true, data: { recurring_services: [...] } }
        const result = await api.post<{ 
            success: boolean, 
            data: RecurringServiceLookupResponse, // This now matches the API
            error?: string 
        }>(
            API_CONFIG.ENDPOINTS.RECURRING_SERVICES_LOOKUP,
            payload
        );
        if (result.success) {
            // Return the entire 'data' object
            return { success: true, data: result.data };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_FETCH_RECURRING_SERVICES };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.NETWORK_ERROR_CODE_LOOKUP };
    }
}