import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { summaryApi } from "../api/summary";
import type { SummaryResponse } from "../types";

export function DashboardPage() {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    summaryApi
      .today()
      .then(setSummary)
      .catch((err) => setError(err instanceof Error ? err.message : "Error"));
  }, []);

  if (error) return <p className="rounded bg-coral p-3 text-red-700">{error}</p>;
  if (!summary) return <p>Cargando dashboard...</p>;

  const isFallback = summary.analysis.source === "fallback";

  return (
    <div className="space-y-6">
      {/* Degraded mode banner */}
      {isFallback && (
        <div className="flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <span className="text-lg">⚠️</span>
          <span>
            <strong>Modo degradado:</strong> El proveedor de IA no está disponible.
            Las estadísticas y el CRUD de tareas siguen operativos.
          </span>
        </div>
      )}

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl bg-white p-4 shadow-soft">
          <p className="text-sm text-slate-500">Total tareas</p>
          <p className="text-3xl font-black text-ink">{summary.stats.total_tasks}</p>
        </div>
        <div className="rounded-2xl bg-white p-4 shadow-soft">
          <p className="text-sm text-slate-500">Vencidas</p>
          <p className="text-3xl font-black text-red-700">{summary.stats.overdue_count}</p>
        </div>
        <div className="rounded-2xl bg-white p-4 shadow-soft">
          <p className="text-sm text-slate-500">Vencen hoy</p>
          <p className="text-3xl font-black text-amber-700">{summary.stats.due_today_count}</p>
        </div>
      </section>

      <section className="rounded-2xl bg-white p-5 shadow-soft">
        <div className="mb-2 flex items-center gap-2">
          <h2 className="text-lg font-bold">Diagnostico del dia</h2>
          {isFallback && (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              fallback
            </span>
          )}
          {!isFallback && (
            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
              IA
            </span>
          )}
        </div>
        <p className="whitespace-pre-line text-slate-700">{summary.analysis.text}</p>
      </section>

      <section className="rounded-2xl bg-white p-5 shadow-soft">
        <h2 className="mb-3 text-lg font-bold">Accesos rapidos</h2>
        <div className="flex flex-wrap gap-2">
          <Link className="rounded-full bg-ink px-4 py-2 text-white" to="/tasks/new">
            Nueva tarea
          </Link>
          <Link className="rounded-full bg-slate-100 px-4 py-2" to="/chat">
            Chat con agente
          </Link>
          <Link className="rounded-full bg-slate-100 px-4 py-2" to="/summary">
            Ver resumen completo
          </Link>
        </div>
      </section>
    </div>
  );
}
