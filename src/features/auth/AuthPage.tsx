// src/features/auth/AuthPage.tsx
import { useState } from 'react';
import { AuthForm } from './components/AuthForm'; // This component also needs to be migrated

// 1. Define the props interface for onLogin and onRegister
interface AuthPageProps {
  onLogin: (username: string, password: string) => Promise<void>;
  onRegister: (username: string, email: string, password: string) => Promise<void>;
}

// 2. Apply the props interface
export default function AuthPage({ onLogin, onRegister }: AuthPageProps) {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [error, setError] = useState<string | null>(null); // 3. Type state
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => { // 4. Type the form event
        e.preventDefault();
        setError(null);
        setIsLoading(true);
        try {
            if (isLogin) {
                await onLogin(username, password);
            } else {
                await onRegister(username, email, password);
            }
        } catch (err: any) { // 5. Type the caught error
            setError(err.message);
        }
        setIsLoading(false);
    };

    // The render is now just a wrapper that passes props
    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <AuthForm
                isLogin={isLogin}
                setIsLogin={setIsLogin}
                username={username}
                setUsername={setUsername}
                password={password}
                setPassword={setPassword}
                email={email}
                setEmail={setEmail}
                error={error}
                isLoading={isLoading}
                handleSubmit={handleSubmit}
            />
        </div>
    );
}