// src/features/transactions/hooks/useTransactionsQuery.ts
import { useQuery } from '@tanstack/react-query';
import { getSalesTransactions, type FormattedSalesTransaction } from '../services/sales.service';
import { getFinanceTransactions, type FormattedFinanceTransaction } from '../services/finance.service';

type View = 'SALES' | 'FINANCE';

export interface TransactionsData {
    transactions: FormattedSalesTransaction[] | FormattedFinanceTransaction[];
    pages: number;
}

export function useTransactionsQuery(
    view: View,
    page: number,
    search?: string,
    startDate?: string
) {
    const fetchFn = view === 'SALES' ? getSalesTransactions : getFinanceTransactions;

    return useQuery<TransactionsData, Error>({
        queryKey: ['transactions', view, page, search, startDate],
        queryFn: async () => {
            const result = await fetchFn(page, search, startDate);
            if (!result.success) {
                throw new Error(result.error || 'Failed to fetch transactions');
            }
            return {
                transactions: result.data || [],
                pages: result.pages || 1,
            };
        },
        placeholderData: (previousData) => previousData,
    });
}
