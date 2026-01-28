// src/features/transactions/TransactionDashboard.tsx
import { useState, useMemo, useEffect, useRef, RefObject } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { UploadIcon } from '@/components/shared/Icons';
import { useDebounce } from '@/hooks/useDebounce';

// --- Shared Imports ---
import { DataPreviewModal, TransactionPreviewContent, SalesPreviewFooter, FinancePreviewFooter } from './components/PreviewModal';
import { TransactionPreviewProvider } from './contexts/TransactionPreviewContext';
import { useTransactionsQuery } from './hooks/useTransactionsQuery';
import { useKpisQuery } from './hooks/useKpisQuery';
import { useAuth } from '@/contexts/AuthContext';
import type { Transaction, TransactionDetailResponse, FixedCost, RecurringService } from '@/types';
import { TransactionDashboardLayout, SalesStatsGrid, FinanceStatsGrid } from './components/Dashboard';
import { UI_LABELS, ERROR_MESSAGES, BUTTON_LABELS, TRANSACTION_STATUS } from '@/config';

// --- Sales-Specific Imports ---
import { SalesTransactionList, FinanceTransactionList } from './components/Table';
import {
    uploadExcelForPreview,
    submitFinalTransaction,
    updateTransaction,
    getSalesTransactionDetails,
    fetchTransactionTemplate,
    type FormattedSalesTransaction
} from './services/sales.service';

// --- Finance-Specific Imports ---
import {
    getTransactionDetails,
    updateTransactionStatus,
    calculateCommission,
    type FormattedFinanceTransaction as FormattedFinanceTx
} from './services/finance.service';

// --- Define Component Props ---
type View = 'SALES' | 'FINANCE';

// --- Define Component Props (UPDATED SalesActions Interface) ---
interface SalesActions {
    uploadLabel: string; // <-- Only two properties
    onUpload: () => void;
}

interface TransactionDashboardProps {
    setSalesActions?: (actions: SalesActions) => void;
}

// --- The Consolidated Component ---
export default function TransactionDashboard({ setSalesActions }: TransactionDashboardProps) {

    const { user, logout } = useAuth();

    // Derive view from user role - SALES users see SALES view, all others see FINANCE view
    const view: View = user?.role === 'SALES' ? 'SALES' : 'FINANCE';

    if (!user) {
        return <div className="text-center py-12">{UI_LABELS.LOADING_USER_DATA}</div>;
    }

    // --- TanStack Query Client for cache invalidation ---
    const queryClient = useQueryClient();

    // --- 2. COMMON UI STATE ---
    const [filter, setFilter] = useState<string>('');
    const debouncedFilter = useDebounce(filter, 300);
    const [isDatePickerOpen, setIsDatePickerOpen] = useState<boolean>(false);
    const [selectedDate, setSelectedDate] = useState<Date | null>(null);
    const datePickerRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [apiError, setApiError] = useState<string | null>(null);

    // --- 1. CORE DATA HOOKS (TanStack Query) ---
    const {
        data: txData,
        isLoading,
        isError: isTxError,
        error: txError
    } = useTransactionsQuery(
        view,
        currentPage,
        debouncedFilter || undefined,
        selectedDate ? selectedDate.toISOString().split('T')[0] : undefined
    );

    const { data: kpiData, isError: isKpiError, error: kpiError } = useKpisQuery();

    // Extract data from query results (now directly typed, no .success check needed)
    const transactions = txData?.transactions || [];
    const totalPages = txData?.pages || 1;

    // Sync TanStack Query errors to local apiError state for UI display
    useEffect(() => {
        if (isTxError && txError) {
            setApiError(txError.message);
        } else if (isKpiError && kpiError) {
            setApiError(kpiError.message);
        } else {
            setApiError(null);
        }
    }, [isTxError, txError, isKpiError, kpiError]);

    // Reset to page 1 when filters change
    useEffect(() => {
        setCurrentPage(1);
    }, [debouncedFilter, selectedDate]);

    // --- 3. VIEW-SPECIFIC MODAL STATE ---
    // Sales Modal State
    const [isPreviewModalOpen, setIsPreviewModalOpen] = useState<boolean>(false);
    const [uploadedData, setUploadedData] = useState<TransactionDetailResponse['data'] | null>(null);
    const [isLoadingTemplate, setIsLoadingTemplate] = useState<boolean>(false);

    // Sales View-Only Modal State (for viewing existing transactions)
    const [selectedSalesTransaction, setSelectedSalesTransaction] = useState<TransactionDetailResponse['data'] | null>(null);
    const [isSalesViewModalOpen, setIsSalesViewModalOpen] = useState<boolean>(false);

    // Finance Modal State
    const [selectedTransaction, setSelectedTransaction] = useState<TransactionDetailResponse['data'] | null>(null);
    const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);

    // --- Helper: Invalidate queries to trigger refetch ---
    const invalidateQueries = () => {
        queryClient.invalidateQueries({ queryKey: ['transactions'] });
        queryClient.invalidateQueries({ queryKey: ['kpis'] });
    };

    // --- 5. COMMON HANDLERS (for filters) ---
    const handleClearDate = () => { setSelectedDate(null); setIsDatePickerOpen(false); };
    const handleSelectToday = () => { setSelectedDate(new Date()); setIsDatePickerOpen(false); };

    // --- 6. VIEW-SPECIFIC HANDLERS ---

    // Sales Handlers
    useEffect(() => {
        if (view === 'SALES' && setSalesActions) {
            setSalesActions({
                uploadLabel: UI_LABELS.CREATE_TEMPLATE,
                onUpload: async () => {
                    setUploadedData(null); // Clear any previous data
                    setIsLoadingTemplate(true);

                    const result = await fetchTransactionTemplate();

                    if (result.success) {
                        setUploadedData(result.data);
                        setIsPreviewModalOpen(true);
                    } else {
                        // NO FALLBACK - Show error and block template creation
                        const errorMessage = result.error || 'Unknown error occurred';

                        if (errorMessage.includes('System rates') || errorMessage.includes('missing')) {
                            alert('❌ Cannot create template\n\nMaster variables (Exchange Rate, Capital Cost, or Bond Rate) are missing from the system.\n\nPlease contact Finance or your administrator to configure these rates before creating proposals.');
                        } else if (errorMessage.includes('Unauthorized') || errorMessage.includes('401')) {
                            alert('⚠️ Session expired\n\nPlease log in again.');
                            // Optionally trigger logout here
                        } else {
                            alert(`❌ Failed to load template\n\n${errorMessage}\n\nYou cannot create new proposals until the system is available.\n\nPlease try again or contact IT support.`);
                        }
                    }

                    setIsLoadingTemplate(false);
                },
            });
            // Cleanup function
            return () => {
                setSalesActions({
                    uploadLabel: UI_LABELS.CREATE_TEMPLATE, // Revert default
                    onUpload: () => console.log(UI_LABELS.UPLOAD_NOT_AVAILABLE),
                    // onExport is gone
                });
            };
        }
    }, [view, setSalesActions]);

    const handleFileSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
        if (!event.target.files || !event.target.files[0]) {
            return; // No file selected
        }
        const file = event.target.files[0];

        setApiError(null);
        const result = await uploadExcelForPreview(file);

        if (result.success && result.data) {
            setUploadedData(result.data); // Set the new data
        } else {
            alert(result.error || ERROR_MESSAGES.UNKNOWN_UPLOAD_ERROR);
        }

        // Reset the input value so the user can upload the same file again
        if (event.target) {
            event.target.value = "";
        }
    };

    const handleConfirmSubmission = async (finalData: TransactionDetailResponse['data']) => {
        setApiError(null);
        
        // Ensure the status is PENDING before submission
        const { timeline: _timeline, ...dataWithoutTimeline } = finalData;
        const finalPayload = {
            ...dataWithoutTimeline,
            transactions: {
                ...finalData.transactions,
                ApprovalStatus: TRANSACTION_STATUS.PENDING // <-- Set status to PENDING
            }
        };

        const result = await submitFinalTransaction(finalPayload);
        if (result.success) {
            setCurrentPage(1);
            invalidateQueries();
            setIsPreviewModalOpen(false);
            setUploadedData(null);
        } else {
            alert(result.error || ERROR_MESSAGES.UNKNOWN_SUBMISSION_ERROR);
        }
    };

    const handleCloseSalesModal = () => {
        setIsPreviewModalOpen(false);
        setUploadedData(null);
    };

    const handleSalesRowClick = async (transaction: FormattedSalesTransaction) => {
        setApiError(null);
        setSelectedSalesTransaction(null);
        const result = await getSalesTransactionDetails(transaction.id);
        if (result.success) {
            setSelectedSalesTransaction(result.data);
            setIsSalesViewModalOpen(true);
        } else {
            setApiError(result.error || ERROR_MESSAGES.UNKNOWN_ERROR);
        }
    };

    const handleCloseSalesViewModal = () => {
        setIsSalesViewModalOpen(false);
        setSelectedSalesTransaction(null);
    };

    // Finance Handlers
    const handleRowClick = async (transaction: FormattedFinanceTx) => {
        setApiError(null);
        setSelectedTransaction(null);
        const result = await getTransactionDetails(transaction.id);
        if (result.success) {
            setSelectedTransaction(result.data);
            setIsDetailModalOpen(true);
        } else {
            setApiError(result.error || ERROR_MESSAGES.UNKNOWN_ERROR);
        }
    };

    const handleUpdateStatus = async (
        transactionId: number,
        status: 'approve' | 'reject',
        modifiedData: Partial<Transaction>,
        fixedCosts: FixedCost[] | null,
        recurringServices: RecurringService[] | null
    ) => {
        setApiError(null);
        const result = await updateTransactionStatus(transactionId, status, modifiedData, fixedCosts, recurringServices);
        if (result.success) {
            setIsDetailModalOpen(false);
            setSelectedTransaction(null);
            invalidateQueries();
        } else {
            alert(`${UI_LABELS.ERROR_PREFIX}${result.error}`);
        }
    };

    const handleCalculateCommission = async (transactionId: number) => {
        setApiError(null);
        const result = await calculateCommission(transactionId);
        if (result.success) {
            setSelectedTransaction(result.data);
            invalidateQueries();
        } else {
            alert(`${UI_LABELS.ERROR_PREFIX}${result.error}`);
        }
    };

    const handleSaveTransaction = async (
        transactionId: number,
        modifiedData: Partial<Transaction>,
        fixedCosts: FixedCost[] | null,
        recurringServices: RecurringService[] | null
    ) => {
        setApiError(null);
        const payload = {
            fixed_costs: fixedCosts ?? undefined,
            recurring_services: recurringServices ?? undefined,
            transactions: modifiedData
        };
        const result = await updateTransaction(transactionId, payload);
        if (result.success) {
            alert('Cambios guardados exitosamente');
            setIsDetailModalOpen(false);
            setSelectedTransaction(null);
            invalidateQueries();
        } else {
            alert(`${UI_LABELS.ERROR_PREFIX}${result.error}`);
        }
    };

    // Wrapper for Sales view to match SalesPreviewFooter signature
    const handleSalesUpdate = async (finalData: TransactionDetailResponse['data']) => {
        const transactionId = finalData.transactions.id;
        await handleSaveTransaction(
            transactionId,
            finalData.transactions,
            finalData.fixed_costs,
            finalData.recurring_services
        );
        handleCloseSalesViewModal();
    };

    const handleCloseFinanceModal = () => {
        setIsDetailModalOpen(false);
        setSelectedTransaction(null);
    };

    // --- 7. COMMON & CONDITIONAL MEMOIZED LOGIC ---

    // Sales Stats - Using KPI data from API
    const salesStats = useMemo(() => {
        if (!kpiData) {
            // Return default values while loading
            return {
                pendingApprovals: 0,
                pendingMrc: 0,
                pendingComisiones: 0,
                avgGrossMargin: 0,
            };
        }

        return {
            pendingApprovals: kpiData.pendingCount,
            pendingMrc: kpiData.pendingMrc,
            pendingComisiones: kpiData.pendingComisiones,
            avgGrossMargin: kpiData.averageGrossMargin,
        };
    }, [kpiData]);

    // Finance Stats - Using KPI data from API
    const financeStats = useMemo(() => {
        if (!kpiData) {
            // Return default values while loading
            return {
                pendingMrc: 0,
                pendingCount: 0,
                pendingComisiones: 0,
                avgGrossMargin: 0,
            };
        }

        return {
            pendingMrc: kpiData.pendingMrc,
            pendingCount: kpiData.pendingCount,
            pendingComisiones: kpiData.pendingComisiones,
            avgGrossMargin: kpiData.averageGrossMargin,
        };
    }, [kpiData]);

    // --- 8. CONDITIONAL RENDER ---
    return (
        <>
            <TransactionDashboardLayout
                apiError={apiError}
                placeholder={
                    view === 'SALES'
                        ? UI_LABELS.FILTRA_POR_CLIENTE
                        : UI_LABELS.FILTER_BY_CLIENT
                }
                statsGrid={
                    view === 'SALES'
                        ? <SalesStatsGrid stats={salesStats} />
                        : <FinanceStatsGrid stats={financeStats} />
                }
                transactionList={
                    view === 'SALES' ? (
                        <SalesTransactionList
                            isLoading={isLoading}
                            transactions={transactions as FormattedSalesTransaction[]}
                            currentPage={currentPage}
                            totalPages={totalPages}
                            onPageChange={setCurrentPage}
                            onRowClick={handleSalesRowClick}
                        />
                    ) : (
                        <FinanceTransactionList
                            isLoading={isLoading}
                            transactions={transactions as FormattedFinanceTx[]}
                            onRowClick={handleRowClick}
                            currentPage={currentPage}
                            totalPages={totalPages}
                            onPageChange={setCurrentPage}
                        />
                    )
                }
                // Pass all common filter props
                filter={filter}
                setFilter={setFilter}
                isDatePickerOpen={isDatePickerOpen}
                setIsDatePickerOpen={setIsDatePickerOpen}
                selectedDate={selectedDate}
                setSelectedDate={setSelectedDate}
                datePickerRef={datePickerRef as RefObject<HTMLDivElement | null>}
                onClearDate={handleClearDate}
                onSelectToday={handleSelectToday}
            />

            {/* --- Conditional Sales Modals --- */}
            {view === 'SALES' && (
                <>
                    {/* --- 1. ADD THE HIDDEN FILE INPUT --- */}
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelected}
                        className="hidden"
                        accept=".xlsx, .xls"
                    />
                    {/* --- 2. REMOVED the <FileUploadModal> --- */}

                    {/* The Preview Modal only opens when uploadedData is available */}
                    {isPreviewModalOpen && uploadedData && (
                        <TransactionPreviewProvider
                            baseTransaction={uploadedData}
                            view="SALES"
                            isNewTemplateMode={!uploadedData.transactions.id}
                        >
                            <DataPreviewModal
                                isOpen={isPreviewModalOpen}
                                // Title is dynamic
                                title={uploadedData.fileName ? UI_LABELS.PREVIEW_LABEL.replace('{fileName}', uploadedData.fileName) : UI_LABELS.NUEVA_PLANTILLA}
                                onClose={handleCloseSalesModal}
                                // Status from uploaded data
                                status={uploadedData.transactions.ApprovalStatus}
                                // --- 3. UPDATE THE BUTTON'S onClick ---
                                headerActions={
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50"
                                    >
                                        <UploadIcon className="w-4 h-4" />
                                        <span>{UI_LABELS.CARGAR_EXCEL}</span>
                                    </button>
                                }
                                footer={
                                    <SalesPreviewFooter
                                        onConfirm={handleConfirmSubmission}
                                        onClose={handleCloseSalesModal}
                                    />
                                }
                            >
                                <TransactionPreviewContent isFinanceView={false} />
                            </DataPreviewModal>
                        </TransactionPreviewProvider>
                    )}

                    {/* Modal for existing transactions - Editable if PENDING */}
                    {isSalesViewModalOpen && selectedSalesTransaction && (
                        <TransactionPreviewProvider
                            baseTransaction={selectedSalesTransaction}
                            view="SALES"
                            isNewTemplateMode={false}
                        >
                            <DataPreviewModal
                                isOpen={isSalesViewModalOpen}
                                title={UI_LABELS.TRANSACTION_ID_LABEL.replace('{id}', String(selectedSalesTransaction.transactions.transactionID || selectedSalesTransaction.transactions.id))}
                                onClose={handleCloseSalesViewModal}
                                status={selectedSalesTransaction.transactions.ApprovalStatus}
                                footer={
                                    selectedSalesTransaction.transactions.ApprovalStatus === TRANSACTION_STATUS.PENDING ? (
                                        <SalesPreviewFooter
                                            onConfirm={handleSalesUpdate}
                                            onClose={handleCloseSalesViewModal}
                                        />
                                    ) : (
                                        <div className="w-full flex justify-end items-center p-5 border-t bg-white">
                                            <button
                                                onClick={handleCloseSalesViewModal}
                                                className="px-5 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                                            >
                                                {BUTTON_LABELS.CANCELAR}
                                            </button>
                                        </div>
                                    )
                                }
                            >
                                <TransactionPreviewContent isFinanceView={false} />
                            </DataPreviewModal>
                        </TransactionPreviewProvider>
                    )}
                </>
            )}

            {/* --- Conditional Finance Modal --- */}
            {view === 'FINANCE' && selectedTransaction && (
                <TransactionPreviewProvider
                    baseTransaction={selectedTransaction}
                    view="FINANCE"
                    isNewTemplateMode={false}
                >
                    <DataPreviewModal
                        isOpen={isDetailModalOpen}
                        title={UI_LABELS.TRANSACTION_ID_LABEL.replace('{id}', String(selectedTransaction.transactions.transactionID || selectedTransaction.transactions.id))}
                        onClose={handleCloseFinanceModal}
                        // Pass status for the new modal header structure (Point 2)
                        status={selectedTransaction.transactions.ApprovalStatus}
                        footer={
                            <FinancePreviewFooter
                                onApprove={handleUpdateStatus}
                                onReject={handleUpdateStatus}
                                onCalculateCommission={handleCalculateCommission}
                                onSave={handleSaveTransaction}
                            />
                        }
                    >
                        <TransactionPreviewContent isFinanceView={true} />
                    </DataPreviewModal>
                </TransactionPreviewProvider>
            )}

            {/* Loading Modal for Template Fetch */}
            {isLoadingTemplate && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 shadow-xl">
                        <p className="text-gray-900 text-lg">Loading template...</p>
                    </div>
                </div>
            )}
        </>
    );
}
