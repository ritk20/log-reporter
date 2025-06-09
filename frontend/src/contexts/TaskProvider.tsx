import { useState } from "react";
import { TaskContext, type TaskInfo } from "./TaskContext";

export function TaskProvider({ children }: { children: React.ReactNode }) {
  const [task, setTaskState] = useState<TaskInfo>({
    taskId: null,
    status: "idle",
    error: null,
    progress: null
  });

  const setTask = (t: TaskInfo) => setTaskState(t);
  const clearTask = () => setTaskState({ taskId: null, status: "idle", error: null, progress: null });

  return (
    <TaskContext.Provider value={{ task, setTask, clearTask }}>
      {children}
    </TaskContext.Provider>
  );
}
