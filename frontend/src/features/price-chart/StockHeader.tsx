import type { PricePoint, Stock } from "../../shared/types/stock";

interface StockHeaderProps {
  stocks: Stock[];
  ticker: string;
  prices: PricePoint[];
}

export function StockHeader({ stocks, ticker, prices }: StockHeaderProps) {
  const stock = stocks.find((s) => s.ticker === ticker);
  const latest = prices[prices.length - 1];
  const prev = prices[prices.length - 2];

  if (!latest) {
    return <p className="empty-state">가격 정보를 불러오는 중입니다...</p>;
  }

  const diff = prev ? latest.close - prev.close : null;
  const arrow = latest.change_percent > 0 ? "▲" : latest.change_percent < 0 ? "▼" : "-";
  const changeClass =
    latest.change_percent > 0 ? "value--positive" : latest.change_percent < 0 ? "value--negative" : "";

  return (
    <div className="stock-header">
      <div className="stock-header__identity">
        <div className="stock-header__name">{stock?.name ?? ticker}</div>
        <div className="stock-header__code">{ticker}</div>
      </div>
      <div className="stock-header__price">
        <div className="stock-header__close">{latest.close.toLocaleString()}원</div>
        <div className={`stock-header__change ${changeClass}`}>
          {arrow} {diff !== null ? Math.abs(diff).toLocaleString() : ""} ({latest.change_percent > 0 ? "+" : ""}
          {latest.change_percent.toFixed(2)}%)
        </div>
      </div>
    </div>
  );
}
