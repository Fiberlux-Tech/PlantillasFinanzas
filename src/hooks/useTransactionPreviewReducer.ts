// src/features/transactions/hooks/useTransactionPreviewReducer.ts
import type {
    TransactionDetailResponse,
    KpiCalculationResponse,
    FixedCost,
    RecurringService
} from '@/types';

// 1. Define the shape of our "draft" state
export interface PreviewState {
    liveEdits: Record<string, any>;
    currentFixedCosts: FixedCost[];
    currentRecurringServices: RecurringService[];
    liveKpis: KpiCalculationResponse['data'] | null;
    apiError: string | null;
    isRecalculating: boolean;
}

// 2. Define all possible actions
export type PreviewAction =
    | { type: 'UPDATE_TRANSACTION_FIELD'; payload: { key: string; value: any | null } }
    | { type: 'UPDATE_MULTIPLE_TRANSACTION_FIELDS'; payload: Record<string, any> }
    | { type: 'ADD_FIXED_COSTS'; payload: FixedCost[] }
    | { type: 'REMOVE_FIXED_COST'; payload: number } // payload is index (for trash icon in table)
    | { type: 'REMOVE_FIXED_COST_BY_CODE'; payload: string } // payload is 'ticket' code (for code manager)
    | { type: 'UPDATE_FIXED_COST'; payload: { index: number; field: keyof FixedCost; value: any } }
    | { type: 'REPLACE_FIXED_COST'; payload: { index: number; updatedCost: FixedCost } } // Index-based replacement for modal edits
    | { type: 'UPDATE_RECURRING_SERVICE'; payload: { index: number; field: keyof RecurringService; value: any } }
    | { type: 'REPLACE_RECURRING_SERVICE'; payload: { index: number; updatedService: RecurringService } } // Index-based replacement for modal edits
    | { type: 'ADD_RECURRING_SERVICES'; payload: RecurringService[] }
    | { type: 'REMOVE_RECURRING_SERVICE'; payload: number } // payload is index (for trash icon in table)
    | { type: 'REMOVE_RECURRING_SERVICE_BY_CODE'; payload: string } // payload is code (for code manager)
    | { type: 'RECALCULATION_START' }
    | { type: 'RECALCULATION_SUCCESS'; payload: KpiCalculationResponse['data'] }
    | { type: 'RECALCULATION_ERROR'; payload: string }
    | { type: 'SET_API_ERROR'; payload: string | null }
    | { type: 'RESET_STATE'; payload: TransactionDetailResponse['data'] };

// 3. Create the initializer function
export function getInitialState(
    baseTransaction: TransactionDetailResponse['data']
): PreviewState {
    const initialKpis = {
        ...baseTransaction.transactions,
        timeline: baseTransaction.transactions.timeline || baseTransaction.timeline,
    };

    return {
        liveEdits: {},
        currentFixedCosts: baseTransaction.fixed_costs || [],
        currentRecurringServices: baseTransaction.recurring_services || [],
        liveKpis: initialKpis as KpiCalculationResponse['data'],
        apiError: null,
        isRecalculating: false,
    };
}

// 4. Create the reducer function
export function transactionPreviewReducer(
    state: PreviewState,
    action: PreviewAction
): PreviewState {
    switch (action.type) {
        case 'UPDATE_TRANSACTION_FIELD':
            return {
                ...state,
                liveEdits: {
                    ...state.liveEdits,
                    [action.payload.key]: action.payload.value,
                },
            };

        case 'UPDATE_MULTIPLE_TRANSACTION_FIELDS':
            return {
                ...state,
                liveEdits: {
                    ...state.liveEdits,
                    ...action.payload, // Spread the object of key/value updates
                },
            };

        case 'ADD_FIXED_COSTS':
            return {
                ...state,
                currentFixedCosts: [
                    ...state.currentFixedCosts,
                    ...action.payload,
                ],
            };

        case 'REMOVE_FIXED_COST':
            // Index-based removal (trash icon in table)
            return {
                ...state,
                currentFixedCosts: state.currentFixedCosts.filter(
                    (_, index) => index !== action.payload
                ),
            };

        case 'REMOVE_FIXED_COST_BY_CODE':
            // Code-based batch removal (code manager)
            return {
                ...state,
                currentFixedCosts: state.currentFixedCosts.filter(
                    (cost) => cost.ticket !== action.payload
                ),
            };

        case 'UPDATE_FIXED_COST': {
            const newCosts = state.currentFixedCosts.map((cost, index) => {
                if (index !== action.payload.index) {
                    return cost;
                }
                return {
                    ...cost,
                    [action.payload.field]: action.payload.value,
                };
            });
            return { ...state, currentFixedCosts: newCosts };
        }

        case 'REPLACE_FIXED_COST':
            // Index-based replacement (modal save)
            return {
                ...state,
                currentFixedCosts: state.currentFixedCosts.map((cost, index) =>
                    index === action.payload.index ? action.payload.updatedCost : cost
                ),
            };

        case 'UPDATE_RECURRING_SERVICE': {
            const newServices = state.currentRecurringServices.map((service, index) => {
                if (index !== action.payload.index) {
                    return service;
                }
                return {
                    ...service,
                    [action.payload.field]: action.payload.value,
                };
            });
            return { ...state, currentRecurringServices: newServices };
        }

        case 'REPLACE_RECURRING_SERVICE':
            // Index-based replacement (modal save)
            return {
                ...state,
                currentRecurringServices: state.currentRecurringServices.map((service, index) =>
                    index === action.payload.index ? action.payload.updatedService : service
                ),
            };

        case 'ADD_RECURRING_SERVICES':
            return {
                ...state,
                currentRecurringServices: [
                    ...state.currentRecurringServices,
                    ...action.payload,
                ],
            };

        case 'REMOVE_RECURRING_SERVICE':
            // Index-based removal (trash icon in table)
            return {
                ...state,
                currentRecurringServices: state.currentRecurringServices.filter(
                    (_, index) => index !== action.payload
                ),
            };

        case 'REMOVE_RECURRING_SERVICE_BY_CODE':
            // Code-based batch removal (code manager)
            return {
                ...state,
                currentRecurringServices: state.currentRecurringServices.filter(
                    (service) => String(service.id) !== String(action.payload)
                ),
            };

        case 'RECALCULATION_START':
            return {
                ...state,
                isRecalculating: true,
                apiError: null,
            };

        case 'RECALCULATION_SUCCESS':
            return {
                ...state,
                isRecalculating: false,
                liveKpis: action.payload,
                apiError: null,
            };

        case 'RECALCULATION_ERROR':
            return {
                ...state,
                isRecalculating: false,
                liveKpis: null,
                apiError: action.payload,
            };

        case 'SET_API_ERROR':
            return {
                ...state,
                apiError: action.payload,
            };

        case 'RESET_STATE':
            console.log('🔄 RESETTING STATE with new baseTransaction:', {
                newFixedCostsCount: action.payload.fixed_costs?.length,
                newRecurringServicesCount: action.payload.recurring_services?.length
            });
            return getInitialState(action.payload);

        default:
            return state;
    }
}