// src/App.tsx
import { useState, useEffect, useCallback, Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import { checkAuthStatus, loginUser, registerUser, logoutUser } from '@/features/auth';
import GlobalHeader from '@/components/shared/GlobalHeader';

const AuthPage = lazy(() => import('@/features/auth').then(m => ({ default: m.AuthPage })));
const LandingPage = lazy(() => import('@/features/landing').then(m => ({ default: m.LandingPage })));
const TransactionDashboard = lazy(() => import('@/features/transactions').then(m => ({ default: m.TransactionDashboard })));
const PermissionManagementModule = lazy(() => import('@/features/admin').then(m => ({ default: m.PermissionManagementModule })));
const MasterDataManagement = lazy(() => import('@/features/masterdata').then(m => ({ default: m.MasterDataManagement })));
import { AuthProvider } from '@/contexts/AuthContext';
import type { User, UserRole } from '@/types';

interface SalesActions {
    uploadLabel: string;
    onUpload: () => void;
}
const defaultSalesActions: SalesActions = {
    uploadLabel: 'Cargar Archivo',
    onUpload: () => console.log('Upload handler not yet mounted'),
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
                setUser(null);
            }
            setIsLoading(false);
        };
        checkUser();
    }, []);

    // Pure JWT Authentication: Email-based login
    const handleLogin = async (email: string, password: string) => {
        const result = await loginUser(email, password);
        if (result.success) {
            setUser(result.data);
        } else {
            throw new Error(result.error);
        }
    };

    // Pure JWT Authentication: Email-based registration (username auto-derived)
    const handleRegister = async (email: string, password: string) => {
        // Username will be auto-derived from email in authService.ts: email.split('@')[0]
        const result = await registerUser('', email, password);
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
            <Suspense fallback={<div className="min-h-screen bg-gray-100 flex items-center justify-center"><h1 className="text-2xl">Loading...</h1></div>}>
                <Routes>
                    <Route path="/auth" element={<AuthPage onLogin={handleLogin} onRegister={handleRegister} />} />
                    <Route path="*" element={<Navigate to="/auth" replace />} />
                </Routes>
            </Suspense>
        );
    }

    // Authenticated user routes
    return (
        <AuthProvider user={user} logout={handleLogout}>
            <div className="min-h-screen flex flex-col bg-slate-50">
                <GlobalHeader
                    salesActions={salesActions}
                />
                <main className="flex-grow">
                    <Suspense fallback={<div className="min-h-screen bg-gray-100 flex items-center justify-center"><h1 className="text-2xl">Loading...</h1></div>}>
                    <Routes>
                        <Route path="/" element={<LandingPage />} />

                        <Route path="/dashboard" element={
                            <ProtectedRoute user={user} roles={['SALES', 'FINANCE', 'ADMIN']}>
                                <TransactionDashboard setSalesActions={setSalesActions} />
                            </ProtectedRoute>
                        } />

                        <Route path="/admin/users" element={
                            <ProtectedRoute user={user} roles={['ADMIN']}>
                                <PermissionManagementModule />
                            </ProtectedRoute>
                        } />

                        <Route path="/admin/master-data" element={
                            <ProtectedRoute user={user} roles={['ADMIN', 'FINANCE', 'SALES']}>
                                <MasterDataManagement />
                            </ProtectedRoute>
                        } />

                        <Route path="/auth" element={<Navigate to="/" replace />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                    </Suspense>
                </main>
            </div>
        </AuthProvider>
    );
}
