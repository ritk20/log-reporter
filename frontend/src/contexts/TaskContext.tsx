// src/contexts/TaskContext.tsx
import { createContext } from "react";

export interface TaskProgress {
  current: number;
  total: number;
  message?: string;
}

export interface TaskInfo {
  taskId: string | null;
  status: TaskStatus;
  error: string | null;
  progress: TaskProgress | null;
}

type TaskStatus = 
  | "idle"
  | "uploading"
  | "processing"
  | "extracting_files"
  | "parsing_logs"
  | "processing_records"
  | "storing_data"
  | "generating_report"
  | "completed"
  | "failed";

interface TaskContextValue {
  task: TaskInfo;
  setTask: (t: TaskInfo) => void;
  clearTask: () => void;
}

export const TaskContext = createContext<TaskContextValue | undefined>(undefined);