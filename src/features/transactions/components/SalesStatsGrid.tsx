// src/features/sales/components/SalesStatsGrid.tsx
import StatsCard from './StatsCard';
import {
    TrendUpIcon,
    DollarSignIcon,
    FileTextIcon,
} from '../../../components/shared/Icons';
import { SALES_STATS_LABELS } from '@/config';
import { formatCurrency } from '@/lib/formatters';

// 1. Define the props interface for 'stats'
interface SalesStatsGridProps {
    stats: {
        pendingApprovals: number;
        pendingMrc: number;
        pendingComisiones: number;
        avgGrossMargin: number;
    };
}

// 2. Apply the props interface
export function SalesStatsGrid({ stats }: SalesStatsGridProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatsCard
                title={SALES_STATS_LABELS.PENDING_APPROVALS}
                value={stats.pendingApprovals}
                icon={<FileTextIcon />}
                iconBgColor="bg-yellow-100"
            />
            <StatsCard
                title={SALES_STATS_LABELS.PENDING_MRC}
                value={formatCurrency(stats.pendingMrc)}
                icon={<DollarSignIcon />}
                iconBgColor="bg-green-100"
            />
            <StatsCard
                title={SALES_STATS_LABELS.PENDING_COMISIONES}
                value={formatCurrency(stats.pendingComisiones)}
                icon={<DollarSignIcon />}
                iconBgColor="bg-blue-100"
            />
            <StatsCard
                title={SALES_STATS_LABELS.AVG_GROSS_MARGIN}
                value={`${(stats.avgGrossMargin * 100).toFixed(2)}%`}
                icon={<TrendUpIcon />}
                iconBgColor="bg-purple-100"
            />
        </div>
    );
}
