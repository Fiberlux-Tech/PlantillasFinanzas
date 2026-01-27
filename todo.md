# TODO.md: Development Action Plan

## 0. How to Use & Conventions
This document is the project's **"Engine Room,"** tracking immediate actions, technical debt, and modular expansions. It is the most frequently updated file in the repository.

### How to Use
* **Action Plan**: Refer to this file to see what needs to be built next.
* **Streamlined Workflow**: This file uses a single consolidated list for all pending items to reduce categorization overhead.
* **AI Context**: AI agents use this file to understand current development velocity and the immediate roadmap.

---

## 1. Pending Tasks


* [x] (2026-01-26) **Remove Odoo/Datawarehouse Connections**: Removed datawarehouse connections from backend (`fixed_costs.py`, `config.py`, `transactions.py`) and frontend (code manager components, lookup services).
* [x] (2026-01-26) **Master Variable Logic Sync**: MasterVariables (`tipoCambio`, `costoCapital`, `tasaCartaFianza`) are now frozen at transaction creation. Added `master_variables_snapshot` JSON column for audit trail. Rate fields removed from `updatable_fields` to enforce immutability. Frontend already displays these as read-only text.
* [x] (2026-01-26) **Financial Snapshotting**: Already implemented - `financial_cache` JSON column stores calculated KPIs upon Approval/Rejection (see `approve_transaction` and `reject_transaction` in `transactions.py`).
* [x] (2026-01-27) **Fix Template Endpoint Variable Name Mismatch**: `get_transaction_template()` in `transactions.py` was requesting `costoCapitalAnual` instead of `costoCapital` from master variables, causing a 400 error on "Crear Plantilla". Fixed to use `costoCapital` (matching `config.py` and `excel_parser.py`) and map it to the `costoCapitalAnual` field in the template response.
* [ ] **Vercel Execution Context Audit**: Verify if the asynchronous email threads in `email_service.py` survive the Vercel serverless lifecycle or require a move to a managed task queue.
* [ ] **Environment Secret Check**: Confirm all critical variables (e.g., `SUPABASE_SERVICE_ROLE_KEY`, `MAIL_PASSWORD`) are manually set in the Vercel Dashboard.



## 2. Someday
* [ ] **TIR/VAN Threshold Warnings**: Implement visual UI indicators (e.g., yellow badges) if calculated metrics fall below predefined Finance benchmarks.
* [ ] **Mandatory Rejection Notes**: Ensure the frontend blocks the "Reject" action unless a `rejection_note` has been provided.
* [ ] **Modular Feature Prototype**: Draft the directory structure for a second department module (e.g., "Procurement") to test the webapp's multi-module capability.
* [ ] **Direct ERP Integration**: Prototype a "Project Code" fetch system that pulls raw data directly from the enterprise ERP instead of relying on Excel uploads.
* [ ] **Auto-Approval Rules**: Build "Auto-Accept" logic for deals that meet 100% of the KPI criteria, bypassing manual Finance review.

---