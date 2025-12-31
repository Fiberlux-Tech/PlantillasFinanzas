// src/features/transactions/components/TransactionOverviewInputs.tsx

import { GigaLanCommissionInputs } from '@/features/transactions/components/GigaLanCommissionInputs';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { BUSINESS_UNITS, REGIONS, SALE_TYPES, CURRENCIES, PLACEHOLDERS, VALIDATION_MESSAGES, UI_LABELS, BOOLEAN_LABELS } from '@/config';
import { formatCurrency } from '@/lib/formatters';
import { useTransactionPreview } from '@/contexts/TransactionPreviewContext';
import { InlineEditWrapper } from './InlineEditWrapper'; 


interface TransactionOverviewInputsProps {
    isFinanceView: boolean;
}

// Local utility to format value and append currency for display mode
const formatCurrencyDisplay = (value: number | string | null | undefined, currency: string | null | undefined = CURRENCIES.DEFAULT): string => {
    const formattedValue = formatCurrency(value);

    // Only add the currency if the value is not "-"
    if (formattedValue === '-') {
        return formattedValue;
    }

    return `${formattedValue} ${currency || CURRENCIES.DEFAULT}`;
};

// --- Custom Renderer Components for InlineEditWrapper ---

// Custom Rendering Component for Select fields (Unidad, Region, Sale Type)
interface SelectInputProps {
    options: readonly string[];
    valueKey: string;
}
const SelectInput: React.FC<SelectInputProps & { 
    localValue: string | number | null; 
    setLocalValue: React.Dispatch<React.SetStateAction<any>>;
    onConfirm: () => void;
}> = ({ 
    options, 
    valueKey, 
    localValue, 
    setLocalValue,
}) => (
    <Select value={localValue as string || ''} onValueChange={setLocalValue}>
        <SelectTrigger className="text-sm h-9 bg-white w-40"> {/* <-- ADD w-40 HERE */}
            <SelectValue placeholder={PLACEHOLDERS.SELECT_FIELD.replace('{field}', valueKey)} />
        </SelectTrigger>
        <SelectContent>
            {options.map(option => (<SelectItem key={option} value={option}>{option}</SelectItem>))}
        </SelectContent>
    </Select>
);

// Custom Rendering Component for Number Input fields (Plazo)
const NumberInput: React.FC<{ 
    localValue: string | number | null; 
    setLocalValue: React.Dispatch<React.SetStateAction<any>>;
    onConfirm: () => void; 
}> = ({ localValue, setLocalValue, onConfirm }) => (
    <Input 
        type="number" 
        value={localValue || ''} 
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocalValue(e.target.value)}
        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && onConfirm()}
        className="h-9 w-24 text-sm p-2 border-input ring-ring focus-visible:ring-1 bg-white" 
        min="1" 
        step="1" 
        autoFocus
    />
);

// Custom Rendering Component for Currency Input fields (MRC/NRC)
const CurrencyInput: React.FC<{
    localValue: string | number | null;
    setLocalValue: React.Dispatch<React.SetStateAction<any>>;
    localCurrency: string | null;
    setLocalCurrency: React.Dispatch<React.SetStateAction<string | null>>;
    onConfirm: () => void;
}> = ({ localValue, setLocalValue, localCurrency, setLocalCurrency, onConfirm }) => {
    // Format the value to 2 decimal places for display in the input
    const formattedValue = localValue !== null && localValue !== ''
        ? Number(localValue).toFixed(2)
        : '';

    return (
        <>
            {/* Input for Value */}
            <Input
                type="number"
                value={formattedValue}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocalValue(e.target.value)}
                onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && onConfirm()}
                className="h-9 w-24 text-sm p-2 border-input ring-ring focus-visible:ring-1 bg-white"
                min="0"
                step="0.01"
                autoFocus
            />

            {/* Select for Currency */}
            <div className="w-20">
                <Select
                    value={localCurrency || ''}
                    onValueChange={(value) => setLocalCurrency(value)}
                >
                    <SelectTrigger className="text-sm h-9 bg-white">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value={CURRENCIES.PEN}>{CURRENCIES.PEN}</SelectItem>
                        <SelectItem value={CURRENCIES.USD}>{CURRENCIES.USD}</SelectItem>
                    </SelectContent>
                </Select>
            </div>
        </>
    );
};

// Custom Rendering Component for Boolean (SI/NO) fields
const BooleanSelectInput: React.FC<{
    localValue: boolean | null | undefined;
    setLocalValue: React.Dispatch<React.SetStateAction<any>>;
    onConfirm: () => void;
}> = ({ localValue, setLocalValue }) => (
    <Select
        // We convert the boolean to a string for the Select component
        value={localValue === true ? "true" : "false"}
        onValueChange={(value) => {
            // Convert the string back to a boolean for our state
            setLocalValue(value === "true");
        }}
    >
        <SelectTrigger className="text-sm h-9 bg-white w-24">
            <SelectValue />
        </SelectTrigger>
        <SelectContent>
            <SelectItem value="true">{BOOLEAN_LABELS.TRUE}</SelectItem>
            <SelectItem value="false">{BOOLEAN_LABELS.FALSE}</SelectItem>
        </SelectContent>
    </Select>
);
// --- END of new component ---


export function TransactionOverviewInputs({ isFinanceView: _isFinanceView }: TransactionOverviewInputsProps) {

    const {
        baseTransaction,
        draftState,
        dispatch,
        canEdit,
        isFieldReadOnly
    } = useTransactionPreview();

    const {
        liveKpis,
        liveEdits, 
    } = draftState;

    // Helper for dispatching updates to liveEdits (REMAINS THE SAME)
    const onValueChange = (key: string, newValue: string | number | null) => {
        dispatch({
            type: 'UPDATE_TRANSACTION_FIELD',
            payload: { key, value: newValue }
        });
    }

    const tx = baseTransaction.transactions;
    const kpiData = liveKpis || tx;
    const gigalanInputs = liveEdits;

    // --- NEW Confirmed Values (read from liveEdits or baseTx) ---
    const confirmedPlazo = liveEdits?.plazoContrato ?? kpiData.plazoContrato ?? tx.plazoContrato;
    
    const confirmedUnidad = liveEdits?.unidadNegocio ?? tx.unidadNegocio;
    const confirmedRegion = liveEdits?.gigalan_region ?? tx.gigalan_region;
    const confirmedSaleType = liveEdits?.gigalan_sale_type ?? tx.gigalan_sale_type;

    const confirmedMrcValue = liveEdits?.MRC_original ?? kpiData.MRC_original ?? tx.MRC_original;
    const confirmedMrcCurrency = liveEdits?.MRC_currency ?? kpiData.MRC_currency ?? tx.MRC_currency ?? CURRENCIES.DEFAULT;
    const confirmedNrcValue = liveEdits?.NRC_original ?? kpiData.NRC_original ?? tx.NRC_original;
    const confirmedNrcCurrency = liveEdits?.NRC_currency ?? kpiData.NRC_currency ?? tx.NRC_currency ?? CURRENCIES.DEFAULT;
    const confirmedAplicaCartaFianza = liveEdits?.aplicaCartaFianza ?? tx.aplicaCartaFianza;

    const confirmedCompanyID = liveEdits?.companyID ?? tx.companyID;
    const confirmedClientName = liveEdits?.clientName ?? tx.clientName;
    
    // Helper for static display blocks (RUC/DNI, Nombre Cliente, Comisión)
    const StaticField = ({ label, value, currency }: { label: string, value: React.ReactNode, currency?: string }) => (
        <div className="min-h-[60px]">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
            <div className="font-semibold text-gray-900">{value} {currency}</div>
        </div>
    );
    
    // --- Handlers now consolidated to simple onConfirm callbacks ---
    
    const handleConfirmPlazo = (finalValue: number | string | null) => {
        const newPlazo = parseInt(finalValue as string, 10);
        if (!isNaN(newPlazo) && newPlazo > 0 && Number.isInteger(newPlazo)) {
            // FIX: Use ATOMIC dispatch for PlazoContrato
            dispatch({
                type: 'UPDATE_MULTIPLE_TRANSACTION_FIELDS',
                payload: { plazoContrato: newPlazo }
            });
        } else {
            alert(VALIDATION_MESSAGES.PLAZO_INVALID);
        }
    };
    
    const handleConfirmUnidad = (finalValue: string | number | null) => {
        if (!finalValue || !(BUSINESS_UNITS.LIST as readonly string[]).includes(finalValue as string)) {
            alert(VALIDATION_MESSAGES.UNIDAD_REQUIRED);
            return;
        }
        onValueChange('unidadNegocio', finalValue as string);
    };
    
    const handleConfirmRegion = (finalValue: string | number | null) => {
        if (!finalValue || !(REGIONS.LIST as readonly string[]).includes(finalValue as string)) {
            alert(VALIDATION_MESSAGES.REGION_REQUIRED);
            return;
        }
        onValueChange('gigalan_region', finalValue as string);
    };
    
    const handleConfirmSaleType = (finalValue: string | number | null) => {
        if (!finalValue || !SALE_TYPES.LIST.includes(finalValue as any)) {
            alert(VALIDATION_MESSAGES.TIPO_VENTA_REQUIRED);
            return;
        }
        onValueChange('gigalan_sale_type', finalValue as "NUEVO" | "EXISTENTE");
    };

    // 1. FIX: Make the second parameter optional to match InlineEditWrapper's definition
    const handleConfirmMrc = (finalValue: number | string | null, finalCurrency?: string | null) => {
        const newValue = parseFloat(finalValue as string);
        const finalCurrencySafe = finalCurrency || confirmedMrcCurrency;

        if (!isNaN(newValue) && newValue >= 0) {
            // FIX: Use single, ATOMIC dispatch for MRC/Currency pair
            dispatch({
                type: 'UPDATE_MULTIPLE_TRANSACTION_FIELDS',
                payload: {
                    MRC_original: newValue,
                    MRC_currency: finalCurrencySafe
                }
            });
        } else {
            alert(VALIDATION_MESSAGES.MRC_INVALID);
        }
    };

    const handleConfirmNrc = (finalValue: number | string | null, finalCurrency?: string | null) => {
        const newValue = parseFloat(finalValue as string);
        const finalCurrencySafe = finalCurrency || confirmedNrcCurrency;

        if (!isNaN(newValue) && newValue >= 0) {
            // FIX: Use single, ATOMIC dispatch for NRC/Currency pair
            dispatch({
                type: 'UPDATE_MULTIPLE_TRANSACTION_FIELDS',
                payload: {
                    NRC_original: newValue,
                    NRC_currency: finalCurrencySafe
                }
            });
        } else {
            alert(VALIDATION_MESSAGES.NRC_INVALID);
        }
    };

    const handleConfirmCartaFianza = (finalValue: boolean | null | undefined) => {
        // Use single, ATOMIC dispatch
        dispatch({
            type: 'UPDATE_MULTIPLE_TRANSACTION_FIELDS',
            payload: { aplicaCartaFianza: finalValue === true } // Ensure it's a boolean
        });
    };

    // Wrapper function for GigaLanCommissionInputs
    const handleGigaLanOldMrcChange = (key: string, value: number | null) => {
        onValueChange(key, value);
    };

    return (
        <div className="mb-6">
            <div className="flex justify-between items-start mb-3"> 
                <h3 className="font-semibold text-gray-800 text-lg">{UI_LABELS.TRANSACTION_OVERVIEW}</h3>

                {/* --- Master Variables (Horizontal) --- */}
                <div className="flex space-x-4 text-xs text-gray-500">
                    <p>
                        {UI_LABELS.TIPO_CAMBIO}:
                        <span className="font-semibold text-gray-700 ml-1">
                            {formatCurrency(tx.tipoCambio, { decimals: 4 })}
                        </span>
                    </p>
                    <p>
                        {UI_LABELS.COSTO_CAPITAL}:
                        <span className="font-semibold text-gray-700 ml-1">
                            {formatCurrency(tx.costoCapitalAnual * 100, { decimals: 2 })}%
                        </span>
                    </p>
                    {/* --- ADD THESE TWO <p> BLOCKS --- */}
                    <p>
                        {UI_LABELS.TASA_CARTA_FIANZA}:
                        <span className="font-semibold text-gray-700 ml-1">
                            {formatCurrency((tx.tasaCartaFianza || 0) * 100, { decimals: 2 })}%
                        </span>
                    </p>
                    <p>
                        {UI_LABELS.COSTO_CARTA_FIANZA}:
                        <span className="font-semibold text-gray-700 ml-1">
                            {formatCurrency(kpiData.costoCartaFianza)}
                        </span>
                    </p>
                    {/* --- END OF ADDED BLOCK --- */}
                </div>
            </div>
            <div className="bg-gray-100 p-4 rounded-lg grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-6 items-start">
                
                {/* 1. UNIDAD DE NEGOCIO (Using InlineEditWrapper) */}
                <div className="min-h-[60px]">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{UI_LABELS.UNIDAD_NEGOCIO}</p>
                    <InlineEditWrapper<string | null>
                        fieldKey={UI_LABELS.UNIDAD_NEGOCIO}
                        currentValue={confirmedUnidad}
                        canEdit={canEdit && !isFieldReadOnly('unidadNegocio')}
                        renderDisplay={(value) => value || "Selecciona obligatorio"}
                        renderEdit={(localValue, setLocalValue, _, __, onConfirm) => (
                            <SelectInput
                                options={BUSINESS_UNITS.LIST}
                                valueKey={UI_LABELS.UNIDAD_NEGOCIO}
                                localValue={localValue}
                                setLocalValue={setLocalValue}
                                onConfirm={onConfirm}
                            />
                        )}
                        onConfirm={handleConfirmUnidad}
                    />
                </div>
                {/* 2. RUC/DNI (Static Field) */}
                <StaticField label={UI_LABELS.RUC_DNI} value={confirmedCompanyID || '-'} />

                {/* 3. NOMBRE CLIENTE (Static Field) */}
                <StaticField label={UI_LABELS.NOMBRE_CLIENTE} value={confirmedClientName} />

                {/* 4. PLAZO DE CONTRATO (Using InlineEditWrapper) */}
                <div className="min-h-[60px]">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{UI_LABELS.PLAZO_CONTRATO}</p>
                    <InlineEditWrapper<number | null>
                        fieldKey={UI_LABELS.PLAZO_CONTRATO}
                        currentValue={confirmedPlazo}
                        canEdit={canEdit && !isFieldReadOnly('plazoContrato')}
                        initialValueTransformer={(value) => value ?? 0}
                        renderDisplay={(value) => `${value ?? '-'} ${UI_LABELS.MESES}`}
                        renderEdit={(localValue, setLocalValue, _, __, onConfirm) => (
                            <NumberInput 
                                localValue={localValue} 
                                setLocalValue={setLocalValue} 
                                onConfirm={onConfirm}
                            />
                        )}
                        onConfirm={handleConfirmPlazo}
                    />
                </div>

                {/* 5. MRC (Using InlineEditWrapper for dual input) */}
                <div className="min-h-[60px]">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{UI_LABELS.MRC_RECURRENTE}</p>
                    <InlineEditWrapper<number | null>
                        fieldKey={UI_LABELS.MRC_RECURRENTE}
                        currentValue={confirmedMrcValue}
                        currentCurrency={confirmedMrcCurrency}
                        canEdit={canEdit && !isFieldReadOnly('MRC_original')}
                        initialValueTransformer={(value) => value ?? 0}
                        initialCurrencyTransformer={(c) => c ?? CURRENCIES.DEFAULT}
                        renderDisplay={formatCurrencyDisplay}
                        renderEdit={(localValue, setLocalValue, localCurrency, setLocalCurrency, onConfirm) => (
                            <CurrencyInput 
                                localValue={localValue} 
                                setLocalValue={setLocalValue} 
                                localCurrency={localCurrency}
                                setLocalCurrency={setLocalCurrency}
                                onConfirm={onConfirm}
                            />
                        )}
                        onConfirm={handleConfirmMrc}
                    />
                </div>
                
                {/* 6. NRC (Using InlineEditWrapper for dual input) */}
                <div className="min-h-[60px]">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{UI_LABELS.NRC_PAGO_UNICO}</p>
                    <InlineEditWrapper<number | null>
                        fieldKey={UI_LABELS.NRC_PAGO_UNICO}
                        currentValue={confirmedNrcValue}
                        currentCurrency={confirmedNrcCurrency}
                        canEdit={canEdit && !isFieldReadOnly('NRC_original')}
                        initialValueTransformer={(value) => value ?? 0}
                        initialCurrencyTransformer={(c) => c ?? CURRENCIES.DEFAULT}
                        renderDisplay={formatCurrencyDisplay}
                        renderEdit={(localValue, setLocalValue, localCurrency, setLocalCurrency, onConfirm) => (
                            <CurrencyInput 
                                localValue={localValue} 
                                setLocalValue={setLocalValue} 
                                localCurrency={localCurrency}
                                setLocalCurrency={setLocalCurrency}
                                onConfirm={onConfirm}
                            />
                        )}
                        onConfirm={handleConfirmNrc}
                    />
                </div>
                {/* 7. COMISION DE VENTAS (Static Field) */}
                {((): React.ReactNode => {
                    const formattedValue = formatCurrency(kpiData.comisiones);
                    const displayCurrency = formattedValue === '-' ? undefined : CURRENCIES.DEFAULT;
                    return (
                        <StaticField
                            label={UI_LABELS.COMISION_VENTAS}
                            value={formattedValue}
                            currency={displayCurrency}
                        />
                    );
                })()}

                {/* 8. APLICA CARTA FIANZA (Using InlineEditWrapper) */}
                <div className="min-h-[60px]">
                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{UI_LABELS.APLICA_CARTA_FIANZA}</p>
                    <InlineEditWrapper<boolean | null>
                        fieldKey={UI_LABELS.APLICA_CARTA_FIANZA}
                        currentValue={confirmedAplicaCartaFianza || false}
                        canEdit={canEdit && !isFieldReadOnly('aplicaCartaFianza')}
                        initialValueTransformer={(value) => value === true}
                        renderDisplay={(value) => (value === true ? BOOLEAN_LABELS.TRUE : BOOLEAN_LABELS.FALSE)}
                        renderEdit={(localValue, setLocalValue, _, __, onConfirm) => (
                            <BooleanSelectInput
                                localValue={localValue}
                                setLocalValue={setLocalValue}
                                onConfirm={onConfirm}
                            />
                        )}
                        onConfirm={handleConfirmCartaFianza}
                    />
                </div>

                {/* --- GIGALAN FIELDS --- */}
                {confirmedUnidad === BUSINESS_UNITS.GIGALAN && (
                    <>
                        {/* --- EDITABLE REGION (8) --- */}
                        <div className="min-h-[60px]">
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{UI_LABELS.REGION}</p>
                            <InlineEditWrapper<string | null>
                                fieldKey={UI_LABELS.REGION}
                                currentValue={confirmedRegion}
                                canEdit={canEdit && !isFieldReadOnly('gigalan_region')}
                                renderDisplay={(value) => value || "Selecciona obligatorio"}
                                renderEdit={(localValue, setLocalValue, _, __, onConfirm) => (
                                    <SelectInput
                                        options={REGIONS.LIST}
                                        valueKey={UI_LABELS.REGION}
                                        localValue={localValue}
                                        setLocalValue={setLocalValue}
                                        onConfirm={onConfirm}
                                    />
                                )}
                                onConfirm={handleConfirmRegion}
                            />
                        </div>
                        {/* --- EDITABLE TYPE OF SALE --- */}
                        <div className="min-h-[60px]">
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{UI_LABELS.TIPO_VENTA}</p>
                            <InlineEditWrapper<string | null>
                                fieldKey={UI_LABELS.TIPO_VENTA}
                                currentValue={confirmedSaleType}
                                canEdit={canEdit && !isFieldReadOnly('gigalan_sale_type')}
                                renderDisplay={(value) => value || "Selecciona obligatorio"}
                                renderEdit={(localValue, setLocalValue, _, __, onConfirm) => (
                                    <SelectInput
                                        options={SALE_TYPES.LIST}
                                        valueKey={UI_LABELS.TIPO_VENTA}
                                        localValue={localValue}
                                        setLocalValue={setLocalValue}
                                        onConfirm={onConfirm}
                                    />
                                )}
                                onConfirm={handleConfirmSaleType}
                            />
                        </div>
                        {/* --- GigaLan PREVIOUS MONTHLY CHARGE Input (10) --- */}
                        {canEdit && confirmedSaleType === SALE_TYPES.EXISTENTE && (
                            <div className="min-h-[60px]">
                                <GigaLanCommissionInputs
                                    inputs={{ ...gigalanInputs, gigalan_sale_type: confirmedSaleType }}
                                    onInputChange={handleGigaLanOldMrcChange}
                                />
                            </div>
                        )}

                        {!canEdit && tx.gigalan_sale_type === SALE_TYPES.EXISTENTE && (
                            <div className="min-h-[60px]">
                                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{UI_LABELS.MRC_PREVIO}</p>
                                <p className="font-semibold text-gray-900">{tx.gigalan_old_mrc ? formatCurrency(tx.gigalan_old_mrc) : '-'}</p>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}