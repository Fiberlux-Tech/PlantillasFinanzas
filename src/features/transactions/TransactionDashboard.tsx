// src/features/transactions/TransactionDashboard.tsx
import { useState, useMemo, useEffect, useRef, RefObject, useCallback } from 'react';
import { UploadIcon } from '@/components/shared/Icons';
import { useDebounce } from '@/hooks/useDebounce';

// --- Shared Imports ---
import DataPreviewModal from '@/features/transactions/components/DataPreviewModal';
import { TransactionPreviewProvider } from '@/contexts/TransactionPreviewContext';
import { useTransactionDashboard } from '@/hooks/useTransactionDashboard';
import { useAuth } from '@/contexts/AuthContext';
import type { Transaction, TransactionDetailResponse, FixedCost, RecurringService } from '@/types';
import { TransactionDashboardLayout } from './components/TransactionDashboardLayout';
import { TransactionPreviewContent } from './components/TransactionPreviewContent';
import { UI_LABELS, ERROR_MESSAGES, BUTTON_LABELS, TRANSACTION_STATUS } from '@/config';
import { getAllKpis, type KpiData } from './services/kpi.service';

// --- Sales-Specific Imports ---
import { SalesStatsGrid } from './components/SalesStatsGrid';
import { SalesTransactionList } from './components/SalesTransactionList';
import { SalesPreviewFooter } from './footers/SalesPreviewFooter';
import {
    uploadExcelForPreview,
    submitFinalTransaction,
    updateTransaction,
    getSalesTransactionDetails,
    fetchTransactionTemplate,
    type FormattedSalesTransaction
} from './services/sales.service';

// --- Finance-Specific Imports ---
import { FinanceStatsGrid } from './components/FinanceStatsGrid';
import { TransactionList as FinanceTransactionList } from './components/FinanceTransactionList';
import { FinancePreviewFooter } from './footers/FinancePreviewFooter';
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
    view: View;
    setSalesActions?: (actions: SalesActions) => void;
}

// --- The Consolidated Component ---
export default function TransactionDashboard({ view, setSalesActions }: TransactionDashboardProps) {

    const { user, logout } = useAuth();

    if (!user) {
        return <div className="text-center py-12">{UI_LABELS.LOADING_USER_DATA}</div>;
    }

    // --- 1. CORE DATA HOOK ---
    // This hook fetches the correct data based on the 'view' prop
    const {
        transactions, isLoading, currentPage, totalPages, setCurrentPage,
        apiError, setApiError,
        fetchTransactions,
    } = useTransactionDashboard({
        user,
        view,
        onLogout: logout
    });

    // --- 2. COMMON UI STATE ---
    // All filter/date state is now in one place
    const [filter, setFilter] = useState<string>('');
    const debouncedFilter = useDebounce(filter, 250); // Debounce with 250ms delay
    const [isDatePickerOpen, setIsDatePickerOpen] = useState<boolean>(false);
    const [selectedDate, setSelectedDate] = useState<Date | null>(null);
    const datePickerRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null); // <-- ADD THIS LINE

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

    // --- KPI STATE (MODIFIED) ---
    const [kpiData, setKpiData] = useState<KpiData | null>(null);
    const [isLoadingKpis, setIsLoadingKpis] = useState<boolean>(true);
    const [kpiRefreshToggle, setKpiRefreshToggle] = useState(false); // <-- NEW: State to force refresh

    // --- 4. FETCH KPIs LOGIC (MODIFIED) ---
    const fetchKpis = useCallback(async () => {
        setIsLoadingKpis(true);
        const result = await getAllKpis();
        if (result.success && result.data) {
            setKpiData(result.data);
        }
        setIsLoadingKpis(false);
    }, []); // <-- Dependency array is empty to keep fetchKpis stable

    // Run on mount AND when toggle state changes
    useEffect(() => {
        fetchKpis();
    }, [fetchKpis, kpiRefreshToggle]); // <-- Dependency now includes the toggle

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
        const finalPayload = { 
            ...finalData, 
            transactions: { 
                ...finalData.transactions,
                ApprovalStatus: TRANSACTION_STATUS.PENDING // <-- Set status to PENDING
            } 
        };
        delete (finalPayload as any).timeline;

        const result = await submitFinalTransaction(finalPayload);
        if (result.success) {
            fetchTransactions(1);
            setKpiRefreshToggle(prev => !prev); // <-- ADDED: Trigger KPI refresh
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
            fetchTransactions(currentPage);
            setKpiRefreshToggle(prev => !prev); // <-- ADDED: Trigger KPI refresh
        } else {
            alert(`${UI_LABELS.ERROR_PREFIX}${result.error}`);
        }
    };

    const handleCalculateCommission = async (transactionId: number) => {
        setApiError(null);
        const result = await calculateCommission(transactionId);
        if (result.success) {
            setSelectedTransaction(result.data); // Re-set data to show commission changes
            fetchTransactions(currentPage); // Re-fetch list to update status/values
            setKpiRefreshToggle(prev => !prev); // <-- ADDED: Trigger KPI refresh
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
            fixed_costs: fixedCosts,
            recurring_services: recurringServices,
            transactions: modifiedData
        };
        const result = await updateTransaction(transactionId, payload);
        if (result.success) {
            alert('Cambios guardados exitosamente');
            setIsDetailModalOpen(false);
            setSelectedTransaction(null);
            fetchTransactions(currentPage);
            setKpiRefreshToggle(prev => !prev);
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

    // Generalized Filter Logic - Now uses debouncedFilter instead of filter
    const filteredTransactions = useMemo(() => {
        // Pre-compute selectedDate string if needed (outside the loop)
        const selectedDateString = selectedDate?.toDateString();

        return transactions.filter(t => {
            const filterLower = debouncedFilter.toLowerCase();

            // Handle different property names for client
            let clientMatch = false;
            if (view === 'SALES') {
                clientMatch = (t as FormattedSalesTransaction).client.toLowerCase().includes(filterLower);
            } else {
                clientMatch = (t as FormattedFinanceTx).clientName.toLowerCase().includes(filterLower);
            }

            // Common date logic - only create Date object if we need to compare
            if (!selectedDateString) return clientMatch;

            // Create date without unnecessary string concatenation
            const transactionDate = new Date(t.submissionDate);
            return clientMatch && transactionDate.toDateString() === selectedDateString;
        });
    }, [transactions, debouncedFilter, selectedDate, view]); // Now depends on debouncedFilter


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
                            transactions={filteredTransactions as FormattedSalesTransaction[]}
                            currentPage={currentPage}
                            totalPages={totalPages}
                            onPageChange={setCurrentPage}
                            onRowClick={handleSalesRowClick}
                        />
                    ) : (
                        <FinanceTransactionList
                            isLoading={isLoading}
                            transactions={filteredTransactions as FormattedFinanceTx[]}
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
                                        transaction={uploadedData}
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
                                            transaction={selectedSalesTransaction}
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
