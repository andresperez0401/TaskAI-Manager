import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { tasksApi } from "../api/tasks";
import { formatDate } from "../lib/date";
import type { Task, TaskPriority, TaskStatus } from "../types";

export function TasksPage() {
  const [items, setItems] = useState<Task[]>([]);
  const [status, setStatus] = useState<TaskStatus | "">("");
  const [priority, setPriority] = useState<TaskPriority | "">("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await tasksApi.list({
        status: status || undefined,
        priority: priority || undefined,
        search: search || undefined,
      });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function removeTask(id: number) {
    if (!window.confirm("Eliminar tarea?")) return;
    await tasksApi.remove(id);
    await load();
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-2xl font-black text-ink">Listado de tareas</h2>
        <Link className="rounded-full bg-ink px-4 py-2 text-white" to="/tasks/new">
          Crear tarea
        </Link>
      </div>

      <div className="grid gap-3 rounded-2xl bg-white p-4 shadow-soft sm:grid-cols-4">
        <select
          className="rounded-lg border border-slate-300 px-3 py-2"
          value={status}
          onChange={(e) => setStatus(e.target.value as TaskStatus | "")}
        >
          <option value="">Estado</option>
          <option value="pending">pending</option>
          <option value="in_progress">in_progress</option>
          <option value="completed">completed</option>
        </select>

        <select
          className="rounded-lg border border-slate-300 px-3 py-2"
          value={priority}
          onChange={(e) => setPriority(e.target.value as TaskPriority | "")}
        >
          <option value="">Prioridad</option>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
        </select>

        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          placeholder="Buscar"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <button className="rounded-lg bg-slate-900 px-3 py-2 text-white" onClick={load}>
          Filtrar
        </button>
      </div>

      {error ? <p className="rounded bg-coral p-3 text-red-700">{error}</p> : null}
      {loading ? <p>Cargando...</p> : null}

      <div className="overflow-auto rounded-2xl bg-white shadow-soft">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="px-4 py-3">Titulo</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Prioridad</th>
              <th className="px-4 py-3">Fecha limite</th>
              <th className="px-4 py-3">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {items.map((task) => (
              <tr key={task.id} className="border-t border-slate-100">
                <td className="px-4 py-3">{task.title}</td>
                <td className="px-4 py-3">{task.status}</td>
                <td className="px-4 py-3">{task.priority}</td>
                <td className="px-4 py-3">{formatDate(task.due_date)}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <Link className="text-blue-700" to={`/tasks/${task.id}`}>
                      Ver
                    </Link>
                    <Link className="text-amber-700" to={`/tasks/${task.id}/edit`}>
                      Editar
                    </Link>
                    <button className="text-red-700" onClick={() => removeTask(task.id)}>
                      Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
