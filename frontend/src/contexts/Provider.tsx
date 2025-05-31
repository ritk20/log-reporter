import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import type { User } from '../types/auth';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('authToken');
    if (token) {
      // Validate token and set user
      setUser({ id: '1', email: 'admin@example.com', role: 'admin' });
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      // Create form data as the backend expects Form data
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('authToken', data.access_token);
        // Parse JWT payload to get user info
        const payload = JSON.parse(atob(data.access_token.split('.')[1]));
        setUser({
          id: payload.sub,
          email: payload.sub,
          role: payload.role
        });
      } else {
        throw new Error('Login failed');
      }
    } catch (error) {
      throw new Error('Login failed' + (error instanceof Error ? `: ${error.message}` : ''));
    }
};

  const logout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}