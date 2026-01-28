// src/features/transactions/hooks/useKpisQuery.ts
import { useQuery } from '@tanstack/react-query';
import { getAllKpis, type KpiData } from '../services/kpi.service';

export function useKpisQuery() {
    return useQuery<KpiData, Error>({
        queryKey: ['kpis'],
        queryFn: async () => {
            const result = await getAllKpis();
            if (!result.success || !result.data) {
                throw new Error(result.error || 'Failed to fetch KPIs');
            }
            return result.data;
        },
    });
}
