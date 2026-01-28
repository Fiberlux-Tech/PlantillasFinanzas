import React from 'react';

export const NumberInput: React.FC<{
    value: number;
    onChange: (value: number) => void;
    label: string;
    step?: string;
}> = ({ value, onChange, label, step = "0.01" }) => {
    const [localValue, setLocalValue] = React.useState(
        value !== undefined && value !== null ? Number(value).toFixed(2) : ''
    );

    React.useEffect(() => {
        // Sync local state with prop value if they differ numerically
        const parsedLocal = parseFloat(localValue);
        const isNumericallyEqual = !isNaN(parsedLocal) && parsedLocal === value;

        if (!isNumericallyEqual) {
            // Format to 2 decimals when syncing from external prop change (e.g. initial load)
            setLocalValue(value !== undefined && value !== null ? Number(value).toFixed(2) : '');
        }
    }, [value]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = e.target.value;

        // Regex to allow: empty string, digits, digits + dot, digits + dot + 1 or 2 digits
        const regex = /^\d*\.?\d{0,2}$/;

        if (newValue === '' || regex.test(newValue)) {
            setLocalValue(newValue);
            onChange(parseFloat(newValue) || 0);
        }
    };

    const handleBlur = () => {
        const parsed = parseFloat(localValue);
        if (!isNaN(parsed)) {
            setLocalValue(parsed.toFixed(2));
        }
    };

    return (
        <div>
            <p className="text-sm font-medium text-gray-500 mb-1">{label}</p>
            <input
                type="number"
                value={localValue}
                onChange={handleChange}
                onBlur={handleBlur}
                className="w-full text-2xl font-semibold text-gray-900 border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                step={step}
            />
        </div>
    );
};

export const TextInput: React.FC<{
    value: string;
    onChange: (value: string) => void;
    label: string;
    className?: string;
}> = ({ value, onChange, label, className = "col-span-2" }) => (
    <div className={className}>
        <p className="text-sm font-medium text-gray-500 mb-1">{label}</p>
        <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-full text-xl font-semibold text-gray-900 border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
    </div>
);

export const CurrencySelect: React.FC<{
    value: "PEN" | "USD";
    onChange: (value: "PEN" | "USD") => void;
}> = ({ value, onChange }) => (
    <select
        value={value}
        onChange={(e) => onChange(e.target.value as "PEN" | "USD")}
        className="text-base font-medium text-gray-600 ml-1 border border-gray-300 rounded px-1 focus:ring-2 focus:ring-blue-500"
    >
        <option value="PEN">PEN</option>
        <option value="USD">USD</option>
    </select>
);
