# TODO.md: Development Action Plan

## 0. How to Use & Conventions
This document is the project's **"Engine Room,"** tracking immediate actions, technical debt, and modular expansions. It is the most frequently updated file in the repository.

### How to Use
* **Action Plan**: Refer to this file to see what needs to be built next.
* **Streamlined Workflow**: This file uses a single consolidated list for all pending items to reduce categorization overhead.
* **AI Context**: AI agents use this file to understand current development velocity and the immediate roadmap.

### When to Update This File
This file is dynamic and should be updated constantly as work progresses:
* **New Tasks**: Whenever a new bug is found, a feature is requested, or a "next step" is identified.
* **Status Changes**: When a task moves from Pending `[ ]` to In Progress `[/]` or Completed `[x]`.
* **Purging**: When the file becomes too large, move completed items to `CHANGELOG.md` following the "Rolling Window" strategy.
* **DO NOT UPDATE FOR**: High-level architectural rules (belongs in `CONTEXT.md`) or core business requirements (belongs in `PRD.md`).

### Conventions
* **Task Marking**:
    * `[ ]` **Pending**: Task has not started.
    * `[/]` **In Progress**: Active development or testing.
    * `[x] (YYYY-MM-DD)` **Completed**: Task is finished. **All completed tasks must include the completion date**.
* **The Rolling Window & Purge Policy**:
    * To keep the context window lean, this file only maintains **Pending** items and **Recently Completed** items from the last 1–2 weeks.
    * **Purge and Log**: Once a month (or when the file feels cluttered), move completed `[x]` items to `CHANGELOG.md`.
* **CHANGELOG.md Rule**: The changelog must only contain **REALLY SUMMARIZED** details of high-level features or fixes to keep the historical record lean.

---

## 1. Pending Tasks
*All active tasks, technical debt, and future improvements.*



* [ ] **Remove Odoo/Datawarehouse Connections**: Remove functions pulling data from the datawarehouse (e.g., in `app/api/variables.py` or `config.py`) to make the Phase 1 code slimmer and more efficient.
* [ ] **Master Variable Logic Sync**: Update the upload service (in `app/services/excel_parser.py` or `transactions.py`) to fetch current MasterVariables and persist them directly into the Transaction record at creation, ensuring they are frozen and immutable for that deal.
* [ ] **Financial Snapshotting**: Persist final calculated KPI results (VAN/TIR) in the `financial_cache` JSON column upon the final Finance decision (Approval/Rejection) to lock the historical audit data.
* [ ] **Vercel Execution Context Audit**: Verify if the asynchronous email threads in `email_service.py` survive the Vercel serverless lifecycle or require a move to a managed task queue.
* [ ] **Environment Secret Check**: Confirm all critical variables (e.g., `SUPABASE_SERVICE_ROLE_KEY`, `MAIL_PASSWORD`) are manually set in the Vercel Dashboard.
* [ ] **TIR/VAN Threshold Warnings**: Implement visual UI indicators (e.g., yellow badges) if calculated metrics fall below predefined Finance benchmarks.
* [ ] **Mandatory Rejection Notes**: Ensure the frontend blocks the "Reject" action unless a `rejection_note` has been provided.
* [ ] **Modular Feature Prototype**: Draft the directory structure for a second department module (e.g., "Procurement") to test the webapp's multi-module capability.
* [ ] **Direct ERP Integration**: Prototype a "Project Code" fetch system that pulls raw data directly from the enterprise ERP instead of relying on Excel uploads.
* [ ] **Auto-Approval Rules**: Build "Auto-Accept" logic for deals that meet 100% of the KPI criteria, bypassing manual Finance review.

---

## 2. Recently Completed
*Move these to CHANGELOG.md during the next monthly purge.*

* [x] (2026-01-05) **Fix Documentation Sync**: Updated `README.MD` database connection string example to use Port `6543` (Transaction Mode).
* [x] (2026-01-05) **Auth Consolidation**: Eliminated legacy `/auth` blueprint and consolidated all authentication under the `/api` prefix.
* [x] (2026-01-05) **Stateless Refactor**: Removed Flask-Login dependencies from the User model and transitioned to pure JWT verification via Supabase.
* [x] (2026-01-05) **Serverless DB Optimization**: Switched SQLAlchemy configuration to `NullPool` to support high-concurrency serverless environments.