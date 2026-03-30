import { useState, type FormEvent } from "react";

import { fromDatetimeLocal, toDatetimeLocal } from "../lib/date";
import type { Task, TaskPriority, TaskStatus } from "../types";

interface TaskFormProps {
  initial?: Partial<Task>;
  onSubmit: (payload: {
    title: string;
    description: string | null;
    status: TaskStatus;
    priority: TaskPriority;
    due_date: string | null;
  }) => Promise<void>;
  submitLabel: string;
}

export function TaskForm({ initial, onSubmit, submitLabel }: TaskFormProps) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [status, setStatus] = useState<TaskStatus>(initial?.status ?? "pending");
  const [priority, setPriority] = useState<TaskPriority>(initial?.priority ?? "medium");
  const [dueDate, setDueDate] = useState(toDatetimeLocal(initial?.due_date ?? null));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError("El titulo es obligatorio");
      return;
    }

    setError("");
    setLoading(true);
    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim() ? description : null,
        status,
        priority,
        due_date: fromDatetimeLocal(dueDate),
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error al guardar";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      {error ? <p className="rounded bg-coral p-3 text-sm text-red-700">{error}</p> : null}

      <div>
        <label className="mb-1 block text-sm font-medium">Titulo</label>
        <input
          className="w-full rounded-lg border border-slate-300 px-3 py-2"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">Descripcion</label>
        <textarea
          className="w-full rounded-lg border border-slate-300 px-3 py-2"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label className="mb-1 block text-sm font-medium">Estado</label>
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={status}
            onChange={(e) => setStatus(e.target.value as TaskStatus)}
          >
            <option value="pending">pending</option>
            <option value="in_progress">in_progress</option>
            <option value="completed">completed</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Prioridad</label>
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
          >
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Fecha limite</label>
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
            type="datetime-local"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="rounded-full bg-ink px-4 py-2 font-semibold text-white disabled:opacity-60"
      >
        {loading ? "Guardando..." : submitLabel}
      </button>
    </form>
  );
}
