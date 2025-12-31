// src/features/masterdata/masterDataService.ts
import { api } from '@/lib/api';
import type { BaseApiResponse } from '@/types';
import { ERROR_MESSAGES, VARIABLE_LABELS } from '@/config';

// --- 2. Define types for this service ---
// FIX: Define the explicit HistoryItem type based on HistoryTable's expectation
export interface HistoryItem {
    id: number | string;
    variable_name: string;
    category: string;
    variable_value: number | string;
    date_recorded: string;
    recorder_username: string;
    comment: string | null;
}

interface EditableVariableConfig {
    name: string;
    label: string;
    category: string;
}

interface UpdatePayload {
    variable_name: string;
    variable_value: number;
    comment: string;
}

// --- Helper Logic (remains the same, but typed) ---
const VARIABLE_LABEL_MAP: Record<string, string> = {
    'costoCapital': VARIABLE_LABELS.COSTO_CAPITAL,
    'tipoCambio': VARIABLE_LABELS.TIPO_CAMBIO,
    'tasaCartaFianza': VARIABLE_LABELS.TASA_CARTA_FIANZA,
};

const parseEditableConfig = (response: any): EditableVariableConfig[] => {
    const variablesObject = response.editable_variables || {};
    return Object.keys(variablesObject).map(name => ({
        name: name,
        label: VARIABLE_LABEL_MAP[name] || name,
        category: variablesObject[name].category
    }));
};


// --- 3. Define typed service functions ---

// FIX: Update HistoryResult to use the explicit HistoryItem
type HistoryResult = {
    success: true;
    data: HistoryItem[];
} | {
    success: false;
    error: string;
    data?: undefined; // Explicitly undefined on error
}

export async function getMasterVariableHistory(): Promise<HistoryResult> {
    try {
        // Use the explicit HistoryItem type in the API call
        const result = await api.get<{ success: boolean, data: HistoryItem[], error?: string }>('/api/master-variables');
        if (result.success) {
            return { success: true, data: result.data || [] };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_FETCH_HISTORY };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER };
    }
}

type ConfigResult = {
    success: true;
    data: EditableVariableConfig[];
} | {
    success: false;
    error: string;
    data?: undefined;
}

export async function getEditableConfig(): Promise<ConfigResult> {
    try {
        const response = await api.get<any>('/api/master-variables/categories'); 

        if (response.success) {
            const parsedConfig = parseEditableConfig(response);
            return { success: true, data: parsedConfig };
        } else {
            return { success: false, error: response.error || ERROR_MESSAGES.FAILED_FETCH_EDITABLE_VARIABLES };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_FETCH_VARIABLE_CONFIG };
    }
}

/**
 * Submits a new variable value.
 * We can reuse BaseApiResponse for the return type.
 */
export async function updateMasterVariable(payload: UpdatePayload): Promise<BaseApiResponse> {
    try {
        const result = await api.post<BaseApiResponse>('/api/master-variables/update', payload);

        if (result.success) {
            return { success: true, data: result.data };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_UPDATE_VARIABLE };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.SERVER_ERROR_VARIABLE_UPDATE };
    }
}