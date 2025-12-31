// src/components/shared/EditableTableCell.tsx
import React, { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { EditPencilIcon, EditCheckIcon, EditXIcon } from '@/components/shared/Icons';
import { formatCellData } from '@/lib/formatters';
import { ARIA_LABELS } from '@/config';

// 1. Define the props interface
interface EditableTableCellProps {
    currentValue: string | number;
    onConfirm: (newValue: string | number) => void;
    canEdit: boolean;
    inputType?: string; // Optional prop
    min?: number; // Optional prop
    step?: number; // Optional prop
}

export function EditableTableCell({ 
    currentValue, 
    onConfirm, 
    canEdit, 
    inputType = "number",
    min = 0,
    step = 1 
}: EditableTableCellProps) {
    // 2. Type the internal state
    const [isEditing, setIsEditing] = useState<boolean>(false);
    const [editedValue, setEditedValue] = useState<string | number>(currentValue);

    useEffect(() => {
        if (!isEditing) {
            setEditedValue(currentValue);
        }
    }, [currentValue, isEditing]);

    const handleConfirm = () => {
        let finalValue: string | number = editedValue;
        
        if (inputType === 'number') {
            finalValue = parseInt(editedValue as string, 10);
            if (isNaN(finalValue)) {
                finalValue = min; 
            }
        }
        
        onConfirm(finalValue);
        setIsEditing(false);
    };

    const handleCancel = () => {
        setEditedValue(currentValue);
        setIsEditing(false);
    };
    
    const handleStartEditing = () => {
        setEditedValue(currentValue);
        setIsEditing(true);
    };

    if (!canEdit) {
        return <>{formatCellData(currentValue)}</>;
    }

    if (isEditing) {
        return (
            <div className="flex items-center justify-center space-x-1">
                <Input
                    type={inputType}
                    value={editedValue}
                    // 3. Type the event handlers
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditedValue(e.target.value)}
                    className="h-8 w-16 text-center"
                    min={min}
                    step={step}
                    autoFocus
                    onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleConfirm()}
                />
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