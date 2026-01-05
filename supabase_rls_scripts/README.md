# Supabase Row Level Security (RLS) Setup

## Overview
This directory contains SQL scripts to enable Row Level Security (RLS) on your Supabase database. RLS provides **defense-in-depth security** by enforcing access control at the database layer, even if the Python API is bypassed.

## Prerequisites
- Supabase project created at: https://eyizlvevbpkhsddwbxrx.supabase.co
- Database migrations already applied (User.id is String/UUID)
- Access to Supabase Dashboard

## Execution Order

Run these scripts in **sequential order** in the Supabase Dashboard → SQL Editor:

### 1. Transactions Table RLS
**File**: `01_transactions_rls.sql`

**What it does**:
- Enables RLS on `transactions` table
- Creates 4 policies:
  - **SELECT**: Sales users see only their own transactions; Finance/Admin see all
  - **INSERT**: Sales users can only insert their own transactions
  - **UPDATE**: Only Finance/Admin can update transactions
  - **DELETE**: Only Admin can delete transactions

**Why it matters**: Protects sensitive financial data. Sales reps can't view competitors' deals.

---

### 2. Master Variable Table RLS
**File**: `02_master_variable_rls.sql`

**What it does**:
- Enables RLS on `master_variable` table
- Creates 2 policies:
  - **SELECT**: Only Finance/Admin can view master variables
  - **ALL (INSERT/UPDATE/DELETE)**: Only Finance/Admin can modify master variables

**Why it matters**: Master variables (exchange rates, cost thresholds) are critical financial parameters. Only authorized roles should access them.

---

### 3. User Table RLS (Optional but Recommended)
**File**: `03_user_rls.sql`

**What it does**:
- Enables RLS on `user` table
- Creates 3 policies:
  - **SELECT (Own Profile)**: Users can view their own profile
  - **SELECT (All Users)**: Admin can view all users
  - **ALL (INSERT/UPDATE/DELETE)**: Only Admin can modify users

**Why it matters**: Prevents users from seeing other users' email addresses or roles. Only Admin manages user accounts.

---

### 4. Test and Verify RLS
**File**: `04_test_rls_policies.sql`

**What it does**:
- Shows all RLS-enabled tables
- Lists all policies created
- Provides testing guidance
- Includes emergency disable commands (for troubleshooting only)

**Why it matters**: Verification ensures policies are active and correctly configured.

---

## Step-by-Step Execution Guide

### Using Supabase Dashboard (Recommended)

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard
   - Navigate to your project: `plantilla-finanzas`

2. **Access SQL Editor**
   - Click on **"SQL Editor"** in left sidebar
   - Click **"New Query"** button

3. **Run Scripts Sequentially**

   **Script 1 - Transactions RLS**:
   - Open `01_transactions_rls.sql` in text editor
   - Copy entire contents
   - Paste into Supabase SQL Editor
   - Click **"Run"** button
   - Verify: You should see "Success. No rows returned" or policy creation messages

   **Script 2 - Master Variable RLS**:
   - Open `02_master_variable_rls.sql`
   - Copy entire contents
   - Paste into Supabase SQL Editor
   - Click **"Run"** button
   - Verify success

   **Script 3 - User RLS**:
   - Open `03_user_rls.sql`
   - Copy entire contents
   - Paste into Supabase SQL Editor
   - Click **"Run"** button
   - Verify success

   **Script 4 - Verification**:
   - Open `04_test_rls_policies.sql`
   - Copy entire contents
   - Paste into Supabase SQL Editor
   - Click **"Run"** button
   - **Review output**: You should see 9 total policies (4 + 2 + 3)

4. **Expected Results**

   After running all scripts, you should see:
   - **transactions**: 4 policies
   - **master_variable**: 2 policies
   - **user**: 3 policies

   Example output from verification query:
   ```
   | tablename       | policy_count |
   |----------------|-------------|
   | transactions    | 4           |
   | master_variable | 2           |
   | user            | 3           |
   ```

---

## How RLS Works

### Authentication Flow
1. User logs in via Supabase (frontend)
2. Supabase issues JWT token containing `auth.uid()` (user's UUID)
3. Backend verifies JWT and extracts user context
4. Database queries automatically filtered by RLS policies

### Policy Enforcement
- **Python code doesn't change** - it continues making normal queries
- **Database enforces policies** - automatically filters results based on `auth.uid()` and user role
- **Works with direct database access** - even if someone bypasses the API, RLS still protects data

### Example: Sales User Query
```python
# Python code (unchanged)
transactions = Transaction.query.all()

# Without RLS: Returns ALL transactions
# With RLS: Database automatically filters to only transactions where salesman = current_user.username
```

---

## Testing RLS Policies

### Manual Testing Steps

1. **Create Test Users** (Supabase Dashboard → Authentication → Users):
   - Sales user: `test_sales@example.com` (role: SALES)
   - Finance user: `test_finance@example.com` (role: FINANCE)
   - Admin user: `test_admin@example.com` (role: ADMIN)

2. **Test from Python Backend**:
   ```python
   # Login as each user via Supabase
   # Make API calls to /api/transactions
   # Verify each user sees appropriate data
   ```

3. **Expected Behavior**:
   - **SALES**: Sees only transactions where `salesman = their_username`
   - **FINANCE**: Sees all transactions, can update them
   - **ADMIN**: Full access to everything

### Automated Testing
Implement integration tests in your test suite:
```python
def test_sales_user_sees_only_own_transactions():
    # Login as sales user
    # Query transactions
    # Assert all results have salesman = current_user.username

def test_finance_user_sees_all_transactions():
    # Login as finance user
    # Query transactions
    # Assert results include multiple salesmen
```

---

## Troubleshooting

### Issue: Policies blocking legitimate access

**Symptom**: Users can't see data they should be able to access

**Solution**:
1. Check user's role in database: `SELECT * FROM "user" WHERE email = 'user@example.com';`
2. Verify JWT token contains correct `auth.uid()`: Check backend logs
3. Temporarily disable RLS for testing:
   ```sql
   ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
   ```
4. Test if issue resolves (if yes, policy needs adjustment)
5. Re-enable RLS after fixing policy:
   ```sql
   ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
   ```

### Issue: Policy syntax errors

**Symptom**: "ERROR: syntax error at or near..." when running script

**Solution**:
- Ensure you're copying the entire script (including semicolons)
- Check for special characters that may have been corrupted during copy/paste
- Try running each policy creation separately

### Issue: Policies not filtering data

**Symptom**: All users see all data despite RLS enabled

**Possible Causes**:
1. **JWT not being sent**: Verify frontend includes token in Authorization header
2. **auth.uid() returns NULL**: Check if Supabase JWT is properly configured
3. **User not in database**: Verify user record exists in `user` table with correct `id` matching Supabase UUID

**Debug Query**:
```sql
-- Check if auth.uid() is working
SELECT auth.uid();

-- Should return: Your Supabase user UUID (when logged in)
-- If returns NULL: JWT authentication is not working
```

---

## Rollback Procedure

If you need to completely remove RLS:

```sql
-- Disable RLS on all tables
ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE master_variable DISABLE ROW LEVEL SECURITY;
ALTER TABLE "user" DISABLE ROW LEVEL SECURITY;

-- Drop all policies
DROP POLICY IF EXISTS "sales_view_own_transactions" ON transactions;
DROP POLICY IF EXISTS "sales_insert_own_transactions" ON transactions;
DROP POLICY IF EXISTS "finance_admin_update_transactions" ON transactions;
DROP POLICY IF EXISTS "admin_delete_transactions" ON transactions;

DROP POLICY IF EXISTS "finance_admin_view_master_variables" ON master_variable;
DROP POLICY IF EXISTS "finance_admin_modify_master_variables" ON master_variable;

DROP POLICY IF EXISTS "users_view_own_profile" ON "user";
DROP POLICY IF EXISTS "admin_view_all_users" ON "user";
DROP POLICY IF EXISTS "admin_modify_users" ON "user";
```

**Warning**: Only use rollback for troubleshooting. Running without RLS removes database-level security.

---

## Security Best Practices

1. **Defense in Depth**: RLS is an **additional layer**, not a replacement for:
   - JWT authentication (verifies user identity)
   - Python role checks (validates permissions)
   - Input validation (prevents injection attacks)

2. **Least Privilege**: Policies enforce minimum necessary access:
   - Sales: Own data only
   - Finance: Financial operations
   - Admin: User management

3. **Audit Trail**: Consider adding logging:
   ```sql
   -- Example: Log all transaction updates
   CREATE TABLE audit_log (
       id SERIAL PRIMARY KEY,
       table_name TEXT,
       operation TEXT,
       user_id TEXT,
       timestamp TIMESTAMP DEFAULT NOW()
   );
   ```

4. **Regular Review**: Periodically verify policies:
   ```sql
   -- Run verification query
   SELECT * FROM pg_policies WHERE schemaname = 'public';
   ```

---

## Integration with Backend

### No Code Changes Required
Your Python backend continues working as before. RLS operates transparently:

```python
# app/services/transactions.py (unchanged)
def get_transactions():
    # This query is automatically filtered by RLS
    transactions = Transaction.query.all()
    return transactions

# For SALES user: Returns only their transactions
# For FINANCE user: Returns all transactions
# For unauthenticated: Returns empty (401 from @require_jwt)
```

### JWT Token Flow
1. Frontend sends request with `Authorization: Bearer <supabase_jwt>`
2. Backend `@require_jwt` decorator verifies token
3. SQLAlchemy executes query
4. **PostgreSQL checks RLS policies** using `auth.uid()` from token
5. Results automatically filtered
6. Backend returns filtered data to frontend

---

## Next Steps

After running these scripts:

1. ✅ **Verify Policies Created**: Run `04_test_rls_policies.sql`
2. ✅ **Test with Different Roles**: Create test users and verify access
3. ✅ **Monitor Logs**: Check Supabase logs for RLS policy violations
4. ✅ **Update Documentation**: Document role-based access in your API docs
5. ✅ **Deploy to Production**: No backend changes needed - just run scripts in prod Supabase

---

## Support

If you encounter issues:
1. Check Supabase logs: Dashboard → Logs → Postgres Logs
2. Review policy definitions: `SELECT * FROM pg_policies WHERE tablename = 'your_table';`
3. Test with simple queries first before complex filtering
4. Consult Supabase RLS documentation: https://supabase.com/docs/guides/auth/row-level-security

---

**Phase 2 Status**: Backend consolidation ✅ | Frontend handshake ✅ | RLS scripts ready ⏳

**Last Updated**: 2026-01-05
