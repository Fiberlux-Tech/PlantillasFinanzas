# Documentation: `src/features/transactions` Folder

---

## 1. The Main Job

**In plain English:** This folder handles everything related to viewing, creating, editing, and approving financial transactions in the application.

Think of it like a **digital paperwork desk** where:
- **Sales teams** upload new deals (transactions) and submit them for approval
- **Finance teams** review those deals, check the numbers, and either approve or reject them

The folder contains 39 files that work together to:
- Show lists of transactions in a table format
- Display key metrics (like pending approvals, total value, profit margins)
- Let users click on a transaction to see its full details in a popup window
- Allow editing of transaction data with live recalculation of financial metrics
- Handle the approval/rejection workflow

---

## 2. The Flow

### Where does data come from?

1. **From the Backend API** - When you open the transactions page:
   - The system calls the server to fetch a list of transactions
   - It also fetches summary statistics (KPIs) like "5 pending approvals" or "Total value: $50,000"

2. **From User Uploads** - Sales users can:
   - Upload Excel files containing transaction data
   - The system parses the file and shows a preview before saving

### Where does data go?

1. **To the Screen** - Data flows through these steps:
   ```
   Backend API → Services (format the data) → Hooks (manage loading states) → Components (display on screen)
   ```

2. **Back to the Backend** - When users take action:
   - **Sales submits a transaction** → Data sent to server → Saved in database
   - **Finance approves/rejects** → Status update sent to server → Transaction state changes
   - **User edits values** → Changes sent for recalculation → Updated metrics returned and displayed

### Visual Flow:
```
[User Opens Page]
       ↓
[Fetch Transaction List] ←→ [Backend API]
       ↓
[Display in Table]
       ↓
[User Clicks a Row]
       ↓
[Fetch Full Details] ←→ [Backend API]
       ↓
[Show in Popup Modal]
       ↓
[User Edits Values]
       ↓
[Send for Recalculation] ←→ [Backend API] (with 1.5 second delay to avoid too many calls)
       ↓
[Display Updated Metrics]
       ↓
[User Clicks Approve/Submit]
       ↓
[Save to Backend] ←→ [Backend API]
       ↓
[Refresh List & Statistics]
```

---

## 3. The Repeats (Repeated Patterns)

### Pattern A: "Sales vs Finance" Switch
The code constantly checks: "Are we in Sales view or Finance view?" and shows different things accordingly.

**Example locations:**
- Different tables for each view
- Different statistics cards
- Different action buttons in the popup footer

This pattern appears in almost every file.

### Pattern B: "Try, Check, Return" for API Calls
Every time the code talks to the server, it follows this exact pattern:
```
1. Try to call the API
2. Check if it worked (success = true?)
3. If yes: format the data and return it
4. If no: return an error message
```

This is repeated in all 4 service files.

### Pattern C: "Fetch Details When Clicked"
When a user clicks on any row in the table:
1. Call the server to get full details
2. Store the details in memory
3. Open the popup modal
4. Display the details

This same pattern is used for both Sales and Finance views.

### Pattern D: "Edit, Wait, Recalculate"
When users edit values in the popup:
1. Update the value immediately on screen
2. Wait 1.5 seconds (in case they're still typing)
3. Send all values to the server
4. Server recalculates metrics (profit, margin, etc.)
5. Display the new calculated values

### Pattern E: "Formatted Types"
The raw data from the API contains many fields. Each view creates a "formatted" version with only the fields needed for display.

---

## 4. The Connections

### Folders This Feature Depends On:

| Folder/File | What It Provides |
|-------------|------------------|
| `@/lib/api` | The tool to talk to the backend server |
| `@/config` | All text labels, error messages, button names, status values |
| `@/types` | Definitions of what a "Transaction", "FixedCost", etc. look like |
| `@/components/ui/table` | Ready-made table components (Table, TableRow, TableCell) |
| `@/components/ui/card` | Ready-made card components for statistics display |
| `@/components/shared/Icons` | Icons like Upload, Warning, Check, Dollar sign |
| `@/lib/formatters` | Functions to format currency ($1,234.56) and other data |
| `@/hooks/useDebounce` | The "wait before sending" functionality |
| `@/contexts/AuthContext` | Information about who is logged in |

### Key External Files:
- **API_CONFIG.ENDPOINTS** - URLs for all server calls
- **TRANSACTION_STATUS** - Possible statuses: PENDING, APPROVED, REJECTED
- **UI_LABELS, ERROR_MESSAGES, BUTTON_LABELS** - All text shown to users

---

## 5. The Identity

### Label: **"The Approval Desk"**

### Why This Label?

This folder is like a **processing desk** where financial transactions arrive, get reviewed, and either move forward (approved) or get sent back (rejected).

Just like a real approval desk:
- **Transactions arrive** (uploaded by Sales or fetched from the system)
- **They sit in a queue** (the pending transactions list)
- **Reviewers examine them** (Finance opens the detail modal)
- **Numbers are checked** (KPIs are calculated and displayed)
- **Decisions are made** (Approve, Reject, or Request Changes)
- **Records are kept** (everything is saved to the backend)

The folder doesn't store the actual data (that's the backend/database's job), and it doesn't make business decisions (that's the human's job). It simply provides the **desk, the paperwork, and the stamps** needed to process transactions through an approval workflow.

---

## File Structure Summary

```
src/features/transactions/
├── TransactionDashboard.tsx    ← Main orchestrator (the desk itself)
├── index.ts                    ← Public exports
├── services/                   ← Backend communication (4 files)
│   ├── sales.service.ts        ← Sales-specific API calls
│   ├── finance.service.ts      ← Finance-specific API calls
│   ├── kpi.service.ts          ← Statistics fetching
│   └── shared.service.ts       ← Shared recalculation
├── hooks/                      ← State management (2 files)
│   ├── useTransactionDashboard.ts
│   └── useTransactionPreviewReducer.ts
├── contexts/                   ← Shared state for popup (1 file)
│   └── TransactionPreviewContext.tsx
├── components/                 ← Visual elements (28 files)
│   ├── Layout components
│   ├── Stats/KPI cards
│   ├── Transaction tables
│   ├── Preview modal content
│   ├── Fixed costs components
│   ├── Recurring services components
│   └── Supporting UI elements
└── footers/                    ← Action buttons (2 files)
    ├── SalesPreviewFooter.tsx
    └── FinancePreviewFooter.tsx
```

**Total: 39 files working together as "The Approval Desk"**
