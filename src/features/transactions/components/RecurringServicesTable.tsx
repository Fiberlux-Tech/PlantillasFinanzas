// src/components/shared/RecurringServicesTable.tsx
import { useState } from 'react';
import type { RecurringService } from '@/types';
import { useTransactionPreview } from '@/contexts/TransactionPreviewContext';
import { formatCurrency, formatCellData } from '@/lib/formatters';
import type { ReactNode } from 'react';
import { UI_LABELS, EMPTY_STATE_MESSAGES } from '@/config';
import { TableActionIcons } from '@/components/shared/TableActionIcons';
import { RecurringServiceDetailModal } from '@/features/transactions/components/RecurringServiceDetailModal';

interface RecurringServicesTableProps {
    EmptyStateComponent?: React.FC<{ canEdit: boolean }> | (() => ReactNode);
}

const RecurringServicesTable = ({ EmptyStateComponent }: RecurringServicesTableProps) => {

    // 1. Get draftState and dispatch from the context
    const {
        canEdit,
        isFieldReadOnly,
        draftState, // Get the draft state
        dispatch,   // Get the dispatch function
    } = useTransactionPreview();

    // 2. Get the services from the draftState
    const data = draftState.currentRecurringServices;

    // 3. Modal state for detail view
    const [selectedService, setSelectedService] = useState<RecurringService | null>(null);
    const [selectedIndex, setSelectedIndex] = useState<number>(-1);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isEditMode, setIsEditMode] = useState(false);

    // 4. Handler to open modal in view mode
    const handleViewDetails = (index: number, service: RecurringService) => {
        setSelectedService(service);
        setSelectedIndex(index);
        setIsEditMode(false);
        setIsModalOpen(true);
    };

    // 5. Handler to open modal in edit mode
    const handleEditService = (index: number, service: RecurringService) => {
        setSelectedService(service);
        setSelectedIndex(index);
        setIsEditMode(true);
        setIsModalOpen(true);
    };

    // 6. Handler to close modal
    const handleCloseModal = () => {
        setIsModalOpen(false);
        setSelectedService(null);
        setSelectedIndex(-1);
    };

    // 7. Handler to save edited service
    const handleSaveService = (updatedService: RecurringService) => {
        dispatch({
            type: 'REPLACE_RECURRING_SERVICE',
            payload: { index: selectedIndex, updatedService }
        });
    };

    // 8. Handler to delete service (index-based for trash icon)
    const handleDeleteService = (index: number, service: RecurringService) => {
        if (window.confirm(`¿Estás seguro de eliminar el servicio "${service.tipo_servicio}"?`)) {
            dispatch({
                type: 'REMOVE_RECURRING_SERVICE',
                payload: index
            });
        }
    };

    if (!data || data.length === 0) {
        if (EmptyStateComponent) {
            // Use the passed-in empty state
            return <EmptyStateComponent canEdit={canEdit} />;
        }
        return <p className="text-center text-gray-500 py-4">{EMPTY_STATE_MESSAGES.NO_RECURRING_SERVICES}</p>;
    }

    // 4. The entire JSX render tree
    return (
        <>
            <div className="overflow-x-auto bg-white rounded-lg">
                <table className="w-full text-sm divide-y divide-gray-200 table-fixed">
                <thead className="bg-gray-50">
                    <tr>
                        <th scope="col" className="w-32 px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{UI_LABELS.TIPO_SERVICIO}</th>
                        <th scope="col" className="w-40 px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{UI_LABELS.UBICACION}</th>
                        <th scope="col" className="w-24 px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">{UI_LABELS.CANTIDAD}</th>
                        <th scope="col" className="w-32 px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{UI_LABELS.MRR}</th>
                        <th scope="col" className="w-32 px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{UI_LABELS.COSTO_RECURRENTE}</th>
                        <th scope="col" className="w-28 px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">{UI_LABELS.ACCIONES}</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {data.map((item, index) => (
                        <tr key={`recurring-service-${item.id}-${index}`} className="hover:bg-gray-50">
                            <td className="px-3 py-2 text-gray-800 align-middle">
                                <div className="truncate" title={item.tipo_servicio || undefined}>
                                    {formatCellData(item.tipo_servicio)}
                                </div>
                            </td>
                            <td className="px-3 py-2 text-gray-800 align-middle">
                                <div className="truncate" title={item.ubicacion || undefined}>
                                    {formatCellData(item.ubicacion)}
                                </div>
                            </td>
                            <td className="px-3 py-2 text-gray-800 align-middle text-center whitespace-nowrap">{formatCellData(item.Q)}</td>
                            <td className="px-3 py-2 text-green-600 font-medium align-middle text-right whitespace-nowrap">{formatCurrency(item.ingreso_pen)}</td>
                            <td className="px-3 py-2 text-red-600 font-medium align-middle text-right whitespace-nowrap">{formatCurrency(item.egreso_pen)}</td>
                            <td className="px-3 py-2 align-middle">
                                <TableActionIcons
                                    onView={() => handleViewDetails(index, item)}
                                    onEdit={canEdit && !isFieldReadOnly('recurring_services') ? () => handleEditService(index, item) : undefined}
                                    onDelete={canEdit && !isFieldReadOnly('recurring_services') ? () => handleDeleteService(index, item) : undefined}
                                />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>

        {/* Detail Modal */}
        <RecurringServiceDetailModal
            service={selectedService}
            isOpen={isModalOpen}
            onClose={handleCloseModal}
            isEditMode={isEditMode}
            onSave={handleSaveService}
        />
        </>
    );
};

export default RecurringServicesTable;