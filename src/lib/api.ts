// src/lib/api.ts
/**
 * Centralized API Client for Frontend-Backend Communication
 *
 * This module provides a type-safe API client that handles all HTTP requests
 * to the Flask backend using relative paths for Vercel monorepo architecture.
 *
 * RELATIVE PATH STRATEGY (CRITICAL FOR VERCEL):
 * =============================================
 * - API_BASE_URL defaults to "" (empty string) for relative paths
 * - All endpoints start with /api or /auth (e.g., "/api/transactions")
 * - Frontend and backend share the same domain in production
 *
 * HOW IT WORKS:
 * =============
 * DEVELOPMENT (localhost):
 *   - Frontend runs on http://localhost:3000 (Vite dev server)
 *   - Backend runs on http://localhost:5000 (Flask)
 *   - Vite proxy (vite.config.ts) forwards /api and /auth to :5000
 *   - Example: fetch("/api/transactions") → proxied to → http://localhost:5000/api/transactions
 *
 * PRODUCTION (Vercel):
 *   - Frontend and backend both at https://yourdomain.com
 *   - Vercel routing (vercel.json) directs /api/* to serverless functions
 *   - Example: fetch("/api/transactions") → https://yourdomain.com/api/transactions → api/index.py
 *
 * BENEFITS:
 * =========
 * ✓ No CORS issues (same origin)
 * ✓ Works in dev, preview, and production automatically
 * ✓ No environment-specific configuration needed
 * ✓ Secure (no exposed backend URLs)
 *
 * @see vite.config.ts - Development proxy configuration
 * @see vercel.json - Production routing configuration
 */
import { API_CONFIG } from '@/config';
import { supabase } from '@/lib/supabase';

/**
 * API Base URL - Configured for relative paths
 *
 * IMPORTANT: Should remain empty ("") for Vercel monorepo deployment
 * Only set VITE_API_BASE_URL if backend is on a completely different domain
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

/**
 * Extracts CSRF token from cookies
 * Looks for common CSRF cookie names from configuration
 */
function getCsrfToken(): string | null {
    const cookies = document.cookie.split(';');

    for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (API_CONFIG.CSRF.COOKIE_NAMES.includes(name as any)) {
            return decodeURIComponent(value);
        }
    }
    return null;
}

/**
 * A centralized request function that handles responses and errors.
 *
 * AUTHENTICATION: Automatically attaches JWT token from Supabase session
 * to the Authorization header for all requests.
 *
 * ARCHITECTURE: Pure JWT Authentication
 * - Retrieves access_token from Supabase session (stored in localStorage)
 * - Attaches token to Authorization header as "Bearer <token>"
 * - Backend validates token using @require_jwt decorator
 * - No cookie-based authentication (removed credentials: 'include')
 *
 * @param {string} url - The endpoint URL (e.g., '/api/transactions')
 * @param {object} options - The standard 'fetch' options object
 * @returns {Promise<T>} - The JSON response data
 * @throws {Error} - Throws an error for non-successful HTTP responses
 */
async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
    const config: RequestInit = {
        ...options,
        // REMOVED: credentials: 'include' - we're using JWT tokens now, not cookies
    };

    // 1. Set default headers, but allow overrides
    const headers = new Headers(config.headers);

    // 2. CRITICAL: Attach JWT token from Supabase session
    try {
        const { data: { session } } = await supabase.auth.getSession();

        if (session?.access_token) {
            // Attach JWT token in Authorization header (required by backend @require_jwt)
            headers.set('Authorization', `Bearer ${session.access_token}`);
        } else {
            // No active session - request will likely get 401 Unauthorized
            // This is expected for unauthenticated users or expired sessions
            console.warn('No active Supabase session - request may be unauthorized');
        }
    } catch (error) {
        // Session retrieval failed - log but continue (request will fail with 401)
        console.error('Failed to retrieve Supabase session:', error);
    }

    // 3. Add CSRF token for state-changing requests (defense in depth)
    const method = config.method?.toUpperCase();
    if (method && API_CONFIG.CSRF.METHODS_REQUIRING_CSRF.includes(method as any)) {
        const csrfToken = getCsrfToken();
        if (csrfToken) {
            // Use X-XSRF-TOKEN header (common pattern with XSRF-TOKEN cookie)
            headers.set(API_CONFIG.CSRF.HEADERS.XSRF, csrfToken);
            // Also set X-CSRF-Token as a fallback for different backend implementations
            headers.set(API_CONFIG.CSRF.HEADERS.CSRF, csrfToken);
        }
    }

    // 4. Smartly set Content-Type, unless it's FormData
    if (config.body && !(config.body instanceof FormData)) {
        // Default to JSON if not specified
        if (!headers.has(API_CONFIG.HTTP.CONTENT_TYPE_HEADER)) {
            headers.set(API_CONFIG.HTTP.CONTENT_TYPE_HEADER, API_CONFIG.HTTP.CONTENT_TYPE_JSON);
        }
        // Stringify body if it's a JS object
        config.body = JSON.stringify(config.body);
    }

    config.headers = headers;

    // 5. Make the request
    const response = await fetch(`${API_BASE_URL}${url}`, config);

    // 6. GLOBAL ERROR HANDLER (for all non-ok responses)
    if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

        // Only try to parse JSON if content type indicates JSON
        const contentType = response.headers.get('content-type');
        if (contentType?.includes(API_CONFIG.HTTP.CONTENT_TYPE_JSON)) {
            try {
                const err = await response.json();
                errorMessage = err.message || err.error || errorMessage;
            } catch (e) {
                // If JSON parsing fails, keep the HTTP status message
            }
        }

        // SPECIAL CASE: 401 Unauthorized - token may have expired or be invalid
        if (response.status === 401) {
            console.warn('Received 401 Unauthorized - token may have expired or be invalid');
            // Note: Supabase client automatically refreshes tokens before expiration,
            // so a 401 here likely means:
            // 1. User logged out
            // 2. Token was revoked server-side
            // 3. User's session expired (shouldn't happen if refresh worked)
            //
            // The App.tsx useEffect will handle redirecting to login on next auth check
        }

        // This is where the 401 error will now be caught and thrown
        throw new Error(errorMessage);
    }

    // 7. SUCCESS HANDLER
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes(API_CONFIG.HTTP.CONTENT_TYPE_JSON)) {
        return response.json() as Promise<T>; // Parse and return typed JSON
    }

    // Return undefined for 204 No Content, cast as T
    return undefined as T;
}

// --- Our clean, typed API methods ---

export const api = {
    get: <T>(url: string) => request<T>(url, { method: API_CONFIG.HTTP.METHOD_GET }),

    post: <T>(url: string, data: any) => request<T>(url, { method: API_CONFIG.HTTP.METHOD_POST, body: data }),

    postForm: <T>(url: string, formData: FormData) => request<T>(url, { method: API_CONFIG.HTTP.METHOD_POST, body: formData }),

    put: <T>(url: string, data: any) => request<T>(url, { method: 'PUT', body: data }),
};