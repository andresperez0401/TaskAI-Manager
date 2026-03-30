import { apiFetch } from "./client";
import type { SummaryResponse } from "../types";

export const summaryApi = {
  today: () => apiFetch<SummaryResponse>("/api/summary/today"),
};
