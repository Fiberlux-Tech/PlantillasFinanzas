// src/features/admin/adminService.ts
import { api } from '@/lib/api';
import type { User, BaseApiResponse } from '@/types';
import { ERROR_MESSAGES } from '@/config';

// 2. Define a more specific type for the service function's return
interface GetUsersResult {
    success: boolean;
    data?: User[];
    error?: string;
}

/**
 * Fetches the list of all users from the backend.
 */
export async function getAllUsers(): Promise<GetUsersResult> {
    try {
        // 3. Type the expected API response
        const data = await api.get<{ users: User[] }>('/api/admin/users');
        
        return { success: true, data: data.users || [] };
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_LOAD_USER_DATA };
    }
}

/**
 * Updates the role of a specific user.
 * We can reuse BaseApiResponse for simple success/error messages
 */
export async function updateUserRole(userId: number, newRole: string): Promise<BaseApiResponse> {
    try {
        await api.post<BaseApiResponse>(`/api/admin/users/${userId}/role`, { role: newRole.toUpperCase() });
        return { success: true };
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_UPDATE_ROLE };
    }
}

/**
 * Resets the password for a specific user.
 */
export async function resetUserPassword(userId: number, newPassword: string): Promise<BaseApiResponse> {
    try {
        await api.post<BaseApiResponse>(`/api/admin/users/${userId}/reset-password`, { new_password: newPassword });
        return { success: true };
    } catch (error: any) {
        return { success: false, error: error.message || ERROR_MESSAGES.FAILED_RESET_PASSWORD };
    }
}