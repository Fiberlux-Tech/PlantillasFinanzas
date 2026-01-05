// src/lib/jwtUtils.ts
/**
 * JWT Token Utilities for Pure JWT Authentication
 *
 * This module provides helper functions for decoding Supabase JWT tokens
 * to extract user data on the frontend without backend calls.
 *
 * ARCHITECTURE: Pure JWT Model
 * - Token is single source of truth
 * - Frontend self-hydrates by decoding access_token
 * - No /api/me endpoint needed
 * - Backend validates token via @require_jwt decorator
 *
 * CTO's Warning - The "Metadata" Bridge:
 * Backend app/jwt_auth.py (lines 148-149) reads 'role' from JWT user_metadata.
 * If role is missing from user_metadata, backend defaults to 'SALES'.
 * CRITICAL RISK: Finance team can't approve anything if role not set correctly.
 */

import { jwtDecode } from 'jwt-decode';
import type { User } from '@/types';

/**
 * Supabase JWT Token Claims Structure
 * Based on Supabase Auth token format
 */
interface SupabaseJWTClaims {
  sub: string;                    // User ID (Supabase UUID)
  email: string;                  // User email
  user_metadata: {
    username?: string;            // Custom: derived from email or set during registration
    role?: 'SALES' | 'FINANCE' | 'ADMIN';  // Custom: user role for RBAC
  };
  aud: string;                    // Audience (e.g., 'authenticated')
  exp: number;                    // Expiration timestamp
  iat: number;                    // Issued at timestamp
}

/**
 * Decodes a Supabase JWT access token and extracts user data
 *
 * CRITICAL: This function does NOT verify the token signature.
 * Token verification happens:
 * 1. Client-side: By Supabase client when obtaining session
 * 2. Server-side: By backend @require_jwt decorator when making API calls
 *
 * @param accessToken - The JWT access token from Supabase session
 * @returns User object with id, email, username, role
 * @throws Error if token is malformed or missing required claims
 */
export function decodeUserFromToken(accessToken: string): User {
  try {
    // Decode token (no verification - already verified by Supabase)
    const claims = jwtDecode<SupabaseJWTClaims>(accessToken);

    // Extract user_metadata
    const { username, role } = claims.user_metadata || {};

    // Derive username from email if not in metadata
    const finalUsername = username || claims.email.split('@')[0];

    // Default role to SALES if not specified (matches backend fallback)
    const finalRole = role || 'SALES';

    // CRITICAL WARNING: If role is missing from user_metadata,
    // user defaults to SALES (lowest privilege level)
    if (!role) {
      console.warn(
        `Token for ${claims.email} missing 'role' in user_metadata. ` +
        `Defaulting to SALES. This may cause permission issues for Finance/Admin users.`
      );
    }

    // Construct User object (matches backend UserContext structure)
    const user: User = {
      id: claims.sub,
      email: claims.email,
      username: finalUsername,
      role: finalRole,
      is_authenticated: true,
    };

    return user;

  } catch (error) {
    console.error('Failed to decode JWT token:', error);
    throw new Error('Invalid JWT token format');
  }
}

/**
 * Validates that user_metadata contains required fields
 *
 * Use this during registration to verify token has correct structure
 * before trusting it for authorization decisions.
 *
 * CTO's Warning - The "Metadata" Bridge:
 * This validation ensures the metadata bridge between frontend and backend
 * is intact. If validation fails, Finance users may be treated as SALES users.
 *
 * @param accessToken - The JWT access token to validate
 * @returns Validation result with missing fields
 */
export function validateTokenMetadata(accessToken: string): {
  valid: boolean;
  missingFields: string[];
} {
  try {
    const claims = jwtDecode<SupabaseJWTClaims>(accessToken);
    const missingFields: string[] = [];

    if (!claims.user_metadata?.username) {
      missingFields.push('user_metadata.username');
    }

    if (!claims.user_metadata?.role) {
      missingFields.push('user_metadata.role');
    }

    return {
      valid: missingFields.length === 0,
      missingFields,
    };
  } catch {
    return {
      valid: false,
      missingFields: ['token_decode_failed'],
    };
  }
}
