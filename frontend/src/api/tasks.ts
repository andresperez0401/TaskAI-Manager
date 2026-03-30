import { apiFetch } from "./client";
import type { Task, TaskListResponse, TaskPriority, TaskStats, TaskStatus } from "../types";

export interface TaskFilters {
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date_from?: string;
  due_date_to?: string;
  search?: string;
}

export interface TaskPayload {
  title: string;
  description?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string | null;
}

function toQuery(filters: TaskFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v) params.set(k, v);
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const tasksApi = {
  list: (filters: TaskFilters = {}) =>
    apiFetch<TaskListResponse>(`/api/tasks${toQuery(filters)}`),
  get: (id: number) => apiFetch<Task>(`/api/tasks/${id}`),
  create: (payload: TaskPayload) =>
    apiFetch<Task>("/api/tasks", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: number, payload: Partial<TaskPayload>) =>
    apiFetch<Task>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  complete: (id: number) => apiFetch<Task>(`/api/tasks/${id}/complete`, { method: "PATCH" }),
  remove: (id: number) => apiFetch<void>(`/api/tasks/${id}`, { method: "DELETE" }),
  stats: () => apiFetch<TaskStats>("/api/tasks/stats"),
};
