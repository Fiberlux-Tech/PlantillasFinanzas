// src/features/transactions/footers/SalesPreviewFooter.tsx
import { CheckCircleIcon } from '../../../components/shared/Icons';
import { useTransactionPreview } from '@/contexts/TransactionPreviewContext';
import type { TransactionDetailResponse } from '@/types';
import { BUSINESS_UNITS, VALIDATION_MESSAGES, STATUS_MESSAGES, BUTTON_LABELS } from '@/config';

// --- PROPS INTERFACE (Updated - removed onSubmit) ---
interface SalesPreviewFooterProps {
    transaction: TransactionDetailResponse['data'];
    onConfirm: (finalData: TransactionDetailResponse['data']) => void;
    onClose: () => void;
}

export function SalesPreviewFooter({ transaction, onConfirm, onClose }: SalesPreviewFooterProps) {

    // --- 1. GET DATA FROM CONTEXT (Refactored) ---
    // Get dispatch and draftState
    const {
        baseTransaction,
        draftState,
        dispatch
    } = useTransactionPreview();

    // 2. Destructure all state from draftState
    const {
        liveEdits,
        currentFixedCosts,
        currentRecurringServices,
        apiError // Get apiError from here
    } = draftState;

    const handleConfirmClick = () => {
        dispatch({ type: 'SET_API_ERROR', payload: null });

        // Combine base transaction with any live edits to get the final state
        const finalTransactionState = { ...baseTransaction.transactions, ...liveEdits };

        // Validation
        if (!finalTransactionState.unidadNegocio || !(BUSINESS_UNITS.LIST as readonly string[]).includes(finalTransactionState.unidadNegocio)) {
            const errorMsg = VALIDATION_MESSAGES.UNIDAD_REQUIRED;
            dispatch({ type: 'SET_API_ERROR', payload: errorMsg });
            alert(errorMsg);
            return;
        }

        // All transactions use the standard confirm logic (save transaction)
        const finalPayload = {
            ...baseTransaction,
            fixed_costs: currentFixedCosts,
            recurring_services: currentRecurringServices,
            transactions: finalTransactionState,
        };
        onConfirm(finalPayload);
    };

    return (
        <div className="w-full flex justify-between items-center p-5 border-t bg-white space-x-3">
            <div className="flex-grow flex items-center text-sm">
                {/* 4. Read error from draftState */}
                {apiError ? (
                    <span className="text-red-600 font-medium">{apiError}</span>
                ) : (
                    <>
                        <CheckCircleIcon />
                        <span className="ml-2 text-gray-600">{STATUS_MESSAGES.DATA_FROM_EXCEL}</span>
                    </>
                )}
            </div>
            <button
                onClick={onClose}
                className="px-5 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
                {BUTTON_LABELS.CANCELAR}
            </button>
            <button
                onClick={handleConfirmClick}
                className="px-5 py-2 text-sm font-medium text-white bg-black rounded-lg hover:bg-gray-800"
            >
                {BUTTON_LABELS.CONFIRMAR}
            </button>
        </div>
    );
}