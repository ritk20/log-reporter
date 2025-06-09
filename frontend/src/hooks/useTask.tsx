import { useContext } from "react";
import { TaskContext } from "../contexts/TaskContext";

export function useTask() {
  const ctx = useContext(TaskContext);
  if (!ctx) throw new Error("useTask must be used within TaskProvider");
  return ctx;
}