import { useCallback, useState } from "react";

import { ApiError } from "../../shared/api/client";
import { fetchStockAnalysis } from "../../shared/api/stockAnalysis";
import type { StockAnalysisResponse } from "../../types/stockAnalysis";

export type StockAnalysisStatus = "idle" | "loading" | "success" | "error";

interface UseStockAnalysisResult {
  status: StockAnalysisStatus;
  data: StockAnalysisResponse | null;
  error: string | null;
  analyze: (ticker: string, selectedDate: string) => Promise<void>;
  reset: () => void;
}

export function useStockAnalysis(): UseStockAnalysisResult {
  const [status, setStatus] = useState<StockAnalysisStatus>("idle");
  const [data, setData] = useState<StockAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (ticker: string, selectedDate: string) => {
    // Drop the previous date's result immediately so a new selection never appears to
    // reuse stale analysis while the new one loads.
    setData(null);
    setStatus("loading");
    setError(null);

    try {
      const response = await fetchStockAnalysis({ ticker, selected_date: selectedDate });
      setData(response);
      setStatus("success");
    } catch (err) {
      const message =
        err instanceof ApiError ? `분석 요청이 실패했습니다. (${err.status})` : "분석 요청 중 알 수 없는 오류가 발생했습니다.";
      setError(message);
      setStatus("error");
    }
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setData(null);
    setError(null);
  }, []);

  return { status, data, error, analyze, reset };
}
