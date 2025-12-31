// src/contexts/AuthContext.tsx
import React, { createContext, useContext } from 'react';
import type { User } from '@/types';

// 1. Define the shape of the context data
interface IAuthContext {
    user: User | null;
    logout: () => void;
}

// 2. Create the context
const AuthContext = createContext<IAuthContext | null>(null);

// 3. Create the Provider component
interface AuthProviderProps {
    children: React.ReactNode;
    user: User | null;
    logout: () => void;
}

export function AuthProvider({ children, user, logout }: AuthProviderProps) {
    const value = {
        user,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

// 4. Create the custom hook for easy consumption
export const useAuth = (): IAuthContext => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};