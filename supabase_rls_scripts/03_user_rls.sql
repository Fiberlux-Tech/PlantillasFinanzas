-- ============================================================================
-- SUPABASE RLS SCRIPT 3: USER TABLE (Optional but Recommended)
-- ============================================================================
-- Run this script in: Supabase Dashboard → SQL Editor
-- Purpose: Enable Row Level Security on user table
-- Access: Users can view their own profile, ADMIN can manage all users
-- ============================================================================

-- Enable RLS on user table
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- POLICY 1: Users can view their own profile
-- ============================================================================
CREATE POLICY "users_view_own_profile"
ON "user"
FOR SELECT
USING (id = auth.uid()::text);

-- ============================================================================
-- POLICY 2: ADMIN can view all users
-- ============================================================================
CREATE POLICY "admin_view_all_users"
ON "user"
FOR SELECT
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) = 'ADMIN'
);

-- ============================================================================
-- POLICY 3: Only ADMIN can modify users
-- ============================================================================
-- This policy covers INSERT, UPDATE, and DELETE operations
CREATE POLICY "admin_modify_users"
ON "user"
FOR ALL  -- INSERT, UPDATE, DELETE
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
WHERE tablename = 'user';
