import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { tasksApi } from "../api/tasks";
import { formatDate } from "../lib/date";
import type { Task } from "../types";

export function TaskDetailPage() {
  const { taskId } = useParams();
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!taskId) return;
    tasksApi
      .get(Number(taskId))
      .then(setTask)
      .catch((err) => setError(err instanceof Error ? err.message : "Error"));
  }, [taskId]);

  if (error) return <p className="rounded bg-coral p-3 text-red-700">{error}</p>;
  if (!task) return <p>Cargando detalle...</p>;

  return (
    <div className="space-y-4 rounded-2xl bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-2">
        <h2 className="text-2xl font-black text-ink">{task.title}</h2>
        <Link className="rounded-full bg-slate-100 px-3 py-2" to={`/tasks/${task.id}/edit`}>
          Editar
        </Link>
      </div>

      <p className="text-slate-700">{task.description || "Sin descripcion"}</p>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs uppercase text-slate-500">Estado</p>
          <p className="font-semibold">{task.status}</p>
        </div>
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs uppercase text-slate-500">Prioridad</p>
          <p className="font-semibold">{task.priority}</p>
        </div>
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs uppercase text-slate-500">Fecha limite</p>
          <p className="font-semibold">{formatDate(task.due_date)}</p>
        </div>
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs uppercase text-slate-500">Actualizada</p>
          <p className="font-semibold">{formatDate(task.updated_at)}</p>
        </div>
      </div>
    </div>
  );
}
