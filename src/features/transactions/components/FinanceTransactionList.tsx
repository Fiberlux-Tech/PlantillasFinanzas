// src/features/transactions/components/FinanceTransactionList.tsx
import StatusBadge from '@/features/transactions/components/StatusBadge';
import { PaginatedTable, type ColumnDef } from './PaginatedTable';
import { TableCell, TableRow } from '@/components/ui/table';
import type { FormattedFinanceTransaction } from '../services/finance.service';
import { UI_LABELS, EMPTY_STATE_MESSAGES } from '@/config';

// 1. Define Columns (UPDATED - Removed ID column)
const columns: ColumnDef[] = [
    { header: UI_LABELS.UNIDAD_NEGOCIO, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.CLIENTE, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.VENDEDOR, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.MRC, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.PLAZO, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.MARGEN_PERCENT, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.PAYBACK_MESES, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.FECHA, className: 'px-6 py-3 text-center' },
    { header: UI_LABELS.STATUS, className: 'px-6 py-3 text-center' },
];

// 2. Define Props
interface TransactionListProps {
    isLoading: boolean;
    transactions: FormattedFinanceTransaction[];
    onRowClick: (transaction: FormattedFinanceTransaction) => void;
    currentPage: number;
    totalPages: number;
    // --- 1. PROP TYPE CHANGED ---
    // This now matches the new prop type
    onPageChange: (newPage: number) => void;
}

export function TransactionList({
    transactions,
    onRowClick,
    ...props // Pass through isLoading, currentPage, totalPages, onPageChange
}: TransactionListProps) {

    // 3. Define the specific row render function (UPDATED - Removed ID cell)
    const renderRow = (tx: FormattedFinanceTransaction) => (
        <TableRow
            key={tx.id}
            className="bg-white border-b hover:bg-gray-50 cursor-pointer"
            onClick={() => onRowClick(tx)}
        >
            <TableCell className="px-6 py-4 text-center">{tx.unidadNegocio}</TableCell>
            <TableCell className="px-6 py-4 font-bold text-gray-900 text-center">{tx.clientName}</TableCell>
            <TableCell className="px-6 py-4 text-center">{tx.salesman}</TableCell>
            <TableCell className="px-6 py-4 text-center">{tx.MRC_pen.toLocaleString()}</TableCell>
            <TableCell className="px-6 py-4 text-center">{tx.plazoContrato}</TableCell>
            <TableCell className="px-6 py-4 font-medium text-blue-600 text-center">{`${(tx.grossMarginRatio * 100).toFixed(2)}%`}</TableCell>
            <TableCell className="px-6 py-4 text-center">{tx.payback}</TableCell>
            <TableCell className="px-6 py-4 text-center">{tx.submissionDate}</TableCell>
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