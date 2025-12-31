// src/features/transactions/services/finance.service.ts
import { api } from '@/lib/api';
import type {
    TransactionDetailResponse,
    BaseApiResponse,
    Transaction,
    FixedCost,
    RecurringService,
    FinanceTransactionListResponse
} from '@/types';
import { API_CONFIG, PAGINATION, ERROR_MESSAGES, type TransactionStatus } from '@/config';

// --- Types ---

export interface FormattedFinanceTransaction {
    id: number;
    unidadNegocio: string;
    clientName: string;
    salesman: string;
    MRC_pen: number;
    plazoContrato: number;
    grossMarginRatio: number;
    payback: number;
    submissionDate: string;
    status: TransactionStatus;
}

interface GetFinanceTransactionsResult {
    success: boolean;
    data?: FormattedFinanceTransaction[];
    pages?: number;
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

type CalculateCommissionResult = {
    success: true;
    data: TransactionDetailResponse['data'];
} | {
    success: false;
    error: string;
    data?: undefined;
}

// --- Functions ---

export async function getFinanceTransactions(page: number): Promise<GetFinanceTransactionsResult> {
    try {
        const result = await api.get<FinanceTransactionListResponse>(`${API_CONFIG.ENDPOINTS.TRANSACTIONS_LIST}?page=${page}&per_page=${PAGINATION.PER_PAGE}`); 
 
        if (result.success) {
            const formattedTransactions: FormattedFinanceTransaction[] = result.data.transactions.map((tx: Transaction) => ({
                id: tx.id,
                unidadNegocio: tx.unidadNegocio,
                clientName: tx.clientName,
                salesman: tx.salesman,
                MRC_pen: tx.MRC_pen,
                plazoContrato: tx.plazoContrato,
                grossMarginRatio: tx.grossMarginRatio,
                payback: tx.payback,
                submissionDate: new Date(tx.submissionDate).toISOString().split('T')[0],
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

export async function getTransactionDetails(transactionId: number): Promise<GetTransactionDetailsResult> {
    try {
        const result = await api.get<TransactionDetailResponse>(`${API_CONFIG.ENDPOINTS.TRANSACTION_DETAIL}/${transactionId}`);
        if (result.success) {
            return { success: true, data: result.data };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_FETCH_TRANSACTION_DETAILS };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER };
    }
}

export async function updateTransactionStatus(
    transactionId: number,
    action: 'approve' | 'reject',
    modifiedData: Partial<Transaction> = {},
    fixedCosts: FixedCost[] | null = null,
    recurringServices: RecurringService[] | null = null
): Promise<BaseApiResponse> {

    const endpoint = action === 'approve' ? API_CONFIG.ENDPOINTS.APPROVE_TRANSACTION : API_CONFIG.ENDPOINTS.REJECT_TRANSACTION;

    const payload: {
        transactions?: Partial<Transaction>;
        fixed_costs?: FixedCost[] | null;
        recurring_services?: RecurringService[] | null;
        rejection_note?: string;
    } = {};

    // For both approve and reject, send full data (backend saves edits before status change)
    payload.transactions = modifiedData;
    if (fixedCosts) {
        payload.fixed_costs = fixedCosts;
    }
    if (recurringServices) {
        payload.recurring_services = recurringServices;
    }

    // For reject, ensure rejection_note is included
    if (action === 'reject' && modifiedData.rejection_note) {
        payload.rejection_note = modifiedData.rejection_note;
    }

    try {
        const result = await api.post<BaseApiResponse>(`${API_CONFIG.ENDPOINTS.TRANSACTION_DETAIL}/${endpoint}/${transactionId}`, payload);

        if (result.success) {
            return { success: true };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_ACTION_TRANSACTION.replace('{action}', action) };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER };
    }
}

export async function calculateCommission(transactionId: number): Promise<CalculateCommissionResult> {
    try {
        const result = await api.post<TransactionDetailResponse>(
            `${API_CONFIG.ENDPOINTS.TRANSACTION_DETAIL}/${transactionId}/calculate-commission`,
            {}
        );
        
        if (result.success) {
            return { success: true, data: result.data };
        } else {
            return { success: false, error: result.error || ERROR_MESSAGES.FAILED_CALCULATE_COMMISSION };
        }
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_CONNECT_SERVER_COMMISSION };
    }
}

