import React from 'react';
import { Eye, Pencil, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

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
      <Button
        variant="ghost"
        size="icon"
        onClick={onView}
        className={cn("text-gray-400 hover:text-blue-600")}
        aria-label="View details"
        title="Ver detalle"
      >
        <Eye className="w-4 h-4" />
      </Button>
      {onEdit && (
        <Button
          variant="ghost"
          size="icon"
          onClick={onEdit}
          className={cn("text-gray-400 hover:text-green-600")}
          aria-label="Edit"
          title="Editar"
        >
          <Pencil className="w-4 h-4" />
        </Button>
      )}
      {onDelete && (
        <Button
          variant="ghost"
          size="icon"
          onClick={onDelete}
          className={cn("text-gray-400 hover:text-red-600")}
          aria-label="Delete"
          title="Eliminar"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      )}
    </div>
  );
};
