// src/features/auth/authService.ts
import { api } from '@/lib/api';
// 1. Import shared types
import type { User } from '@/types'; // 1. Import shared types

// FIX: This type is now an alias for the full User object, assuming the backend returns it.
export interface AuthSuccessData extends User {}

// 3. Define the return types for our service functions
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

// FIX: Changed AuthStatus to return the full User object on success.
export type AuthStatus = {
    is_authenticated: true;
    user: User;
} | {
    is_authenticated: false;
    error: string;
}

/**
 * Attempts to log in a user.
 */
export async function loginUser(username: string, password: string): Promise<AuthResult> {
    try {
        const data = await api.post<AuthSuccessData>('/auth/login', { username, password });
        return { success: true, data };
    } catch (error: any) {
        return { success: false, error: error.message || 'Login failed.' };
    }
}

/**
 * Attempts to register a new user.
 */
export async function registerUser(username: string, email: string, password: string): Promise<AuthResult> {
    try {
        const data = await api.post<AuthSuccessData>('/auth/register', { username, email, password });
        return { success: true, data };
    } catch (error: any) {
        return { success: false, error: error.message || 'Registration failed.' };
    }
}

/**
 * Logs out the current user.
 */
export async function logoutUser(): Promise<LogoutResult> {
    try {
        // FIX: Pass an empty object {} as the data argument to satisfy api.post signature.
        await api.post<unknown>('/auth/logout', {});
        return { success: true };
    } catch (error: any) {
        return { success: false, error: error.message || 'Logout failed.' };
    }
}

/**
 * Checks if a user is authenticated.
 */
export async function checkAuthStatus(): Promise<AuthStatus> {
    try {
        // The API will return the full AuthSuccessData (which is User)
        const data = await api.get<AuthSuccessData>('/auth/me'); 
        
        // FIX: Return the full user object
        return { is_authenticated: true, user: data };
    } catch (error: any) {
        // If it throws (401 or network error), we are not authenticated
        return { is_authenticated: false, error: error.message || 'Failed to check authentication status.' };
    }
}