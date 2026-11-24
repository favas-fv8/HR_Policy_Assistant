import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../services/http';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const TOKEN_KEY = 'hr_token';

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'hr_admin' | 'employee';
  employee_id: string;
  full_name?: string;
  is_active?: boolean;
}

export interface AuthContextValue {
  user: User | null;
  token: string | null;
  initialized: boolean;
  login: (credentials: { username: string; password: string }) => Promise<User>;
  logout: () => void;
}

export const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export const useAuth = (): AuthContextValue => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [initialized, setInitialized] = useState<boolean>(
    () => localStorage.getItem(TOKEN_KEY) === null,
  );

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      setInitialized(true);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const profile = await apiFetch(`${API_BASE}/v1/accounts/users/me/`, {
          headers: { Authorization: `Bearer ${stored}` },
        });
        if (!cancelled) {
          setToken(stored);
          setUser(profile);
        }
      } catch {
        if (!cancelled) {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
        }
      } finally {
        if (!cancelled) {
          setInitialized(true);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = async (credentials: { username: string; password: string }): Promise<User> => {
    const data = await apiFetch(`${API_BASE}/v1/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    const key = (data as any)?.key;
    if (!key) {
      throw new Error('Login failed');
    }

    const profile = await apiFetch(`${API_BASE}/v1/accounts/users/me/`, {
      headers: { Authorization: `Bearer ${key}` },
    });

    localStorage.setItem(TOKEN_KEY, key);
    setToken(key);
    setUser(profile);
    return profile;
  };

  const logout = () => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      fetch(`${API_BASE}/v1/auth/logout/`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${stored}` },
      }).catch(() => {});
    }
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ user, token, initialized, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
