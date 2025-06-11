import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthProvider';
import { Layout } from './components/public/Layout';
import { RoleBasedRoute } from './components/auth/RoleBasedRoute';
import { PrivateRoute } from './components/auth/PrivateRoute';
import Login from './pages/Auth/Login';
import Upload from './pages/Admin/upload';
// import Dashboard from './pages/Admin/Dashboard';
import AnalyticsDashboard from './pages/Public/analytics';
import { ErrorBoundary } from './components/public/ErrorBoundary';
import { TaskProvider } from './contexts/TaskProvider';

function App() {
  return (
    <AuthProvider>
      <TaskProvider>
        <ErrorBoundary>
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
                
                {/* <Route path="*" element={<Navigate to="/unauthorized" replace />} /> */}
                
                {/* Analytics - Available to all authenticated users */}
                <Route element={<PrivateRoute />}>
                  <Route path="/analytics" element={<AnalyticsDashboard />} />
                </Route>
                
                <Route path="/unauthorized" element={<div className='text-red-500 flex justify-center text-2xl font-semibold'>Access Denied</div>} />
              </Routes>
            </Layout>
          </BrowserRouter>
        </ErrorBoundary>
      </TaskProvider>
    </AuthProvider>
  );
}

export default App;
