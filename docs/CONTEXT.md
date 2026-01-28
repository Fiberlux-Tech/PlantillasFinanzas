# CONTEXT.md: Deal Approval System (Vercel + Supabase)

## 0. How to Use & Conventions
This document serves as the **"Technical Compass"** for the Deal Approval System. It is the primary source of truth for the project's architecture, naming conventions, and technical patterns.

### How to Use
* **Onboarding:** Every developer or AI coding assistant must read this file first to understand the "how" and "why" behind the code.
* **Decision Making:** Use this document to resolve architectural disputes. Patterns defined here (e.g., Stateless Auth, NullPool) are mandatory.
* **AI Instruction:** AI agents should prioritize the rules in this file over general programming knowledge to ensure compatibility with our serverless environment.

### When to Update This File
To prevent this file from filling with "junk" or minor details, only update it when **Foundational** changes occur:
* **Architectural Shifts:** Changes in core infrastructure (e.g., moving away from Supabase or Vercel).
* **Tech Stack Changes:** Adding or banning major libraries (e.g., the ban on Pandas).
* **Structural Changes:** Significant modifications to the folder hierarchy or project organization.
* **Global Rules:** New mandatory coding patterns, naming conventions, or security protocols.
* **DO NOT UPDATE FOR:** Minor bug fixes, individual feature logic, UI tweaks, or transient tasks. These belong in `TODO.md` or the specific service files.

### Conventions
* **Authority:** This file is the "Technical North Star." Any major structural change must be reflected here immediately.
* **Strictness:** "Forbidden" items are non-negotiable due to infrastructure constraints.

---

## 1. System Overview
The goal of this system is to transition the Deal Approval process from a resource-constrained VM to a scalable, cloud-native Monorepo. It serves as a centralized platform for processing financial templates, calculating KPIs like VAN/TIR, and managing approval workflows across SALES, FINANCE, and ADMIN roles.

## 2. Tech Stack
* **Backend:** Flask (Python 3.11), SQLAlchemy ORM, and `openpyxl` for Excel parsing (Pandas is strictly forbidden to save memory).
* **Frontend:** React 18 with Vite, TypeScript, Tailwind CSS, and Radix UI components.
* **Database & Auth:** Supabase (PostgreSQL) for data storage and Supabase Auth for identity management.
* **Infrastructure:** Vercel for serverless hosting, utilizing the monorepo structure with `/api` as the bridge.

## 3. Project Structure
The repository is organized to meet Vercel's serverless requirements:

/project-root
├── api/                # Vercel entry point (bridge to Flask)
├── app/                # BACKEND: Stateless Flask logic
│   ├── api/            # URL routes and blueprints
│   ├── services/       # Business logic (KPIs, OpenPyXL parser)
│   ├── models.py       # SQLAlchemy database schemas
│   └── jwt_auth.py     # JWT verification & RBAC decorators
├── src/                # FRONTEND: React/TypeScript source
│   ├── features/       # Modular UI logic (admin, auth, transactions)
│   ├── lib/            # Shared utilities (API client, Supabase config)
│   └── types/          # Centralized TypeScript interfaces
├── migrations/         # Alembic database migration history
├── vercel.json         # Deployment & routing configuration
└── requirements.txt    # Python dependencies (Pandas is FORBIDDEN)

## 4. Architectural Patterns & Rules
* **Stateless Auth:** All authentication is offloaded to Supabase. The backend is strictly stateless, verifying JWT tokens in the `Authorization: Bearer` header using `@require_jwt` decorators.
* **Serverless DB Connections:**
    * **Runtime (Vercel Functions):** MUST use Port 6543 (Transaction Mode Pooler). SQLAlchemy is configured with `NullPool` to prevent connection exhaustion, as serverless functions cannot manage persistent pools.
    * **Migrations (CI/CD Only):** MUST use Port 5432 (Direct Connection). Alembic migrations require direct database access for DDL operations, advisory locks, and long-running transactions that are incompatible with the connection pooler. Migrations run exclusively in GitHub Actions before deployment, never in serverless functions.
* **CI/CD Migrations:** Database migrations are externalized to GitHub Actions workflows (`.github/workflows/deploy-*.yml`). Running migrations in serverless functions is an anti-pattern that causes race conditions and database locks. The pipeline automatically backs up the database, runs migrations, and deploys code. See `docs/DEPLOYMENT.md` for details.
* **Performance Optimization:** * **Lazy Config:** Critical variables (DB, JWT) validate at startup; non-critical services (Email) validate only when first called to reduce "Cold Start" delays.
    * **Caching:** Expensive KPIs (VAN, TIR) are stored in a `financial_cache` JSON column to prevent recalculation.
    * **Coarse-Grained API:** Dashboard KPI metrics are served via a single consolidated endpoint (`GET /api/kpi/summary`) instead of individual per-metric endpoints. This eliminates redundant SSL handshake, JWT verification, and DB connection overhead. The backend uses a shared `_apply_kpi_filters()` helper to centralize RBAC logic across all KPI queries.

## 5. Security Model (Defense in Depth)
* **JWT & Claims:** User roles are stored in Supabase User Metadata. The backend extracts these claims from the JWT to verify permissions without additional database lookups.
* **RBAC Decorators:** Permission logic is enforced via Python decorators like `@admin_required` or `@finance_admin_required`.
* **Database Access:** The backend uses a `service_role` connection string for full access, while frontend data safety relies on the JWT validation layer.

## 6. Development Standards
* **API Client:** The frontend uses relative paths (e.g., `/api/me`) and includes a `refreshSessionAndRetry` mechanism to handle 403 errors if a user's role is updated mid-session.
* **Naming Conventions:** * Backend: `snake_case` for Python functions and variables.
    * Frontend: `camelCase` for variables/functions and `PascalCase` for React components.
* **DRY Principles:** All financial calculations and state-changing logic (e.g., PEN/USD conversion for database entry) must reside in app/utils/. Frontend utilities in src/lib/ are strictly limited to display formatting and UI-only transformations to prevent "rounding drift" or logic duplication.