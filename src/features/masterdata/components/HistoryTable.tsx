// src/features/masterdata/components/HistoryTable.tsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CategoryBadge } from '@/components/shared/CategoryBadge';
import type { HistoryItem as HistoryRecord } from '../masterDataService';
import { formatDate } from '@/lib/formatters';
import { UI_LABELS } from '@/config';

// Define the props interface
interface HistoryTableProps {
    isLoading: boolean;
    history: HistoryRecord[];
}


export function HistoryTable({ isLoading, history }: HistoryTableProps) {
    return (
        <div className="bg-white p-6 rounded-lg shadow-md mt-8">
            <h2 className="text-xl font-semibold mb-4">{UI_LABELS.UPDATE_HISTORY}</h2>
            <p className="text-sm text-gray-500 mb-6">{UI_LABELS.RECENT_UPDATES}</p>

            <div className="overflow-x-auto">
                {isLoading && history.length === 0 ? (
                    <p className="text-center py-4 text-gray-500">{UI_LABELS.LOADING_HISTORY}</p>
                ) : history.length === 0 ? (
                    <p className="text-center py-4 text-gray-500">{UI_LABELS.NO_HISTORY}</p>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow className="bg-gray-50">
                                <TableHead className="w-[120px]">{UI_LABELS.VARIABLE}</TableHead>
                                <TableHead className="w-[100px]">{UI_LABELS.CATEGORY}</TableHead>
                                <TableHead className="text-right w-[80px]">{UI_LABELS.VALUE}</TableHead>
                                <TableHead className="text-center w-[150px]">{UI_LABELS.DATE_UPDATED}</TableHead>
                                <TableHead className="w-[150px]">{UI_LABELS.USER_UPDATER}</TableHead>
                                <TableHead className="w-[200px]">{UI_LABELS.COMMENT}</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {history.map((record, index) => (
                                <TableRow key={record.id || index} className="hover:bg-gray-50">
                                    <TableCell className="font-medium">{record.variable_name}</TableCell>
                                    <TableCell>
                                        <CategoryBadge category={record.category} />
                                    </TableCell>
                                    <TableCell className="text-right font-mono">{record.variable_value}</TableCell>
                                    <TableCell className="text-center text-xs">{formatDate(record.date_recorded)}</TableCell>
                                    <TableCell>{record.recorder_username}</TableCell>
                                    <TableCell className="text-sm max-w-xs truncate" title={record.comment || undefined}>{record.comment || '-'}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </div>
        </div>
    );
}
