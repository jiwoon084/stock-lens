import { apiRequest } from "./client";
import type { ChecklistResponse } from "../types/checklist";

export function fetchChecklist(ticker: string): Promise<ChecklistResponse> {
  return apiRequest<ChecklistResponse>(`/api/v1/stocks/${ticker}/checklist`);
}
