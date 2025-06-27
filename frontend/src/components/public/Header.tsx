import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useTask } from '../../hooks/useTask';
import { useState, useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE;

export function Header() {
  const { user, logout } = useAuth();
  const { task, taskHistory, clearTask } = useTask();
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const [latestDate, setLatestDate] = useState(null);
  const notificationRef = useRef<HTMLDivElement>(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target as Node)) {
        setShowNotifications(false);
      }
    };

    if (showNotifications) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showNotifications]);

  useEffect(() => {
    if (task.status === "completed") {
      const fetchLatestDate = async () => {
        try {
          const token = localStorage.getItem("authToken");
          const res = await fetch(`${API_BASE}/analytics/latest-date?token_type=access`, {
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (res.ok) {
            const data = await res.json();
            if (data.date) {
              setLatestDate(data.date);
            }
          }
        } catch (err) {
          console.error("Failed to fetch latest date:", err);
        }
      };
      fetchLatestDate();
    }
  }, [task.status]);

  const handleViewAnalysis = () => {
    if (latestDate) {
      navigate(`/analytics?date=${latestDate}`);
      setShowNotifications(false);
    }
  };

  const getStatusIcon = () => {
    switch (task.status) {
      case 'uploading':
      case 'processing':
        return '🔄';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '📋';
    }
  };

  const getStatusMessage = () => {
    if (task.progress) {
      return task.progress.message || `${task.progress.current}/${task.progress.total}`;
    }
    return task.status === 'idle' ? 'No active tasks' : task.status;
  };

  if (!user) return null;

  const hasActiveTask = task.taskId && task.status !== 'idle';
  const notificationCount = (hasActiveTask ? 1 : 0) + taskHistory.length;

  return (
    <header className="bg-white shadow-md">
      <div className="flex items-center justify-between px-6 py-4">
        <Link to="/" className="text-xl font-bold text-gray-800">
          ABAS Analytics
        </Link>

        <div className="flex items-center space-x-4">
          {/* Notification Bell */}
          <div className="relative" ref={notificationRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 text-gray-600 hover:text-gray-800 focus:outline-none"
            >
              <span className="text-xl">🔔</span>
              {notificationCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                  {notificationCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border z-50">
                <div className="p-4 border-b">
                  <h3 className="font-semibold text-gray-800">Notifications</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {hasActiveTask && (
                    <div className="p-4 border-b bg-blue-50">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <span className="text-lg">{getStatusIcon()}</span>
                          <div>
                            <p className="font-medium text-sm">Current Analysis</p>
                            <p className="text-xs text-gray-600">{getStatusMessage()}</p>
                          </div>
                        </div>
                        {task.status === 'completed' && latestDate && (
                          <button
                            onClick={handleViewAnalysis}
                            className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                          >
                            View Analysis
                          </button>
                        )}
                      </div>
                      {task.progress && task.status !== 'completed' && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${(task.progress.current / task.progress.total) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {taskHistory.length > 0 && (
                    <div className="p-2">
                      <p className="text-xs font-medium text-gray-500 px-2 mb-2">Recent Tasks</p>
                      {taskHistory.map((historyTask, index) => (
                        <div key={index} className="p-2 hover:bg-gray-50 rounded">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm">
                                {historyTask.status === 'completed' ? '✅' : '❌'}
                              </span>
                              <div>
                                <p className="text-xs font-medium">
                                  Analysis {historyTask.status}
                                </p>
                                <p className="text-xs text-gray-500">
                                  {historyTask.completedAt ? new Date(historyTask.completedAt).toLocaleDateString() : 'N/A'}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {notificationCount === 0 && (
                    <div className="p-4 text-center text-gray-500 text-sm">
                      No notifications
                    </div>
                  )}
                </div>

                {hasActiveTask && (
                  <div className="p-3 border-t">
                    <button
                      onClick={() => {
                        clearTask();
                        setShowNotifications(false);
                      }}
                      className="w-full px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded"
                    >
                      Clear Current Task
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          <nav className="flex space-x-4 text-gray-700 font-medium">
            <Link to="/analytics" className="hover:text-blue-600 transition-colors">Analytics</Link>
            <Link to="/query" className="hover:text-blue-600 transition-colors">Query</Link>
            <Link to="/search" className="hover:text-blue-600 transition-colors">Search</Link>
            {user.role === 'admin' && (
              <>
                <Link to="/admin/upload" className="hover:text-blue-600 transition-colors">Upload Logs</Link>
                <Link to="/admin/dashboard" className="hover:text-blue-600 transition-colors">Admin Dashboard</Link>
              </>
            )}
            <button onClick={handleLogout} className="hover:text-red-600 transition-colors">Logout</button>
          </nav>
        </div>
      </div>
    </header>
  );
}
