// src/App.tsx
import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom'; 

import { checkAuthStatus, loginUser, registerUser, logoutUser } from '@/features/auth/authService';
import AuthPage from '@/features/auth/AuthPage';
import LandingPage from '@/features/landing/LandingPage';
import TransactionDashboard from '@/features/transactions/TransactionDashboard';
import { PermissionManagementModule } from '@/features/admin/AdminUserManagement';
import MasterDataManagement from '@/features/masterdata/MasterDataManagement';
import GlobalHeader from '@/components/shared/GlobalHeader';
import { AuthProvider } from '@/contexts/AuthContext'; // <-- 1. Import AuthProvider
import type { User, UserRole } from '@/types';

interface SalesActions {
    uploadLabel: string; // <-- MODIFIED
    onUpload: () => void;
    // Removed: onExport
}
const defaultSalesActions: SalesActions = {
    uploadLabel: 'Cargar Archivo', // <-- MODIFIED
    onUpload: () => console.log('Upload handler not yet mounted'),
    // Removed: onExport
};

interface ProtectedRouteProps {
    user: User | null;
    roles: UserRole[];
    children: React.ReactNode;
}

function ProtectedRoute({ user, roles, children }: ProtectedRouteProps) {
    if (!user) {
        return <Navigate to="/auth" replace />;
    }
    const hasPermission = roles.includes(user.role) || user.role === 'ADMIN';
    if (!hasPermission) {
        return <Navigate to="/" replace />;
    }
    return <>{children}</>;
}


export default function App() {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [salesActions, setSalesActions] = useState<SalesActions>(defaultSalesActions);

    useEffect(() => {
        const checkUser = async () => {
            try {
                const data = await checkAuthStatus();
                if (data.is_authenticated) {
                    setUser(data.user);
                }
            } catch (error) {
                console.error("Failed to fetch user", error);
                setUser(null); // <-- This correctly handles the thrown 401 error
            }
            setIsLoading(false);
        };
        checkUser();
    }, []);

    const handleLogin = async (username: string, password: string) => {
        const result = await loginUser(username, password);
        if (result.success) {
            setUser(result.data);
        } else {
            throw new Error(result.error);
        }
    };

    const handleRegister = async (username: string, email: string, password: string) => {
        const result = await registerUser(username, email, password);
        if (result.success) {
            setUser(result.data);
        } else {
            throw new Error(result.error);
        }
    };

    const handleLogout = useCallback(async () => {
        await logoutUser();
        setUser(null);
    }, []); 

    if (isLoading) {

        return (
            <div className="min-h-screen bg-gray-100 flex items-center justify-center">
                <h1 className="text-2xl">Loading...</h1>
            </div>
        );
    }

    if (!user) {
        return (
            <Routes>
                <Route path="/auth" element={<AuthPage onLogin={handleLogin} onRegister={handleRegister} />} />
                <Route path="*" element={<Navigate to="/auth" replace />} />
            </Routes>
        );
    }

    // Authenticated user routes
    return (
        // 2. Wrap the authenticated app in the AuthProvider
        <AuthProvider user={user} logout={handleLogout}>
            <div className="min-h-screen flex flex-col bg-slate-50">
                <GlobalHeader 
                    // 3. Remove onLogout prop
                    salesActions={salesActions} 
                />
                <main className="flex-grow">
                    <Routes>
                        {/* 4. Remove 'user' prop from all children */}
                        <Route path="/" element={<LandingPage />} />
                        
                        <Route path="/sales" element={
                            <ProtectedRoute user={user} roles={['SALES']}>
                                <TransactionDashboard
                                    view="SALES"
                                    setSalesActions={setSalesActions}
                                />
                            </ProtectedRoute>
                        } />

                        <Route path="/finance" element={
                            <ProtectedRoute user={user} roles={['FINANCE']}>
                                <TransactionDashboard view="FINANCE" />
                            </ProtectedRoute>
                        } />
                        
                        <Route path="/admin/users" element={
                            <ProtectedRoute user={user} roles={['ADMIN']}>
                                <PermissionManagementModule />
                            </ProtectedRoute>
                        } />

                        <Route path="/admin/master-data" element={
                            <ProtectedRoute user={user} roles={['ADMIN', 'FINANCE', 'SALES', 'USER']}>
                                <MasterDataManagement />
                            </ProtectedRoute>
                        } />

                        <Route path="/auth" element={<Navigate to="/" replace />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </main>
            </div>
        </AuthProvider>
    );
}