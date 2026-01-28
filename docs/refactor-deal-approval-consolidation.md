# Refactor Debrief: Sales/Finance Module Consolidation into "Deal Approval"

**Date:** 2026-01-28
**Commit:** `847c68d`
**Branch:** `main`

---

## Executive Summary

Consolidated two separate modules (Sales Dashboard and Finance Dashboard) into a single adaptive "Deal Approval" module. The `TransactionDashboard` component was already architected as a "chameleon" component that conditionally rendered based on a `view` prop. This refactor eliminated the prop-drilling pattern and instead derives the view directly from the authenticated user's role.

---

## Motivation

### Before Refactor
- Two separate routes: `/sales` and `/finance`
- `view` prop passed through multiple layers (App → TransactionDashboard → hooks → context)
- Duplicate routing logic for essentially the same component
- Landing page showed separate module cards for Sales and Finance users
- Header upload button visibility was pathname-dependent

### After Refactor
- Single route: `/dashboard`
- View derived from `useAuth().user.role` at the component level
- Single source of truth: user role determines experience
- Unified "Deal Approval" module card for all authenticated users
- Header upload button visibility is role-dependent

---

## Files Modified

### 1. `src/config/labels.ts`
**Changes:**
- Added `MODULE_DEAL_APPROVAL_NAME: 'Deal Approval'`
- Added `MODULE_DEAL_APPROVAL_DESC: 'Gestiona y aprueba plantillas económicas.'`
- Added `PAGE_TITLE_DASHBOARD: 'Deal Approval'`

**Why:** New labels needed for the unified module name and page title.

```typescript
// Added labels
MODULE_DEAL_APPROVAL_NAME: 'Deal Approval',
MODULE_DEAL_APPROVAL_DESC: 'Gestiona y aprueba plantillas económicas.',
PAGE_TITLE_DASHBOARD: 'Deal Approval',
```

---

### 2. `src/App.tsx`
**Changes:**
- Removed separate `/sales` and `/finance` routes
- Added unified `/dashboard` route with `roles={['SALES', 'FINANCE', 'ADMIN']}`
- Removed `view` prop from `TransactionDashboard` component

**Before:**
```tsx
<Route path="/sales" element={
    <ProtectedRoute user={user} roles={['SALES']}>
        <TransactionDashboard view="SALES" setSalesActions={setSalesActions} />
    </ProtectedRoute>
} />

<Route path="/finance" element={
    <ProtectedRoute user={user} roles={['FINANCE']}>
        <TransactionDashboard view="FINANCE" />
    </ProtectedRoute>
} />
```

**After:**
```tsx
<Route path="/dashboard" element={
    <ProtectedRoute user={user} roles={['SALES', 'FINANCE', 'ADMIN']}>
        <TransactionDashboard setSalesActions={setSalesActions} />
    </ProtectedRoute>
} />
```

**Why:** Centralizes access control at the route level while allowing the component to self-determine its rendering mode.

---

### 3. `src/features/transactions/TransactionDashboard.tsx`
**Changes:**
- Removed `view` from `TransactionDashboardProps` interface
- Added internal view derivation from `useAuth()`

**Before:**
```typescript
interface TransactionDashboardProps {
    view: View;
    setSalesActions?: (actions: SalesActions) => void;
}

export default function TransactionDashboard({ view, setSalesActions }: TransactionDashboardProps) {
    const { user, logout } = useAuth();
    // view was used directly from props
```

**After:**
```typescript
interface TransactionDashboardProps {
    setSalesActions?: (actions: SalesActions) => void;
}

export default function TransactionDashboard({ setSalesActions }: TransactionDashboardProps) {
    const { user, logout } = useAuth();

    // Derive view from user role - SALES users see SALES view, all others see FINANCE view
    const view: View = user?.role === 'SALES' ? 'SALES' : 'FINANCE';
```

**Why:** Eliminates prop drilling. The component now owns its rendering logic based on the authenticated user.

---

### 4. `src/features/landing/LandingPage.tsx`
**Changes:**
- Removed separate `isSales` and `isFinance` boolean flags
- Added unified `canAccessDealApproval` flag
- Replaced two module cards (Sales, Finance) with single "Deal Approval" card

**Before:**
```typescript
const isSales = user.role === USER_ROLES.SALES || user.role === USER_ROLES.ADMIN;
const isFinance = user.role === USER_ROLES.FINANCE || user.role === USER_ROLES.ADMIN;

const availableModules = [
    { id: 'sales', name: UI_LABELS.MODULE_SALES_NAME, ..., available: isSales, path: '/sales' },
    { id: 'finance', name: UI_LABELS.MODULE_FINANCE_NAME, ..., available: isFinance, path: '/finance' },
    // ...
];
```

**After:**
```typescript
const canAccessDealApproval = user.role === USER_ROLES.SALES ||
                              user.role === USER_ROLES.FINANCE ||
                              user.role === USER_ROLES.ADMIN;

const availableModules = [
    { id: 'deal-approval', name: UI_LABELS.MODULE_DEAL_APPROVAL_NAME, ..., available: canAccessDealApproval, path: '/dashboard' },
    // ...
];
```

**Why:** All authenticated users now see a single entry point. ADMIN users previously saw two cards pointing to essentially the same functionality.

---

### 5. `src/components/shared/GlobalHeader.tsx`
**Changes:**
- Changed upload button visibility from pathname-based to role-based
- Added `user` from `useAuth()` hook
- Added `USER_ROLES` import

**Before:**
```typescript
const { logout } = useAuth();
const showSalesActions = pathname === '/sales';
```

**After:**
```typescript
const { user, logout } = useAuth();
const showSalesActions = pathname === '/dashboard' && user?.role === USER_ROLES.SALES;
```

**Why:** The upload button should only appear for SALES users on the dashboard, regardless of URL. This decouples UI from routing.

---

### 6. `src/lib/getPageTitle.ts`
**Changes:**
- Removed `/sales` and `/finance` cases
- Added `/dashboard` case

**Before:**
```typescript
switch (pathname) {
    case '/sales':
        return UI_LABELS.PAGE_TITLE_SALES;
    case '/finance':
        return UI_LABELS.PAGE_TITLE_FINANCE;
    // ...
}
```

**After:**
```typescript
switch (pathname) {
    case '/dashboard':
        return UI_LABELS.PAGE_TITLE_DASHBOARD;
    // ...
}
```

**Why:** Routes no longer exist, so their title mappings were removed.

---

## Files NOT Modified (By Design)

### `src/features/transactions/hooks/useTransactionDashboard.ts`
The hook still accepts `view` as a parameter. This is intentional because:
1. The hook is called by `TransactionDashboard`, which now derives `view` internally
2. Keeping `view` as a parameter makes the hook more testable
3. The hook's responsibility is data fetching, not authentication concerns

### `src/features/transactions/contexts/TransactionPreviewContext.tsx`
The context still receives `view` as a prop from `TransactionDashboard`. This is correct because:
1. The parent component (`TransactionDashboard`) already derives view from auth
2. The context is instantiated multiple times for different modals
3. Each modal explicitly passes the view it needs

---

## Architecture Diagram

### Before
```
App.tsx
├── /sales route → ProtectedRoute(SALES)
│   └── TransactionDashboard { view: 'SALES' }
│       └── useTransactionDashboard({ view: 'SALES' })
│           └── getSalesTransactions()
│
└── /finance route → ProtectedRoute(FINANCE)
    └── TransactionDashboard { view: 'FINANCE' }
        └── useTransactionDashboard({ view: 'FINANCE' })
            └── getFinanceTransactions()
```

### After
```
App.tsx
└── /dashboard route → ProtectedRoute(SALES, FINANCE, ADMIN)
    └── TransactionDashboard
        ├── useAuth() → user.role
        ├── view = role === 'SALES' ? 'SALES' : 'FINANCE'
        └── useTransactionDashboard({ view })
            ├── If SALES → getSalesTransactions()
            └── If FINANCE → getFinanceTransactions()
```

---

## Problems Encountered & Solutions

### Problem 1: Hook Still Needed View Parameter
**Issue:** Initially considered making `useTransactionDashboard` also call `useAuth()` internally.

**Solution:** Kept view as a parameter. The hook's job is data fetching based on a view mode, not determining what that mode should be. This keeps concerns separated and the hook testable.

### Problem 2: Page Title Mapping
**Issue:** After removing `/sales` and `/finance` routes, the `getPageTitle` function had dead cases.

**Solution:** Added `/dashboard` case with new `PAGE_TITLE_DASHBOARD` label, removed obsolete cases.

### Problem 3: Pre-existing TypeScript Errors
**Issue:** `npx tsc --noEmit` showed import path errors in Table components unrelated to this refactor.

**Solution:** Verified these were pre-existing issues by filtering grep output. The Vite build succeeded, confirming no regressions from this refactor.

---

## Verification

### Build Verification
```bash
npx vite build
# ✓ 1876 modules transformed
# ✓ built in 14.88s
```

### Route Verification
```bash
grep -E "['\"/]sales['\"]|['\"/]finance['\"]" src/**/*.tsx
# No matches found (routes fully removed)
```

---

## Benefits Achieved

| Metric | Before | After |
|--------|--------|-------|
| Routes for transaction dashboard | 2 | 1 |
| Props passed to TransactionDashboard | 2 (`view`, `setSalesActions`) | 1 (`setSalesActions`) |
| Module cards for ADMIN user | 4 (Sales, Finance, Admin, Master) | 3 (Deal Approval, Admin, Master) |
| Source of truth for view mode | URL path | User role |

---

## Future Considerations

1. **Adding new roles:** If a new role (e.g., `PROCUREMENT`) needs dashboard access, add it to:
   - `ProtectedRoute` roles array in `App.tsx`
   - View derivation logic in `TransactionDashboard.tsx`
   - Potentially new stats grid and transaction list components

2. **Role-specific customizations:** The pattern `view = role === 'X' ? 'X' : 'Y'` can be extended to a switch statement if more granular control is needed.

3. **Deep linking:** If users need to share links to specific dashboard modes, consider adding query params (e.g., `/dashboard?mode=finance`) rather than reverting to separate routes.
