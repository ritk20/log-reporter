import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <header className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <h1 className="text-xl font-bold">ABAS Analytics</h1>
          
          <nav className="flex space-x-4">
            <Link to="/analytics" className="hover:underline">
              Analytics
            </Link>
            {user.role === 'admin' && (
              <>
                <Link to="/admin/upload" className="hover:underline">
                  Upload Logs
                </Link>
                <Link to="/admin/dashboard" className="hover:underline">
                  Admin Dashboard
                </Link>
              </>
            )}
            <button onClick={handleLogout} className="hover:underline">
              Logout ({user.email})
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}
