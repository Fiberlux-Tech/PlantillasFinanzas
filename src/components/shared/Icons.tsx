// src/components/shared/Icons.tsx
// Thin wrappers around lucide-react for consistent icon API across the app.
import type { LucideProps } from 'lucide-react';
import {
    Clock,
    TrendingUp,
    DollarSign,
    FileText,
    Upload,
    Download,
    Search,
    Calendar,
    X,
    AlertTriangle,
    CheckCircle,
    Pencil,
    Check,
    Plus,
    ChevronDown,
    ChevronUp,
    ChevronRight,
    User,
    LogOut,
    Home,
    ShoppingCart,
    Landmark,
    ArrowLeft,
} from 'lucide-react';
import React from 'react';

interface IconProps {
    className?: string;
    size?: number;
}

function wrap(Icon: React.FC<LucideProps>, defaults?: { size?: number; strokeWidth?: number }) {
    const Wrapped: React.FC<IconProps> = ({ className, size }) => (
        <Icon
            className={className}
            size={size ?? defaults?.size}
            strokeWidth={defaults?.strokeWidth}
        />
    );
    return Wrapped;
}

// 1. KPI / Dashboard Icons
export const ClockIcon = wrap(Clock);
export const TrendUpIcon = wrap(TrendingUp);
export const DollarSignIcon = wrap(DollarSign);
export const FileTextIcon = wrap(FileText);
export const WarningIcon = wrap(AlertTriangle, { size: 20 });
export const CheckCircleIcon = wrap(CheckCircle, { size: 20 });

// 2. Action Icons
export const UploadIcon = wrap(Upload, { size: 20 });
export const ExportIcon = wrap(Download, { size: 20 });
export const SearchIcon = wrap(Search, { size: 18 });
export const CalendarIcon = wrap(Calendar, { size: 18 });
export const CloseIcon = wrap(X);
export const FileUploadIcon = wrap(Upload, { size: 48, strokeWidth: 1.5 });
export const PlusIcon = wrap(Plus);

// 3. Chevrons
export const ChevronDownIcon = wrap(ChevronDown, { size: 16 });
export const ChevronUpIcon = wrap(ChevronUp, { size: 16 });
export const ChevronRightIcon = wrap(ChevronRight, { size: 20 });

// 4. Navigation / Sidebar Icons
export function UserIcon({ className = "w-5 h-5", size }: IconProps) {
    return <User className={className} size={size} />;
}
export function LogOutIcon({ className = "w-5 h-5", size }: IconProps) {
    return <LogOut className={className} size={size} />;
}
export function HomeIcon({ className = "w-5 h-5", size }: IconProps) {
    return <Home className={className} size={size} />;
}
export function SalesIcon({ className = "w-5 h-5", size }: IconProps) {
    return <ShoppingCart className={className} size={size} />;
}
export function FinanceIcon({ className = "w-5 h-5", size }: IconProps) {
    return <Landmark className={className} size={size} />;
}
export function ArrowLeftIcon({ className = "w-5 h-5", size }: IconProps) {
    return <ArrowLeft className={className} size={size} />;
}

// 5. Inline Edit Icons
export const EditPencilIcon = wrap(Pencil, { size: 16 });
export const EditCheckIcon = wrap(Check, { size: 18, strokeWidth: 2.5 });
export const EditXIcon = wrap(X, { size: 18, strokeWidth: 2.5 });
