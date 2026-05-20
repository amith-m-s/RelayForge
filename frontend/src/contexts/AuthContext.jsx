import { createContext, useState, useEffect, useCallback } from 'react';
import { api, apiJson, setTokens, clearTokens } from '../api/client';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const token = localStorage.getItem('rf_access_token');
      if (!token) { setLoading(false); return; }
      const data = await apiJson('/auth/me');
      setUser(data);
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchUser(); }, [fetchUser]);

  const login = async (email, password) => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error?.message || 'Login failed');
    }
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    await fetchUser();
  };

  const register = async (email, full_name, password, organization_name) => {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, full_name, password, organization_name }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error?.message || 'Registration failed');
    }
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    await fetchUser();
  };

  const logout = async () => {
    try {
      const rt = localStorage.getItem('rf_refresh_token');
      if (rt) {
        await api('/auth/logout', { method: 'POST', body: { refresh_token: rt } });
      }
    } catch { /* ignore */ }
    clearTokens();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}
