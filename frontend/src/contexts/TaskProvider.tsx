import { useState, useEffect, useCallback } from "react";
import { TaskContext, type TaskInfo } from "./TaskContext";

export function TaskProvider({ children }: { children: React.ReactNode }) {
  const initialTaskState: TaskInfo = {
    taskId: null,
    status: "idle" as const,
    error: null,
    progress: null
  };

  const API_BASE = import.meta.env.VITE_API_BASE;

  const [task, setTaskState] = useState<TaskInfo>(initialTaskState);

  const [taskHistory, setTaskHistory] = useState<TaskInfo[]>([]);

  const setTask = (t: TaskInfo) => setTaskState(t);
  
  const clearTask = () => setTaskState({ 
    taskId: null, 
    status: "idle", 
    error: null, 
    progress: null 
  });

  const addToHistory = useCallback((completedTask: TaskInfo) => {
    setTaskHistory(prev => [completedTask, ...prev.slice(0, 9)]); // Keep last 10
  }, []);

  // Background polling effect
  useEffect(() => {
    if(task.status === 'idle' || task.status === 'uploading') {
      return; // Don't poll if idle or uploading
    }
    if (!task.taskId || task.status === 'completed' || task.status === 'failed') {
      return;
    }

    const token = localStorage.getItem("authToken");
    if (!token) return;

    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/upload/task/${task.taskId}?token_type=access`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) {
          setTask({ ...task, status: 'failed', error: 'Network error' });
          return;
        }

        const data = await res.json();
        
        const updatedTask = {
          taskId: task.taskId,
          status: data.status,
          error: data.error || null,
          progress: data.progress || null
        };
        console.log("task status:", updatedTask);
        setTask(updatedTask);

        if (data.status === "completed" || data.status === "failed") {
          // Add to history when task completes
          addToHistory({
            ...updatedTask,
            completedAt: new Date().toISOString()
          });
        }

      } catch {
        setTask({ ...task, status: 'failed', error: 'Network error while polling' });
      }
    };

    const interval = setInterval(checkStatus, 1000);
    return () => clearInterval(interval);

  }, [task.taskId, task.status, addToHistory]);

  const contextValue = {
    task,
    setTask,
    clearTask,
    taskHistory
  };

  return (
    <TaskContext.Provider value={contextValue}>
      {children}
    </TaskContext.Provider>
  );
}
