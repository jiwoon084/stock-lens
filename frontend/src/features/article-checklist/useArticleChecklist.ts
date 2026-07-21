import { useEffect, useState } from "react";

import { generateMockChecklist } from "../../mocks/checklistData";
import { fetchChecklist } from "../../shared/api/checklist";
import type { ChecklistResponse } from "../../shared/types/checklist";

interface UseArticleChecklistResult {
  checklist: ChecklistResponse | null;
  loading: boolean;
  error: string | null;
  checkedIds: Set<string>;
  toggleChecked: (id: string) => void;
}

export function useArticleChecklist(ticker: string): UseArticleChecklistResult {
  const [checklist, setChecklist] = useState<ChecklistResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setCheckedIds(new Set());

    fetchChecklist(ticker)
      .then((data) => {
        if (!cancelled) setChecklist(data);
      })
      .catch(() => {
        if (!cancelled) {
          setError("체크리스트를 불러오지 못해 임시 데이터를 표시합니다.");
          setChecklist(generateMockChecklist(ticker));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [ticker]);

  function toggleChecked(id: string) {
    setCheckedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return { checklist, loading, error, checkedIds, toggleChecked };
}
