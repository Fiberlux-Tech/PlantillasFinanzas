// src/features/transactions/services/sales.service.ts
import { api } from '@/lib/api';
import type {
    SalesTransactionListResponse,
    TransactionDetailResponse,
    BaseApiResponse,
    Transaction,
} from '@/types';
import { API_CONFIG, PAGINATION, DISPLAY_VALUES, ERROR_MESSAGES, type TransactionStatus } from '@/config';

// --- Types ---

export interface FormattedSalesTransaction {
    id: number;
    client: string;
    MRC_pen: number;
    grossMarginRatio: number;
    payback: number;
    comisiones: number;
    submissionDate: string;
    approvalDate: string;
    status: TransactionStatus;
}

interface GetSalesTransactionsResult {
    success: boolean;
    data?: FormattedSalesTransaction[];
    pages?: number;
    error?: string;
}

interface UploadExcelResult {
    success: boolean;
    data?: TransactionDetailResponse['data']; // Reuse the data shape
    error?: string;
}

type GetTransactionDetailsResult = {
    success: true;
    data: TransactionDetailResponse['data'];
} | {
    success: false;
    error: string;
    data?: undefined;
}

// --- Functions ---

export async function getSalesTransactions(page: number): Promise<GetSalesTransactionsResult> {
    try {
        const result = await api.get<SalesTransactionListResponse>(`${API_CONFIG.ENDPOINTS.TRANSACTIONS_LIST}?page=${page}&per_page=${PAGINATION.PER_PAGE}`);

        if (result.success) {
            const formattedTransactions: FormattedSalesTransaction[] = result.data.transactions.map((tx: Transaction) => ({
                id: tx.id,
                client: tx.clientName,
                MRC_pen: tx.MRC_pen,
                grossMarginRatio: tx.grossMarginRatio,
                payback: tx.payback,
                comisiones: tx.comisiones,
                submissionDate: new Date(tx.submissionDate).toISOString().split('T')[0],
                approvalDate: tx.approvalDate ? new Date(tx.approvalDate).toISOString().split('T')[0] : DISPLAY_VALUES.NOT_AVAILABLE,
                status: tx.ApprovalStatus,
            }));
            return {
                success: true,
                data: formattedTransactions,
                pages: result.data.pages
            };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_FETCH_TRANSACTIONS };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER };
    }
}

export async function uploadExcelForPreview(file: File): Promise<UploadExcelResult> {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const result = await api.postForm<TransactionDetailResponse>(API_CONFIG.ENDPOINTS.PROCESS_EXCEL, formData);

        if (result.success) {
            const dataWithFilename = { ...result.data, fileName: file.name };
            return { success: true, data: dataWithFilename };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_PROCESS_EXCEL };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER_UPLOAD };
    }
}

export async function submitFinalTransaction(finalPayload: any): Promise<BaseApiResponse> {
    try {
        const result = await api.post<BaseApiResponse>(API_CONFIG.ENDPOINTS.SUBMIT_TRANSACTION, finalPayload);

        if (result.success) {
            return { success: true };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_SUBMIT_TRANSACTION };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER_SUBMISSION };
    }
}

export async function updateTransaction(transactionId: number, updatePayload: any): Promise<BaseApiResponse> {
    try {
        const result = await api.put<BaseApiResponse>(`${API_CONFIG.ENDPOINTS.TRANSACTION_DETAIL}/${transactionId}`, updatePayload);

        if (result.success) {
            return { success: true };
        } else {
            return { success: false, error: result.error || 'Failed to update transaction' };
        }
    } catch (error: any) {
        return { success: false, error: error.message || 'Failed to connect to server' };
    }
}

export async function getSalesTransactionDetails(transactionId: number): Promise<GetTransactionDetailsResult> {
    try {
        const result = await api.get<TransactionDetailResponse>(`${API_CONFIG.ENDPOINTS.TRANSACTION_DETAIL}/${transactionId}`);
        if (result.success) {
            // Inject the numeric ID we used for the request since backend doesn't return it
            return {
                success: true,
                data: {
                    ...result.data,
                    transactions: {
                        ...result.data.transactions,
                        id: transactionId
                    }
                }
            };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_FETCH_TRANSACTION_DETAILS };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER };
    }
}

type FetchTransactionTemplateResult = {
    success: true;
    data: TransactionDetailResponse['data'];
} | {
    success: false;
    error: string;
}

export async function fetchTransactionTemplate(): Promise<FetchTransactionTemplateResult> {
    try {
        const result = await api.get<TransactionDetailResponse>(
            API_CONFIG.ENDPOINTS.TRANSACTION_TEMPLATE
        );
        if (result.success) {
            return { success: true, data: result.data };
        } else {
            return {
                success: false,
                error: result.error || ERROR_MESSAGES.FAILED_FETCH_TRANSACTION_DETAILS
            };
        }
    } catch (error: any) {
        return {
            success: false,
            error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER
        };
    }
}