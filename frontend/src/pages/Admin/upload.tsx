import { useRef, useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Navigate, useNavigate } from 'react-router-dom';
import { useTask } from '../../hooks/useTask';
import type { TaskInfo } from '../../contexts/TaskContext';

const API_BASE = import.meta.env.VITE_API_BASE;

export default function Upload() {
  const { user } = useAuth();
  const { setTask, task } = useTask();

  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [showCompletion, setShowCompletion] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Reset completion status when component mounts or when task changes
    setShowCompletion(false);
    
    return () => {
      // Cleanup when component unmounts
      if (task?.status === 'completed') {
        setTask({
          taskId: null,
          status: 'idle',
          error: null,
          progress: null
        });
      }
    };
  }, [task?.status, setTask]);

  useEffect(() => {
    // Show completion when task completes
    if (task?.status === 'completed') {
      setShowCompletion(true);
    }
  }, [task?.status]);

  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'admin') return <Navigate to="/unauthorized" replace />;

  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('authToken');
      if (!token) throw new Error('Not authenticated');

      setTask({
        taskId: "uploading",
        status: 'uploading',
        error: null,
        progress: { current: 0, total: 100, message: 'Uploading file...' }
      });

      const xhr = new XMLHttpRequest();

      xhr.open('POST', 'http://backend:8000/api/upload/upload', true);
      xhr.withCredentials = true;
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);

      xhr.upload.addEventListener('progress', (e) => {
        if (!e.lengthComputable) return;
        const pct = Math.round((e.loaded / e.total) * 100);
        setTask(((prev: TaskInfo) => ({
          ...prev,
          progress: {
            current: pct,
            total: 100,
            message: `Uploading… ${pct}%`
          }
        })) as unknown as TaskInfo);    //quick fix for type error, will need to update your provider to accept updater functions in future
      });

      xhr.onreadystatechange = () => {
        if (xhr.readyState === 4) {
          if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);
            setTask({
              taskId: data.task_id,
              status: 'processing',
              error: null,
              progress: { current: 0, total: 100, message: 'Starting processing…' }
            });
          } else {
            setTask({
              taskId: null,
              status: 'failed',
              error: `Upload failed: ${xhr.status}`,
              progress: null
            });
          }
        }
      };

      xhr.addEventListener('error', () => {
        throw new Error('Upload failed');
      });

      xhr.open('POST', `${API_BASE}/api/upload/upload`);
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.setRequestHeader('filename', encodeURIComponent(file.name));
      xhr.send(formData);

    } catch (err) {
      setMessage(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setTask({
        taskId: null,
        status: 'failed',
        error: err instanceof Error ? err.message : 'Unknown error',
        progress: null
      });
    }
  };

  const handleViewAnalysis = () => {
    setShowCompletion(false);
    navigate('/analytics');
  };

  return (
    <div className="bg-gray-50 h-screen overflow-hidden flex flex-col items-center justify-start pt-8">
      {/* Upload Card - Always visible */}
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm mb-6">
        <h1 className="text-2xl font-bold text-center text-gray-800 mb-8">
          Logs Uploader
        </h1>

        <input
          ref={fileInputRef}
          type="file"
          accept=".zip,.tar,.gz,.log"
          className="hidden"
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            const selectedFile = e.target.files?.[0] || null;
            setFile(selectedFile);
            setMessage('');
          }}
        />

        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex items-center justify-center px-4 py-2 border-2 border-blue-600 text-blue-600 rounded-lg mb-6 transition-all hover:bg-blue-50 hover:scale-105 active:scale-95 focus:outline-none"
        >
          {file ? file.name : 'Choose File'}
        </button>

        <button
          onClick={handleUpload}
          disabled={task?.status === 'uploading' || task?.status === 'processing'}
          className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg transition-all hover:bg-blue-700 hover:scale-105 active:scale-95 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {task?.status === 'uploading' || task?.status === 'processing' ? 'UPLOADING...' : 'UPLOAD FILE'}
        </button>

        {message && (
          <p className={`mt-6 text-center font-medium ${message.toLowerCase().includes('failed') ? 'text-red-600' : 'text-green-600'}`}>
            {message}
          </p>
        )}
      </div>

      {/* Progress Indicator */}
      {(task?.status === 'uploading' || task?.status === 'processing') && (
        <div className="w-full max-w-sm bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex items-center justify-center mb-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
            <span className="text-lg font-semibold text-gray-700">
              {task.status === 'uploading' ? 'Uploading...' : 'Processing...'}
            </span>
          </div>
          <div className="flex justify-between text-sm text-gray-600 mb-3">
            <span className="font-medium">{task.progress?.message}</span>
            <span className="font-bold text-blue-600">{task.progress?.current}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out shadow-sm"
              style={{ width: `${task.progress?.current || 0}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Completion Message */}
      {showCompletion && (
        <div className="w-full max-w-sm bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl shadow-lg border border-green-200 p-6 mb-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-green-800 mb-2">Upload Complete!</h3>
            <p className="text-sm text-green-600 mb-6">Your file has been processed successfully</p>
            <button
              onClick={handleViewAnalysis}
              className="w-full py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold rounded-lg hover:from-green-700 hover:to-emerald-700 hover:scale-105 active:scale-95 focus:outline-none"
            >
              🔍 Go To All-Time Analysis
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {task?.status === 'failed' && (
        <div className="w-full max-w-sm bg-gradient-to-br from-red-50 to-pink-50 rounded-xl shadow-lg border border-red-200 p-6 mb-6">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-red-800 mb-2">Upload Failed</h3>
            <p className="text-sm text-red-600 mb-4">{task.error || 'Something went wrong'}</p>
            <button
              onClick={() => setTask({ taskId: null, status: 'idle', error: null, progress: null })}
              className="px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700"
            >
              Try Again
            </button>
          </div>
        </div>
      )}
    </div>
  );
}