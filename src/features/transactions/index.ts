// src/features/transactions/index.ts

// Main component - THE ONLY UI EXPORT
export { default as TransactionDashboard } from './TransactionDashboard';

// Services (public API)
export * from './services/sales.service';
export * from './services/finance.service';
export * from './services/kpi.service';  // Uses single GET /api/kpi/summary endpoint
export * from './services/shared.service';

// Hook & Context
export { useTransactionDashboard } from './hooks/useTransactionDashboard';
export { TransactionPreviewProvider, useTransactionPreview } from './contexts/TransactionPreviewContext';

// DO NOT EXPORT internal components (FixedCostsTable, KpiMetricsGrid, etc.)
// Keep the feature's "Front Door" clean
