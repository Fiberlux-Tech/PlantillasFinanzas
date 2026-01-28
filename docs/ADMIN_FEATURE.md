# Admin Feature Documentation

> **Folder:** `src/features/admin/`
> **Label:** "The Control Room"

This document describes the admin user management feature in plain English.

---

## Table of Contents

- [The Main Job](#the-main-job)
- [The Flow](#the-flow)
- [The Repeats](#the-repeats)
- [The Connections](#the-connections)
- [The Identity](#the-identity)
- [File Summary](#file-summary)
- [API Endpoints](#api-endpoints)

---

## The Main Job

**This folder is the "Control Room" for managing users in your application.**

In simple terms: It lets an administrator (someone with special permissions) do three things:

1. **See all users** - View a list of everyone who has an account
2. **Change what someone can do** - Assign roles like "Admin", "Sales", or "Finance" to control what parts of the app they can access
3. **Reset passwords** - If someone forgets their password, the admin can set a new one for them

Think of it like the HR department's control panel - they can see who works at the company, change someone's job title (role), and issue them a new badge (password) if they lose theirs.

---

## The Flow

Here's how data moves through this folder:

```
[Backend Database]
       |
       |  (1) "Get me all users"
       v
[adminService.ts] <-- The messenger that talks to the server
       |
       |  (2) Returns list of users
       v
[AdminUserManagement.tsx] <-- The "brain" that holds and manages the data
       |
       |  (3) Passes data down to display
       v
+------+------+
|             |
v             v
[UserListTable]    [ResetPasswordForm]
Shows users        Allows password reset
in a table         with search feature
```

**In plain English:**

1. When the page loads, it asks the server: "Give me all the users"
2. The server responds with a list of users (name, email, role)
3. That list is stored in memory and shown in a table
4. When an admin changes a role -> the change is sent to the server -> the table updates
5. When an admin resets a password -> the new password is sent to the server -> a success message appears

---

## The Repeats

Yes! There are several patterns that repeat throughout these files:

### Repeat #1: The "Try, Catch, Tell" Pattern

Every time the code talks to the server, it follows the same steps:

```
1. TRY to do the action
2. If it works -> return success
3. If it fails (CATCH) -> TELL the user what went wrong
```

This pattern appears in ALL 3 service functions and in ALL action handlers.

### Repeat #2: The "Loading -> Error -> Content" Pattern

The main screen always checks:

1. "Am I still loading?" -> Show a spinner
2. "Did something go wrong?" -> Show an error message
3. "All good?" -> Show the actual content

### Repeat #3: The "Search and Filter" Pattern

When searching for a user to reset their password:

1. User types in a search box
2. Code filters the full list to only show matches
3. Shows dropdown with filtered results
4. User clicks one to select

### Repeat #4: All Text Comes from Config Files

Instead of writing "Submit" directly in the code, every label like "Submit", "Cancel", "Error loading users" comes from a central configuration file. This makes it easy to change text or translate to another language.

---

## The Connections

This folder depends on these other parts of your project:

| Folder/File | What It Provides | Why It's Needed |
|-------------|------------------|-----------------|
| `src/lib/api/` | `api.get()`, `api.post()` functions | To send requests to the server |
| `src/config/enums.ts` | `USER_ROLES` (ADMIN, SALES, FINANCE) | To know what roles exist |
| `src/config/labels.ts` | All button text, error messages, labels | For consistent user-facing text |
| `src/types/` | `User` and `ApiResponse` type definitions | To ensure data has the right shape |
| `src/components/ui/` | Card, Table, Button, Input, Select, Badge | Pre-built UI building blocks |

**Visual representation:**

```
src/features/admin/
        |
        +---> src/lib/api/        (How to talk to server)
        +---> src/config/         (Text labels & role names)
        +---> src/types/          (Data shapes)
        +---> src/components/ui/  (Visual building blocks)
```

---

## The Identity

### Label: "The Control Room"

**Why this name?**

Just like a building's control room where security guards can:

- See all visitors on monitors (view users)
- Change access levels on badges (change roles)
- Issue new badges when someone loses theirs (reset passwords)

This folder is the administrative control center of your application. It doesn't do the main work of the app (like managing finances), but it controls **who** can do that work and **what** they're allowed to do.

It's also isolated and secure - only administrators can access these features, just like only authorized personnel can enter a building's control room.

---

## File Summary

| File | Plain English Purpose |
|------|----------------------|
| `adminService.ts` | The "messenger" - sends requests to the server and brings back answers |
| `AdminUserManagement.tsx` | The "brain" - the main screen that coordinates everything |
| `components/UserListTable.tsx` | The "display board" - shows all users in a neat table |
| `components/ResetPasswordForm.tsx` | The "password desk" - where you reset someone's password |
| `components/UserSearchInput.tsx` | The "search tool" - helps you find a specific user by typing their name |
| `index.ts` | The "front door" - controls what other parts of the app can access from this folder |

---

## API Endpoints

| Action | Server Address | What It Does |
|--------|----------------|--------------|
| Get all users | `/api/admin/users` | Retrieves the complete list of users |
| Change a role | `/api/admin/users/{userId}/role` | Updates what a user is allowed to do |
| Reset password | `/api/admin/users/{userId}/reset-password` | Sets a new password for a user |

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - How to deploy the application
- [ROLLBACK.md](./ROLLBACK.md) - How to rollback failed deployments
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Database migration procedures
