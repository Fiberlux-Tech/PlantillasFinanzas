// src/components/shared/CategoryBadge.tsx
import { Badge, badgeVariants } from '@/components/ui/badge';
import type { VariantProps } from 'class-variance-authority';
import { CATEGORY_VARIANT, CATEGORY_DEFAULT_VARIANT, type Category } from '@/config/enums';

interface CategoryBadgeProps {
    category: string;
}

export function CategoryBadge({ category }: CategoryBadgeProps) {
    const variant = ((category in CATEGORY_VARIANT ? CATEGORY_VARIANT[category as Category] : CATEGORY_DEFAULT_VARIANT)) as VariantProps<typeof badgeVariants>['variant'];
    return <Badge variant={variant}>{category}</Badge>;
}
