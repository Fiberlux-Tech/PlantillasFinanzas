import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { User } from "../AdminUserManagement" // Import the User interface
import { UI_LABELS, USER_ROLES } from "@/config"

// Define the component's props
interface UserListTableProps {
  users: User[];
  onRoleChange: (userId: number, newRole: string) => void;
}

export function UserListTable({ users, onRoleChange }: UserListTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{UI_LABELS.USER_MANAGEMENT}</CardTitle>
        <CardDescription>{UI_LABELS.VIEW_ALL_USERS}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{UI_LABELS.USERNAME}</TableHead>
                <TableHead>{UI_LABELS.EMAIL}</TableHead>
                <TableHead>{UI_LABELS.CURRENT_ROLE}</TableHead>
                 <TableHead>{UI_LABELS.CHANGE_ROLE}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.username}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{user.role}</Badge>
                  </TableCell>
                  <TableCell>
                    <Select value={user.role} onValueChange={(value) => onRoleChange(user.id, value)}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={USER_ROLES.ADMIN}>Admin</SelectItem>
                        <SelectItem value={USER_ROLES.SALES}>Sales</SelectItem>
                        <SelectItem value={USER_ROLES.FINANCE}>Finance</SelectItem>
                        <SelectItem value={USER_ROLES.USER}>User</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {users.length === 0 && (
          <div className="text-center py-8">
            <p className="text-slate-600">{UI_LABELS.NO_USERS_FOUND}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
