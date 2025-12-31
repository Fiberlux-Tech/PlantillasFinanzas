// src/features/admin/AdminUserManagement.tsx (Refactored)

"use client"

import { useState, useEffect } from "react"
import { UserListTable } from "./components/UserListTable"
import { ResetPasswordForm } from "./components/ResetPasswordForm"
import { getAllUsers, updateUserRole } from "./adminService";
import { UI_LABELS, SUCCESS_MESSAGES, ERROR_MESSAGES, type UserRole } from "@/config";

export interface User {
  id: number
  email: string
  username: string
  role: UserRole
}

export function PermissionManagementModule() {
  // --- STATE (CLEANED UP) ---
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // --- DATA FETCHING (Unchanged) ---
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await getAllUsers();

      if (result.success && result.data) {
        setUsers(result.data as User[])
      } else {
        throw new Error(result.error);
      }

    } catch (err: any) {
      setError(err.message || ERROR_MESSAGES.FAILED_LOAD_USER_DATA)
    } finally {
      setLoading(false)
    }
  }

  // --- EVENT HANDLERS (CLEANED UP) ---
  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      setError(null)
      const result = await updateUserRole(userId, newRole);

      if (result.success) {
        const updatedUsers = users.map((u) =>
          u.id === userId ? { ...u, role: newRole.toUpperCase() as UserRole } : u
        )
        setUsers(updatedUsers)
        alert(SUCCESS_MESSAGES.ROLE_UPDATED.replace('{role}', newRole.toUpperCase()))
      } else {
        throw new Error(result.error)
      }
    } catch (err: any) {
      setError(err.message || ERROR_MESSAGES.FAILED_UPDATE_ROLE)
    }
  }

  // --- RENDER (CLEANED UP) ---
  if (loading) {
    return (
      <div className="container mx-auto px-8 py-8">
        <div className="flex items-center justify-center p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-slate-600">{UI_LABELS.LOADING}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-8 py-8">
      <div className="space-y-6">
        {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">{error}</div>}

        <UserListTable
          users={users}
          onRoleChange={handleRoleChange}
        />

        <ResetPasswordForm
          allUsers={users}
          onSuccess={(message) => {
            setError(null);
            alert(message);
          }}
          onError={(message) => {
            setError(message);
          }}
        />
      </div>
    </div>
  )
}
