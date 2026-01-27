// Main component
export { default as TransactionDashboard } from './TransactionDashboard'

// Services (public API)
export * from './services/sales.service'
export * from './services/finance.service'
export * from './services/kpi.service'
export * from './services/shared.service'

// Hook & Context
export { useTransactionDashboard } from './hooks/useTransactionDashboard'
export { TransactionPreviewProvider, useTransactionPreview } from './contexts/TransactionPreviewContext'

// Public components
export { EditableKpiCard } from './components/EditableKpiCard'
