import React, { useState, useEffect } from 'react';
import type { FixedCost } from '@/types';
import { formatCurrency } from '@/lib/formatters';
import { useTransactionPreview } from '@/contexts/TransactionPreviewContext';
import { convertToPEN, calculateFixedCostTotal } from '@/lib/calculations';
import { X, Save } from 'lucide-react';

interface FixedCostDetailModalProps {
  cost: FixedCost | null;
  isOpen: boolean;
  onClose: () => void;
  isEditMode?: boolean;
  onSave?: (updatedCost: FixedCost) => void;
}

export const FixedCostDetailModal: React.FC<FixedCostDetailModalProps> = ({
  cost,
  isOpen,
  onClose,
  isEditMode = false,
  onSave,
}) => {
  // Local state for edited values
  const [editedValues, setEditedValues] = useState<Partial<FixedCost>>({});
  const [calculatedTotal, setCalculatedTotal] = useState(0);

  // Access tipoCambio from context
  const { baseTransaction } = useTransactionPreview();
  const tipoCambio = baseTransaction.transactions.tipoCambio;

  // Derive effective PEN value from current state
  const effectiveCostoUnitario_pen = convertToPEN(
    editedValues.costoUnitario_original ?? cost?.costoUnitario_original ?? 0,
    editedValues.costoUnitario_currency ?? cost?.costoUnitario_currency ?? "PEN",
    tipoCambio
  );

  // Initialize edited values when cost changes
  useEffect(() => {
    if (cost && isEditMode) {
      setEditedValues({
        cantidad: cost.cantidad,
        costoUnitario_original: cost.costoUnitario_original,
        costoUnitario_currency: cost.costoUnitario_currency,
        costoUnitario_pen: cost.costoUnitario_pen,
        ubicacion: cost.ubicacion,
        periodo_inicio: cost.periodo_inicio,
        duracion_meses: cost.duracion_meses,
      });
      setCalculatedTotal(cost.total_pen || 0);
    }
  }, [cost, isEditMode]);

  // Real-time calculation with 300ms debounce
  useEffect(() => {
    if (!isEditMode || !cost) return;

    const timer = setTimeout(() => {
      const cantidad = editedValues.cantidad ?? cost.cantidad ?? 0;

      const total = calculateFixedCostTotal(cantidad, effectiveCostoUnitario_pen);
      setCalculatedTotal(total);
    }, 300);

    return () => clearTimeout(timer);
  }, [
    editedValues.cantidad,
    editedValues.costoUnitario_original,
    editedValues.costoUnitario_currency,
    effectiveCostoUnitario_pen,
    tipoCambio,
    cost,
    isEditMode,
  ]);

  const getCurrentValue = (field: keyof FixedCost) => {
    if (isEditMode && editedValues[field] !== undefined) {
      return editedValues[field];
    }
    return cost?.[field];
  };

  const handleFieldChange = (field: keyof FixedCost, value: any) => {
    setEditedValues(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    if (!cost || !onSave) return;

    // Calculate final PEN value explicitly before saving
    const finalCostoUnitario_pen = convertToPEN(
      editedValues.costoUnitario_original ?? cost.costoUnitario_original ?? 0,
      editedValues.costoUnitario_currency ?? cost.costoUnitario_currency ?? "PEN",
      tipoCambio
    );

    const updatedCost: FixedCost = {
      ...cost,
      ...editedValues,
      costoUnitario_pen: finalCostoUnitario_pen,
      total_pen: calculatedTotal,
    };

    onSave(updatedCost);
    onClose();
  };

  if (!isOpen || !cost) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/20 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        {/* Header Section */}
        <div className="bg-gray-50/50 p-5 rounded-t-2xl">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">
                {cost.categoria || 'INVERSIÓN'}
              </p>
              <h2 className="text-xl font-extrabold text-gray-900">
                {cost.tipo_servicio}
              </h2>
              <p className="text-xs text-gray-500 mt-1">Ticket: {cost.ticket}</p>
            </div>
            <div className="flex items-start gap-4">
              {cost.ubicacion && (
                <div className="text-right">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">
                    UBICACIÓN
                  </p>
                  <p className="text-xs font-medium text-gray-600">{cost.ubicacion}</p>
                </div>
              )}
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Total Cost Card */}
          <div className="bg-red-50 border border-red-100 rounded-xl p-4 mb-8">
            <p className="text-[10px] font-bold uppercase tracking-wider text-red-600 mb-2">
              COSTO TOTAL (PEN)
            </p>
            <div className="flex items-baseline">
              <span className="text-2xl font-bold text-red-900">
                {formatCurrency(isEditMode ? calculatedTotal : cost.total_pen || (cost.costoUnitario_pen * cost.cantidad))}
              </span>
              <span className="text-[11px] font-normal text-red-500 ml-1">PEN</span>
            </div>
          </div>

          {/* Detail Grid Section */}
          <div className="bg-gray-50 border border-gray-100 rounded-xl p-5">
            <div className="flex flex-col gap-y-5">
              {/* Cantidad and Costo Unitario Row */}
              {isEditMode ? (
                <div className="flex gap-4">
                  {/* Cantidad - narrower */}
                  <div className="w-24">
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Cantidad</p>
                    <input
                      type="number"
                      value={getCurrentValue('cantidad') as number}
                      onChange={(e) => handleFieldChange('cantidad', parseFloat(e.target.value) || 0)}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      step="1"
                    />
                  </div>

                  {/* Costo Unitario - takes remaining space */}
                  <div className="flex-1">
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Costo Unitario</p>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={getCurrentValue('costoUnitario_original') as number}
                        onChange={(e) => handleFieldChange('costoUnitario_original', parseFloat(e.target.value) || 0)}
                        className="flex-1 bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                        step="0.01"
                      />
                      <select
                        value={getCurrentValue('costoUnitario_currency') as string}
                        onChange={(e) => handleFieldChange('costoUnitario_currency', e.target.value)}
                        className="bg-white border border-gray-300 rounded-lg px-2 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      >
                        <option value="PEN">PEN</option>
                        <option value="USD">USD</option>
                      </select>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                  <div>
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Cantidad</p>
                    <p className="text-sm font-bold text-gray-800">{cost.cantidad || '-'}</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Costo Unitario</p>
                    <p className="text-sm font-bold text-gray-800">
                      {formatCurrency(cost.costoUnitario_original) || '-'}
                      {cost.costoUnitario_original !== null && cost.costoUnitario_original !== undefined && cost.costoUnitario_original !== 0 && (
                        <span className="text-xs font-medium text-gray-600 ml-1">{cost.costoUnitario_currency || 'USD'}</span>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* Separator */}
              {isEditMode && <div className="border-t border-gray-200/60"></div>}

              {/* Periodo Inicio & Duración (Edit Mode Only) */}
              {isEditMode && (
                <div className="flex gap-4">
                  <div className="flex-1">
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Inicio (Mes)</p>
                    <input
                      type="number"
                      value={getCurrentValue('periodo_inicio') as number}
                      onChange={(e) => handleFieldChange('periodo_inicio', parseInt(e.target.value) || 0)}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      step="1"
                    />
                  </div>
                  <div className="flex-1">
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Duración (Meses)</p>
                    <input
                      type="number"
                      value={getCurrentValue('duracion_meses') as number}
                      onChange={(e) => handleFieldChange('duracion_meses', parseInt(e.target.value) || 0)}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      step="1"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Section */}
        <div className="bg-gray-50/50 p-4 rounded-b-2xl flex justify-end gap-3">
          {isEditMode ? (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-semibold transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-colors flex items-center gap-2"
              >
                <Save size={16} />
                Guardar Cambios
              </button>
            </>
          ) : (
            <button
              onClick={onClose}
              className="px-6 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-50 transition-colors"
            >
              Cerrar
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
