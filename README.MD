# Fiberlux | System for Financial Approval & Consolidation

## 0. How to Use & Conventions
This document is the **"Front Door"** of the project. It provides general orientation, purpose, and the necessary instructions for setting up the development environment.

### How to Use
* **Onboarding**: The first stop for any developer or stakeholder to understand the business problem and the system's role in solving it.
* **Quick Start**: Refer to the "Setup & Installation" section to get the local environment running.
* **Guiding Principles**: Review the "Standardization & Development Rules" to understand the non-negotiable constraints of the project.

### When to Update This File
To keep this document as a clean, high-level entry point, only update it when **System-Wide** or **Onboarding** changes occur:
* **Setup Changes**: If the installation steps, prerequisites, or required environment variables change.
* **Core Orientation**: If the primary business goal or the "Why" behind the project evolves.
* **Feature Expansion**: When adding new high-level pillars to the "Key Features" section.
* **Rule Updates**: When the "Standardization & Development Rules" need adjustment for all developers.
* **DO NOT UPDATE FOR**: Deep technical implementation details (belongs in `CONTEXT.md`), specific business logic for features (belongs in `PRD.md`), or immediate development tasks (belongs in `TODO.md`).

### Conventions
* **Clarity**: Keep explanations high-level and accessible to both technical and non-technical stakeholders.
* **Maintenance**: Ensure all setup steps and links are kept current to minimize onboarding friction.

---
## 📌 Project Orientation: The "Why"
Before this system, Fiberlux managed project approvals through a fragmented, manual workflow. Business Units (**Corporativo, Gigalan, Estado, and Mayorista**) submitted project spreadsheets via email. The Finance team had to manually review these files and copy-paste key data into a master database for tracking.

**This platform replaces that manual bottleneck by:**
* **Consolidating Workflows:** Providing a single portal for all four Business Units to submit projects.
* **Automating Consolidation:** Data is parsed directly from uploaded spreadsheets into a centralized PostgreSQL database.
* **Financial Intelligence:** Automatically calculating complex KPIs (EBITDA, operational margins, GigaLan commissions) during the review process.
* **Traceability:** Maintaining a clear audit trail of approvals, rejections, and financial adjustments.

---

## 🚀 Key Features

### 1. Unified Approval Pipeline
* **Specialized Logic:** Tailored financial processing for Corporativo, Gigalan, Estado, and Mayorista.
* **Finance Review Portal:** A dedicated view for the Finance team to analyze, edit, and approve/reject submissions.
* **Rejection Tracking:** Integrated note system to explain why projects were sent back for correction.

### 2. Financial & KPI Engine
* **Real-time Metrics:** Instant calculation of project profitability and tax implications.
* **GigaLan Commissions:** Custom logic to handle unique commission structures for the GigaLan unit.
* **Master Data Management:** A secure module for admins to update global variables (exchange rates, tax percentages) that drive the math engine.

### 3. Efficiency Tools
* **Excel Parser:** High-speed backend service that extracts data from standard "Plantilla" (template) files.
* **Status Dashboards:** Visual badges (Pending, Approved, Rejected) to give Sales teams instant visibility on their project status.

---

## 📂 Project Structure

```text
├── app/                    # Flask Backend (The "Brain")
│   ├── api/                # Route definitions (Transactions, Admin, Variables)
│   ├── services/           # Business Logic: KPI math, Commission rules, Excel parsing
│   ├── utils/              # Math helpers and general utilities
│   └── models.py           # Database Schema
├── src/                    # React Frontend (The "Dashboard")
│   ├── features/           # Domain modules (Auth, Admin, Transactions)
│   ├── components/         # UI library (Shadcn/UI components)
│   └── lib/                # API clients and formatters
├── migrations/             # Database version history (Alembic)
├── supabase_rls_scripts/   # SQL scripts for database-level security (RLS)
└── api/index.py            # Entry point for Vercel production
```
---

## ⚙️ Setup & Installation

### 1. Prerequisites
* **Python 3.11+**
* **Node.js 18+** (with npm or pnpm)
* **PostgreSQL** instance (or a Supabase Project)

### 2. Backend Setup
The backend handles parsing, complex financial math, and database communication.

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install required packages
pip install -r requirements.txt

# Run migrations to set up your local or remote database schema
alembic upgrade head
```

### 3. Frontend Setup
The frontend provides the interactive dashboards for Sales and Finance teams.

```bash
# Install dependencies
npm install

# Start the development server (Vite)
npm run dev
```

## 🔑 Environment Configuration
Create a `.env` file in the project root. This file is required to connect the application to the database and authentication services.

| Variable | Description |
| :--- | :--- |
| `DATABASE_URL` | SQLAlchemy connection string (e.g., `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:6543/postgres`) |
| `VITE_SUPABASE_URL` | Your Supabase project URL (found in project settings) |
| `VITE_SUPABASE_ANON_KEY` | The public anonymous key for client-side API calls |
| `JWT_SECRET_KEY` | A secure, random string used to sign backend authentication tokens |

---

## 🛡️ Standardization & Development Rules
To maintain the integrity of financial data and ensure the project remains scalable for future developers, follow these rules:

1. **The "Single Source of Truth" Rule:** All core financial math (KPIs, EBITDA, GigaLan commissions, and margin calculations) **must** reside in `app/services/` on the backend. Never implement core financial logic on the frontend to avoid "rounding drift" or inconsistent results.
2. **Database Governance:** Never modify the database schema via the Supabase UI. All changes must be recorded using Alembic migrations (`alembic revision --autogenerate`). This ensures every environment (Dev, Staging, Prod) stays in sync.
3. **Security Protocol:** While tables are currently tagged as "unrestricted" in Supabase, any security updates should be implemented via the scripts in `supabase_rls_scripts/`. This centralizes the Row Level Security (RLS) logic.
4. **Type Safety:** All data structures returned by the API must have a corresponding interface in `src/types/`. This prevents runtime errors when the UI attempts to render complex financial objects.
5. **Excel Parsing:** If a Business Unit changes their template format, update the corresponding logic in `app/services/excel_parser.py` immediately to prevent consolidation failures.

---

## 👥 Audience & Roles
* **Sales & Business Units (Corporativo, Gigalan, Estado, Mayorista):** Submitters who use the dashboard to upload spreadsheets, calculate initial commissions, and track the approval status of their projects.
* **Finance Team:** The primary reviewers and "Gatekeepers." They use the platform to validate submissions, add rejection notes, and manage the "Master Data" variables (Exchange rates, etc.) that drive the system.
* **Administrators / Developers:** Responsible for maintaining the parsing engine, monitoring database health, and ensuring the transition from "email-based" workflows to "system-based" workflows remains seamless.# Test CI/CD
