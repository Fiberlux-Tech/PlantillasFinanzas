// src/components/shared/GlobalHeader.tsx
import { useNavigate, useLocation } from 'react-router-dom';
import { LogOutIcon, ArrowLeftIcon, UploadIcon } from './Icons';
import { useAuth } from '@/contexts/AuthContext';
import { UI_LABELS } from '@/config';
import { getPageTitle } from '@/lib/getPageTitle';
import { Button } from '@/components/ui/button';

// CORRECTED SalesActions interface
interface SalesActions {
    uploadLabel: string;
    onUpload: () => void;
}

interface GlobalHeaderProps {
    salesActions: SalesActions;
}

export default function GlobalHeader({
    salesActions
}: GlobalHeaderProps) {

    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuth();
    const pathname = location.pathname;

    const showSalesActions = pathname === '/sales';
    const showBackButton = pathname !== '/';
    const currentTitle = getPageTitle(pathname);

    return (
        <header className="bg-white shadow-sm h-16 w-full flex-shrink-0">
            <div className="container mx-auto px-8 h-full flex items-center justify-between">

                <div className="flex items-center space-x-4">
                    {showBackButton ? (
                        <Button
                            variant="outline"
                            onClick={() => navigate('/')}
                            className="flex items-center shadow-sm"
                        >
                            <ArrowLeftIcon className="w-5 h-5 mr-2 text-gray-500" />
                            {UI_LABELS.BACK}
                        </Button>
                    ) : (
                        <div className="invisible pointer-events-none">
                            <Button variant="outline" className="flex items-center shadow-sm">
                                <ArrowLeftIcon className="w-5 h-5 mr-2 text-gray-500" />
                                {UI_LABELS.BACK}
                            </Button>
                        </div>
                    )}

                    <h1 className="text-3xl font-bold text-gray-800">
                        {currentTitle}
                    </h1>
                </div>

                <div className="flex items-center space-x-2">
                    {showSalesActions && salesActions && (
                        <>
                            <Button
                                onClick={salesActions.onUpload}
                                className="flex items-center space-x-2 shadow-sm"
                            >
                                <UploadIcon />
                                <span>{UI_LABELS.CREATE_TEMPLATE}</span>
                            </Button>
                        </>
                    )}

                    <Button
                        variant="outline"
                        onClick={logout}
                        className="flex items-center shadow-sm"
                    >
                        <LogOutIcon className="w-5 h-5 mr-2 text-gray-500" />
                        {UI_LABELS.LOGOUT}
                    </Button>
                </div>
            </div>
        </header>
    );
}
