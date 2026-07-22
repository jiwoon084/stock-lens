import { apiRequest } from "./client";
import type { StockAnalysisRequest, StockAnalysisResponse } from "../../types/stockAnalysis";

export function fetchStockAnalysis(request: StockAnalysisRequest): Promise<StockAnalysisResponse> {
  return apiRequest<StockAnalysisResponse>("/api/analysis/date", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
