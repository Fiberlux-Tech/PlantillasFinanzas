// src/components/shared/GlobalHeader.tsx
import { useNavigate, useLocation } from 'react-router-dom';
import { LogOutIcon, ArrowLeftIcon, UploadIcon } from './Icons';
import { useAuth } from '@/contexts/AuthContext';
import { UI_LABELS } from '@/config';

// CORRECTED SalesActions interface
interface SalesActions {
    uploadLabel: string;
    onUpload: () => void;
}

interface GlobalHeaderProps {
    salesActions: SalesActions;
}

// Helper function getPageTitle using centralized constants
const getPageTitle = (pathname: string): string => {
    switch (pathname) {
        case '/sales':
            return UI_LABELS.PAGE_TITLE_SALES;
        case '/finance':
            return UI_LABELS.PAGE_TITLE_FINANCE;
        case '/admin/users':
            return UI_LABELS.PAGE_TITLE_ADMIN_USERS;
        case '/admin/master-data':
            return UI_LABELS.PAGE_TITLE_ADMIN_MASTER_DATA;
        case '/':
        default:
            return UI_LABELS.PAGE_TITLE_MAIN_MENU;
    }
};

export default function GlobalHeader({
    salesActions
}: GlobalHeaderProps) {

    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuth();
    const pathname = location.pathname;

    const buttonStyles = "flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50";
    const primaryButtonStyles = "flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-black rounded-lg shadow-sm hover:bg-gray-800";

    const showSalesActions = pathname === '/sales';
    const showBackButton = pathname !== '/';
    const currentTitle = getPageTitle(pathname);

    return (
        <header className="bg-white shadow-sm h-16 w-full flex-shrink-0">
            <div className="container mx-auto px-8 h-full flex items-center justify-between">

                <div className="flex items-center space-x-4">
                    {showBackButton ? (
                        <button
                            onClick={() => navigate('/')}
                            className={buttonStyles}
                        >
                            <ArrowLeftIcon className="w-5 h-5 mr-2 text-gray-500" />
                            {UI_LABELS.BACK}
                        </button>
                    ) : (
                        <div className="invisible pointer-events-none">
                            <button className={buttonStyles}>
                                <ArrowLeftIcon className="w-5 h-5 mr-2 text-gray-500" />
                                {UI_LABELS.BACK}
                            </button>
                        </div>
                    )}

                    <h1 className="text-3xl font-bold text-gray-800">
                        {currentTitle}
                    </h1>
                </div>

                <div className="flex items-center space-x-2">
                    {showSalesActions && salesActions && (
                        <>

                            <button
                                onClick={salesActions.onUpload}
                                className={primaryButtonStyles}
                            >
                                <UploadIcon />
                                <span>{UI_LABELS.CREATE_TEMPLATE}</span>
                            </button>
                        </>
                    )}

                    <button
                        onClick={logout}
                        className={buttonStyles}
                    >
                        <LogOutIcon className="w-5 h-5 mr-2 text-gray-500" />
                        {UI_LABELS.LOGOUT}
                    </button>
                </div>
            </div>
        </header>
    );
}
