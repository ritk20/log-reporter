import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';
import { LoadingSpinner } from '../public/Loading';

interface RoleBasedRouteProps {
  allowedRoles: string[];
}

export function RoleBasedRoute({ allowedRoles }: RoleBasedRouteProps) {
  const { user, isLoading, logout } = useAuth();

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const decoded = jwtDecode<{ exp: number }>(token);
        if (Date.now() >= decoded.exp * 1000) {
          logout();
        }
      } catch {
        logout();
      }
    }
  }, [logout]);

  if (isLoading) {
    return <LoadingSpinner/>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
