import { useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { AuthContext } from './AuthContext';
import type { User } from '../types/auth';
import { jwtDecode } from 'jwt-decode';

interface JWTPayload {
  exp: number;
  sub: string;
  role: 'admin' | 'viewer';
}

const API_BASE = import.meta.env.VITE_API_BASE;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const validateToken = useCallback((): boolean => {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return false;
    }

    try {
      const decoded = jwtDecode<JWTPayload>(token);
      const currentTime = Date.now() / 1000;

      if (decoded.exp < currentTime) {
        return false;
      }
      
      setUser({
        email: decoded.sub,
        role: decoded.role
      });
      return true;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  }, []);

  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    try {
      const response = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('authToken', data.access_token);
        return data.access_token;
      }
      return null;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    }
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true);
      
      if (!validateToken()) {
        const newToken = await refreshAccessToken();
        if (newToken) {
          validateToken();
        } else {
          localStorage.removeItem('authToken');
          setUser(null);
        }
      }
      
      setIsLoading(false);
    };

    checkAuth();

    const interval = setInterval(checkAuth, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [validateToken, refreshAccessToken]);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('authToken', data.access_token);
        const decoded = jwtDecode<JWTPayload>(data.access_token);
        
        setUser({
          email: decoded.sub,
          role: decoded.role
        });
        return true;
      }
      else return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });

    localStorage.removeItem('authToken');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      logout, 
      isLoading,
      refreshAccessToken
    }}>
      {children}
    </AuthContext.Provider>
  );
}