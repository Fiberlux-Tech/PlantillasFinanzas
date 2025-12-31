// src/features/landing/LandingPage.tsx
import { ModuleCard } from './components/ModuleCard';
import { useAuth } from '@/contexts/AuthContext';
import { USER_ROLES, UI_LABELS } from '@/config';

interface LandingPageProps {
}

export default function LandingPage({}: LandingPageProps) {
    const { user } = useAuth();

    // Add a check in case user is somehow null
    if (!user) {
        return <div className="text-center py-12">{UI_LABELS.LOADING_USER_DATA}</div>;
    }

    const isSales = user.role === USER_ROLES.SALES || user.role === USER_ROLES.ADMIN;
    const isFinance = user.role === USER_ROLES.FINANCE || user.role === USER_ROLES.ADMIN;
    const isAdmin = user.role === USER_ROLES.ADMIN;
    const isMasterData = true;

    const availableModules = [
        { id: 'sales', name: UI_LABELS.MODULE_SALES_NAME, icon: '📝', description: UI_LABELS.MODULE_SALES_DESC, available: isSales, path: '/sales' },
        { id: 'finance', name: UI_LABELS.MODULE_FINANCE_NAME, icon: '📊', description: UI_LABELS.MODULE_FINANCE_DESC, available: isFinance, path: '/finance' },
        { id: 'admin-management', name: UI_LABELS.MODULE_ADMIN_NAME, icon: '🔒', description: UI_LABELS.MODULE_ADMIN_DESC, available: isAdmin, path: '/admin/users' },
        { id: 'variable-master', name: UI_LABELS.MODULE_MASTER_DATA_NAME, icon: '⚙️', description: UI_LABELS.MODULE_MASTER_DATA_DESC, available: isMasterData, path: '/admin/master-data' }
    ].filter(module => module.available);

    return (
        <div>
            <div className="container mx-auto px-8 py-12">
                {availableModules.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {availableModules.map((module) => (
                            <ModuleCard
                                key={module.id}
                                module={module}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12">
                       <p className="text-slate-600">{UI_LABELS.NO_MODULES_AVAILABLE.replace('{role}', user.role)}</p>
                    </div>
                )}
            </div>
        </div>
    );
}
