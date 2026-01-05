# TODO.md: Development Action Plan

## 1. How to Use This File
This file is the project's **"Engine Room,"** tracking immediate actions, technical debt, and modular expansions. It is designed for maximum **token efficiency** when working with AI coding assistants by following a "Rolling Window" strategy.

### Conventions
* **Task Marking**:
    * `[ ]` **Pending**: Task has not started.
    * `[/]` **In Progress**: Active development or testing.
    * `[x] (YYYY-MM-DD)` **Completed**: Task is finished. **All completed tasks must include the completion date**.
* **The Rolling Window & Purge Policy**:
    * To keep the context window lean, this file only maintains **Pending** items and **Recently Completed** items from the last 1–2 weeks.
    * **Purge and Log**: Once a month (or when the file feels cluttered), all completed `[x]` items are moved to `CHANGELOG.md`.
* **CHANGELOG.md Rule**: The changelog must only contain **REALLY SUMMARIZED** details of high-level features or fixes to keep the historical record lean.

---

## 2. High Priority (MVP & Reliability)
*Tasks required to ensure the system is production-ready and stable on Vercel.*

* [ ] **Fix Documentation Sync**: Update the `README.MD` database connection example to use Port `6543` (Transaction Mode) instead of `5432` to prevent serverless connection exhaustion.
* [ ] **Vercel Execution Context Audit**: Verify if the asynchronous email threads in `email_service.py` survive the Vercel serverless lifecycle or require a move to a managed task queue.
* [ ] **Environment Secret Check**: Confirm all critical variables (e.g., `SUPABASE_SERVICE_ROLE_KEY`, `MAIL_PASSWORD`) are manually set in the Vercel Dashboard.
* [ ] **Financial Snapshotting**: Implement logic to save a final snapshot of all deal data into the `financial_cache` column upon approval to "freeze" the historical record.

---

## 3. Medium Priority (The "Financial Brain" V2)
*Enhancing the logic and integrity of the approval engine.*

* [ ] **Master Variable Real-time Sync**: Update KPI calculations in `kpi.py` to explicitly fetch the most recent entries from the `MasterVariable` table before processing, ensuring calculations reflect current market data.
* [ ] **TIR/VAN Threshold Warnings**: Implement visual UI indicators (e.g., yellow badges) if calculated metrics fall below predefined Finance benchmarks.
* [ ] **Mandatory Rejection Notes**: Ensure the frontend blocks the "Reject" action unless a `rejection_note` has been provided.

---

## 4. Low Priority (Platform & Modularity)
*Strategic goals for expanding the system to other departments.*

* [ ] **Modular Feature Prototype**: Draft the directory structure for a second department module (e.g., "Procurement") to test the webapp's ability to host multiple automation tools.
* [ ] **Direct ERP Integration**: Prototyping a "Project Code" fetch system that pulls raw data directly from the enterprise ERP instead of relying on Excel uploads.
* [ ] **Auto-Approval Rules**: Build "Auto-Accept" logic for deals that meet 100% of the KPI criteria, bypassing manual Finance review.

---

## 5. Recently Completed
*Move these to CHANGELOG.md during the next monthly purge.*

* [x] (2026-01-05) **Auth Consolidation**: Eliminated legacy `/auth` blueprint and consolidated all authentication under the `/api` prefix.
* [x] (2026-01-05) **Stateless Refactor**: Removed Flask-Login dependencies from the User model and transitioned to pure JWT verification via Supabase.
* [x] (2026-01-05) **Serverless DB Optimization**: Switched SQLAlchemy configuration to `NullPool` to support high-concurrency serverless environments.