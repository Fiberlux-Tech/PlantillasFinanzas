// src/features/transactions/components/SalesTransactionList.tsx
import StatusBadge from '@/features/transactions/components/StatusBadge';
import { PaginatedTable, type ColumnDef } from './PaginatedTable';
import { TableCell, TableRow } from '@/components/ui/table';
import type { FormattedSalesTransaction } from '../services/sales.service';
import { UI_LABELS, EMPTY_STATE_MESSAGES } from '@/config';
import { formatCurrency } from '@/lib/formatters';

// 1. Define Columns (UPDATED - New Order, Centered)
const columns: ColumnDef[] = [
    { header: UI_LABELS.CLIENTE, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.MRC, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.MARGEN_PERCENT, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.PAYBACK_MESES, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.COMISION_VENTAS, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.FECHA, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.FECHA_APROBACION, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.STATUS, className: 'px-6 py-3 text-center' },
];

// 2. Define Props
interface SalesTransactionListProps {
    isLoading: boolean;
    transactions: FormattedSalesTransaction[];
    currentPage: number;
    totalPages: number;
    onPageChange: (newPage: number) => void;
    onRowClick?: (transaction: FormattedSalesTransaction) => void;
}

export function SalesTransactionList({
    transactions,
    onRowClick,
    ...props // Pass through isLoading, currentPage, totalPages, onPageChange
}: SalesTransactionListProps) {

    // 3. Define the specific row render function with click handler (UPDATED - New Order)
    const renderRow = (tx: FormattedSalesTransaction) => (
        <TableRow
            key={tx.id}
            className="bg-white border-b hover:bg-gray-50 cursor-pointer"
            onClick={() => onRowClick?.(tx)}
        >
            <TableCell className="px-6 py-4 font-bold text-gray-900 text-center">{tx.client}</TableCell>
            <TableCell className="px-6 py-4 font-medium text-gray-900 text-center">{formatCurrency(tx.MRC_pen)}</TableCell>
            <TableCell className="px-6 py-4 font-medium text-blue-600 text-center">{`${(tx.grossMarginRatio * 100).toFixed(2)}%`}</TableCell>
            <TableCell className="px-6 py-4 text-center">{tx.payback}</TableCell>
            <TableCell className="px-6 py-4 font-medium text-green-600 text-center">{formatCurrency(tx.comisiones)}</TableCell>
            <TableCell className="px-6 py-4 text-center">{tx.submissionDate}</TableCell>
            <TableCell className="px-6 py-4 text-center">{tx.approvalDate}</TableCell>
            <TableCell className="px-6 py-4 text-center"><StatusBadge status={tx.status} /></TableCell>
        </TableRow>
    );

    // 4. Render the generic table (Unchanged)
    return (
        <PaginatedTable
            {...props}
            columns={columns}
            data={transactions}
            renderRow={renderRow}
            emptyStateMessage={EMPTY_STATE_MESSAGES.NO_TRANSACTIONS_FOUND}
        />
    );
}