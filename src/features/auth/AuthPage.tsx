// src/features/auth/AuthPage.tsx
/**
 * Authentication Page - Pure JWT with Email-Based Authentication
 *
 * ARCHITECTURAL CHANGE: Email-based authentication (no username field)
 * - Login: Email + Password
 * - Register: Email + Password (username auto-derived from email in backend)
 * - Prepares for future SSO integration
 */
import { useState } from 'react';
import { AuthForm } from './components/AuthForm';

// Define the props interface for onLogin and onRegister
interface AuthPageProps {
  onLogin: (email: string, password: string) => Promise<void>;
  onRegister: (email: string, password: string) => Promise<void>;
}

// Apply the props interface
export default function AuthPage({ onLogin, onRegister }: AuthPageProps) {
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);
        try {
            if (isLogin) {
                // Login with email and password
                await onLogin(email, password);
            } else {
                // Register with email and password
                // Username will be auto-derived from email in authService.ts
                await onRegister(email, password);
            }
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        }
        setIsLoading(false);
    };

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <AuthForm
                isLogin={isLogin}
                setIsLogin={setIsLogin}
                email={email}
                setEmail={setEmail}
                password={password}
                setPassword={setPassword}
                error={error}
                isLoading={isLoading}
                handleSubmit={handleSubmit}
            />
        </div>
    );
}
