import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { agentApi } from "../api/agent";
import type { AgentAction, AgentMessage } from "../types";

export function ChatPage() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [providerUnavailable, setProviderUnavailable] = useState(false);
  const [providerHint, setProviderHint] = useState("");
  const panelRef = useRef<HTMLDivElement | null>(null);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  useEffect(() => {
    async function checkHealth() {
      try {
        const status = await agentApi.health();
        if (!status.data.can_chat) {
          setProviderUnavailable(true);
          if (!status.data.ai_enabled) {
            setProviderHint("La IA está deshabilitada por configuración (AI_ENABLED=false).");
          } else if (status.data.error?.message) {
            setProviderHint(status.data.error.message);
          } else if (!status.data.configured) {
            setProviderHint("Falta configuración del proveedor IA en el backend (.env).");
          } else {
            setProviderHint("El proveedor IA está configurado pero no responde correctamente.");
          }
        } else {
          setProviderUnavailable(false);
          setProviderHint("");
        }
      } catch {
        setProviderUnavailable(true);
        setProviderHint("No se pudo consultar el estado IA. Revisa backend y red.");
      }
    }

    checkHealth();
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSend) return;

    setLoading(true);
    setError("");
    try {
      const res = await agentApi.chat(input.trim());
      setMessages(res.history);
      setActions(res.actions);
      setInput("");

      // Check if the provider is unavailable
      if (!res.success || !res.provider_available) {
        setProviderUnavailable(true);
        setProviderHint(res.error?.message ?? "Proveedor IA no disponible en este momento.");
      } else {
        setProviderUnavailable(false);
        setProviderHint("");
      }

      setTimeout(() => {
        panelRef.current?.scrollTo({ top: panelRef.current.scrollHeight, behavior: "smooth" });
      }, 50);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error de chat");
    } finally {
      setLoading(false);
    }
  }

  async function clearChat() {
    try {
      await agentApi.clear();
    } catch {
      // Clear history locally even if backend call fails
    }
    setMessages([]);
    setActions([]);
    setProviderUnavailable(false);
    setError("");
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
      <section className="rounded-2xl bg-white p-4 shadow-soft">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-black text-ink">Chat con agente</h2>
          <button className="rounded-full bg-slate-100 px-3 py-2 text-sm" onClick={clearChat}>
            Limpiar historial
          </button>
        </div>

        {/* Provider unavailable banner */}
        {providerUnavailable && (
          <div className="mb-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
            <span>⚠️</span>
            <span>
              <strong>IA en modo degradado.</strong> {providerHint} El CRUD de tareas sigue
              operativo desde la sección de Tareas.
            </span>
          </div>
        )}

        <div ref={panelRef} className="h-[420px] space-y-3 overflow-auto rounded-lg border border-slate-200 p-3">
          {messages.length === 0 ? (
            <p className="text-sm text-slate-500">Escribe una instruccion natural para comenzar.</p>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={`${msg.role}-${idx}`}
                className={`max-w-[90%] rounded-2xl px-3 py-2 text-sm ${
                  msg.role === "user"
                    ? "ml-auto bg-ink text-white"
                    : "bg-slate-100 text-slate-800"
                }`}
              >
                {msg.content}
              </div>
            ))
          )}
        </div>

        <form className="mt-3 flex gap-2" onSubmit={handleSubmit}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ej: crea una tarea urgente para enviar reporte hoy"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2"
          />
          <button
            disabled={!canSend}
            className="rounded-lg bg-ink px-4 py-2 font-semibold text-white disabled:opacity-60"
            type="submit"
          >
            {loading ? "Enviando..." : "Enviar"}
          </button>
        </form>

        {error ? <p className="mt-2 rounded bg-coral p-2 text-sm text-red-700">{error}</p> : null}
      </section>

      <section className="rounded-2xl bg-white p-4 shadow-soft">
        <h3 className="mb-2 text-lg font-bold">Acciones ejecutadas</h3>
        <div className="space-y-2 text-sm">
          {actions.length === 0 ? (
            <p className="text-slate-500">Sin acciones en esta respuesta.</p>
          ) : (
            actions.map((action, idx) => (
              <div key={`${action.tool_name}-${idx}`} className="rounded-lg bg-slate-50 p-2">
                <p className="font-semibold text-slate-800">{action.tool_name}</p>
                <p className="text-xs text-slate-600">args: {JSON.stringify(action.arguments)}</p>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
