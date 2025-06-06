import { useEffect } from "react";
import { useTask } from "../../contexts/TaskContext";

export default function UploadWidget() {
  const { task, setTask, clearTask } = useTask();
  const { taskId, status, error } = task;

  // Polling effect: once taskId exists & status is 'processing'
  useEffect(() => {
    if (!taskId || status !== "processing") {
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
        if (data.status === "completed") {
          setTask({ taskId, status: "completed", error: null });
          // Automatically hide widget after a short delay
          setTimeout(() => clearTask(), 3000);
        } else if (data.status === "failed") {
          setTask({ taskId, status: "failed", error: data.error || "Unknown error" });
          // Leave it open so user can see error; they can close manually
        }
      } catch {
        setTask({ taskId, status: "failed", error: "Network error while polling" });
      }
    };

    const interval = setInterval(checkStatus, 2000);
    return () => clearInterval(interval);
  }, [taskId, status, setTask, clearTask]);

  // Don’t render anything unless task is active
  if (!taskId) return null;

  return (
    <div className="fixed bottom-10 right-10 z-50">
      <div className="w-64 bg-white border border-gray-200 rounded shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between bg-blue-600 text-white px-3 py-2 rounded-t">
          <span className="font-medium text-sm">Upload Status</span>
          <button
            onClick={() => clearTask()}
            className="text-lg leading-none"
            title="Close"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="p-3 space-y-2 text-sm">
          {status === "processing" && (
            <div className="flex items-center space-x-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
              <span>Processing...</span>
            </div>
          )}

          {status === "completed" && (
            <div className="space-y-2">
              <p className="text-green-700">✅ Completed!</p>
              <a
                href={`/analysis`}
                className="block w-full text-center px-2 py-1 bg-green-600 text-white rounded text-xs"
              >
                View Analysis (24h)
              </a>
            </div>
          )}

          {status === "failed" && (
            <div className="space-y-2">
              <p className="text-red-600">❌ {error}</p>
              <button
                onClick={() => clearTask()}
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
