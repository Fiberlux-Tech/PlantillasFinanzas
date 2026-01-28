# Authentication Module Documentation

> **Folder:** `src/features/auth`
> **Identity Label:** "The Gatekeeper"

This document describes the authentication feature folder for developers and architects who need to understand how user authentication works in this application.

---

## Table of Contents

- [The Main Job](#the-main-job)
- [The Flow](#the-flow)
- [The Repeats](#the-repeats)
- [The Connections](#the-connections)
- [File Summary](#file-summary)
- [Key Architectural Decision](#key-architectural-decision)

---

## The Main Job

**This folder handles user login and registration.** It's the "front door" of the application - it decides who gets in and who doesn't. When someone visits the app, this code:

1. Shows them a form to enter their email and password
2. Checks if those credentials are valid (via Supabase, the database service)
3. If valid, gives them a "digital key" (called a JWT token) that proves who they are
4. Remembers them so they don't have to log in again when they refresh the page

---

## The Flow

```
User types email & password
        ↓
    AuthForm.tsx (the visual form)
        ↓
    AuthPage.tsx (manages what happens when they click "Login" or "Register")
        ↓
    authService.ts (talks to Supabase to verify credentials)
        ↓
    Supabase returns a "token" (digital ID card)
        ↓
    Token is saved in browser's localStorage (so user stays logged in)
        ↓
    User info is decoded from token and sent back to App.tsx
        ↓
    App.tsx updates to show the logged-in experience
```

**In plain English:**
- Data comes FROM: The user typing in the form
- Data goes TO: The browser's local storage (to remember them) and the main App component (to unlock the rest of the app)

---

## The Repeats

Yes, there are a few repeated patterns:

### 1. Success/Failure Result Pattern

Every function that talks to Supabase returns data in the same shape:

```typescript
// Either this:
{ success: true, data: {...} }

// Or this:
{ success: false, error: "Something went wrong" }
```

This pattern appears in `loginUser`, `registerUser`, `logoutUser`, and `checkAuthStatus`. It's a good practice - it forces the code to always handle both success and failure cases.

### 2. Token Decoding

The `decodeUserFromToken()` function is called in 3 places:
- After login
- After registration
- When checking if user is already logged in

This could potentially be centralized, but it's acceptable given the different contexts.

---

## The Connections

This folder relies on **4 other parts** of the codebase:

| Dependency | Location | What It Provides |
|------------|----------|------------------|
| **Supabase Client** | `src/lib/supabase.ts` | The connection to the database/auth service |
| **JWT Utilities** | `src/lib/jwtUtils.ts` | Functions to decode the "digital ID card" (token) |
| **Type Definitions** | `src/types/index.ts` | Defines what a "User" looks like (id, email, role, etc.) |
| **UI Labels** | `src/config/labels.ts` | Text strings shown to users (for easy translation later) |

**Dependency diagram:**

```
src/features/auth/
    │
    ├──► src/lib/supabase.ts (external service connection)
    │
    ├──► src/lib/jwtUtils.ts (token decoder)
    │
    ├──► src/types/index.ts (data shapes)
    │
    └──► src/config/labels.ts (display text)
```

---

## The Identity

### Label: "The Gatekeeper"

**Why this name?**

Like a gatekeeper at a building entrance, this folder:

1. **Checks credentials** - "Do you have the right password?"
2. **Issues passes** - Gives authenticated users a token (their "building pass")
3. **Remembers faces** - Keeps track of who's logged in via localStorage
4. **Controls access** - Without passing through here, users can't access the rest of the app

The auth folder doesn't store any business data, doesn't process transactions, and doesn't display dashboards. Its single job is deciding: **"Are you allowed in, and who are you?"**

---

## File Summary

| File | Role | Approx. Lines |
|------|------|---------------|
| `index.ts` | "Public menu" - lists what this folder offers to others | ~10 |
| `AuthPage.tsx` | "Reception desk" - manages the login/register experience | ~80 |
| `authService.ts` | "Security office" - actually verifies credentials | ~100 |
| `components/AuthForm.tsx` | "The clipboard" - the actual form users fill out | ~60 |

---

## Key Architectural Decision

This system uses **"Pure JWT" authentication**, which means:

- The user's identity is stored *inside* their token (not on the server)
- No need to call the server to ask "who is this user?" - just read the token
- Faster and simpler, but requires careful handling of user roles

**Important note:** During registration, the user's role (ADMIN, SALES, or FINANCE) is baked into the token. If this isn't set correctly, FINANCE users might accidentally be treated as SALES users and lose access to approval features.

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Migration best practices
- [ROLLBACK.md](./ROLLBACK.md) - Rollback procedures
