// src/features/transactions/components/RejectionNoteModal.tsx
import { useState } from 'react';
import { BUTTON_LABELS, VALIDATION_MESSAGES } from '@/config';

interface RejectionNoteModalProps {
    isOpen: boolean;
    onConfirm: (note: string) => void;
    onCancel: () => void;
}

export function RejectionNoteModal({ isOpen, onConfirm, onCancel }: RejectionNoteModalProps) {
    const [note, setNote] = useState('');
    const maxLength = VALIDATION_MESSAGES.REJECTION_NOTE_MAX_LENGTH;

    if (!isOpen) return null;

    const handleConfirm = () => {
        onConfirm(note.trim());
        setNote('');
    };

    const handleCancel = () => {
        setNote('');
        onCancel();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black bg-opacity-50"
                onClick={handleCancel}
            />

            {/* Modal */}
            <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
                {/* Header */}
                <div className="px-6 py-4 border-b">
                    <h3 className="text-lg font-semibold text-gray-900">
                        Motivo del Rechazo
                    </h3>
                </div>

                {/* Body */}
                <div className="px-6 py-4">
                    <p className="text-sm text-gray-600 mb-3">
                        Por favor, ingresa el motivo por el cual rechazas esta transacción:
                    </p>
                    <textarea
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        maxLength={maxLength}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none"
                        placeholder="Ejemplo: Los márgenes de ganancia no cumplen con los requisitos mínimos."
                        autoFocus
                    />
                    <div className="text-right text-xs text-gray-500 mt-1">
                        {note.length}/{maxLength} caracteres
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t flex justify-end space-x-3">
                    <button
                        onClick={handleCancel}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                        {BUTTON_LABELS.CANCELAR}
                    </button>
                    <button
                        onClick={handleConfirm}
                        className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700"
                    >
                        {BUTTON_LABELS.RECHAZAR}
                    </button>
                </div>
            </div>
        </div>
    );
}
