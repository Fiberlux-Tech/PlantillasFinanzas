// src/features/auth/authService.ts
/**
 * Authentication Service - Pure JWT Implementation with Supabase
 *
 * This service provides a clean interface for authentication operations
 * using Supabase Auth with Pure JWT architecture.
 *
 * ARCHITECTURE: Pure JWT Authentication
 * - Uses Supabase for authentication (JWT tokens)
 * - Frontend self-hydrates by decoding access_token (no /api/me call)
 * - Token is single source of truth
 * - Backend validates JWT tokens using @require_jwt decorator
 * - Session stored in localStorage, auto-refreshed by Supabase client
 *
 * CTO's Warning - The "Metadata" Bridge:
 * Backend app/jwt_auth.py reads 'role' from JWT user_metadata.
 * Registration MUST include { username, role } in options.data or
 * Finance users will be treated as SALES users.
 */

import { supabase } from '@/lib/supabase';
import { decodeUserFromToken, validateTokenMetadata } from '@/lib/jwtUtils';
import type { User } from '@/types';

// 1. Define the return types for our service functions
export interface AuthSuccessData extends User {}

type AuthResult = {
    success: true;
    data: AuthSuccessData;
} | {
    success: false;
    error: string;
}

type LogoutResult = {
    success: true;
} | {
    success: false;
    error: string;
}

export type AuthStatus = {
    is_authenticated: true;
    user: User;
} | {
    is_authenticated: false;
    error: string;
}

/**
 * Attempts to log in a user using Supabase Auth.
 *
 * PURE JWT FLOW:
 * 1. Call Supabase signInWithPassword with email and password
 * 2. Supabase returns JWT token (automatically stored in localStorage)
 * 3. Decode token to extract user data (email, role, username)
 * 4. Return decoded user data directly (NO backend call)
 *
 * ARCHITECTURAL CHANGE:
 * - UI now uses Email field instead of Username
 * - Corporate emails for authentication (prepares for SSO)
 * - Token is single source of truth
 *
 * @param email - User's corporate email address
 * @param password - User's password
 * @returns AuthResult with user data or error
 */
export async function loginUser(email: string, password: string): Promise<AuthResult> {
    try {
        // Sign in with Supabase
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password,
        });

        if (error) {
            // Supabase auth error (invalid credentials, user not found, etc.)
            return { success: false, error: error.message };
        }

        if (!data.session) {
            // No session returned (shouldn't happen if no error, but defensive)
            return { success: false, error: 'Login failed: No session returned' };
        }

        // PURE JWT: Decode token to extract user data (no /api/me call)
        const user = decodeUserFromToken(data.session.access_token);

        return { success: true, data: user };

    } catch (error: any) {
        // Network error or token decoding error
        return { success: false, error: error.message || 'Login failed.' };
    }
}

/**
 * Attempts to register a new user using Supabase Auth.
 *
 * PURE JWT FLOW:
 * 1. Call Supabase signUp with email, password, and user_metadata
 * 2. Supabase creates user and returns JWT token (automatically stored)
 * 3. User_metadata (username, role) is stored in JWT token claims
 * 4. Decode token to extract user data
 * 5. Backend extracts username/role from JWT user_metadata claims
 *
 * CTO's WARNING - THE "METADATA" BRIDGE:
 * Must include { username, role } in options.data (user_metadata).
 * Backend app/jwt_auth.py (lines 148-149) reads these from token.
 * If missing, backend defaults to role='SALES' and derives username from email.
 * CRITICAL RISK: Finance users can't approve anything if role not set correctly.
 *
 * @param username - Desired username (derived from email if not provided)
 * @param email - User's corporate email address
 * @param password - User's password
 * @returns AuthResult with user data or error
 */
export async function registerUser(username: string, email: string, password: string): Promise<AuthResult> {
    try {
        // Derive username from email if not provided
        const finalUsername = username || email.split('@')[0];

        // Sign up with Supabase
        // CRITICAL: Include username and role in user_metadata
        // Backend jwt_auth.py expects these fields in JWT token claims
        const { data, error } = await supabase.auth.signUp({
            email: email,
            password: password,
            options: {
                data: {
                    // CRITICAL: These fields MUST be in user_metadata
                    // Backend jwt_auth.py line 148: username = user_metadata.get('username')
                    // Backend jwt_auth.py line 149: role = user_metadata.get('role', 'SALES')
                    username: finalUsername,
                    role: 'SALES', // Default role for new users (can be changed by admin later)
                }
            }
        });

        if (error) {
            // Supabase registration error (email already exists, weak password, etc.)
            return { success: false, error: error.message };
        }

        if (!data.session) {
            // Email confirmation might be required
            // Check your Supabase Dashboard → Authentication → Settings → Email Auth
            // If "Confirm email" is enabled, user must verify email before logging in
            return {
                success: false,
                error: 'Registration successful! Please check your email to confirm your account before logging in.'
            };
        }

        // PURE JWT: Decode token to extract user data (no /api/me call)
        const user = decodeUserFromToken(data.session.access_token);

        // CRITICAL VERIFICATION: Validate that metadata was set correctly
        const validation = validateTokenMetadata(data.session.access_token);
        if (!validation.valid) {
            console.error(
                'CTO WARNING: Token missing required metadata:',
                validation.missingFields,
                'This will cause permission issues!'
            );
        }

        return { success: true, data: user };

    } catch (error: any) {
        // Network error, Supabase error, or token decoding error
        return { success: false, error: error.message || 'Registration failed.' };
    }
}

/**
 * Logs out the current user.
 *
 * PURE JWT FLOW:
 * 1. Call Supabase signOut to invalidate session
 * 2. Supabase removes JWT token from localStorage
 * 3. No backend call needed (stateless auth - backend doesn't track sessions)
 *
 * @returns LogoutResult indicating success or error
 */
export async function logoutUser(): Promise<LogoutResult> {
    try {
        // Sign out from Supabase
        // This will:
        // - Remove JWT token from localStorage
        // - Invalidate the refresh token server-side
        // - Clear all session data
        const { error } = await supabase.auth.signOut();

        if (error) {
            return { success: false, error: error.message };
        }

        return { success: true };

    } catch (error: any) {
        // Network error or Supabase error
        return { success: false, error: error.message || 'Logout failed.' };
    }
}

/**
 * Checks if a user is authenticated by decoding the JWT token.
 *
 * PURE JWT STRATEGY:
 * We decode the access_token directly instead of calling /api/me.
 * The token is the single source of truth for user data.
 *
 * WHY PURE JWT (NO /api/me)?
 * - Token contains all user data (id, email, username, role) in user_metadata
 * - No backend roundtrip needed → faster authentication check
 * - Backend only validates token when accessing protected endpoints
 * - Simpler architecture, fewer moving parts
 *
 * FLOW:
 * 1. Get Supabase session from localStorage
 * 2. If session exists, decode access_token to extract user data
 * 3. Return user data from token claims
 * 4. If no session or token invalid, return not authenticated
 *
 * @returns AuthStatus with user data or not authenticated
 */
export async function checkAuthStatus(): Promise<AuthStatus> {
    try {
        // Get current session from Supabase (stored in localStorage)
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) {
            // No session in localStorage - user not logged in
            return { is_authenticated: false, error: 'No active session' };
        }

        // PURE JWT: Decode token to extract user data (no /api/me call)
        const user = decodeUserFromToken(session.access_token);

        return { is_authenticated: true, user };

    } catch (error: any) {
        // Token decoding failed - token invalid or malformed
        // This will happen if:
        // 1. Token format is invalid
        // 2. Token is corrupted in localStorage
        // 3. User manually edited localStorage

        // Clear the invalid session from Supabase
        await supabase.auth.signOut();

        return { is_authenticated: false, error: error.message || 'Failed to check authentication status.' };
    }
}
