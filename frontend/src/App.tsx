import { useRef, useState } from 'react';

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file");
      return;
    }
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMessage(data.detail || "Uploaded successfully");
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      // console.error("Upload error:", err);
      setMessage(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
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
            if (file.type === 'application/zip' ||
            file.type === 'application/x-tar' ||
            file.type === 'application/gzip' ||
            file.type === 'text/plain' ||
            file.type === 'application/x-zip-compressed') {
              setFile(file);
              setMessage('');
            } else {
              setMessage('Please select a ZIP file');
              setFile(null);
            }
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