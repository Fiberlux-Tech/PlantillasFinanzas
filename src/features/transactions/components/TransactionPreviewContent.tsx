// src/features/transactions/components/TransactionPreviewContent.tsx
import { useState, useMemo } from 'react';
import CostBreakdownRow from '@/features/transactions/components/CostBreakdownRow';
import {
    WarningIcon,
    CheckCircleIcon,
} from '@/components/shared/Icons';
import FixedCostsTable from '@/features/transactions/components/FixedCostsTable';
import RecurringServicesTable from './RecurringServicesTable';
import CashFlowTimelineTable from '@/features/transactions/components/CashFlowTimelineTable';
import { formatCurrency } from '@/lib/formatters';
import { TransactionOverviewInputs } from './TransactionOverviewInputs';
import { KpiMetricsGrid } from './KpiMetricsGrid';
import { useTransactionPreview } from '../contexts/TransactionPreviewContext';
import { TRANSACTION_STATUS, STATUS_MESSAGES, UI_LABELS } from '@/config';

type OpenSectionsState = Record<string, boolean>;

export function TransactionPreviewContent({ isFinanceView = false }: { isFinanceView?: boolean }) {

    // (State and Memos remain the same)
    const {
        baseTransaction,
        draftState,
        isNewTemplateMode
    } = useTransactionPreview();
    const {
        liveKpis,
        currentFixedCosts,
        currentRecurringServices
    } = draftState;
    const [openSections, setOpenSections] = useState<OpenSectionsState>({
        'cashFlow': false,
        'recurringCosts': false,
        'fixedCosts': false
    });
    const tx = baseTransaction.transactions;
    const timeline = liveKpis?.timeline || baseTransaction?.timeline;
    const isPending = tx.ApprovalStatus === TRANSACTION_STATUS.PENDING;
    const toggleSection = (section: string) => {
        setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
    };
    const totalFixedCosts = useMemo(() => (currentFixedCosts || []).reduce((acc, item) => acc + (item.total_pen || 0), 0), [currentFixedCosts]);
    const totalRecurringCosts = useMemo(() => (currentRecurringServices || []).reduce((acc, item) => acc + (item.egreso_pen || 0), 0), [currentRecurringServices]);
    const totalRecurringIncome = useMemo(() => (currentRecurringServices || []).reduce((acc, item) => acc + (item.ingreso_pen || 0), 0), [currentRecurringServices]);

    // Determine if we should show Transaction Overview and KPIs
    // Logic based on isNewTemplateMode flag instead of status
    const showOverviewAndKpis = useMemo(() => {
        // Finance view: always expanded
        if (isFinanceView) return true;

        // Sales view AND new template mode: collapsed until data loaded
        if (isNewTemplateMode) {
            const hasFileName = baseTransaction.fileName &&
                              baseTransaction.fileName !== UI_LABELS.NUEVA_PLANTILLA;
            const hasServices = (currentRecurringServices || []).length > 0;
            const hasFixedCosts = (currentFixedCosts || []).length > 0;

            // Show sections only if data has been loaded
            return hasFileName || hasServices || hasFixedCosts;
        }

        // Sales view with existing transaction: always expanded
        return true;
    }, [
        isFinanceView,
        isNewTemplateMode,
        baseTransaction.fileName,
        currentRecurringServices,
        currentFixedCosts
    ]);


    const CustomFixedCostTotalsNode = () => (
        <div>
            <p className="font-semibold text-red-600 text-right">{formatCurrency(totalFixedCosts)}</p>
            <p className="text-xs text-gray-500 text-right">{UI_LABELS.TOTAL}</p>
        </div>
    );

    const CustomRecurringServiceTotalsNode = () => (
        <div className="flex space-x-4">
            <div>
                <p className="font-semibold text-green-600 text-right">{formatCurrency(totalRecurringIncome)}</p>
                <p className="text-xs text-gray-500 text-right">{UI_LABELS.INGRESO}</p>
            </div>
            <div>
                <p className="font-semibold text-red-600 text-right">{formatCurrency(totalRecurringCosts)}</p>
                <p className="text-xs text-gray-500 text-right">{UI_LABELS.EGRESO}</p>
            </div>
        </div>
    );

    return (
        <>
            {/* Animated Container for Overview and KPIs */}
            <div
                className={`grid transition-all duration-700 ease-in-out ${showOverviewAndKpis
                    ? "grid-rows-[1fr] opacity-100 mb-6"
                    : "grid-rows-[0fr] opacity-0 mb-0"
                    }`}
            >
                <div className="overflow-hidden">

                    {!isFinanceView && isPending && (<div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-md mb-6 flex items-start"> <WarningIcon className="flex-shrink-0 mt-0.5" /> <div className="ml-3"> <p className="font-semibold text-yellow-800">{STATUS_MESSAGES.REVIEW_DATA_CAREFULLY}</p> <p className="text-sm text-yellow-700">{STATUS_MESSAGES.REVIEW_DATA_MESSAGE}</p> </div> </div>)}
                    {isFinanceView && tx.ApprovalStatus === TRANSACTION_STATUS.PENDING && (<div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-md mb-6 flex items-start"> <CheckCircleIcon className="flex-shrink-0 mt-0.5 text-blue-800" /> <div className="ml-3"> <p className="font-semibold text-blue-800">{STATUS_MESSAGES.FINANCE_EDIT_MODE}</p> <p className="text-sm text-blue-700">{STATUS_MESSAGES.FINANCE_EDIT_INFO}</p> </div> </div>)}
                    {isFinanceView && tx.ApprovalStatus === TRANSACTION_STATUS.APPROVED && (<div className="bg-green-50 border-l-4 border-green-400 p-4 rounded-md mb-6 flex items-start"> <CheckCircleIcon className="flex-shrink-0 mt-0.5 text-green-800" /> <div className="ml-3"> <p className="font-semibold text-green-800">{STATUS_MESSAGES.APPROVED_TITLE}</p> <p className="text-sm text-green-700">{STATUS_MESSAGES.APPROVED_MESSAGE}</p> </div> </div>)}
                    {isFinanceView && tx.ApprovalStatus === TRANSACTION_STATUS.REJECTED && (<div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-md mb-6 flex items-start"> <WarningIcon className="flex-shrink-0 mt-0.5 text-red-800" /> <div className="ml-3"> <p className="font-semibold text-red-800">{STATUS_MESSAGES.REJECTED_TITLE}</p> <p className="text-sm text-red-700">{STATUS_MESSAGES.REJECTED_MESSAGE}</p> </div> </div>)}
                    {!isFinanceView && (tx.ApprovalStatus === TRANSACTION_STATUS.REJECTED || tx.ApprovalStatus === TRANSACTION_STATUS.APPROVED) && (
                        <div className={`border-l-4 p-4 rounded-md mb-6 flex items-start ${tx.ApprovalStatus === TRANSACTION_STATUS.REJECTED
                            ? 'bg-red-50 border-red-400'
                            : 'bg-green-50 border-green-400'
                            }`}>
                            {tx.ApprovalStatus === TRANSACTION_STATUS.REJECTED ? (
                                <WarningIcon className="flex-shrink-0 mt-0.5 text-red-800" />
                            ) : (
                                <CheckCircleIcon className="flex-shrink-0 mt-0.5 text-green-800" />
                            )}
                            <div className="ml-3">
                                <p className={`font-semibold ${tx.ApprovalStatus === TRANSACTION_STATUS.REJECTED
                                    ? 'text-red-800'
                                    : 'text-green-800'
                                    }`}>
                                    {tx.ApprovalStatus === TRANSACTION_STATUS.REJECTED
                                        ? STATUS_MESSAGES.REJECTED_TITLE
                                        : STATUS_MESSAGES.APPROVED_TITLE}
                                </p>
                                <p className={`text-sm ${tx.ApprovalStatus === TRANSACTION_STATUS.REJECTED
                                    ? 'text-red-700'
                                    : 'text-green-700'
                                    }`}>
                                    {tx.ApprovalStatus === TRANSACTION_STATUS.REJECTED
                                        ? (tx.rejection_note || STATUS_MESSAGES.REJECTED_MESSAGE)
                                        : STATUS_MESSAGES.APPROVED_MESSAGE}
                                </p>
                            </div>
                        </div>
                    )}

                    <TransactionOverviewInputs
                        isFinanceView={isFinanceView}
                    />

                    <KpiMetricsGrid />
                </div>
            </div>

            <div className="mb-6">
                <h3 className="font-semibold text-gray-800 mb-3 text-lg">{UI_LABELS.DETALLE_SERVICIOS}</h3>
                <div className="space-y-3">
                    <CostBreakdownRow
                        title={UI_LABELS.SERVICIOS_RECURRENTES}
                        items={(currentRecurringServices || []).length}
                        total={null}
                        isOpen={openSections['recurringCosts']}
                        onToggle={() => toggleSection('recurringCosts')}
                        customTotalsNode={<CustomRecurringServiceTotalsNode />}
                    >
                        <RecurringServicesTable />
                    </CostBreakdownRow>

                    <CostBreakdownRow
                        title={UI_LABELS.INVERSION_COSTOS_FIJOS}
                        items={(currentFixedCosts || []).length}
                        total={totalFixedCosts}
                        isOpen={openSections['fixedCosts']}
                        onToggle={() => toggleSection('fixedCosts')}
                        customTotalsNode={CustomFixedCostTotalsNode()}
                    >
                        <FixedCostsTable />
                    </CostBreakdownRow>
                    <CostBreakdownRow
                        title={UI_LABELS.FLUJO_CAJA}
                        items={null}
                        total={null}
                        isOpen={openSections['cashFlow']}
                        onToggle={() => toggleSection('cashFlow')}
                        customTotalsNode={
                            <div className="text-xs text-gray-500 text-right">
                                {UI_LABELS.VALORES_POR_PERIODO}
                            </div>
                        }
                    >
                        <CashFlowTimelineTable timeline={timeline} />
                    </CostBreakdownRow>
                </div>
            </div>
        </>
    );
}