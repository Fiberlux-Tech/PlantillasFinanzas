// src/features/admin/adminService.ts
import { api } from '@/lib/api';
import type { User, ApiResponse } from '@/types';
import { ERROR_MESSAGES } from '@/config';

/**
 * Fetches the list of all users from the backend.
 */
export async function getAllUsers(): Promise<ApiResponse<User[]>> {
    try {
        const data = await api.get<{ users: User[] }>('/api/admin/users');

        return { success: true, data: data.users || [] };
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : ERROR_MESSAGES.FAILED_LOAD_USER_DATA;
        return { success: false, error: message };
    }
}

/**
 * Updates the role of a specific user.
 */
export async function updateUserRole(userId: string, newRole: string): Promise<ApiResponse> {
    try {
        await api.post<ApiResponse>(`/api/admin/users/${userId}/role`, { role: newRole.toUpperCase() });
        return { success: true };
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : ERROR_MESSAGES.FAILED_UPDATE_ROLE;
        return { success: false, error: message };
    }
}

/**
 * Resets the password for a specific user.
 */
export async function resetUserPassword(userId: string, newPassword: string): Promise<ApiResponse> {
    try {
        await api.post<ApiResponse>(`/api/admin/users/${userId}/reset-password`, { new_password: newPassword });
        return { success: true };
    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : ERROR_MESSAGES.FAILED_RESET_PASSWORD;
        return { success: false, error: message };
    }
}