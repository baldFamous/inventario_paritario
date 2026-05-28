'use client';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch, clearTokens, login as apiLogin } from './api';
import { Usuario } from '@/types';

interface AuthContextType {
  user: Usuario | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      apiFetch<Usuario>('/auth/me/')
        .then(setUser)
        .catch(() => { clearTokens(); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    await apiLogin(username, password);
    const me = await apiFetch<Usuario>('/auth/me/');
    setUser(me);
    router.push('/dashboard');
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
