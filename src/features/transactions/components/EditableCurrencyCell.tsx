// src/components/shared/EditableCurrencyCell.tsx
import { useState, useEffect } from 'react';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from '@/components/ui/select';
import { EditPencilIcon, EditCheckIcon, EditXIcon } from '@/components/shared/Icons';
import { formatCellData } from '@/lib/formatters';
import { CURRENCIES, ARIA_LABELS, type Currency } from '@/config';

// Define props interface
interface EditableCurrencyCellProps {
    currentValue: Currency | string | null | undefined;
    onConfirm: (newValue: Currency) => void;
    canEdit: boolean;
}

// Helper function to validate and normalize currency
const validateCurrency = (value: Currency | string | null | undefined): Currency => {
    if (typeof value === 'string' && CURRENCIES.LIST.includes(value as Currency)) {
        return value as Currency;
    }
    return CURRENCIES.DEFAULT_FIXED_COST; // Default fallback
};

export function EditableCurrencyCell({
    currentValue,
    onConfirm,
    canEdit
}: EditableCurrencyCellProps) {
    // 3. Type the internal state with validated currency
    const [isEditing, setIsEditing] = useState(false);
    const [editedValue, setEditedValue] = useState<Currency>(
        validateCurrency(currentValue)
    );

    useEffect(() => {
        if (!isEditing) {
            setEditedValue(validateCurrency(currentValue));
        }
    }, [currentValue, isEditing]);

    const handleConfirm = () => {
        onConfirm(editedValue);
        setIsEditing(false);
    };

    const handleCancel = () => {
        setEditedValue(validateCurrency(currentValue));
        setIsEditing(false);
    };

    const handleStartEditing = () => {
        setEditedValue(validateCurrency(currentValue));
        setIsEditing(true);
    };

    if (!canEdit) {
        return <>{formatCellData(currentValue)}</>;
    }

    if (isEditing) {
        return (
            <div className="flex items-center justify-center space-x-1">
                <div className="w-20">
                    {/* 4. Type the onValueChange */}
                    <Select value={editedValue} onValueChange={(value: Currency) => setEditedValue(value)}>
                        <SelectTrigger className="h-8 text-xs">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value={CURRENCIES.PEN}>{CURRENCIES.PEN}</SelectItem>
                            <SelectItem value={CURRENCIES.USD}>{CURRENCIES.USD}</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <button
                    onClick={handleConfirm}
                    className="p-1 rounded hover:bg-gray-200 text-green-600"
                    aria-label={ARIA_LABELS.CONFIRM}
                >
                    <EditCheckIcon />
                </button>
                <button
                    onClick={handleCancel}
                    className="p-1 rounded hover:bg-gray-200 text-red-600"
                    aria-label={ARIA_LABELS.CANCEL}
                >
                    <EditXIcon />
                </button>
            </div>
        );
    }

    return (
        <div 
            className="group relative flex items-center justify-center cursor-pointer min-h-[32px]"
            onClick={handleStartEditing}
        >
            <span>{formatCellData(currentValue)}</span>
            <button
                className="absolute right-0 p-1 rounded bg-gray-100 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-200"
                aria-label={ARIA_LABELS.EDIT_VALUE}
            >
                <EditPencilIcon />
            </button>
        </div>
    );
}