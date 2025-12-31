// src/features/auth/components/AuthForm.tsx
import React from 'react';
import { UI_LABELS } from '@/config';

// Define the props interface
interface AuthFormProps {
    isLogin: boolean;
    setIsLogin: React.Dispatch<React.SetStateAction<boolean>>;
    username: string;
    setUsername: React.Dispatch<React.SetStateAction<string>>;
    password: string;
    setPassword: React.Dispatch<React.SetStateAction<string>>;
    email: string;
    setEmail: React.Dispatch<React.SetStateAction<string>>;
    error: string | null;
    isLoading: boolean;
    handleSubmit: (e: React.FormEvent) => Promise<void>;
}

// Apply the props interface
export function AuthForm({
    isLogin,
    setIsLogin,
    username,
    setUsername,
    password,
    setPassword,
    email,
    setEmail,
    error,
    isLoading,
    handleSubmit
}: AuthFormProps) {
    return (
        <div className="bg-white p-10 rounded-lg shadow-xl w-full max-w-md">
            <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">
                {isLogin ? UI_LABELS.WELCOME_BACK : UI_LABELS.CREATE_ACCOUNT}
            </h2>
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6" role="alert">
                    {error}
                </div>
            )}
            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <label className="block text-sm font-medium text-gray-700" htmlFor="username">
                        {UI_LABELS.USUARIO}
                    </label>
                    <input
                        id="username"
                        type="text"
                        value={username}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
                        required
                        className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-md shadow-sm focus:ring-black focus:border-black"
                    />
                </div>

                {!isLogin && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700" htmlFor="email">
                            {UI_LABELS.EMAIL}
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                            required
                            className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-md shadow-sm focus:ring-black focus:border-black"
                        />
                    </div>
                )}

                <div>
                    <label className="block text-sm font-medium text-gray-700" htmlFor="password">
                        {UI_LABELS.CONTRASENA}
                    </label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                        required
                        className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-md shadow-sm focus:ring-black focus:border-black"
                    />
                </div>

                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black disabled:bg-gray-400"
                >
                    {isLoading ? UI_LABELS.PROCESSING : (isLogin ? UI_LABELS.LOGIN : UI_LABELS.SIGN_UP)}
                </button>
            </form>
            <div className="text-center mt-6">
                <button
                    onClick={() => setIsLogin(!isLogin)}
                    className="text-sm text-gray-600 hover:text-black"
                >
                    {isLogin ? UI_LABELS.NEED_ACCOUNT : UI_LABELS.ALREADY_HAVE_ACCOUNT}
                </button>
            </div>
        </div>
    );
}
