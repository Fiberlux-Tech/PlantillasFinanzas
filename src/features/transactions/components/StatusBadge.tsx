// src/components/shared/StatusBadge.tsx
import { Badge, badgeVariants } from '@/components/ui/badge';
import type { VariantProps } from 'class-variance-authority'; // 1. Import VariantProps
import { TRANSACTION_STATUS, type TransactionStatus } from '@/config';

// 2. Define the component props
interface StatusBadgeProps {
    status: TransactionStatus | string; // Allow other strings
}

function StatusBadge({ status }: StatusBadgeProps) {
    // 3. Strongly type the 'variant' variable
    let variant: VariantProps<typeof badgeVariants>['variant'] = 'categoryUser';
    
    switch (status) {
        case TRANSACTION_STATUS.PENDING:
            variant = 'statusPending';
            break;
        case TRANSACTION_STATUS.APPROVED:
            variant = 'statusApproved';
            break;
        case TRANSACTION_STATUS.REJECTED:
            variant = 'statusRejected';
            break;
        default:
            variant = 'categoryUser';
    }

    return <Badge variant={variant}>{status}</Badge>;
}

export default StatusBadge;