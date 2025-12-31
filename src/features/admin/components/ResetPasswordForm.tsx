// src/features/admin/components/ResetPasswordForm.tsx
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { UserSearchInput } from "./UserSearchInput";
import { useState } from "react";
import { resetUserPassword } from "../adminService";
import type { User } from "../AdminUserManagement";
import { UI_LABELS, BUTTON_LABELS, VALIDATION_MESSAGES, SUCCESS_MESSAGES } from "@/config";

// Define a simpler props interface
interface ResetPasswordFormProps {
  allUsers: User[];
  onSuccess: (message: string) => void;
  onError: (message: string) => void;
}

export function ResetPasswordForm({ allUsers, onSuccess, onError }: ResetPasswordFormProps) {
  // All state now lives inside this component
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [form, setForm] = useState({
    usernameSearch: "",
    newPassword: "",
    confirmPassword: "",
  });

  // All handlers are now internal
  const handleUserNameChange = (value: string) => {
    setForm({ ...form, usernameSearch: value });
    if (value.trim()) {
      const filtered = allUsers.filter((u) =>
        u.username.toLowerCase().includes(value.toLowerCase())
      );
      setFilteredUsers(filtered);
      setShowUserDropdown(true);
    } else {
      setFilteredUsers([]);
      setShowUserDropdown(false);
      setSelectedUser(null);
    }
  };

  const handleSelectUser = (user: User) => {
    setSelectedUser(user);
    setForm({ ...form, usernameSearch: user.username });
    setShowUserDropdown(false);
  };

  const handleResetPasswordSubmit = async () => {
    try {
      // Client-side validation
      if (!selectedUser) {
        onError(VALIDATION_MESSAGES.SELECT_USER_REQUIRED);
        return;
      }
      if (!form.newPassword) {
        onError(VALIDATION_MESSAGES.PASSWORD_REQUIRED);
        return;
      }
      if (form.newPassword !== form.confirmPassword) {
        onError(VALIDATION_MESSAGES.PASSWORDS_DO_NOT_MATCH);
        return;
      }

      // Call service directly
      const result = await resetUserPassword(selectedUser.id, form.newPassword);

      if (result.success) {
        onSuccess(SUCCESS_MESSAGES.PASSWORD_RESET.replace('{username}', selectedUser.username));
        // Reset UI state on success
        setForm({ usernameSearch: "", newPassword: "", confirmPassword: "" });
        setSelectedUser(null);
        setFilteredUsers([]);
      } else {
        throw new Error(result.error);
      }
    } catch (err: any) {
      onError(err.message || "Failed to reset password.");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{UI_LABELS.RESET_USER_PASSWORD}</CardTitle>
        <CardDescription>{UI_LABELS.SELECT_USER_PASSWORD}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex space-x-4 items-end">
          <div className="flex-1">
            <UserSearchInput
              value={form.usernameSearch}
              onChange={handleUserNameChange}
              onFocus={() => {
                if (form.usernameSearch.trim() && filteredUsers.length > 0) {
                  setShowUserDropdown(true);
                }
              }}
              showDropdown={showUserDropdown}
              filteredUsers={filteredUsers}
              onSelectUser={handleSelectUser}
            />
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">{UI_LABELS.NEW_PASSWORD}</label>
            <Input
              type="password"
              placeholder={UI_LABELS.ENTER_NEW_PASSWORD}
              value={form.newPassword}
              onChange={(e) => setForm({ ...form, newPassword: e.target.value })}
            />
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">{UI_LABELS.CONFIRM_PASSWORD}</label>
            <Input
              type="password"
              placeholder={UI_LABELS.CONFIRM_NEW_PASSWORD}
              value={form.confirmPassword}
              onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
            />
          </div>

          <Button onClick={handleResetPasswordSubmit} disabled={!selectedUser}>
            {BUTTON_LABELS.RESET_PASSWORD}
          </Button>
        </div>

        {selectedUser && (
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md max-w-md">
            <p className="text-sm">
              <span className="font-medium">{UI_LABELS.SELECTED}:</span> {selectedUser.username} ({selectedUser.email})
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
