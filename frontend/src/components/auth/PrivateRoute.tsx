import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { LoadingSpinner } from '../public/Loading';

export function PrivateRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner/>;
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />;
}
