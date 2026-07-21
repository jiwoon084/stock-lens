import { useEffect, useState } from "react";

import { MOCK_STOCKS } from "../../mocks/stockData";
import { fetchStocks } from "../../shared/api/stocks";
import type { Stock } from "../../shared/types/stock";

export function useStocks(): Stock[] {
  const [stocks, setStocks] = useState<Stock[]>(MOCK_STOCKS);

  useEffect(() => {
    fetchStocks()
      .then(setStocks)
      .catch(() => setStocks(MOCK_STOCKS));
  }, []);

  return stocks;
}
