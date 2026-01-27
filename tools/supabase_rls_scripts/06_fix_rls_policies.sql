-- ============================================================================
-- SUPABASE RLS FIX: Add Bypass Policies for Service Role
-- ============================================================================
-- Run this in Supabase Dashboard → SQL Editor
--
-- PROBLEM: RLS policies only work when authenticated via Supabase Auth.
-- Your Python backend connects using a connection string (not Supabase Auth),
-- so auth.uid() returns NULL, blocking all access.
--
-- SOLUTION: Add policies that allow access from service role (backend connection)
-- while still enforcing RLS for direct Supabase client access.
-- ============================================================================

-- ============================================================================
-- OPTION 1: DISABLE RLS (Recommended for Backend-Only Applications)
-- ============================================================================
-- If your application ONLY uses the Python backend (not direct Supabase client),
-- you can safely disable RLS since the Python backend enforces role-based access.

-- Uncomment these lines to disable RLS:
-- ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE master_variable DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE "user" DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- OPTION 2: ADD SERVICE ROLE BYPASS POLICIES (Keep RLS for Client Access)
-- ============================================================================
-- If you want to keep RLS active for future Supabase client access,
-- add these bypass policies that allow service role (your backend) to access everything.

-- STEP 1: Drop existing policies (we'll recreate them with service role bypass)
DROP POLICY IF EXISTS "sales_view_own_transactions" ON transactions;
DROP POLICY IF EXISTS "sales_insert_own_transactions" ON transactions;
DROP POLICY IF EXISTS "finance_admin_update_transactions" ON transactions;
DROP POLICY IF EXISTS "admin_delete_transactions" ON transactions;

DROP POLICY IF EXISTS "finance_admin_view_master_variables" ON master_variable;
DROP POLICY IF EXISTS "finance_admin_modify_master_variables" ON master_variable;

DROP POLICY IF EXISTS "users_view_own_profile" ON "user";
DROP POLICY IF EXISTS "admin_view_all_users" ON "user";
DROP POLICY IF EXISTS "admin_modify_users" ON "user";

-- STEP 2: Recreate policies with service role bypass

-- ============================================================================
-- TRANSACTIONS TABLE - With Service Role Bypass
-- ============================================================================

-- Policy: Allow service role (backend) full access
CREATE POLICY "service_role_all_transactions"
ON transactions
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Authenticated users - Sales see own, Finance/Admin see all
CREATE POLICY "authenticated_view_transactions"
ON transactions
FOR SELECT
TO authenticated
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

-- Policy: Authenticated users - Sales insert own
CREATE POLICY "authenticated_insert_transactions"
ON transactions
FOR INSERT
TO authenticated
WITH CHECK (
  auth.uid()::text = (
    SELECT id FROM "user"
    WHERE username = transactions.salesman
  )
);

-- Policy: Authenticated users - Finance/Admin update
CREATE POLICY "authenticated_update_transactions"
ON transactions
FOR UPDATE
TO authenticated
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) IN ('FINANCE', 'ADMIN')
);

-- Policy: Authenticated users - Admin delete
CREATE POLICY "authenticated_delete_transactions"
ON transactions
FOR DELETE
TO authenticated
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) = 'ADMIN'
);

-- ============================================================================
-- MASTER_VARIABLE TABLE - With Service Role Bypass
-- ============================================================================

-- Policy: Allow service role (backend) full access
CREATE POLICY "service_role_all_master_variables"
ON master_variable
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Authenticated users - Finance/Admin only
CREATE POLICY "authenticated_view_master_variables"
ON master_variable
FOR SELECT
TO authenticated
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) IN ('FINANCE', 'ADMIN')
);

CREATE POLICY "authenticated_modify_master_variables"
ON master_variable
FOR ALL
TO authenticated
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) IN ('FINANCE', 'ADMIN')
);

-- ============================================================================
-- USER TABLE - With Service Role Bypass
-- ============================================================================

-- Policy: Allow service role (backend) full access
CREATE POLICY "service_role_all_users"
ON "user"
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Authenticated users - View own profile
CREATE POLICY "authenticated_view_own_profile"
ON "user"
FOR SELECT
TO authenticated
USING (id = auth.uid()::text);

-- Policy: Authenticated users - Admin view all
CREATE POLICY "authenticated_admin_view_all_users"
ON "user"
FOR SELECT
TO authenticated
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) = 'ADMIN'
);

-- Policy: Authenticated users - Admin modify all
CREATE POLICY "authenticated_admin_modify_users"
ON "user"
FOR ALL
TO authenticated
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) = 'ADMIN'
);

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- Check that policies were created successfully
SELECT
    tablename,
    policyname,
    roles,
    cmd AS operation
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Expected result:
-- - Each table should have policies for 'service_role' AND 'authenticated'
-- - service_role policies allow full access (bypasses RLS for backend)
-- - authenticated policies enforce role-based access for client connections

-- ============================================================================
-- EXPLANATION
-- ============================================================================
--
-- Your Python backend connects to Supabase using a PostgreSQL connection string:
-- postgresql://postgres.eyizlvev...@aws-0-us-west-2.pooler.supabase.com:6543/postgres
--
-- This connection uses the 'service_role' PostgreSQL role, NOT Supabase Auth.
-- Therefore, auth.uid() returns NULL, and the original policies blocked all access.
--
-- By adding 'TO service_role' policies with USING (true), we allow the backend
-- to bypass RLS while still enforcing RLS for Supabase client connections.
--
-- SECURITY NOTES:
-- - Your Python backend enforces role-based access via @require_jwt decorator
-- - RLS is an additional layer for direct database/client access
-- - service_role bypass is safe because only your backend has service_role credentials
--
-- ============================================================================
