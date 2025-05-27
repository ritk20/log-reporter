import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/Provider';
import { Layout } from './components/public/Layout';
import { RoleBasedRoute } from './components/auth/RoleBasedRoute';
import { PrivateRoute } from './components/auth/PrivateRoute';
import Login from './pages/Auth/Login';
import Upload from './pages/Admin/upload';
// import Dashboard from './pages/Admin/Dashboard';
// import AnalyticsDashboard from './pages/Analytics/AnalyticsDashboard';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Navigate to="/analytics" replace />} />
            
            {/* Admin Routes */}
            <Route element={<RoleBasedRoute allowedRoles={['admin']} />}>
              <Route path="/admin/upload" element={<Upload />} />
              {/* <Route path="/admin/dashboard" element={<Dashboard />} /> */}
            </Route>
            
            {/* Analytics - Available to all authenticated users */}
            <Route element={<PrivateRoute />}>
              {/* <Route path="/analytics" element={<AnalyticsDashboard />} /> */}
            </Route>
            
            <Route path="/unauthorized" element={<div>Access Denied</div>} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
