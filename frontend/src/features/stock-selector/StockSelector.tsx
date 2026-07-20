import type { Stock } from "../../shared/types/stock";

interface StockSelectorProps {
  stocks: Stock[];
  selectedTicker: string;
  onSelect: (ticker: string) => void;
}

export function StockSelector({ stocks, selectedTicker, onSelect }: StockSelectorProps) {
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
