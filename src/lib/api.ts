// src/lib/api.ts
import { API_CONFIG } from '@/config';

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
 * We use a generic <T> to type the successful response.
 * @param {string} url - The endpoint URL (e.g., '/auth/login')
 * @param {object} options - The standard 'fetch' options object
 * @returns {Promise<T>} - The JSON response data
 * @throws {Error} - Throws an error for non-successful HTTP responses
 */
async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
    const config: RequestInit = {
        ...options,
        credentials: 'include', // Always send cookies
    };

    // 2. Set default headers, but allow overrides
    const headers = new Headers(config.headers);

    // 3. Add CSRF token for state-changing requests
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