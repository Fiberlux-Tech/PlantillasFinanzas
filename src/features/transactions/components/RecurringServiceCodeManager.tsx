// src/features/transactions/components/RecurringServiceCodeManager.tsx
import { useState, useCallback, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { CloseIcon } from '../../../components/shared/Icons';
import { getRecurringServicesByCodes } from '@/features/transactions/services/shared.service';
import type { RecurringService } from '@/types';
import { PLACEHOLDERS, UI_LABELS, VALIDATION_MESSAGES } from '@/config';

// 1. Define the type we expect from the service
interface RecurringServiceLookupResponse {
    recurring_services: RecurringService[];
}

// 2. Define props for this component
interface RecurringServiceCodeManagerProps {
    loadedCodes: string[]; 
    // This prop's signature now matches the service's return type
    onRecurringServiceAdd: (data: RecurringServiceLookupResponse) => void;
    onToggle: () => void; 
    onCodeRemove: (codeToRemove: string) => void;
}

export function RecurringServiceCodeManager({ 
    loadedCodes, 
    onRecurringServiceAdd, 
    onToggle, 
    onCodeRemove 
}: RecurringServiceCodeManagerProps) {
    const [newCodeInput, setNewCodeInput] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const managerRef = useRef<HTMLDivElement>(null);
    const onToggleRef = useRef(onToggle);

    // Keep onToggleRef up to date
    useEffect(() => {
        onToggleRef.current = onToggle;
    }, [onToggle]);

    // Click-away logic
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (managerRef.current && !managerRef.current.contains(event.target as Node)) {
                onToggleRef.current();
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []); // Empty deps - listener only added/removed once

    const handleAddAndConfirmCode = useCallback(async () => {
        const code = newCodeInput.trim().toUpperCase();
        if (!code) {
             setError(VALIDATION_MESSAGES.CODE_EMPTY);
             return;
        }

        if (loadedCodes.includes(code)) {
            setError(VALIDATION_MESSAGES.CODE_ALREADY_LOADED.replace('{code}', code));
            return;
        }

        setIsLoading(true);
        setError(null);

        const result = await getRecurringServicesByCodes([code]);

        // 3. Update the success logic
        if (result.success && result.data?.recurring_services?.length > 0) {
            // Pass the entire 'data' object { recurring_services: [...] } up
            onRecurringServiceAdd(result.data);
            setNewCodeInput('');
            onToggle();
        } else {
            let errorMessage: string = VALIDATION_MESSAGES.CODIGO_NO_VALIDO;
            if (!result.success) {
                errorMessage = result.error || errorMessage;
            }
            setError(errorMessage);
        }
        setIsLoading(false);
    }, [newCodeInput, loadedCodes, onRecurringServiceAdd, onToggle]);


    return (
        // (The JSX for this component remains exactly the same)
        <div ref={managerRef} className="absolute right-0 w-80 mt-2 bg-white border border-gray-300 rounded-lg shadow-xl z-20 p-4" onClick={(e) => e.stopPropagation()}>
            <h4 className="text-md font-semibold mb-3">{UI_LABELS.CODIGO_SERVICIO_RECURRENTE}</h4>
            <div className="flex space-x-2 items-center">
                <div className="flex-grow">
                    <Input
                        type="text"
                        placeholder={PLACEHOLDERS.SERVICE_CODE}
                        value={newCodeInput}
                        onChange={(e) => {
                            setNewCodeInput(e.target.value);
                            setError(null);
                        }}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddAndConfirmCode()}
                        className="h-10 text-base"
                        disabled={isLoading}
                    />
                    {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
                </div>
                <Button
                    onClick={handleAddAndConfirmCode}
                    size="default"
                    className="w-16 h-10 bg-blue-600 hover:bg-blue-700 text-white"
                    disabled={isLoading}
                >
                    {UI_LABELS.IR}
                </Button>
            </div>
            <hr className="my-4 border-gray-200" />
            {loadedCodes.length > 0 && (
                <div className="pt-2">
                    <p className="text-sm font-medium text-gray-700 mb-2">{UI_LABELS.CODIGOS_CARGADOS}</p>
                    <div className="flex flex-col gap-2 max-h-40 overflow-y-auto">
                        {loadedCodes.map(code => (
                            <div
                                key={`loaded-${code}`}
                                className="inline-flex items-center text-sm font-medium bg-white text-gray-800 px-3 py-2 rounded border border-gray-300 justify-between"
                            >
                                <span className="font-medium">{code}</span>
                                <button
                                    onClick={() => onCodeRemove(code)}
                                    className="ml-2 text-gray-500 hover:text-red-600 transition-colors"
                                    aria-label={UI_LABELS.REMOVE_CODE.replace('{code}', code)}
                                >
                                    <CloseIcon className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export const RecurringServiceEmptyState = ({ onToggle: _onToggle }: { onToggle: () => void }) => (
    <div className="flex flex-col items-center justify-center py-6 text-center">
        <p className="text-gray-500 mb-1">{UI_LABELS.NO_SERVICIOS_RECURRENTES}</p>
        <p className="text-sm text-gray-400 mb-4">{UI_LABELS.USE_CARGAR_BUTTON_SERVICIOS}</p>
    </div>
);