// src/components/shared/InlineEditWrapper.tsx

import React, { useState, useCallback, ReactNode, useEffect } from 'react';
import { EditPencilIcon, EditCheckIcon, EditXIcon } from '@/components/shared/Icons';
import { ARIA_LABELS } from '@/config';

interface InlineEditWrapperProps<T> {
    // Unique identifier for the field (for accessibility, etc.)
    fieldKey: string;
    // Current value as seen by the parent component (used for display and reset)
    currentValue: T; 
    // Current currency (or second value) as seen by the parent
    currentCurrency?: string | null; 
    
    // Function to render the value in read-only mode
    renderDisplay: (value: T, currency?: string | null) => ReactNode;
    // Function to render the custom input/select field in editing mode
    renderEdit: (
        localValue: T, 
        setLocalValue: React.Dispatch<React.SetStateAction<T>>,
        localCurrency: string | null,
        setLocalCurrency: React.Dispatch<React.SetStateAction<string | null>>,
        onConfirm: () => void // Pass confirm down to allow 'Enter' key submit
    ) => ReactNode;
    
    // 1. FIX: Changed signature to be explicit and match the intended output flow.
    onConfirm: (finalValue: T, finalCurrency?: string | null) => void; 
    
    // Flag to enable/disable editing
    canEdit: boolean;
    // Optional utility to ensure only valid data is set initially (e.g. for number fields)
    initialValueTransformer?: (value: any) => T; 
    // Optional utility to ensure only valid currency is set initially
    initialCurrencyTransformer?: (currency: any) => string | null;
}

export function InlineEditWrapper<T>({
    fieldKey,
    currentValue,
    currentCurrency,
    renderDisplay,
    renderEdit,
    onConfirm: parentOnConfirm,
    canEdit,
    initialValueTransformer,
    initialCurrencyTransformer = (c) => (c as string) || null,
}: InlineEditWrapperProps<T>) {
    
    const initialValue = initialValueTransformer ? initialValueTransformer(currentValue) : currentValue;
    const initialCurrency = initialCurrencyTransformer(currentCurrency);

    // 1. Core State Management
    const [isEditing, setIsEditing] = useState(false);
    // Use initialValue for typing consistency
    const [localValue, setLocalValue] = useState<T>(initialValue);
    const [localCurrency, setLocalCurrency] = useState<string | null>(initialCurrency);

    // 2. Sync local state with props when not editing
    useEffect(() => {
        if (!isEditing) {
            setLocalValue(initialValue);
            setLocalCurrency(initialCurrency);
        }
    }, [initialValue, initialCurrency, isEditing]); // initialValue/initialCurrency already capture currentValue/currentCurrency changes

    const handleStartEditing = useCallback(() => {
        if (!canEdit) return;
        setLocalValue(initialValue);
        setLocalCurrency(initialCurrency);
        setIsEditing(true);
    }, [canEdit, initialValue, initialCurrency]);

    const handleConfirm = useCallback(() => {
        // Pass the local state back to the parent component's handler
        // 2. FIX: We now explicitly pass localCurrency which is (string | null)
        parentOnConfirm(localValue, localCurrency); 
        setIsEditing(false); // Close edit mode regardless of success, rely on parent re-render for value sync
    }, [parentOnConfirm, localValue, localCurrency]);

    const handleCancel = useCallback(() => {
        setIsEditing(false);
    }, []);

    if (!canEdit) {
        return <p className="font-semibold text-gray-900">{renderDisplay(currentValue, currentCurrency)}</p>;
    }

    if (isEditing) {
        return (
            <div className="flex items-center space-x-2">
                {/* Render the custom input/select field */}
                <div className={localCurrency ? "flex items-center space-x-2" : ""}>
                    {renderEdit(localValue, setLocalValue, localCurrency, setLocalCurrency, handleConfirm)}
                </div>

                {/* Render the control buttons */}
                <button
                    onClick={handleConfirm}
                    className="p-1 rounded hover:bg-gray-200 text-green-600 transition-colors flex-shrink-0"
                    aria-label={ARIA_LABELS.CONFIRM_FIELD.replace('{field}', fieldKey)}
                >
                    <EditCheckIcon />
                </button>
                <button
                    onClick={handleCancel}
                    className="p-1 rounded hover:bg-gray-200 text-red-600 transition-colors flex-shrink-0"
                    aria-label={ARIA_LABELS.CANCEL_FIELD.replace('{field}', fieldKey)}
                >
                    <EditXIcon />
                </button>
            </div>
        );
    }

    return (
        <div 
            className="group flex items-center space-x-2 cursor-pointer" 
            onClick={handleStartEditing}
        >
            <p className="font-semibold text-gray-900">{renderDisplay(currentValue, currentCurrency)}</p>
            <div className="text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity"><EditPencilIcon /></div>
        </div>
    );
}