# Database Schema Documentation

**Project:** PlantillaFinanzas
**Database:** Supabase PostgreSQL
**Generated:** 2026-01-26

---

## Overview

This application uses 5 main tables (plus 1 Alembic migration tracking table):

| Table | Description |
|-------|-------------|
| `user` | User accounts with role-based access (synced with Supabase Auth) |
| `transaction` | Main deal/approval workflow records |
| `fixed_cost` | One-time costs associated with transactions |
| `recurring_service` | Recurring revenue/expense items for transactions |
| `master_variable` | System-wide configuration variables with audit history |

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌───────────────────┐
│    user     │       │   transaction   │       │    fixed_cost     │
├─────────────┤       ├─────────────────┤       ├───────────────────┤
│ id (PK)     │◄──┐   │ id (PK)         │◄──────│ id (PK)           │
│ username    │   │   │ unidadNegocio   │       │ transaction_id(FK)│
│ email       │   │   │ clientName      │       │ categoria         │
│ role        │   │   │ salesman        │       │ tipo_servicio     │
└─────────────┘   │   │ ...             │       │ ...               │
                  │   └─────────────────┘       └───────────────────┘
                  │           ▲
                  │           │
┌─────────────────┤           │
│ master_variable │           │
├─────────────────┤           │         ┌───────────────────┐
│ id (PK)         │           │         │ recurring_service │
│ variable_name   │           │         ├───────────────────┤
│ variable_value  │           └─────────│ id (PK)           │
│ user_id (FK)────┘                     │ transaction_id(FK)│
│ ...             │                     │ tipo_servicio     │
└─────────────────┘                     │ ...               │
                                        └───────────────────┘
```

---

## Table Definitions

### 1. `user`

Stores user metadata synchronized with Supabase Auth. Authentication is handled entirely by Supabase; this table stores only profile data and role information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NO | auto | Primary key (Supabase UUID) |
| `username` | VARCHAR(64) | NO | - | Unique username |
| `email` | VARCHAR(120) | NO | - | Unique email address |
| `role` | VARCHAR(10) | NO | - | User role: `SALES`, `FINANCE`, or `ADMIN` |

**Indexes:**
- `user_pkey` - Primary key on `id`
- `ix_user_username` - Unique index on `username`
- `ix_user_email` - Unique index on `email`

---

### 2. `transaction`

Main table for deal submissions and approval workflow. Contains financial metrics, client information, and approval status.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(128) | NO | - | Primary key |
| `unidadNegocio` | VARCHAR(128) | NO | - | Business unit |
| `clientName` | VARCHAR(128) | YES | - | Client name |
| `companyID` | VARCHAR(128) | YES | - | Company identifier |
| `salesman` | VARCHAR(128) | YES | - | Salesperson name |
| `orderID` | VARCHAR(128) | YES | - | Order identifier |
| `tipoCambio` | DOUBLE PRECISION | YES | - | Exchange rate |
| `MRC_original` | DOUBLE PRECISION | YES | - | Monthly Recurring Charge (original currency) |
| `MRC_currency` | VARCHAR(3) | NO | - | MRC currency code |
| `MRC_pen` | DOUBLE PRECISION | NO | 0 | MRC converted to PEN |
| `NRC_original` | DOUBLE PRECISION | YES | - | Non-Recurring Charge (original currency) |
| `NRC_currency` | VARCHAR(3) | NO | - | NRC currency code |
| `NRC_pen` | DOUBLE PRECISION | NO | 0 | NRC converted to PEN |
| `VAN` | DOUBLE PRECISION | YES | - | Net Present Value |
| `TIR` | DOUBLE PRECISION | YES | - | Internal Rate of Return |
| `payback` | DOUBLE PRECISION | YES | - | Payback period |
| `totalRevenue` | DOUBLE PRECISION | YES | - | Total revenue |
| `totalExpense` | DOUBLE PRECISION | YES | - | Total expense |
| `comisiones` | DOUBLE PRECISION | YES | - | Commissions amount |
| `comisionesRate` | DOUBLE PRECISION | YES | - | Commission rate |
| `costoInstalacion` | DOUBLE PRECISION | YES | - | Installation cost |
| `costoInstalacionRatio` | DOUBLE PRECISION | YES | - | Installation cost ratio |
| `grossMargin` | DOUBLE PRECISION | YES | - | Gross margin |
| `grossMarginRatio` | DOUBLE PRECISION | YES | - | Gross margin ratio |
| `plazoContrato` | INTEGER | YES | - | Contract term (months) |
| `costoCapitalAnual` | DOUBLE PRECISION | YES | - | Annual cost of capital |
| `tasaCartaFianza` | DOUBLE PRECISION | YES | - | Letter of guarantee rate |
| `costoCartaFianza` | DOUBLE PRECISION | YES | - | Letter of guarantee cost |
| `aplicaCartaFianza` | BOOLEAN | NO | false | Whether letter of guarantee applies |
| `gigalan_region` | VARCHAR(128) | YES | - | GigaLan region |
| `gigalan_sale_type` | VARCHAR(128) | YES | - | GigaLan sale type |
| `gigalan_old_mrc` | DOUBLE PRECISION | YES | - | GigaLan previous MRC |
| `ApprovalStatus` | VARCHAR(64) | YES | - | Status: `PENDING`, `APPROVED`, `REJECTED` |
| `submissionDate` | TIMESTAMP | YES | - | Submission timestamp |
| `approvalDate` | TIMESTAMP | YES | - | Approval/rejection timestamp |
| `rejection_note` | VARCHAR(500) | YES | - | Rejection reason |
| `financial_cache` | JSON | YES | - | Cached financial metrics snapshot |

**Indexes:**
- `transaction_pkey` - Primary key on `id`
- `ix_transaction_salesman` - Index on `salesman`
- `ix_transaction_ApprovalStatus` - Index on `ApprovalStatus`
- `ix_transaction_submissionDate` - Index on `submissionDate`
- `idx_transaction_salesman_approval` - Composite index on (`salesman`, `ApprovalStatus`)
- `idx_transaction_salesman_submission` - Composite index on (`salesman`, `submissionDate`)
- `idx_transaction_approval_salesman_submission` - Composite index on (`ApprovalStatus`, `salesman`, `submissionDate`)

---

### 3. `fixed_cost`

Stores one-time/fixed costs associated with transactions. Has a many-to-one relationship with `transaction`.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INTEGER | NO | auto | Primary key (serial) |
| `transaction_id` | VARCHAR(128) | NO | - | Foreign key to `transaction.id` |
| `categoria` | VARCHAR(128) | YES | - | Cost category |
| `tipo_servicio` | VARCHAR(128) | YES | - | Service type |
| `ticket` | VARCHAR(128) | YES | - | Ticket reference |
| `ubicacion` | VARCHAR(128) | YES | - | Location |
| `cantidad` | DOUBLE PRECISION | YES | - | Quantity |
| `costoUnitario_original` | DOUBLE PRECISION | YES | - | Unit cost (original currency) |
| `costoUnitario_currency` | VARCHAR(3) | NO | - | Currency code |
| `costoUnitario_pen` | DOUBLE PRECISION | NO | 0 | Unit cost in PEN |
| `periodo_inicio` | INTEGER | NO | 0 | Start period (month) |
| `duracion_meses` | INTEGER | NO | 1 | Duration in months |

**Indexes:**
- `fixed_cost_pkey` - Primary key on `id`

**Foreign Keys:**
- `transaction_id` → `transaction.id`

---

### 4. `recurring_service`

Stores recurring revenue and expense items for transactions. Has a many-to-one relationship with `transaction`.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INTEGER | NO | auto | Primary key (serial) |
| `transaction_id` | VARCHAR(128) | NO | - | Foreign key to `transaction.id` |
| `tipo_servicio` | VARCHAR(128) | YES | - | Service type |
| `nota` | VARCHAR(256) | YES | - | Notes |
| `ubicacion` | VARCHAR(128) | YES | - | Location |
| `Q` | DOUBLE PRECISION | YES | - | Quantity |
| `P_original` | DOUBLE PRECISION | YES | - | Price (original currency) |
| `P_currency` | VARCHAR(3) | NO | 'PEN' | Price currency |
| `P_pen` | DOUBLE PRECISION | NO | 0 | Price in PEN |
| `CU1_original` | DOUBLE PRECISION | YES | - | Unit cost 1 (original currency) |
| `CU2_original` | DOUBLE PRECISION | YES | - | Unit cost 2 (original currency) |
| `CU_currency` | VARCHAR(3) | NO | - | Cost currency |
| `CU1_pen` | DOUBLE PRECISION | NO | 0 | Unit cost 1 in PEN |
| `CU2_pen` | DOUBLE PRECISION | NO | 0 | Unit cost 2 in PEN |
| `proveedor` | VARCHAR(128) | YES | - | Supplier/provider |

**Indexes:**
- `recurring_service_pkey` - Primary key on `id`

**Foreign Keys:**
- `transaction_id` → `transaction.id`

---

### 5. `master_variable`

Centralized table for system-critical configuration variables (exchange rates, thresholds, etc.). Maintains full audit history of all changes.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | INTEGER | NO | auto | Primary key (serial) |
| `variable_name` | VARCHAR(64) | NO | - | Variable identifier |
| `variable_value` | DOUBLE PRECISION | NO | - | Variable value |
| `category` | VARCHAR(64) | NO | - | Category (e.g., `FINANCIAL`, `UNITARY_COST`) |
| `date_recorded` | TIMESTAMP | NO | - | When the value was recorded |
| `user_id` | VARCHAR(36) | YES | - | Foreign key to `user.id` (who made the change) |
| `comment` | VARCHAR(255) | YES | - | Optional comment explaining the change |

**Indexes:**
- `master_variable_pkey` - Primary key on `id`
- `ix_master_variable_variable_name` - Index on `variable_name`
- `ix_master_variable_category` - Index on `category`
- `ix_master_variable_date_recorded` - Index on `date_recorded`
- `idx_master_variable_name_date` - Composite index on (`variable_name`, `date_recorded`)

**Foreign Keys:**
- `user_id` → `user.id`

---

### 6. `alembic_version`

Internal table used by Alembic to track database migration versions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `version_num` | VARCHAR(32) | NO | - | Current migration version |

---

## Foreign Key Relationships Summary

| From Table | Column | To Table | Column |
|------------|--------|----------|--------|
| `fixed_cost` | `transaction_id` | `transaction` | `id` |
| `recurring_service` | `transaction_id` | `transaction` | `id` |
| `master_variable` | `user_id` | `user` | `id` |

---

## Notes

### Currency Architecture
- All monetary values are stored in dual format: original currency and PEN equivalent
- Fields ending in `_original` store the value in the source currency
- Fields ending in `_currency` store the 3-letter currency code (e.g., `PEN`, `USD`)
- Fields ending in `_pen` store the PEN-converted value for consistent calculations

### Role-Based Access
- **SALES**: Can create and view own transactions
- **FINANCE**: Can view all transactions, approve/reject pending ones
- **ADMIN**: Full access including user management

### Cascade Behavior
- Deleting a `transaction` cascades to delete related `fixed_cost` and `recurring_service` records
