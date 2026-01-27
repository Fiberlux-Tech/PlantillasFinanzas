// src/components/shared/EditableKpiCard.tsx
import { useState, useEffect } from 'react';
import KpiCard from '@/features/transactions/components/KpiCard';
import { Input } from '@/components/ui/input';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from '@/components/ui/select';
import { EditPencilIcon, EditCheckIcon, EditXIcon } from '@/components/shared/Icons';
import { CURRENCIES, DISPLAY_VALUES, type Currency } from '@/config';

// 2. Define props interface
interface EditableKpiCardProps {
    title: string;
    currentValue: number | null | undefined;
    currentCurrency: Currency | string | null | undefined;
    canEdit: boolean;
    onValueChange: (key: string, newValue: string | number) => void;
    kpiKey: string;
    currencyKey: string;
    subtext?: string;
}

// Local utility
const formatCurrencyDisplay = (value: number | string | null | undefined): string => {
    const numValue = parseFloat(value as string);
    if (typeof numValue !== 'number' || isNaN(numValue) || numValue === 0) return '-';
    return numValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};


export function EditableKpiCard({ 
    title, 
    currentValue, 
    currentCurrency, 
    canEdit, 
    onValueChange, 
    kpiKey, 
    currencyKey, 
    subtext 
}: EditableKpiCardProps) {
    // 3. Type internal state
    const [isEditing, setIsEditing] = useState(false);
    const [editedValue, setEditedValue] = useState<string | number>(currentValue ?? '');
    const [editedCurrency, setEditedCurrency] = useState<Currency>(
        (currentCurrency as Currency) || CURRENCIES.DEFAULT
    );

    useEffect(() => {
        if (!isEditing) {
            setEditedValue(currentValue ?? '');
            setEditedCurrency((currentCurrency as Currency) || CURRENCIES.DEFAULT);
        }
    }, [currentValue, currentCurrency, isEditing]);

    const handleEditSubmit = () => {
        const newValue = parseFloat(editedValue as string);
        if (!isNaN(newValue) && newValue >= 0) {
            onValueChange(kpiKey, newValue);
            onValueChange(currencyKey, editedCurrency);
            setIsEditing(false);
        } else {
            alert(`Please enter a valid non-negative number for ${title}.`);
        }
    };

    const handleCancelEdit = () => {
        setEditedValue(currentValue ?? '');
        setEditedCurrency((currentCurrency as Currency) || CURRENCIES.DEFAULT);
        setIsEditing(false);
    };

    const handleStartEditing = () => {
        setEditedValue(currentValue ?? '');
        setEditedCurrency((currentCurrency as Currency) || CURRENCIES.DEFAULT);
        setIsEditing(true);
    };

    const displayValue = formatCurrencyDisplay(currentValue);

    return (
        <div className="relative group">
            {canEdit && isEditing ? (
                <div className="bg-white p-3 rounded-lg border border-blue-300 shadow-md h-full flex flex-col justify-center">
                    <label className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Edit {title}</label>
                    <div className="flex items-center space-x-2 mt-1">
                        <Input
                            type="number"
                            value={editedValue}
                            // 4. Type event handler
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditedValue(e.target.value)}
                            className="h-9 flex-grow text-sm p-2 border-input ring-ring focus-visible:ring-1 bg-white"
                            min="0"
                            step="0.01"
                            autoFocus
                        />
                        <div className="w-20">
                            <Select value={editedCurrency} onValueChange={(value: Currency) => setEditedCurrency(value)}>
                                <SelectTrigger className="h-9 text-sm">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value={CURRENCIES.PEN}>{CURRENCIES.PEN}</SelectItem>
                                    <SelectItem value={CURRENCIES.USD}>{CURRENCIES.USD}</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <button onClick={handleEditSubmit} className="p-1 rounded hover:bg-gray-200 text-green-600 flex-shrink-0" aria-label="Confirm"><EditCheckIcon /></button>
                        <button onClick={handleCancelEdit} className="p-1 rounded hover:bg-gray-200 text-red-600 flex-shrink-0" aria-label="Cancel"><EditXIcon /></button>
                    </div>
                </div>
            ) : (
                <>
                    <KpiCard
                        title={title}
                        value={displayValue}
                        currency={currentCurrency || DISPLAY_VALUES.NOT_AVAILABLE}
                        subtext={subtext}
                    />
                    {canEdit && (
                        <button
                            onClick={handleStartEditing}
                            className="absolute top-2 right-2 p-1 rounded bg-gray-100 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-200"
                            aria-label={`Edit ${title}`}
                        >
                            <EditPencilIcon />
                        </button>
                    )}
                </>
            )}
        </div>
    );
}