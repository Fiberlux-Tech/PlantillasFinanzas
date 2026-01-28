# TODO.md: Development Action Plan


### How to Use
* **Action Plan**: Refer to this file to see what needs to be built next.
* **Streamlined Workflow**: This file uses a single consolidated list for all pending items to reduce categorization overhead.
* **AI Context**: AI agents use this file to understand current development velocity and the immediate roadmap.

---

## 1. Pending Tasks

* [ ] **Vercel Execution Context Audit**: Verify if the asynchronous email threads in `email_service.py` survive the Vercel serverless lifecycle or require a move to a managed task queue.
* [ ] **Environment Secret Check**: Confirm all critical variables (e.g., `SUPABASE_SERVICE_ROLE_KEY`, `MAIL_PASSWORD`) are manually set in the Vercel Dashboard.

---

## 3. Someday
* [ ] **TIR/VAN Threshold Warnings**: Implement visual UI indicators (e.g., yellow badges) if calculated metrics fall below predefined Finance benchmarks.
* [ ] **Mandatory Rejection Notes**: Ensure the frontend blocks the "Reject" action unless a `rejection_note` has been provided.
* [ ] **Modular Feature Prototype**: Draft the directory structure for a second department module (e.g., "Procurement") to test the webapp's multi-module capability.
* [ ] **Direct ERP Integration**: Prototype a "Project Code" fetch system that pulls raw data directly from the enterprise ERP instead of relying on Excel uploads.
* [ ] **Auto-Approval Rules**: Build "Auto-Accept" logic for deals that meet 100% of the KPI criteria, bypassing manual Finance review.

---