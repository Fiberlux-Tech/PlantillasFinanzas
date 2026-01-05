# PRD.md: Deal Approval System

## 1. Executive Summary & Goal
The **Deal Approval System** is a centralized, high-integrity platform designed to replace Fiberlux’s fragmented, spreadsheet-based approval workflows. Beyond solving the immediate "Excel-risk" for project approvals, the system is architected as a **modular automation hub**. It serves as a scalable foundation where additional department-specific automations can be integrated as new modules within the same web application framework.

## 2. Target Audience & Roles
* **Sales Representatives (Submitters):** Need a fast way to upload templates and track deal progress.
* **Finance Team (Reviewers/Gatekeepers):** Need to analyze KPIs (VAN, TIR) and enforce data integrity by restricting which values can be edited.
* **Enterprise Admins:** Manage global parameters and modular extensions for other departments.

## 3. User Stories
* **As a Sales Rep,** I want to upload my project spreadsheet so the system can extract data automatically, eliminating manual entry.
* **As a Finance Reviewer,** I want to view calculated KPIs based on the latest global financial variables to ensure deal profitability.
* **As an Admin,** I want to update a master variable (e.g., Exchange Rate) once and have it instantly reflect across all active transactions.
* **As a Developer,** I want to add a new automation module for a different department without rebuilding the core authentication or UI infrastructure.

## 4. Specific Feature Requirements

### A. Controlled Excel Parsing & Consolidation
* **Requirement:** Extract MRC, NRC, and cost structures from standardized files using a memory-efficient backend (OpenPyXL).
* **Integrity Rule:** Only specific fields are editable post-upload, preventing unauthorized formula manipulation.

### B. Aggregate Variable Management (Global Sync)
* **Requirement:** Manage variables like **Exchange Rates**, **Financial Costs**, and **Discount Rates** at an aggregate level.
* **Logic:** Every transaction must pull the **latest** values from the `MasterVariable` table dynamically. This ensures that KPI calculations (VAN/TIR) always reflect current market conditions rather than static, outdated values.

### C. Approval State Machine
* **Requirement:** Transition deals through `PENDING`, `APPROVED`, and `REJECTED` states.
* **Traceability:** Mandate "Rejection Notes" and send asynchronous email notifications upon status changes.

### D. Multi-Module Platform Architecture
* **Requirement:** The application must support modular expansion.
* **Implementation:** The core UI, Auth (Supabase), and API structures must be generic enough to host additional departmental automations as independent "Feature Modules" (e.g., adding a Procurement or Logistics module).

## 5. Success Metrics
* **Calculation Accuracy:** 100% synchronization between master variables and transaction KPIs.
* **Zero Formula Fraud:** Elimination of manual spreadsheet-based calculation overrides.
* **Extensibility:** Successful integration of at least one additional automation module without infrastructure rework.

## 6. Future Roadmap
* **Phase 2 Automation:** Implementation of auto-reject/auto-accept thresholds based on master variable limits.
* **Direct Integration:** Replacing file uploads with direct API pulls from the enterprise system via project codes.