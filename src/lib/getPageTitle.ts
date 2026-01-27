import { UI_LABELS } from '@/config';

export const getPageTitle = (pathname: string): string => {
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
