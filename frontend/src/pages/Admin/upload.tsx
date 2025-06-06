import { useRef, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Navigate } from 'react-router-dom';
import { useTask } from '../../contexts/TaskContext';

export default function Upload() {
  const {user} = useAuth();
  const { setTask } = useTask();

  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== 'admin') {
    return <Navigate to="/unauthorized" replace />;
  }

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Get the auth token from localStorage
      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('Not authenticated');
      }

      const response = await fetch("http://localhost:8000/api/upload/upload", {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (response.status === 401) {
        throw new Error('Authentication failed');
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMessage(data.message || "Uploaded successfully");
      
      // If task_id is returned, poll for status
      if (data.task_id) {
        setTask({ taskId: data.task_id, status: "processing", error: null });
      }

    } catch (err) {
      setMessage(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setTask({ taskId: null, status: "failed", error: err instanceof Error ? err.message : 'Unknown error' });
    }
};

// Add polling function for task status
// const pollTaskStatus = async (taskId: string) => {
//     const token = localStorage.getItem('authToken');
//     if (!token) return;

//     const checkStatus = async () => {
//       try {
//         const response = await fetch(`http://localhost:8000/api/upload/task/${taskId}`, {
//           headers: {
//             'Authorization': `Bearer ${token}`
//           }
//         });
//         const data = await response.json();
        
//         if (data.status === 'completed') {
//           setMessage('File processed successfully!');
//           return true;
//         } else if (data.status === 'failed') {
//           setMessage(`Processing failed: ${data.error || 'Unknown error'}`);
//           return true;
//         }
//         return false;
//       } catch (err) {
//         setMessage('Error checking status');
//         console.error(err);
//         return false; 
//       }
//     };

//     // Poll every 2 seconds until complete
//     const poll = setInterval(async () => {
//       const isDone = await checkStatus();
//       if (isDone) clearInterval(poll);
//     }, 2000);
// };

  return (
    <div className="flex flex-col items-center justify-center min-h-full">
      <div className="p-2">
        <h1 className="text-3xl font-bold text-center text-gray-800">
          Logs Uploader
        </h1>
      </div>
      
      <div className="m-4 flex flex-col align-flex-start max-w-md">
        <input
          ref={fileInputRef}
          type="file"
          accept='.zip, .tar, .gz, .log'
          className="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            if (!e.target.files || e.target.files.length === 0) {
              setFile(null);
              setMessage('No file selected');
              return;
            }
            const file = e.target.files[0];
              setFile(file);
              setMessage('');
          }}
        />
      </div>
      <button 
          onClick={handleUpload} 
          className="py-3 px-4 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 transition duration-200 ease-in-out transform hover:scale-105"
        >
          UPLOAD FILE
      </button>

      {message && (
        <p className={`mt-4 text-center ${
          message.includes('failed') ? 'text-red-600' : 'text-green-600'
        } font-medium`}>
          {message}
        </p>
      )}
    </div>
  );
}