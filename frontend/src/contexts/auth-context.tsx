'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch, clearTokens, getAccessToken, revokeSession, saveTokens } from '@/lib/api';
import type { AuthResponse, User } from '@/types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login(email: string, password: string): Promise<void>;
  logout(): Promise<void>;
  refreshProfile(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshProfile = useCallback(async () => {
    if (!getAccessToken()) { setLoading(false); return; }
    try { setUser(await apiFetch<User>('/users/me')); }
    catch { clearTokens(); setUser(null); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void refreshProfile(); }, [refreshProfile]);
  useEffect(() => {
    const unauthorized = () => { clearTokens(); setUser(null); router.replace('/login'); };
    window.addEventListener('flowlog:unauthorized', unauthorized);
    return () => window.removeEventListener('flowlog:unauthorized', unauthorized);
  }, [router]);

  async function login(email: string, password: string) {
    const response = await apiFetch<AuthResponse>('/auth/login', {
      method: 'POST', body: JSON.stringify({ email, password }),
    });
    saveTokens(response.accessToken, response.refreshToken);
    setUser(await apiFetch<User>('/users/me'));
  }

  const logout = useCallback(async () => {
    try { await revokeSession(); }
    finally { setUser(null); router.replace('/login'); }
  }, [router]);

  const value = useMemo(() => ({ user, loading, login, logout, refreshProfile }), [user, loading, logout, refreshProfile]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth deve ser usado dentro de AuthProvider');
  return context;
}
