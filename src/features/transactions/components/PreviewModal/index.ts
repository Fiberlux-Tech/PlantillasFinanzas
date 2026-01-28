// src/features/transactions/components/PreviewModal/index.ts

// Only export what's needed by TransactionDashboard (keep Front Door clean)
export { default as DataPreviewModal } from './DataPreviewModal';
export { TransactionPreviewContent } from './TransactionPreviewContent';
export { ModalFooter, SalesPreviewFooter, FinancePreviewFooter } from './ModalFooter';
export { EditableKpiCard } from './EditableKpiCard';

// Internal components - no barrel export needed (import directly within PreviewModal/)
