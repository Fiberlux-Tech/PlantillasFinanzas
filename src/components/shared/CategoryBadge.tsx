// src/components/shared/CategoryBadge.tsx
import { Badge, badgeVariants } from '@/components/ui/badge';
import type { VariantProps } from 'class-variance-authority';
import { CATEGORY_VARIANT, CATEGORY_DEFAULT_VARIANT } from '@/config/enums';

interface CategoryBadgeProps {
    category: string;
}

export function CategoryBadge({ category }: CategoryBadgeProps) {
    const variant = (CATEGORY_VARIANT[category] ?? CATEGORY_DEFAULT_VARIANT) as VariantProps<typeof badgeVariants>['variant'];
    return <Badge variant={variant}>{category}</Badge>;
}
