// src/features/transactions/components/PreviewModal/ModalFooter.tsx
import { useState } from 'react';
import { CheckCircleIcon } from '@/components/shared/Icons';
import { useTransactionPreview } from '@/features/transactions/contexts/TransactionPreviewContext';
import type { Transaction, TransactionDetailResponse, FixedCost, RecurringService } from '@/types';
import { BUSINESS_UNITS, VALIDATION_MESSAGES, STATUS_MESSAGES, BUTTON_LABELS, TRANSACTION_STATUS, CONFIRMATION_MESSAGES } from '@/config';
import { RejectionNoteModal } from './RejectionNoteModal';

// --- SALES FOOTER PROPS ---
interface SalesFooterProps {
    view: 'SALES';
    onConfirm: (finalData: TransactionDetailResponse['data']) => void;
    onClose: () => void;
}

// --- FINANCE FOOTER PROPS ---
interface FinanceFooterProps {
    view: 'FINANCE';
    onApprove: (transactionId: number, status: 'approve' | 'reject', modifiedData: Partial<Transaction>, fixedCosts: FixedCost[] | null, recurringServices: RecurringService[] | null) => void;
    onReject: (transactionId: number, status: 'approve' | 'reject', modifiedData: Partial<Transaction>, fixedCosts: FixedCost[] | null, recurringServices: RecurringService[] | null) => void;
    onCalculateCommission: (transactionId: number) => void;
    onSave: (transactionId: number, modifiedData: Partial<Transaction>, fixedCosts: FixedCost[] | null, recurringServices: RecurringService[] | null) => void;
}

// --- UNIFIED PROPS TYPE ---
type ModalFooterProps = SalesFooterProps | FinanceFooterProps;

// --- SALES FOOTER CONTENT ---
function SalesFooterContent({ onConfirm, onClose }: Omit<SalesFooterProps, 'view'>) {
    const { baseTransaction, draftState, dispatch } = useTransactionPreview();
    const { liveEdits, currentFixedCosts, currentRecurringServices, apiError } = draftState;

    const handleConfirmClick = () => {
        dispatch({ type: 'SET_API_ERROR', payload: null });
        const finalTransactionState = { ...baseTransaction.transactions, ...liveEdits };

        if (!finalTransactionState.unidadNegocio || !(BUSINESS_UNITS.LIST as readonly string[]).includes(finalTransactionState.unidadNegocio)) {
            const errorMsg = VALIDATION_MESSAGES.UNIDAD_REQUIRED;
            dispatch({ type: 'SET_API_ERROR', payload: errorMsg });
            alert(errorMsg);
            return;
        }

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
                {apiError ? (
                    <span className="text-red-600 font-medium">{apiError}</span>
                ) : (
                    <>
                        <CheckCircleIcon className="text-green-600" />
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

// --- FINANCE FOOTER CONTENT ---
function FinanceFooterContent({ onApprove, onReject, onCalculateCommission, onSave }: Omit<FinanceFooterProps, 'view'>) {
    const { baseTransaction, draftState } = useTransactionPreview();
    const { liveEdits, currentFixedCosts, currentRecurringServices } = draftState;

    const tx = baseTransaction.transactions;
    const canModify = tx.ApprovalStatus === TRANSACTION_STATUS.PENDING;
    const [isRejectionModalOpen, setIsRejectionModalOpen] = useState(false);

    const handleApproveClick = () => {
        if (window.confirm(CONFIRMATION_MESSAGES.APPROVE_TRANSACTION)) {
            const modifiedFields = { ...tx, ...liveEdits };
            onApprove(tx.id, 'approve', modifiedFields, currentFixedCosts, currentRecurringServices);
        }
    };

    const handleRejectClick = () => {
        setIsRejectionModalOpen(true);
    };

    const handleRejectConfirm = (note: string) => {
        setIsRejectionModalOpen(false);
        const modifiedFields = { ...tx, ...liveEdits, rejection_note: note };
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

// --- MAIN COMPONENT WITH ROLE SWITCH ---
export function ModalFooter(props: ModalFooterProps) {
    if (props.view === 'SALES') {
        return <SalesFooterContent onConfirm={props.onConfirm} onClose={props.onClose} />;
    }
    return (
        <FinanceFooterContent
            onApprove={props.onApprove}
            onReject={props.onReject}
            onCalculateCommission={props.onCalculateCommission}
            onSave={props.onSave}
        />
    );
}

// Also export the legacy names for backwards compatibility during migration
export { SalesFooterContent as SalesPreviewFooter };
export { FinanceFooterContent as FinancePreviewFooter };
