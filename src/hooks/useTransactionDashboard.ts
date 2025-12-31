// src/hooks/useTransactionDashboard.ts
import { useState, useEffect, useCallback } from 'react';
// --- (Imports remain the same) ---
import {
    getSalesTransactions,
    type FormattedSalesTransaction
} from '@/features/transactions/services/sales.service';
import {
    getFinanceTransactions,
    type FormattedFinanceTransaction
} from '@/features/transactions/services/finance.service';
import type { User } from '@/types';
// --- (RefObject is no longer needed) ---

// --- Type Definitions (remain the same) ---
type DashboardTransaction = FormattedSalesTransaction | FormattedFinanceTransaction;
type DashboardStats = { [key: string]: string | number };
type DashboardView = 'SALES' | 'FINANCE';

interface DashboardOptions {
    user: User;
    view: DashboardView;
    onLogout: () => void;
}

// --- 1. The return type is NOW MUCH SMALLER ---
interface DashboardReturn {
    // Data & Pagination
    transactions: DashboardTransaction[];
    stats: DashboardStats;
    isLoading: boolean;
    currentPage: number;
    totalPages: number;
    setCurrentPage: (page: number) => void; // <-- Simplified signature
    fetchTransactions: (pageToFetch: number) => Promise<void>;

    // API Error for the *list* page
    apiError: string | null;
    setApiError: React.Dispatch<React.SetStateAction<string | null>>;
}

// --- Hook Implementation ---

export function useTransactionDashboard({ view, onLogout }: DashboardOptions): DashboardReturn {
    // --- 2. State Initialization (UI State is GONE) ---
    const [transactions, setTransactions] = useState<DashboardTransaction[]>([]);
    const [apiError, setApiError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    // --- (State for filter, datePicker, etc. is REMOVED) ---

    // --- Core Logic: Fetching Transactions (remains the same) ---
    const fetchTransactions = useCallback(async (pageToFetch: number) => {
        setIsLoading(true);
        setApiError(null);

        let result;
        if (view === 'SALES') {
            result = await getSalesTransactions(pageToFetch);
        } else {
            result = await getFinanceTransactions(pageToFetch);
        }

        if (result.success) {
            setTransactions(result.data || []);
            setTotalPages(result.pages || 1);
            setCurrentPage(pageToFetch);
        } else {
            if (view === 'FINANCE' && (result as any).status === 401) {
                onLogout();
                return;
            }
            setApiError(result.error || 'Unknown error');
        }
        setIsLoading(false);
    }, [view, onLogout]);

    // Initial fetch
    useEffect(() => {
        fetchTransactions(1); // Fetch page 1 on mount
    }, [fetchTransactions]);

    // --- 4. Return Hook State and Handlers (Much smaller) ---
    return {
        transactions,
        stats: {} as DashboardStats,
        isLoading,
        currentPage,
        totalPages,
        // 5. setCurrentPage is now a simple function that triggers a fetch
        // Use useCallback to get latest currentPage value
        setCurrentPage: useCallback((newPage: number) => {
            fetchTransactions(newPage);
        }, [fetchTransactions]),
        fetchTransactions: useCallback(() => fetchTransactions(currentPage), [fetchTransactions, currentPage]),

        // --- (All filter and date state returns are REMOVED) ---

        apiError,
        setApiError,
    };
}