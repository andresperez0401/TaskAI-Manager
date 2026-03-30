export type TaskStatus = "pending" | "in_progress" | "completed";
export type TaskPriority = "low" | "medium" | "high";

export interface Task {
  id: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: Task[];
  total: number;
}

export interface TaskStats {
  total: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
}

// ── Summary (new contract) ───────────────────────────────────────────────

export interface SummaryStats {
  total_tasks: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  overdue_count: number;
  due_today_count: number;
  upcoming_count: number;
}

export interface SummaryAnalysis {
  text: string;
  source: "ai" | "fallback";
}

export interface SummaryResponse {
  generated_at: string;
  stats: SummaryStats;
  analysis: SummaryAnalysis;
  overdue_tasks: Task[];
  due_today_tasks: Task[];
  due_this_week_tasks: Task[];
}

// ── Agent (with resilience fields) ───────────────────────────────────────

export interface AgentAction {
  tool_name: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
}

export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AgentChatResponse {
  success: boolean;
  provider_available: boolean;
  fallback_mode: boolean;
  answer: string;
  message: string | null;
  actions: AgentAction[];
  tasks_changed?: Array<{ id: number; operation: string }>;
  history: AgentMessage[];
  data: Record<string, unknown> | null;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  } | null;
}

export interface AIChatApiResponse {
  data: {
    success: boolean;
    provider_available: boolean;
    fallback_mode: boolean;
    answer: string;
    actions: AgentAction[];
    tasks_changed?: Array<{ id: number; operation: string }>;
    history: AgentMessage[];
    error?: {
      code: string;
      message: string;
      details?: Record<string, unknown>;
    } | null;
  };
  meta: Record<string, unknown>;
}

// ── AI Status ────────────────────────────────────────────────────────────

export interface AIStatusResponse {
  ai_enabled: boolean;
  provider: string;
  available: boolean;
  model: string;
  allow_fallback: boolean;
  configured?: boolean;
  can_chat?: boolean;
  error?: {
    code: string;
    message: string;
  } | null;
}

export interface AIHealthApiResponse {
  data: {
    ai_enabled: boolean;
    provider: string;
    model: string;
    configured: boolean;
    provider_available: boolean;
    can_chat: boolean;
    allow_fallback: boolean;
    error?: {
      code: string;
      message: string;
      details?: Record<string, unknown>;
    } | null;
  };
  meta: Record<string, unknown>;
}
