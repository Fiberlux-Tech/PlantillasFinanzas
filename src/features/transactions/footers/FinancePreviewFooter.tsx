// src/features/transactions/footers/FinancePreviewFooter.tsx
import { useState } from 'react';
import type { Transaction, FixedCost, RecurringService } from '@/types';
import { useTransactionPreview } from '@/contexts/TransactionPreviewContext';
import { TRANSACTION_STATUS, CONFIRMATION_MESSAGES, BUTTON_LABELS } from '@/config';
import { RejectionNoteModal } from '@/features/transactions/components/RejectionNoteModal';

// --- PROPS INTERFACE ---
interface FinancePreviewFooterProps {
    onApprove: (transactionId: number, status: 'approve' | 'reject', modifiedData: Partial<Transaction>, fixedCosts: FixedCost[] | null, recurringServices: RecurringService[] | null) => void;
    onReject: (transactionId: number, status: 'approve' | 'reject', modifiedData: Partial<Transaction>, fixedCosts: FixedCost[] | null, recurringServices: RecurringService[] | null) => void;
    onCalculateCommission: (transactionId: number) => void;
    onSave: (transactionId: number, modifiedData: Partial<Transaction>, fixedCosts: FixedCost[] | null, recurringServices: RecurringService[] | null) => void;
}

export function FinancePreviewFooter({
    onApprove,
    onReject,
    onCalculateCommission,
    onSave
}: FinancePreviewFooterProps) {

    // --- 1. GET DATA FROM CONTEXT (Refactored) ---
    // We now get 'draftState' which contains all our draft data
    const {
        baseTransaction,
        draftState
    } = useTransactionPreview();

    // 2. Destructure the state we need from draftState
    const {
        liveEdits,
        currentFixedCosts,
        currentRecurringServices
    } = draftState;

    const tx = baseTransaction.transactions;
    const canModify = tx.ApprovalStatus === TRANSACTION_STATUS.PENDING;

    // 3. State for rejection note modal
    const [isRejectionModalOpen, setIsRejectionModalOpen] = useState(false);

    // 4. Handlers now read from draftState variables
    const handleApproveClick = () => {
        if (window.confirm(CONFIRMATION_MESSAGES.APPROVE_TRANSACTION)) {
            const modifiedFields = { ...tx, ...liveEdits };
            // Pass the current draft state up to the parent handler
            onApprove(tx.id, 'approve', modifiedFields, currentFixedCosts, currentRecurringServices);
        }
    };

    const handleRejectClick = () => {
        // Open the rejection note modal instead of showing confirm dialog
        setIsRejectionModalOpen(true);
    };

    const handleRejectConfirm = (note: string) => {
        setIsRejectionModalOpen(false);
        const modifiedFields = { ...tx, ...liveEdits, rejection_note: note };
        // Pass the current draft state up to the parent handler
        onReject(tx.id, 'reject', modifiedFields, currentFixedCosts, currentRecurringServices);
    };

    const handleRejectCancel = () => {
        setIsRejectionModalOpen(false);
    };

    const handleCalculateCommissionClick = () => {
        if (window.confirm(CONFIRMATION_MESSAGES.CALCULATE_COMMISSION)) {
            onCalculateCommission(tx.id);
        }
    };

    const handleSaveClick = () => {
        if (window.confirm('¿Guardar los cambios realizados?')) {
            const modifiedFields = { ...tx, ...liveEdits };
            onSave(tx.id, modifiedFields, currentFixedCosts, currentRecurringServices);
        }
    };

    return (
        <>
            <div className="w-full flex justify-between items-center p-5 border-t bg-white space-x-3">
                 <div className="flex-grow"></div>
                 <button
                    onClick={handleSaveClick}
                    className="px-5 py-2 text-sm font-medium text-white bg-gray-600 rounded-lg hover:bg-gray-700 disabled:bg-gray-400"
                    disabled={!canModify}
                >
                    Guardar Cambios
                </button>

                 <button
                    onClick={handleCalculateCommissionClick}
                    className="px-5 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                    disabled={!canModify}
                >
                    {BUTTON_LABELS.COMISIONES}
                </button>

                <button
                    onClick={handleRejectClick}
                    className="px-5 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:bg-gray-400"
                    disabled={!canModify}
                >
                    {BUTTON_LABELS.RECHAZAR}
                </button>

                <button
                    onClick={handleApproveClick}
                    className="px-5 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:bg-gray-400"
                    disabled={!canModify}
                >
                    {BUTTON_LABELS.APROBAR}
                </button>
            </div>

            <RejectionNoteModal
                isOpen={isRejectionModalOpen}
                onConfirm={handleRejectConfirm}
                onCancel={handleRejectCancel}
            />
        </>
    );
}