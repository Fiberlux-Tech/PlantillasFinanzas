// src/features/finance/components/FinanceStatsGrid.tsx
import StatsCard from '@/features/transactions/components/StatsCard';
import {
    TrendUpIcon,
    DollarSignIcon,
    FileTextIcon,
} from '@/components/shared/Icons';
import { FINANCE_STATS_LABELS } from '@/config';
import { formatCurrency } from '@/lib/formatters';

// 1. Define the props interface for 'stats'
interface StatsGridProps {
    stats: {
        pendingMrc: number;
        pendingCount: number;
        pendingComisiones: number;
        avgGrossMargin: number;
    };
}

// 2. Apply the props interface
export function FinanceStatsGrid({ stats }: StatsGridProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatsCard
                title={FINANCE_STATS_LABELS.VALOR_TOTAL_APROBADO}
                value={formatCurrency(stats.pendingMrc)}
                icon={<DollarSignIcon />}
                iconBgColor="bg-green-100"
            />
            <StatsCard
                title={FINANCE_STATS_LABELS.MARGEN_PROMEDIO}
                value={`${(stats.avgGrossMargin * 100).toFixed(2)}%`}
                icon={<TrendUpIcon />}
                iconBgColor="bg-blue-100"
            />
            <StatsCard
                title={FINANCE_STATS_LABELS.HIGH_RISK_DEALS}
                value={stats.pendingCount}
                icon={<FileTextIcon />}
                iconBgColor="bg-yellow-100"
            />
            <StatsCard
                title={FINANCE_STATS_LABELS.DEALS_THIS_MONTH}
                value={formatCurrency(stats.pendingComisiones)}
                icon={<DollarSignIcon />}
                iconBgColor="bg-purple-100"
            />
        </div>
    );
}
