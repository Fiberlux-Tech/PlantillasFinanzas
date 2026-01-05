-- ============================================================================
-- SUPABASE RLS SCRIPT 2: MASTER_VARIABLE TABLE
-- ============================================================================
-- Run this script in: Supabase Dashboard → SQL Editor
-- Purpose: Enable Row Level Security on master_variable table
-- Access: Only FINANCE and ADMIN roles can read/modify master variables
-- ============================================================================

-- Enable Row Level Security on master_variable table
ALTER TABLE master_variable ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- POLICY 1: Only FINANCE and ADMIN can read master variables
-- ============================================================================
CREATE POLICY "finance_admin_view_master_variables"
ON master_variable
FOR SELECT
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) IN ('FINANCE', 'ADMIN')
);

-- ============================================================================
-- POLICY 2: Only FINANCE and ADMIN can modify master variables
-- ============================================================================
-- This policy covers INSERT, UPDATE, and DELETE operations
CREATE POLICY "finance_admin_modify_master_variables"
ON master_variable
FOR ALL  -- INSERT, UPDATE, DELETE
USING (
  (
    SELECT role FROM "user"
    WHERE id = auth.uid()::text
  ) IN ('FINANCE', 'ADMIN')
);

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- After running this script, verify policies were created:
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE tablename = 'master_variable';
