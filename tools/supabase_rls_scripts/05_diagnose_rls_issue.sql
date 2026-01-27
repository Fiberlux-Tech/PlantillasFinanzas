-- ============================================================================
-- SUPABASE RLS DIAGNOSTIC SCRIPT
-- ============================================================================
-- Run this in Supabase Dashboard → SQL Editor to diagnose RLS issues
-- ============================================================================

-- ============================================================================
-- 1. CHECK WHICH TABLES HAVE RLS ENABLED
-- ============================================================================
SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- ============================================================================
-- 2. CHECK ALL EXISTING POLICIES
-- ============================================================================
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd AS operation,
    qual AS using_expression,
    with_check AS check_expression
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================================
-- 3. CHECK IF auth.uid() IS WORKING
-- ============================================================================
-- This should return your current Supabase user UUID
-- If it returns NULL, JWT authentication is not working
SELECT auth.uid() AS current_user_uuid;

-- ============================================================================
-- 4. CHECK IF YOUR USER EXISTS IN THE USER TABLE
-- ============================================================================
-- Replace 'your-uuid-here' with the result from auth.uid() above
SELECT id, username, email, role
FROM "user"
WHERE id = auth.uid()::text;

-- ============================================================================
-- 5. TEST POLICY LOGIC MANUALLY
-- ============================================================================
-- This tests if the policy conditions would work for a specific user
-- Replace 'your-uuid-here' with your actual UUID

-- Test: Can current user see transactions?
SELECT
    t.id,
    t.salesman,
    u.id AS user_id,
    u.username,
    u.role,
    CASE
        WHEN auth.uid()::text = u.id THEN 'Matches user (via salesman)'
        WHEN u.role IN ('FINANCE', 'ADMIN') THEN 'Allowed by role'
        ELSE 'BLOCKED'
    END AS access_status
FROM transactions t
LEFT JOIN "user" u ON u.username = t.salesman
WHERE auth.uid()::text IS NOT NULL
LIMIT 10;

-- ============================================================================
-- 6. COUNT POLICIES PER TABLE
-- ============================================================================
SELECT
    tablename,
    COUNT(*) AS policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY tablename;

-- ============================================================================
-- EXPECTED RESULTS
-- ============================================================================
-- Query 1: Should show rls_enabled = true for transactions, master_variable, user
-- Query 2: Should show 9 total policies (4 + 2 + 3)
-- Query 3: Should return a UUID (not NULL)
-- Query 4: Should return your user record
-- Query 5: Should show 'Allowed by role' or 'Matches user'
-- Query 6: Should show:
--   - transactions: 4
--   - master_variable: 2
--   - user: 3
--
-- ============================================================================
-- COMMON ISSUES AND FIXES
-- ============================================================================
--
-- ISSUE 1: auth.uid() returns NULL
-- CAUSE: JWT token not being passed or not configured correctly
-- FIX: Verify SUPABASE_JWT_SECRET in backend .env matches Supabase Dashboard
--
-- ISSUE 2: User record doesn't exist in database
-- CAUSE: Supabase Auth user created but not synced to 'user' table
-- FIX: Manually insert user record with Supabase UUID
--
-- ISSUE 3: Policies created but still showing UNRESTRICTED
-- CAUSE: This is normal - UNRESTRICTED means "no public access without auth"
-- FIX: No fix needed - test from your application with JWT token
--
-- ISSUE 4: Policies blocking legitimate access
-- CAUSE: Policy logic doesn't match your data structure
-- FIX: Review policy conditions and adjust as needed
--
-- ============================================================================
