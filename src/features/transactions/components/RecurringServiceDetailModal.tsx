import React, { useState, useEffect } from 'react';
import type { RecurringService } from '@/types';
import { formatCurrency } from '@/lib/formatters';
import { useTransactionPreview } from '@/contexts/TransactionPreviewContext';
import { convertToPEN, calculateRecurringServiceTotals } from '@/lib/calculations';
import { X, Save } from 'lucide-react';

interface RecurringServiceDetailModalProps {
  service: RecurringService | null;
  isOpen: boolean;
  onClose: () => void;
  isEditMode?: boolean;
  onSave?: (updatedService: RecurringService) => void;
}

export const RecurringServiceDetailModal: React.FC<RecurringServiceDetailModalProps> = ({
  service,
  isOpen,
  onClose,
  isEditMode = false,
  onSave,
}) => {
  // Local state for edited values
  const [editedValues, setEditedValues] = useState<Partial<RecurringService>>({});
  const [calculatedIngreso, setCalculatedIngreso] = useState(0);
  const [calculatedEgreso, setCalculatedEgreso] = useState(0);

  // Access tipoCambio from context
  const { baseTransaction } = useTransactionPreview();
  const tipoCambio = baseTransaction.transactions.tipoCambio;

  // Derive effective PEN values from current state
  const effectiveP_pen = convertToPEN(
    editedValues.P_original ?? service?.P_original ?? 0,
    editedValues.P_currency ?? service?.P_currency ?? "PEN",
    tipoCambio
  );

  const effectiveCU1_pen = convertToPEN(
    editedValues.CU1_original ?? service?.CU1_original ?? 0,
    editedValues.CU_currency ?? service?.CU_currency ?? "PEN",
    tipoCambio
  );

  const effectiveCU2_pen = convertToPEN(
    editedValues.CU2_original ?? service?.CU2_original ?? 0,
    editedValues.CU_currency ?? service?.CU_currency ?? "PEN",
    tipoCambio
  );

  // Initialize edited values when service changes
  useEffect(() => {
    if (service && isEditMode) {
      setEditedValues({
        Q: service.Q,
        P_original: service.P_original,
        P_currency: service.P_currency,
        P_pen: service.P_pen,
        CU1_original: service.CU1_original,
        CU2_original: service.CU2_original,
        CU_currency: service.CU_currency,
        CU1_pen: service.CU1_pen,
        CU2_pen: service.CU2_pen,
        proveedor: service.proveedor,
      });
      setCalculatedIngreso(service.ingreso_pen);
      setCalculatedEgreso(service.egreso_pen);
    }
  }, [service, isEditMode]);

  // Real-time calculation with 300ms debounce
  useEffect(() => {
    if (!isEditMode || !service) return;

    const timer = setTimeout(() => {
      const Q = editedValues.Q ?? service.Q ?? 0;

      const { ingreso_pen, egreso_pen } = calculateRecurringServiceTotals(
        Q,
        effectiveP_pen,
        effectiveCU1_pen,
        effectiveCU2_pen
      );

      setCalculatedIngreso(ingreso_pen);
      setCalculatedEgreso(egreso_pen);
    }, 300);

    return () => clearTimeout(timer);
  }, [
    editedValues.Q,
    editedValues.P_original,
    editedValues.P_currency,
    editedValues.CU1_original,
    editedValues.CU2_original,
    editedValues.CU_currency,
    effectiveP_pen,
    effectiveCU1_pen,
    effectiveCU2_pen,
    tipoCambio,
    service,
    isEditMode,
  ]);

  const getCurrentValue = (field: keyof RecurringService) => {
    if (isEditMode && editedValues[field] !== undefined) {
      return editedValues[field];
    }
    return service?.[field];
  };

  const handleFieldChange = (field: keyof RecurringService, value: any) => {
    setEditedValues(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    if (!service || !onSave) return;

    // Calculate final PEN values explicitly before saving
    const finalP_pen = convertToPEN(
      editedValues.P_original ?? service.P_original ?? 0,
      editedValues.P_currency ?? service.P_currency ?? "PEN",
      tipoCambio
    );

    const finalCU1_pen = convertToPEN(
      editedValues.CU1_original ?? service.CU1_original ?? 0,
      editedValues.CU_currency ?? service.CU_currency ?? "PEN",
      tipoCambio
    );

    const finalCU2_pen = convertToPEN(
      editedValues.CU2_original ?? service.CU2_original ?? 0,
      editedValues.CU_currency ?? service.CU_currency ?? "PEN",
      tipoCambio
    );

    const updatedService: RecurringService = {
      ...service,
      ...editedValues,
      P_pen: finalP_pen,
      CU1_pen: finalCU1_pen,
      CU2_pen: finalCU2_pen,
      ingreso_pen: calculatedIngreso,
      egreso_pen: calculatedEgreso,
    };

    onSave(updatedService);
    onClose();
  };

  if (!isOpen || !service) return null;

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
                SERVICIO
              </p>
              <h2 className="text-xl font-extrabold text-gray-900">
                {service.tipo_servicio}
              </h2>
            </div>
            <div className="flex items-start gap-4">
              {service.ubicacion && (
                <div className="text-right">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">
                    UBICACIÓN
                  </p>
                  <p className="text-xs font-medium text-gray-600">{service.ubicacion}</p>
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
          {/* KPI Cards Section */}
          <div className="grid grid-cols-2 gap-4 mb-8">
            {/* Ingreso Card */}
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-blue-600 mb-2">
                INGRESO MENSUAL (PEN)
              </p>
              <div className="flex items-baseline">
                <span className="text-2xl font-bold text-blue-900">
                  {formatCurrency(isEditMode ? calculatedIngreso : service.ingreso_pen)}
                </span>
                <span className="text-[11px] font-normal text-blue-500 ml-1">PEN</span>
              </div>
            </div>

            {/* Costo Card */}
            <div className="bg-red-50 border border-red-100 rounded-xl p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-red-600 mb-2">
                COSTO MENSUAL (PEN)
              </p>
              <div className="flex items-baseline">
                <span className="text-2xl font-bold text-red-900">
                  {formatCurrency(isEditMode ? calculatedEgreso : service.egreso_pen)}
                </span>
                <span className="text-[11px] font-normal text-red-500 ml-1">PEN</span>
              </div>
            </div>
          </div>

          {/* Detail Grid Section */}
          <div className="bg-gray-50 border border-gray-100 rounded-xl p-5">
            <div className="flex flex-col gap-y-5">
              {/* Cantidad and Precio Unitario Row */}
              {isEditMode ? (
                <div className="flex gap-4">
                  {/* Cantidad - narrower */}
                  <div className="w-24">
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Cantidad</p>
                    <input
                      type="number"
                      value={getCurrentValue('Q') as number}
                      onChange={(e) => handleFieldChange('Q', parseFloat(e.target.value) || 0)}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      step="1"
                    />
                  </div>

                  {/* Precio Unitario - takes remaining space */}
                  <div className="flex-1">
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Precio Unitario</p>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={getCurrentValue('P_original') as number}
                        onChange={(e) => handleFieldChange('P_original', parseFloat(e.target.value) || 0)}
                        className="flex-1 bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                        step="0.01"
                      />
                      <select
                        value={getCurrentValue('P_currency') as string}
                        onChange={(e) => handleFieldChange('P_currency', e.target.value)}
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
                    <p className="text-sm font-bold text-gray-800">{service.Q || '-'}</p>
                  </div>
                  <div>
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Precio Unitario</p>
                    <p className="text-sm font-bold text-gray-800">
                      {formatCurrency(service.P_original) || '-'}
                      {service.P_original !== null && service.P_original !== undefined && service.P_original !== 0 && (
                        <span className="text-xs font-medium text-gray-600 ml-1">{service.P_currency || 'PEN'}</span>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* Separator */}
              <div className="border-t border-gray-200/60"></div>

              {/* Cost Fields Row */}
              {isEditMode ? (
                <div className="flex gap-4">
                  {/* Costo Unitario */}
                  <div className="flex-1">
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Costo Unitario</p>
                    <input
                      type="number"
                      value={getCurrentValue('CU1_original') as number}
                      onChange={(e) => handleFieldChange('CU1_original', parseFloat(e.target.value) || 0)}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      step="0.01"
                    />
                  </div>

                  {/* Costo Unit. (Transporte) */}
                  <div className="flex-1">
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Costo Unit. (Transporte)</p>
                    <input
                      type="number"
                      value={getCurrentValue('CU2_original') as number}
                      onChange={(e) => handleFieldChange('CU2_original', parseFloat(e.target.value) || 0)}
                      className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                      step="0.01"
                    />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-x-6 gap-y-4">
                  <div>
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Costo Unitario</p>
                    <p className="text-sm font-bold text-gray-800">
                      {formatCurrency(service.CU1_original) || '-'}
                      {service.CU1_original !== null && service.CU1_original !== undefined && service.CU1_original !== 0 && (
                        <span className="text-xs font-medium text-gray-600 ml-1">{service.CU_currency || 'USD'}</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] font-medium text-gray-400 mb-1.5">Costo Unit. (Transporte)</p>
                    <p className="text-sm font-bold text-gray-800">
                      {formatCurrency(service.CU2_original) || '-'}
                      {service.CU2_original !== null && service.CU2_original !== undefined && service.CU2_original !== 0 && (
                        <span className="text-xs font-medium text-gray-600 ml-1">{service.CU_currency || 'USD'}</span>
                      )}
                    </p>
                  </div>
                </div>
              )}

              {/* Currency Selector for Costs (Edit Mode Only) */}
              {isEditMode && (
                <div>
                  <p className="text-[11px] font-medium text-gray-400 mb-1.5">Moneda de Costos</p>
                  <select
                    value={getCurrentValue('CU_currency') as string}
                    onChange={(e) => handleFieldChange('CU_currency', e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  >
                    <option value="PEN">PEN</option>
                    <option value="USD">USD</option>
                  </select>
                </div>
              )}

              {/* Separator */}
              <div className="border-t border-gray-200/60"></div>

              {/* Proveedor */}
              <div>
                <p className="text-[11px] font-medium text-gray-400 mb-1.5">Proveedor</p>
                {isEditMode ? (
                  <input
                    type="text"
                    value={getCurrentValue('proveedor') as string}
                    onChange={(e) => handleFieldChange('proveedor', e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                  />
                ) : (
                  <p className="text-sm font-bold text-gray-800">{service.proveedor || '-'}</p>
                )}
              </div>
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
