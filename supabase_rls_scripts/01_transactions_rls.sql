-- ============================================================================
-- SUPABASE RLS SCRIPT 1: TRANSACTIONS TABLE
-- ============================================================================
-- Run this script in: Supabase Dashboard → SQL Editor
-- Purpose: Enable Row Level Security on transactions table with role-based access
-- ============================================================================

-- Enable Row Level Security on transactions table
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- POLICY 1: Sales users can view their own transactions
-- ============================================================================
CREATE POLICY "sales_view_own_transactions"
ON transactions
FOR SELECT
USING (
  -- Allow if user is viewing their own data
  auth.uid()::text = (
    SELECT id FROM "user"
    WHERE username = transactions.salesman
  )
  OR
  -- Allow if user has FINANCE or ADMIN role
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) IN ('FINANCE', 'ADMIN')
);

-- ============================================================================
-- POLICY 2: Sales users can only insert their own transactions
-- ============================================================================
CREATE POLICY "sales_insert_own_transactions"
ON transactions
FOR INSERT
WITH CHECK (
  auth.uid()::text = (
    SELECT id FROM "user"
    WHERE username = transactions.salesman
  )
);

-- ============================================================================
-- POLICY 3: Only FINANCE/ADMIN can update transactions
-- ============================================================================
CREATE POLICY "finance_admin_update_transactions"
ON transactions
FOR UPDATE
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) IN ('FINANCE', 'ADMIN')
);

-- ============================================================================
-- POLICY 4: Only ADMIN can delete transactions
-- ============================================================================
CREATE POLICY "admin_delete_transactions"
ON transactions
FOR DELETE
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) = 'ADMIN'
);

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- After running this script, verify policies were created:
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'transactions';
