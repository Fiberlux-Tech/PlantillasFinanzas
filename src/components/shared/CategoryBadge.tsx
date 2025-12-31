// src/components/shared/CategoryBadge.tsx
import { Badge, badgeVariants } from '@/components/ui/badge';
import type { VariantProps } from 'class-variance-authority';

// 1. Define the component props
interface CategoryBadgeProps {
    category: string;
}

// 2. Utility to map category string to the badge variant
const getCategoryVariant = (category: string): VariantProps<typeof badgeVariants>['variant'] => {
    switch (category) {
        case 'Finance':
            return 'categoryFinance';
        case 'Sales':
            return 'categorySales';
        case 'Mayorista':
            return 'categoryMayorista';
        case 'Admin':
            return 'categoryAdmin';
        default:
            return 'categoryUser'; // Fallback
    }
};

export function CategoryBadge({ category }: CategoryBadgeProps) {
    const variant = getCategoryVariant(category);
    return <Badge variant={variant}>{category}</Badge>;
}