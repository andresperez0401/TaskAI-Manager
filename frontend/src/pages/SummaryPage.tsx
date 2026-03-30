import { useEffect, useState } from "react";

import { summaryApi } from "../api/summary";
import { formatDate } from "../lib/date";
import type { SummaryResponse } from "../types";

export function SummaryPage() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    summaryApi
      .today()
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Error"));
  }, []);

  if (error) return <p className="rounded bg-coral p-3 text-red-700">{error}</p>;
  if (!summary) return <p>Cargando resumen...</p>;

  const isFallback = summary.analysis.source === "fallback";

  return (
    <div className="space-y-4">
      {/* Degraded mode banner */}
      {isFallback && (
        <div className="flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <span className="text-lg">⚠️</span>
          <span>
            <strong>Modo degradado:</strong> El análisis fue generado localmente. El proveedor de IA no está disponible.
          </span>
        </div>
      )}

      <section className="rounded-2xl bg-white p-5 shadow-soft">
        <div className="mb-2 flex items-center gap-2">
          <h2 className="text-xl font-black text-ink">Resumen del dia</h2>
          {isFallback ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              fallback
            </span>
          ) : (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
              IA
            </span>
          )}
        </div>
        <p className="mt-2 whitespace-pre-line text-slate-700">{summary.analysis.text}</p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl bg-white p-4 shadow-soft">
          <h3 className="mb-2 font-bold">Distribucion por estado</h3>
          {Object.entries(summary.stats.by_status).map(([k, v]) => (
            <p key={k} className="text-sm text-slate-700">{k}: {v}</p>
          ))}
        </div>
        <div className="rounded-2xl bg-white p-4 shadow-soft">
          <h3 className="mb-2 font-bold">Distribucion por prioridad</h3>
          {Object.entries(summary.stats.by_priority).map(([k, v]) => (
            <p key={k} className="text-sm text-slate-700">{k}: {v}</p>
          ))}
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl bg-white p-4 shadow-soft text-center">
          <p className="text-sm text-slate-500">Total</p>
          <p className="text-2xl font-black text-ink">{summary.stats.total_tasks}</p>
        </div>
        <div className="rounded-2xl bg-white p-4 shadow-soft text-center">
          <p className="text-sm text-slate-500">Vencidas</p>
          <p className="text-2xl font-black text-red-700">{summary.stats.overdue_count}</p>
        </div>
        <div className="rounded-2xl bg-white p-4 shadow-soft text-center">
          <p className="text-sm text-slate-500">Vencen hoy</p>
          <p className="text-2xl font-black text-amber-700">{summary.stats.due_today_count}</p>
        </div>
      </section>

      <section className="rounded-2xl bg-white p-4 shadow-soft">
        <h3 className="mb-2 font-bold">Urgencias</h3>
        <div className="space-y-2">
          {summary.overdue_tasks.map((task) => (
            <div key={task.id} className="rounded-lg bg-coral p-2 text-sm">
              {task.title} - vencida: {formatDate(task.due_date)}
            </div>
          ))}
          {summary.due_today_tasks.map((task) => (
            <div key={task.id} className="rounded-lg bg-amber-50 p-2 text-sm">
              {task.title} - vence hoy: {formatDate(task.due_date)}
            </div>
          ))}
          {summary.overdue_tasks.length === 0 && summary.due_today_tasks.length === 0 && (
            <p className="text-sm text-slate-500">No hay urgencias. ¡Buen trabajo!</p>
          )}
        </div>
      </section>
    </div>
  );
}
