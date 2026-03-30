import { apiFetch } from "./client";
import type { AIChatApiResponse, AIHealthApiResponse, AgentChatResponse } from "../types";

export const agentApi = {
  chat: (message: string, sessionId = "global") =>
    apiFetch<AIChatApiResponse>("/api/ai/chat", {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId }),
    }).then((res) => ({
      success: res.data.success,
      provider_available: res.data.provider_available,
      fallback_mode: res.data.fallback_mode,
      answer: res.data.answer,
      message: res.data.answer,
      actions: res.data.actions,
      tasks_changed: res.data.tasks_changed ?? [],
      history: res.data.history,
      data: null,
      error: res.data.error ?? null,
    }) as AgentChatResponse),
  health: () => apiFetch<AIHealthApiResponse>("/api/ai/health?probe=true"),
  clear: (sessionId = "global") =>
    apiFetch<void>(`/api/ai/history?session_id=${sessionId}`, { method: "DELETE" }),
};
