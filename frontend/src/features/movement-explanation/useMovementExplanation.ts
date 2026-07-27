import { useCallback, useRef, useState } from "react";

import { fetchMovementExplanation } from "../../shared/api/explanations";
import { ApiError } from "../../shared/api/client";
import type { LlmProvider, MovementExplanationResponse } from "../../shared/types/explanation";

export type ExplanationStatus = "idle" | "loading" | "success" | "error";

interface UseMovementExplanationResult {
  status: ExplanationStatus;
  data: MovementExplanationResponse | null;
  error: string | null;
  explain: (ticker: string, selectedDate: string, interval: string, llmProvider: LlmProvider) => Promise<void>;
  reset: () => void;
}

export function useMovementExplanation(): UseMovementExplanationResult {
  const [status, setStatus] = useState<ExplanationStatus>("idle");
  const [data, setData] = useState<MovementExplanationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Same stale-response guard as useStockAnalysis: a slower request for an older date/provider
  // must not clobber a newer one that already resolved.
  const requestIdRef = useRef(0);

  const explain = useCallback(
    async (ticker: string, selectedDate: string, interval: string, llmProvider: LlmProvider) => {
      const requestId = ++requestIdRef.current;
      setStatus("loading");
      setError(null);

      try {
        const response = await fetchMovementExplanation({
          ticker,
          selected_date: selectedDate,
          interval,
          llm_provider: llmProvider,
        });
        if (requestIdRef.current !== requestId) return;
        setData(response);
        setStatus("success");
      } catch (err) {
        if (requestIdRef.current !== requestId) return;
        const message =
          err instanceof ApiError
            ? `분석 요청이 실패했습니다. (${err.status})`
            : "분석 요청 중 알 수 없는 오류가 발생했습니다.";
        setError(message);
        setStatus("error");
      }
    },
    [],
  );

  const reset = useCallback(() => {
    requestIdRef.current++;
    setStatus("idle");
    setData(null);
    setError(null);
  }, []);

  return { status, data, error, explain, reset };
}
