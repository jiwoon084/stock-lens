import { useEffect, useState } from "react";

import { MOCK_STOCKS } from "../../mocks/stockData";
import { fetchStocks } from "../../shared/api/stocks";
import type { Stock } from "../../shared/types/stock";

interface StockSelectorProps {
  selectedTicker: string;
  onSelect: (ticker: string) => void;
}

export function StockSelector({ selectedTicker, onSelect }: StockSelectorProps) {
  const [stocks, setStocks] = useState<Stock[]>(MOCK_STOCKS);

  useEffect(() => {
    fetchStocks()
      .then(setStocks)
      .catch(() => setStocks(MOCK_STOCKS));
  }, []);

  return (
    <div className="stock-selector">
      {stocks.map((stock) => (
        <button
          key={stock.ticker}
          type="button"
          className={`stock-selector__button ${
            stock.ticker === selectedTicker ? "stock-selector__button--active" : ""
          }`.trim()}
          onClick={() => onSelect(stock.ticker)}
        >
          {stock.name}
        </button>
      ))}
    </div>
  );
}
