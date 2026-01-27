// src/lib/supabase.ts
/**
 * Supabase Client Configuration
 *
 * This module initializes and exports the Supabase client for frontend authentication.
 * The client handles:
 * - JWT token storage in localStorage
 * - Automatic token refresh before expiration
 * - Session persistence across page reloads
 *
 * ARCHITECTURE: Pure JWT Authentication
 * - Token is single source of truth
 * - Frontend self-hydrates by decoding access_token
 * - No /api/me endpoint needed for auth check
 * - Backend validates token via @require_jwt decorator
 *
 * ENVIRONMENT VARIABLES REQUIRED:
 * - VITE_SUPABASE_URL: Your Supabase project URL
 * - VITE_SUPABASE_ANON_KEY: Your Supabase anon/public key
 *
 * @see https://supabase.com/docs/reference/javascript/initializing
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Validate environment variables at initialization
if (!supabaseUrl) {
  throw new Error(
    'Missing VITE_SUPABASE_URL environment variable. ' +
    'Please add it to your .env file. ' +
    'Find it at: Supabase Dashboard → Project Settings → API → Project URL'
  );
}

if (!supabaseAnonKey) {
  throw new Error(
    'Missing VITE_SUPABASE_ANON_KEY environment variable. ' +
    'Please add it to your .env file. ' +
    'Find it at: Supabase Dashboard → Project Settings → API → anon public key'
  );
}

/**
 * Supabase client instance
 *
 * This is a singleton - import this instance throughout your app.
 * The client automatically:
 * - Persists session to localStorage (key: 'sb-<project-ref>-auth-token')
 * - Refreshes access token before expiration (default: 60 min lifetime, refresh at 55 min)
 * - Provides auth state listeners for session changes
 *
 * Usage:
 *   import { supabase } from '@/lib/supabase';
 *   const { data, error } = await supabase.auth.signInWithPassword({ email, password });
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    // Store tokens in localStorage (survives page refresh)
    storage: window.localStorage,

    // Automatically persist session
    autoRefreshToken: true,

    // Detect session from URL hash (for magic links, OAuth callbacks)
    detectSessionInUrl: true,

    // Storage key (default: 'sb-<project-ref>-auth-token')
    // You can customize this if needed: storageKey: 'my-custom-key'
  }
});

/**
 * Helper function to get current session
 *
 * Returns the current session if user is authenticated, null otherwise.
 * Useful for checking auth status without async call.
 *
 * @returns Promise resolving to session object or null
 */
export const getCurrentSession = () => {
  return supabase.auth.getSession();
};

/**
 * Helper function to get current user
 *
 * Returns the current user from the session, null if not authenticated.
 *
 * @returns Promise resolving to user object or null
 */
export const getCurrentUser = async () => {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
};

/**
 * Token provider for the API client.
 * Wraps Supabase auth methods behind the TokenProvider interface
 * so the API client doesn't depend on Supabase directly.
 */
export const supabaseTokenProvider = {
  async getAccessToken(): Promise<string | null> {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ?? null;
  },

  async refreshSession(): Promise<boolean> {
    const { data, error } = await supabase.auth.refreshSession();
    return !error && !!data.session;
  },
};
