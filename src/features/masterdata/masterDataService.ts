// src/features/masterdata/masterDataService.ts
import { api } from '@/lib/api';
import type { ApiResponse, HistoryItem, EditableConfigItem } from '@/types';
import { ERROR_MESSAGES, VARIABLE_LABELS } from '@/config';

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

interface CategoriesResponse {
    success: boolean;
    editable_variables: Record<string, { category: string }>;
    error?: string;
}

const parseEditableConfig = (response: CategoriesResponse): EditableConfigItem[] => {
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
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : ERROR_MESSAGES.FAILED_CONNECT_SERVER;
        return { success: false, error: message };
    }
}

type ConfigResult = {
    success: true;
    data: EditableConfigItem[];
} | {
    success: false;
    error: string;
    data?: undefined;
}

export async function getEditableConfig(): Promise<ConfigResult> {
    try {
        const response = await api.get<CategoriesResponse>('/api/master-variables/categories');

        if (response.success) {
            const parsedConfig = parseEditableConfig(response);
            return { success: true, data: parsedConfig };
        } else {
            return { success: false, error: response.error || ERROR_MESSAGES.FAILED_FETCH_EDITABLE_VARIABLES };
        }
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : ERROR_MESSAGES.FAILED_FETCH_VARIABLE_CONFIG;
        return { success: false, error: message };
    }
}

/**
 * Submits a new variable value.
 * We can reuse ApiResponse for the return type.
 */
export async function updateMasterVariable(payload: UpdatePayload): Promise<ApiResponse> {
    try {
        const result = await api.post<ApiResponse>('/api/master-variables/update', payload);

        if (result.success) {
            return { success: true, data: result.data };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_UPDATE_VARIABLE };
        }
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : ERROR_MESSAGES.SERVER_ERROR_VARIABLE_UPDATE;
        return { success: false, error: message };
    }
}