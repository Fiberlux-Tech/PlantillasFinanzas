# Landing Feature Documentation

This document describes the `src/features/landing` folder — the application's landing page that displays role-based module navigation.

## Table of Contents

- [Overview](#overview)
- [The Main Job](#the-main-job)
- [Data Flow](#data-flow)
- [File Structure](#file-structure)
- [Repeated Patterns](#repeated-patterns)
- [Dependencies](#dependencies)
- [Identity](#identity)
- [Related Documentation](#related-documentation)

---

## Overview

The landing feature creates the "home screen" of the application — the first page users see after logging in. It displays clickable cards representing different app sections (Sales, Finance, Admin, Master Data), but **only shows cards the user has permission to access** based on their role.

---

## The Main Job

**In plain English:** This folder shows a set of clickable cards, where each card represents a different section of the app. The key feature: **not everyone sees the same cards**. The page checks who you are (your role) and only shows the sections you're allowed to access.

Think of it like a building lobby with multiple doors, but the doors you can see depend on your access badge.

---

## Data Flow

```
WHERE DATA COMES FROM:
┌─────────────────────────────────────────────────────────┐
│  AuthContext (knows who the user is and their role)    │
│  Config files (knows what modules exist and their      │
│  names/descriptions)                                   │
└─────────────────────────────────────────────────────────┘
                          ↓
                    LandingPage.tsx
                          │
                          ├── Checks: "What role does this user have?"
                          ├── Filters: "Which modules can they see?"
                          └── Builds a list of visible module cards
                          ↓
                    ModuleCard.tsx (one per module)
                          │
                          └── User clicks a card
                          ↓
WHERE DATA GOES NEXT:
┌─────────────────────────────────────────────────────────┐
│  React Router navigates to the module's page           │
│  (e.g., /sales, /finance, /admin/users)                │
└─────────────────────────────────────────────────────────┘
```

**Simple summary:** It reads user info → decides what to show → displays cards → sends users to the right page when they click.

---

## File Structure

```
src/features/landing/
├── LandingPage.tsx          # Main page component (the "brain")
├── index.ts                 # Barrel export file
└── components/
    └── ModuleCard.tsx       # Reusable card component
```

### LandingPage.tsx

**Purpose:** Main landing page component that displays available modules based on user role and permissions.

**Key Features:**
- Role-based module visibility (Sales, Finance, Admin, Master Data)
- Dynamic module filtering based on user permissions
- Responsive grid layout (1 column on mobile, 2 columns on tablet/desktop)
- Fallback UI for when user data is loading or no modules are available

**Module Configuration:**

| Module | Path | Icon | Visible To |
|--------|------|------|------------|
| Sales | `/sales` | 📝 | SALES, ADMIN |
| Finance | `/finance` | 📊 | FINANCE, ADMIN |
| Admin Management | `/admin/users` | 🔒 | ADMIN only |
| Master Data | `/admin/master-data` | ⚙️ | All users |

---

### ModuleCard.tsx

**Purpose:** Reusable card component that displays a single module with navigation functionality.

**Props Interface:**

```typescript
interface Module {
    id: string;
    name: string;
    icon: string;
    description: string;
    path: string;
}

interface ModuleCardProps {
    module: Module;
}
```

**Features:**
- Clickable card with hover shadow effect
- Displays module icon (emoji), name, and description
- Contains a button labeled "Abrir Modulo" (Open Module)
- Uses React Router navigation on click

---

### index.ts

**Purpose:** Barrel export file for clean imports.

**Enables:**
```typescript
import { LandingPage } from '@/features/landing'
```

---

## Repeated Patterns

The role-checking logic follows the same structure for each module:

```typescript
// Same pattern repeated for each module:
{ available: isSales }      // Sales module
{ available: isFinance }    // Finance module
{ available: isAdmin }      // Admin module
{ available: isMasterData } // Master Data module
```

Each module is defined using the **exact same data shape**:
- `id` (identifier)
- `name` (display name)
- `icon` (emoji)
- `description` (what it does)
- `path` (where to go)
- `available` (true/false based on role)

This repetition is intentional — it allows adding new modules just by adding another object to the list.

---

## Dependencies

### Internal Dependencies

| Dependency | Location | Purpose |
|------------|----------|---------|
| AuthContext | `@/contexts/AuthContext` | Provides current user and their role |
| Config | `@/config` | Provides `USER_ROLES` and `UI_LABELS` constants |

### External Dependencies

| Library | Purpose |
|---------|---------|
| react-router-dom | Navigation when clicking cards |
| Tailwind CSS | All visual styling |

### Config Constants Used

- `USER_ROLES.SALES` - Sales role identifier
- `USER_ROLES.FINANCE` - Finance role identifier
- `USER_ROLES.ADMIN` - Admin role identifier
- `UI_LABELS` - Module names and descriptions (supports localization)

---

## Identity

### Label: "The Lobby" 🚪

**Why this label?**

Just like a building lobby:
- It's the **first place you arrive** after entering (logging in)
- It shows you **which doors/areas you can access** based on your credentials
- It **doesn't do any real work itself** — it just directs you to where the work happens
- It's designed to be **welcoming and easy to navigate**

The landing folder doesn't process sales, manage finances, or handle admin tasks. It simply greets the user and says: "Here are the places you can go. Pick one."

---

## Design Patterns

This feature demonstrates several clean code patterns:

1. **Role-Based Access Control (RBAC)** — Different users see different options
2. **Component Composition** — LandingPage uses ModuleCard as a building block
3. **Configuration-Driven UI** — Module definitions come from data, not hardcoded HTML
4. **Barrel Exports** — Folder exports through index.ts
5. **Responsive Design** — Mobile-first CSS (1 col → 2 col grid)
6. **Loading/Empty States** — Handles user loading and no-modules scenarios

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Migration best practices
