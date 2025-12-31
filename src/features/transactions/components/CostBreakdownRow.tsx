// src/components/shared/CostBreakdownRow.tsx
import type { ReactNode } from 'react';
import { ChevronRightIcon, ChevronDownIcon } from '../../../components/shared/Icons';
import { UI_LABELS } from '@/config';

// Define props interface
interface CostBreakdownRowProps {
    title: string;
    items?: number | null;
    total: number | null;
    isOpen: boolean;
    onToggle: () => void;
    children: ReactNode;
    customTotalsNode?: ReactNode;
}

// Apply props
const CostBreakdownRow = ({
    title,
    items,
    total,
    isOpen,
    onToggle,
    children,
    customTotalsNode
}: CostBreakdownRowProps) => (
    <div>
        <div onClick={onToggle} className="flex justify-between items-center p-4 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 cursor-pointer">
            <div className="flex items-center">
                {isOpen ? <ChevronDownIcon /> : <ChevronRightIcon />}
                <div className="ml-3 flex items-center gap-2">
                    <p className="font-semibold text-gray-800">{title}</p>
                    {items !== null && items !== undefined && (
                        <span className="px-2 py-0.5 rounded-full bg-gray-100 text-xs font-medium text-gray-600">
                            {items} items
                        </span>
                    )}
                </div>
            </div>

            {/* Use a flex container here to manage the layout of the total and the button */}
            <div className="flex items-center space-x-2">
                {customTotalsNode ? (
                    customTotalsNode // This is used for Recurring Services (Income/Egreso)
                ) : (
                    <div className="text-right"> {/* Default alignment for total */}
                        <p className="font-semibold text-red-600">
                            {total !== null
                                ? `$${total.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                : '-'
                            }
                        </p>
                        <p className="text-xs text-gray-500">{UI_LABELS.TOTAL}</p>
                    </div>
                )}

            </div>
        </div>
        {isOpen && <div className="p-4 border border-t-0 border-gray-200 rounded-b-lg">{children}</div>}
    </div>
);

export default CostBreakdownRow;
