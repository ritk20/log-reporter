// src/contexts/TaskContext.tsx
import React, { createContext, useContext, useState } from "react";

type TaskStatus = "idle" | "processing" | "completed" | "failed";

export interface TaskInfo {
  taskId: string | null;
  status: TaskStatus;
  error?: string | null;
}

interface TaskContextValue {
  task: TaskInfo;
  setTask: (t: TaskInfo) => void;
  clearTask: () => void;
}

const TaskContext = createContext<TaskContextValue | undefined>(undefined);

export function useTask() {
  const ctx = useContext(TaskContext);
  if (!ctx) throw new Error("useTask must be used within TaskProvider");
  return ctx;
}

export function TaskProvider({ children }: { children: React.ReactNode }) {
  const [task, setTaskState] = useState<TaskInfo>({
    taskId: null,
    status: "idle",
    error: null,
  });

  const setTask = (t: TaskInfo) => setTaskState(t);
  const clearTask = () => setTaskState({ taskId: null, status: "idle", error: null });

  return (
    <TaskContext.Provider value={{ task, setTask, clearTask }}>
      {children}
    </TaskContext.Provider>
  );
}
