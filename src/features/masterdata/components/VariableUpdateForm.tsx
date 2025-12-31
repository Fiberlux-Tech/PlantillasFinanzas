// src/features/masterdata/components/VariableUpdateForm.tsx
import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { UI_LABELS, BUTTON_LABELS, PLACEHOLDERS } from '@/config';

// Define types for props
interface EditableConfigItem {
    name: string;
    label: string;
    category: string;
}

interface FormInputState {
    variable_name: string;
    variable_value: string;
    comment: string;
}

interface VariableUpdateFormProps {
    editableConfig: EditableConfigItem[];
    formInput: FormInputState;
    setFormInput: React.Dispatch<React.SetStateAction<FormInputState>>;
    handleUpdateSubmit: () => void;
    isLoading: boolean;
}

export function VariableUpdateForm({
    editableConfig,
    formInput,
    setFormInput,
    handleUpdateSubmit,
    isLoading
}: VariableUpdateFormProps) {

    // Type event handlers
    const onVariableChange = (value: string) => {
        setFormInput(prev => ({ ...prev, variable_name: value }));
    };

    const onValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormInput(prev => ({ ...prev, variable_value: e.target.value }));
    };

    const onCommentChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormInput(prev => ({ ...prev, comment: e.target.value }));
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
            <h2 className="text-xl font-semibold mb-4">{UI_LABELS.UPDATE_VARIABLE}</h2>

            <div className="flex space-x-4 items-end">

                <div className="w-[160px] flex-shrink-0">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{UI_LABELS.VARIABLE}</label>
                    <Select
                        value={formInput.variable_name}
                        onValueChange={onVariableChange}
                    >
                        <SelectTrigger className="w-full">
                            <SelectValue placeholder={PLACEHOLDERS.SELECT_VARIABLE} />
                        </SelectTrigger>
                        <SelectContent>
                            {editableConfig.map(config => (
                                <SelectItem key={config.name} value={config.name}>
                                    {config.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <div className="w-[160px] flex-shrink-0">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{UI_LABELS.VALUE}</label>
                    <Input
                        type="number"
                        placeholder={PLACEHOLDERS.ENTER_VALUE}
                        value={formInput.variable_value}
                        onChange={onValueChange}
                    />
                </div>

                <div className="flex-1 min-w-[150px]">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{UI_LABELS.COMENTARIO}</label>
                    <Input
                        type="text"
                        placeholder={PLACEHOLDERS.OPTIONAL_COMMENT}
                        value={formInput.comment}
                        onChange={onCommentChange}
                        maxLength={50}
                    />
                </div>

                <Button onClick={handleUpdateSubmit} disabled={isLoading}>
                    {BUTTON_LABELS.UPDATE_VARIABLE}
                </Button>
            </div>
        </div>
    );
}
