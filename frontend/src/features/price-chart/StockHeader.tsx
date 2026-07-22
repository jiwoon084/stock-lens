import type { PricePoint, Stock } from "../../shared/types/stock";
import { useLivePrice } from "./useLivePrice";

interface StockHeaderProps {
  stocks: Stock[];
  ticker: string;
  prices: PricePoint[];
}

export function StockHeader({ stocks, ticker, prices }: StockHeaderProps) {
  const stock = stocks.find((s) => s.ticker === ticker);
  const latest = prices[prices.length - 1];
  const prev = prices[prices.length - 2];
  const { live, asOf } = useLivePrice(ticker);

  if (!latest) {
    return <p className="empty-state">가격 정보를 불러오는 중입니다...</p>;
  }

  const close = live?.price ?? latest.close;
  const changePercent = live?.change_percent ?? latest.change_percent;
  const diff = live ? live.change : prev ? latest.close - prev.close : null;
  const arrow = changePercent > 0 ? "▲" : changePercent < 0 ? "▼" : "-";
  const changeClass = changePercent > 0 ? "value--positive" : changePercent < 0 ? "value--negative" : "";

  return (
    <div className="stock-header">
      <div className="stock-header__identity">
        <div className="stock-header__name-row">
          <span className="stock-header__name">{stock?.name ?? ticker}</span>
          {stock?.market && <span className="stock-header__market">{stock.market}</span>}
        </div>
        <div className="stock-header__code">{ticker}</div>
      </div>

      <div className="stock-header__price">
        <div className="stock-header__close-row">
          <span className="stock-header__close">{close.toLocaleString()}원</span>
          {live && <span className="stock-header__live-badge">실시간</span>}
        </div>
        <div className={`stock-header__change ${changeClass}`}>
          {arrow} {diff !== null ? Math.abs(diff).toLocaleString() : ""} ({changePercent > 0 ? "+" : ""}
          {changePercent.toFixed(2)}%)
        </div>
        <div className="stock-header__updated">
          {live && asOf
            ? `${new Date(asOf).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })} 기준`
            : `업데이트 기준 ${latest.time}`}
        </div>
      </div>
    </div>
  );
}
