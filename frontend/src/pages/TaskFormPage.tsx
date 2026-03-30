import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { tasksApi } from "../api/tasks";
import { TaskForm } from "../components/TaskForm";
import type { Task } from "../types";

export function TaskFormPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(taskId);
  const [task, setTask] = useState<Task | null>(null);

  useEffect(() => {
    if (!isEdit || !taskId) return;
    tasksApi.get(Number(taskId)).then(setTask);
  }, [isEdit, taskId]);

  async function handleSubmit(payload: {
    title: string;
    description: string | null;
    status: "pending" | "in_progress" | "completed";
    priority: "low" | "medium" | "high";
    due_date: string | null;
  }) {
    if (isEdit && taskId) {
      await tasksApi.update(Number(taskId), payload);
      navigate(`/tasks/${taskId}`);
      return;
    }
    const created = await tasksApi.create(payload);
    navigate(`/tasks/${created.id}`);
  }

  return (
    <div className="rounded-2xl bg-white p-5 shadow-soft">
      <h2 className="mb-4 text-xl font-black text-ink">{isEdit ? "Editar tarea" : "Crear tarea"}</h2>
      {!isEdit || task ? (
        <TaskForm initial={task ?? undefined} onSubmit={handleSubmit} submitLabel={isEdit ? "Actualizar" : "Crear"} />
      ) : (
        <p>Cargando tarea...</p>
      )}
    </div>
  );
}
