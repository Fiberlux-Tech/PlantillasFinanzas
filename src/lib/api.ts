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

/**
 * Token provider interface for dependency injection.
 * Decouples the API client from any specific auth provider (Supabase, Auth0, etc.)
 */
export interface TokenProvider {
    getAccessToken: () => Promise<string | null>;
    refreshSession: () => Promise<boolean>;
}

let tokenProvider: TokenProvider | null = null;

/**
 * Configures the API client with a token provider.
 * Must be called once at app startup before any API calls are made.
 */
export function configureApi(provider: TokenProvider): void {
    tokenProvider = provider;
}

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
 * Refresh Supabase session to get updated JWT with new role claims
 *
 * Called when we receive 403 Forbidden (role may have changed server-side)
 *
 * Flow:
 * 1. Admin updates user role in backend
 * 2. Backend updates Supabase user_metadata
 * 3. User makes request with old JWT (still has old role)
 * 4. Backend returns 403 Forbidden
 * 5. Frontend calls this function to refresh session
 * 6. Supabase returns new JWT with updated role in user_metadata
 * 7. Request is retried with new token
 *
 * @returns Promise<boolean> - true if refresh succeeded, false otherwise
 */
async function refreshSessionAndRetry(): Promise<boolean> {
    if (!tokenProvider) {
        console.error('Token provider not configured - call configureApi() at startup');
        return false;
    }

    try {
        const success = await tokenProvider.refreshSession();

        if (!success) {
            console.error('Session refresh failed');
            return false;
        }

        console.log('Session refreshed - new JWT obtained with updated role claims');
        return true;

    } catch (error) {
        console.error('Unexpected error during session refresh:', error);
        return false;
    }
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

    // 2. CRITICAL: Attach JWT token from configured token provider
    if (tokenProvider) {
        try {
            const accessToken = await tokenProvider.getAccessToken();

            if (accessToken) {
                headers.set('Authorization', `Bearer ${accessToken}`);
            } else {
                console.warn('No active session - request may be unauthorized');
            }
        } catch (error) {
            console.error('Failed to retrieve access token:', error);
        }
    } else {
        console.error('Token provider not configured - call configureApi() at startup');
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

        // SPECIAL CASE: 403 Forbidden - role may have been updated server-side
        if (response.status === 403) {
            console.warn('Received 403 Forbidden - attempting token refresh for updated role');

            // Attempt session refresh to get new JWT with updated role
            const refreshSuccess = await refreshSessionAndRetry();

            if (refreshSuccess) {
                // Check if this is already a retry (prevent infinite loops)
                const isRetry = (config.headers as Headers).get('X-Retry-After-Refresh');

                if (!isRetry) {
                    console.log('Token refreshed, retrying request with new role claims');

                    // Clone headers and add retry marker
                    const retryHeaders = new Headers(config.headers);
                    retryHeaders.set('X-Retry-After-Refresh', 'true');

                    // Retry the original request with new token
                    return request<T>(url, {
                        ...options,
                        headers: retryHeaders,
                    });
                } else {
                    console.error('403 after refresh - user genuinely lacks permission');
                    // Fall through to throw error
                }
            }
            // If refresh failed or second 403, fall through to throw error
        }

        // This is where the 401/403 errors will now be caught and thrown
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