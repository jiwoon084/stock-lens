import { useEffect, useState } from "react";

import { generateMockPrices } from "../../mocks/stockData";
import { fetchStockPrices } from "../../shared/api/stocks";
import type { PricePoint } from "../../shared/types/stock";

interface UsePriceChartResult {
  prices: PricePoint[];
  loading: boolean;
  error: string | null;
}

export function usePriceChart(ticker: string): UsePriceChartResult {
  const [prices, setPrices] = useState<PricePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchStockPrices(ticker)
      .then((data) => {
        if (!cancelled) setPrices(data);
      })
      .catch(() => {
        if (!cancelled) {
          setError("가격 데이터를 불러오지 못해 임시 데이터를 표시합니다.");
          setPrices(generateMockPrices(ticker));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [ticker]);

  return { prices, loading, error };
}
