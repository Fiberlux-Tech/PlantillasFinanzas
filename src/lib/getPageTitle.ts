import { UI_LABELS } from '@/config';

export const getPageTitle = (pathname: string): string => {
    switch (pathname) {
        case '/dashboard':
            return UI_LABELS.PAGE_TITLE_DASHBOARD;
        case '/admin/users':
            return UI_LABELS.PAGE_TITLE_ADMIN_USERS;
        case '/admin/master-data':
            return UI_LABELS.PAGE_TITLE_ADMIN_MASTER_DATA;
        case '/':
        default:
            return UI_LABELS.PAGE_TITLE_MAIN_MENU;
    }
};
