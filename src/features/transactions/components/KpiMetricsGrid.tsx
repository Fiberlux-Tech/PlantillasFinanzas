// src/features/transactions/components/KpiMetricsGrid.tsx
import KpiCard from './KpiCard';
// REMOVED: EditableKpiCard is no longer needed here
import { formatCurrency } from '@/lib/formatters';
import { useTransactionPreview } from '@/contexts/TransactionPreviewContext';
import { UI_LABELS, CURRENCIES } from '@/config'; 

// --- REMOVED PROPS INTERFACE ---

export function KpiMetricsGrid() {

    const {
        baseTransaction,
        draftState, 
    } = useTransactionPreview();

    const { liveKpis } = draftState; 
    const tx = baseTransaction.transactions;
    const kpiData = liveKpis || tx;

    // Filtered/Ordered list of KpiCard elements (Point 4)
    const kpiCards = [
        // 1. INGRESOS TOTALES
        <KpiCard key="totalRevenue" title={UI_LABELS.INGRESOS_TOTALES} value={formatCurrency(kpiData.totalRevenue)} currency={CURRENCIES.PEN} />,
        // 2. GASTOS TOTALES
        <KpiCard key="totalExpense" title={UI_LABELS.GASTOS_TOTALES} value={formatCurrency(kpiData.totalExpense)} currency={CURRENCIES.PEN} isNegative={true} />,
        // 3. UTILIDAD BRUTA
        <KpiCard key="grossMargin" title={UI_LABELS.UTILIDAD_BRUTA} value={formatCurrency(kpiData.grossMargin)} currency={CURRENCIES.PEN} />,
        // 4. MARGEN BRUTO (%)
        <KpiCard key="grossMarginRatio" title={UI_LABELS.MARGEN_BRUTO} value={`${(kpiData.grossMarginRatio * 100)?.toFixed(2)}%`} />,
        // 5. PERIODO DE PAYBACK
        <KpiCard key="payback" title={UI_LABELS.PERIODO_PAYBACK} value={`${kpiData.payback} ${UI_LABELS.MESES}`} />,
        // 6. TIR
        <KpiCard key="TIR" title={UI_LABELS.TIR} value={`${(kpiData.TIR * 100)?.toFixed(2)}%`} />,
        // 7. VAN
        <KpiCard key="VAN" title={UI_LABELS.VAN} value={formatCurrency(kpiData.VAN)} currency={CURRENCIES.PEN} />,
        // 8. COSTO INSTALACION (%)
        <KpiCard key="costoInstalacionRatio" title={UI_LABELS.COSTO_INSTALACION} value={`${(kpiData.costoInstalacionRatio * 100)?.toFixed(2)}%`} />,
    ];

    return (
        <div className="mb-8"> {/* MODIFIED: Increased margin from mb-8 to mb-12 */}
            <h3 className="font-semibold text-gray-800 mb-3 text-lg">{UI_LABELS.KEY_PERFORMANCE_INDICATORS}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {kpiCards}
            </div>
        </div>
    );
}