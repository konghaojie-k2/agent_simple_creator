'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import axios from 'axios';
import Cookies from 'js-cookie';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface User {
  id: string;
  email: string;
  name: string;
  roles?: string[];
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const authAxios = axios.create({
  baseURL: API_BASE.replace('/api/v1', ''),
  headers: { 'Content-Type': 'application/json' },
});

authAxios.interceptors.request.use((config) => {
  const token = Cookies.get('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

authAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('access_token');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const token = Cookies.get('access_token');
      if (!token) { setUser(null); return; }
      const response = await authAxios.get('/auth/me');
      setUser(response.data);
    } catch { 
      Cookies.remove('access_token'); 
      setUser(null); 
    }
  };

  const login = async (email: string, password: string) => {
    const response = await authAxios.post('/auth/login', { email, password });
    Cookies.set('access_token', response.data.access_token, { expires: 1 / 24 });
    await refreshUser();
  };

  const register = async (email: string, password: string, name: string) => {
    const response = await authAxios.post('/auth/register', { email, password, name });
    Cookies.set('access_token', response.data.access_token, { expires: 1 / 24 });
    await refreshUser();
  };

  const logout = async () => {
    try { await authAxios.post('/auth/logout'); }
    finally { Cookies.remove('access_token'); setUser(null); }
  };

  useEffect(() => { refreshUser().finally(() => setIsLoading(false)); }, []);

  return (
    <AuthContext.Provider value={{
      user, 
      isLoading, 
      isAuthenticated: !!user,
      login, 
      register, 
      logout, 
      refreshUser
    }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export { authAxios };
