import { useRef, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Navigate } from 'react-router-dom';
import { useTask } from '../../hooks/useTask';

export default function Upload() {
  const { user } = useAuth();
  const { setTask } = useTask();

  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

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
        taskId: null, 
        status: 'uploading',
        error: null,
        progress: { current: 0, total: 100, message: 'Uploading file...' }
      });

      const response = await fetch('http://localhost:8000/api/upload/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.status === 401) throw new Error('Authentication failed');
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      setMessage(data.message || 'Upload accepted');

      if (data.task_id) {
        setTask({ 
          taskId: data.task_id, 
          status: 'processing',
          error: null,
          progress: { current: 0, total: 100, message: 'Starting processing...' }
        });
      }

      // Reset state for next file
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
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

  return (
    <div className="bg-gray-50 flex items-center justify-center">
      {/* Card Container */}
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm transform transition-all hover:shadow-2xl hover:-translate-y-1">
        <h1 className="text-2xl font-bold text-center text-gray-800 mb-8">
          Logs Uploader
        </h1>

        {/* Hidden native file input */}
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

        {/* Choose File Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex items-center justify-center px-4 py-2 border-2 border-blue-600 text-blue-600 rounded-lg mb-6 transition-all hover:bg-blue-50 hover:scale-105 active:scale-95 focus:outline-none"
        >
          {file ? file.name : 'Choose File'}
        </button>

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg transition-all hover:bg-blue-700 hover:scale-105 active:scale-95 focus:outline-none"
        >
          UPLOAD FILE
        </button>

        {/* Message */}
        {message && (
          <p
            className={`mt-6 text-center font-medium ${
              message.toLowerCase().includes('failed') ? 'text-red-600' : 'text-green-600'
            }`}
          >
            {message}
          </p>
        )}
      </div>
    </div>
  );
}