# Masterdata Folder Documentation

This document provides a comprehensive analysis of the `src/features/masterdata` folder, explaining its purpose, data flow, patterns, and dependencies in plain English.

## Table of Contents

- [The Main Job](#the-main-job)
- [The Flow](#the-flow)
- [The Repeats](#the-repeats)
- [The Connections](#the-connections)
- [The Identity](#the-identity)
- [File Summary](#file-summary)
- [Key Business Variables](#key-business-variables)

---

## The Main Job

**In plain English:** This folder is responsible for letting authorized users view and change important business numbers (like exchange rates or capital costs), while keeping a complete record of who changed what and when.

Think of it like a controlled settings panel for financial variables. Only certain people (Admins and Finance staff) can make changes, but everyone can see the history of what was changed, by whom, and why.

---

## The Flow

**Where does the data come from?**

1. When the page loads, it asks the server for two things:
   - The list of variables that can be edited (like "Costo Capital", "Tipo de Cambio")
   - The complete history of all past changes

**Where does it go?**

1. The list of editable variables fills a dropdown menu in the form
2. The history data fills a table showing all past updates
3. When a user submits a new value:
   - The form data goes to the server (`POST /api/master-variables/update`)
   - The server saves it
   - The page reloads all data to show the new entry in the history

**Visual Flow:**

```
[User Opens Page]
       │
       ▼
[Fetch from Server] ───► [History Table Display]
       │
       ▼
[If Admin/Finance] ───► [Show Update Form]
       │
       ▼
[User Fills Form & Submits]
       │
       ▼
[Send to Server] ───► [Server Saves] ───► [Reload & Show New History]
```

### API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/master-variables` | Fetch all variable update history |
| GET | `/api/master-variables/categories` | Fetch list of editable variables with categories |
| POST | `/api/master-variables/update` | Submit new variable value |

---

## The Repeats

**Repeated patterns found in this folder:**

### 1. Loading/Error State Pattern

The same `isLoading` and error handling logic appears in both data fetching and form submission:

```
1. Set loading to true
2. Try the operation
3. If error, show error message
4. Set loading to false
```

### 2. API Response Structure

All three API functions follow the same response format:

```typescript
{ success: true, data: [...] }   // On success
{ success: false, error: "..." } // On failure
```

### 3. Form Field Pattern

The three form fields (variable dropdown, value input, comment input) all follow the same structure with label, input, and controlled state updates.

### 4. Overall Code Quality

The code is well-organized with minimal copy-paste. Each component has a single responsibility.

---

## The Connections

### Dependencies (What This Folder Relies On)

| Folder/File | What It Provides |
|-------------|------------------|
| `@/contexts/AuthContext` | User info and role (to check if they can edit) |
| `@/config/labels.ts` | All text labels, messages, and placeholders |
| `@/config/enums.ts` | User role constants (ADMIN, FINANCE, SALES) |
| `@/types/index.ts` | TypeScript definitions for data shapes |
| `@/lib/api.ts` | The centralized API client for server communication |
| `@/lib/formatters.ts` | Date formatting utility |
| `@/components/ui/table` | Pre-built table UI components |
| `@/components/shared/CategoryBadge` | Badge component for displaying categories |

### What Connects TO This Folder

- The main app routing system (to navigate to this page)
- Any dashboard or navigation menu that links to "Master Data Management"

---

## The Identity

### Label: "The Vault Keeper"

**Why this name?**

This folder acts like a secure vault for critical business numbers:

1. **Access Control**: Only authorized personnel (Admin/Finance) can make changes - like how only certain people have the vault combination

2. **Audit Trail**: Every change is logged with who, when, and why - like a sign-in sheet for vault access

3. **Precious Contents**: The variables stored here (exchange rates, capital costs) are critical financial parameters that affect calculations throughout the system

4. **View-Only for Others**: People without permission can still see what's in the vault (the history), they just can't touch anything

It's not the brain (that would be business logic), not storage (that's the database), and not a connector (that's the API layer). It's the carefully controlled access point to important configuration values that need protection and accountability.

---

## File Summary

```
src/features/masterdata/
├── index.ts                          # Exports everything for other parts of the app
├── MasterDataManagement.tsx          # Main page - orchestrates everything, checks permissions
├── masterDataService.ts              # Talks to the server (fetch, save)
└── components/
    ├── VariableUpdateForm.tsx        # The form for entering new values
    └── HistoryTable.tsx              # The table showing all past changes
```

| File | Purpose |
|------|---------|
| `index.ts` | Barrel export file that exposes the public API of the feature |
| `MasterDataManagement.tsx` | Main page component - orchestrates data fetching, permission checks, and renders child components |
| `masterDataService.ts` | API service layer - handles all server communication with type safety |
| `components/VariableUpdateForm.tsx` | Form UI for selecting a variable, entering a new value, and optional comment |
| `components/HistoryTable.tsx` | Table displaying all past variable updates with pagination |

---

## Key Business Variables

The following financial parameters are managed through this feature:

| Variable | Display Name | Description |
|----------|--------------|-------------|
| `costoCapital` | Costo Capital | Cost of capital rate |
| `tipoCambio` | Tipo de Cambio | Exchange rate |
| `tasaCartaFianza` | Tasa Carta Fianza (%) | Guarantee letter rate percentage |

These variables are used in calculations elsewhere in the application.

---

## Access Control

### Roles and Permissions

| Role | Can View History | Can Update Variables |
|------|------------------|---------------------|
| ADMIN | Yes | Yes |
| FINANCE | Yes | Yes |
| SALES | Yes | No |

Users without update permission see a blue info banner: "Viewing Access Only: Your role does not permit updating Master Variables."

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Migration best practices
- [ROLLBACK.md](./ROLLBACK.md) - Rollback procedures
