const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    try {
      const data = JSON.parse(text) as { detail?: unknown };
      if (typeof data.detail === "string") {
        throw new Error(data.detail);
      }
      if (Array.isArray(data.detail)) {
        const messages = data.detail
          .map((x) => (typeof x?.msg === "string" ? x.msg : null))
          .filter(Boolean)
          .join("; ");
        throw new Error(messages || `Request failed (${response.status})`);
      }
    } catch {
      throw new Error(text || `Request failed (${response.status})`);
    }
    throw new Error(text || `Request failed (${response.status})`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
