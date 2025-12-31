// src/features/transactions/components/TransactionDashboardLayout.tsx
import React from 'react';
import { DashboardToolbar } from '@/features/transactions/components/DashboardToolBar';
import { UI_LABELS } from '@/config';

// Define the props for the layout
interface TransactionDashboardLayoutProps {
    apiError: string | null;
    statsGrid: React.ReactNode;
    transactionList: React.ReactNode;
    
    // All props needed by the DashboardToolbar
    filter: string;
    setFilter: React.Dispatch<React.SetStateAction<string>>;
    isDatePickerOpen: boolean;
    setIsDatePickerOpen: React.Dispatch<React.SetStateAction<boolean>>;
    selectedDate: Date | null;
    setSelectedDate: React.Dispatch<React.SetStateAction<Date | null>>;
    datePickerRef: React.RefObject<HTMLDivElement | null>;
    onClearDate: () => void;
    onSelectToday: () => void;
    placeholder: string;
}

export function TransactionDashboardLayout({
    apiError,
    statsGrid,
    transactionList,
    ...toolbarProps // Use rest operator to gather all toolbar props
}: TransactionDashboardLayoutProps) {
    return (
        <>
            <div className="container mx-auto px-8 py-8">
                {/* 1. Stats Grid Slot */}
                {statsGrid}

                <div className="bg-white p-6 rounded-lg shadow-sm mt-8">
                    {/* 2. Shared Toolbar */}
                    <DashboardToolbar {...toolbarProps} />
                    
                    {/* 3. Transaction List Slot */}
                    {transactionList}
                </div>
            </div>

            {/* 4. Shared API Error Display */}
            {apiError && (
                <div className="fixed top-5 right-5 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded shadow-lg z-50" role="alert">
                    <strong className="font-bold">{UI_LABELS.ERROR_LABEL}</strong>
                    <span className="block sm:inline">{apiError}</span>
                </div>
            )}
        </>
    );
}