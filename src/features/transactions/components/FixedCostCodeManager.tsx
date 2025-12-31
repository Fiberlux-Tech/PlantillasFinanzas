// src/components/shared/FixedCostCodeManager.tsx
import { useState, useCallback, useRef, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { CloseIcon } from '../../../components/shared/Icons';
import { getFixedCostsByCodes } from '@/features/transactions/services/shared.service';
import type { FixedCost } from '@/types';
import { PLACEHOLDERS, UI_LABELS, VALIDATION_MESSAGES } from '@/config';

// FIX: Define the shape of the component's state and props clearly before use
interface FixedCostCodeManagerProps {
    loadedCodes: string[]; 
    onFixedCostAdd: (newCosts: FixedCost[]) => void;
    onToggle: () => void; 
    onCodeRemove: (codeToRemove: string) => void; // <-- NEW REMOVAL PROP
}

export function FixedCostCodeManager({ loadedCodes, onFixedCostAdd, onToggle, onCodeRemove }: FixedCostCodeManagerProps) {
    const [newCodeInput, setNewCodeInput] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const managerRef = useRef<HTMLDivElement>(null);
    const onToggleRef = useRef(onToggle);

    // Keep onToggleRef up to date
    useEffect(() => {
        onToggleRef.current = onToggle;
    }, [onToggle]);

    // UseEffect for click-away logic
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

        // 1. Fetch data for the single new code
        const result = await getFixedCostsByCodes([code]);

        if (result.success && result.data?.length > 0) {
            // Success path
            onFixedCostAdd(result.data);
            setNewCodeInput('');
            onToggle();
        } else {
            // Failure path
            let errorMessage: string = VALIDATION_MESSAGES.CODIGO_NO_VALIDO;
            if (!result.success) {
                errorMessage = result.error || errorMessage;
            }
            setError(errorMessage);
        }
        setIsLoading(false);
    }, [newCodeInput, loadedCodes, onFixedCostAdd, onToggle]);


    return (
        // Attach the ref for click-away detection
        <div ref={managerRef} className="absolute right-0 w-80 mt-2 bg-white border border-gray-300 rounded-lg shadow-xl z-20 p-4" onClick={(e) => e.stopPropagation()}>
            <h4 className="text-md font-semibold mb-3">{UI_LABELS.CODIGO_INVERSION}</h4>

            {/* Input and "Ir" Button (Grouped and Styled) */}
            <div className="flex space-x-2 items-center">
                <div className="flex-grow">
                    <Input
                        type="text"
                        placeholder={PLACEHOLDERS.INVESTMENT_CODE}
                        value={newCodeInput}
                        onChange={(e) => {
                            setNewCodeInput(e.target.value);
                            setError(null);
                        }}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddAndConfirmCode()}
                        className="h-10 text-base"
                        disabled={isLoading}
                    />
                    {/* Error message placement */}
                    {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
                </div>

                {/* Primary Blue "Ir" Button */}
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

            {/* Codes Loaded (Styled to match the final image) */}
            {loadedCodes.length > 0 && (
                <div className="pt-2">
                    <p className="text-sm font-medium text-gray-700 mb-2">{UI_LABELS.CODIGOS_CARGADOS}</p>
                    <div className="flex flex-col gap-2 max-h-40 overflow-y-auto">
                        {loadedCodes.map(code => (
                            <div
                                key={`loaded-${code}`}
                                // FIX: Apply border, white background, and correct padding/font size to match final image
                                className="inline-flex items-center text-sm font-medium bg-white text-gray-800 px-3 py-2 rounded border border-gray-300 justify-between"
                            >
                                <span className="font-medium">{code}</span>
                                <button
                                    onClick={() => onCodeRemove(code)} // <-- USE THE NEW REMOVAL HANDLER
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

// Export the EmptyState component (remains the same)
export const FixedCostEmptyState = ({  }: { onToggle: () => void }) => (
    <div className="flex flex-col items-center justify-center py-6 text-center">
        <p className="text-gray-500 mb-1">{UI_LABELS.NO_DATOS_INVERSION}</p>
        <p className="text-sm text-gray-400 mb-4">{UI_LABELS.USE_CARGAR_BUTTON_HINT}</p>
    </div>
);