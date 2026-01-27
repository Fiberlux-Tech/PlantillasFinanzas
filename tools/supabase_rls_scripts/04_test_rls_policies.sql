-- ============================================================================
-- SUPABASE RLS TESTING SCRIPT
-- ============================================================================
-- Run this script in: Supabase Dashboard → SQL Editor
-- Purpose: Test RLS policies with different user roles
-- ============================================================================

-- ============================================================================
-- VIEW ALL ENABLED RLS TABLES
-- ============================================================================
SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
    AND rowsecurity = true;

-- ============================================================================
-- VIEW ALL POLICIES
-- ============================================================================
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    cmd AS operation,
    CASE
        WHEN cmd = 'SELECT' THEN 'Read'
        WHEN cmd = 'INSERT' THEN 'Create'
        WHEN cmd = 'UPDATE' THEN 'Modify'
        WHEN cmd = 'DELETE' THEN 'Remove'
        WHEN cmd = 'ALL' THEN 'All Operations'
    END AS operation_description
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================================
-- COUNT POLICIES PER TABLE
-- ============================================================================
SELECT
    tablename,
    COUNT(*) AS policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- ============================================================================
-- TESTING NOTES
-- ============================================================================
-- To test RLS policies effectively, you need to:
--
-- 1. Create test users with different roles in Supabase Auth
-- 2. Generate JWT tokens for each test user
-- 3. Make API calls from your Python backend with those tokens
-- 4. Verify that:
--    - SALES users see only their own transactions
--    - FINANCE users see all transactions
--    - ADMIN can manage users
--    - Unauthorized access is blocked
--
-- Example test scenarios:
--
-- SALES User Test:
-- - Should see transactions where salesman = their username
-- - Should NOT see other salespeople's transactions
-- - Should NOT see master variables
-- - Should NOT be able to update transactions
--
-- FINANCE User Test:
-- - Should see ALL transactions
-- - Should see master variables
-- - Should be able to update transactions
-- - Should NOT be able to delete users
--
-- ADMIN User Test:
-- - Should have full access to all tables
-- - Should be able to manage users
-- - Should be able to delete transactions
--
-- ============================================================================
-- DISABLE RLS (Emergency Rollback - Use with Caution)
-- ============================================================================
-- If RLS is blocking legitimate access, you can temporarily disable it:
--
-- ALTER TABLE transactions DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE master_variable DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE "user" DISABLE ROW LEVEL SECURITY;
--
-- WARNING: Only use this for troubleshooting. Re-enable RLS after fixing policies.
-- ============================================================================
