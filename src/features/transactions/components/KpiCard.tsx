// src/components/shared/KpiCard.tsx
import type { FC, ReactNode } from 'react'; // FIX: Import types explicitly
import { DISPLAY_VALUES } from '@/config';

// 1. Define the props interface
interface KpiCardProps {
  title: string;
  value: ReactNode; // FIX: Use imported type
  subtext?: string; // Optional prop
  currency?: string; // Optional prop
  isNegative?: boolean; // Optional prop
}

// 2. Apply the interface using React.FC (Functional Component)
const KpiCard: FC<KpiCardProps> = ({ // FIX: Use imported type
    title,
    value,
    subtext,
    currency,
    isNegative = false
}) => {
    const displayValue = value === null || value === undefined ? DISPLAY_VALUES.NOT_AVAILABLE : value;
    
    return (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-500 uppercase tracking-wider">{title}</p>
            
            <div className="flex items-baseline mt-1">
                <p className={`text-2xl font-bold ${isNegative ? 'text-red-600' : 'text-gray-800'}`}>
                    {displayValue}
                </p>
                {currency && (
                    <span className="text-lg font-normal text-gray-400 ml-1.5">
                        ({currency})
                    </span>
                )}
            </div>
            
            <p className="text-xs text-gray-400 mt-1">{subtext || '\u00A0'}</p>
        </div>
    );
}

export default KpiCard;