import { useEffect, useState } from "react";
import { useTask } from "../../hooks/useTask";

export default function UploadWidget() {
  const { task, setTask, clearTask } = useTask();
  const { taskId, status, error, progress } = task;
  const [latestDate, setLatestDate] = useState<string | null>(null);

  // Polling effect: once taskId exists & status is 'processing'
  useEffect(() => {
    if (!taskId) {
      return;
    }

    const token = localStorage.getItem("authToken");
    if (!token) return;

    const checkStatus = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/upload/task/${taskId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          // If we get 404 or 500, treat as failure
          clearTask();
          return;
        }
        const data = await res.json();
        setTask({
          taskId,
          status: data.status,
          error: data.error || null,
          progress: data.progress || null
        });
        if (data.status === "completed") {
          setTask({ taskId, status: "completed", error: null, progress: null });
          // Automatically hide widget after a short delay
          setTimeout(() => clearTask(), 5000);
        } else if (data.status === "failed") {
          setTask({ taskId, status: "failed", error: data.error || "Unknown error", progress: null });
          // Leave it open so user can see error; they can close manually
        }
      } catch {
        setTask({ taskId, status: "failed", error: "Network error while polling", progress: null });
      }
    };

    const interval = setInterval(checkStatus, 500);
    return () => clearInterval(interval);
  }, [taskId, status, setTask, clearTask]);

  // Add effect to fetch latest date when upload completes
  useEffect(() => {
    if (status === "completed") {
      const fetchLatestDate = async () => {
        try {
          const token = localStorage.getItem("authToken");
          const res = await fetch("http://localhost:8000/analytics/latest-date", {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setLatestDate(data.date);
            console.log(latestDate)
          }
        } catch (err) {
          console.error("Failed to fetch latest date:", err);
        }
      };
      fetchLatestDate();
    }
  }, [status, latestDate]);

  // Don’t render anything unless task is active
  if (!taskId) return null;

  const getStatusMessage = () => {
    if (!progress) return "Processing...";
    return progress.message || `${progress.current}/${progress.total}`;
  };

  return (
    <div className="fixed bottom-2 right-1 z-50">
      <div className="w-64 bg-white border border-gray-200 rounded shadow-lg">
        <div className="flex items-center justify-between bg-blue-600 text-white px-3 py-2 rounded-t">
          <span className="font-medium text-sm">Upload Status</span>
          <button
            onClick={clearTask}
            className="text-lg leading-none"
            title="Close"
          >
            ×
          </button>
        </div>

        <div className="p-3 space-y-2 text-sm">
          {status !== 'completed' && status !== 'failed' && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                <span>{getStatusMessage()}</span>
              </div>
              {progress && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 rounded-full h-2 transition-all duration-300"
                    style={{ 
                      width: `${(progress.current / progress.total * 100) || 0}%`
                    }} 
                  />
                </div>
              )}
            </div>
          )}

          {status === "completed" && latestDate !== '' && (
            <div className="space-y-2">
              <p className="text-green-700">✅ Completed!</p>
              <a
                href={`/analytics?date=${latestDate || ''}`}
                className="block w-full text-center px-2 py-1 bg-green-600 text-white rounded text-xs"
              >
                View Analysis
              </a>
            </div>
          )}

          {status === "failed" && (
            <div className="space-y-2">
              <p className="text-red-600">❌ {error}</p>
              <button
                onClick={clearTask}
                className="block w-full text-center px-2 py-1 bg-gray-300 text-gray-700 rounded text-xs"
              >
                Dismiss
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}