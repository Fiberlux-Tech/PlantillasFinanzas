import React from 'react';
import { Eye, Pencil, Trash2 } from 'lucide-react';

interface TableActionIconsProps {
  onView?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}

export const TableActionIcons: React.FC<TableActionIconsProps> = ({
  onView,
  onEdit,
  onDelete
}) => {
  return (
    <div className="flex items-center justify-center gap-2">
      <button
        onClick={onView}
        className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
        aria-label="View details"
        title="Ver detalle"
      >
        <Eye className="w-4 h-4" />
      </button>
      {onEdit && (
        <button
          onClick={onEdit}
          className="p-1 text-gray-400 hover:text-green-600 transition-colors"
          aria-label="Edit"
          title="Editar"
        >
          <Pencil className="w-4 h-4" />
        </button>
      )}
      {onDelete && (
        <button
          onClick={onDelete}
          className="p-1 text-gray-400 hover:text-red-600 transition-colors"
          aria-label="Delete"
          title="Eliminar"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
