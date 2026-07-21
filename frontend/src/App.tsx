import { useEffect, useRef, useState } from "react";

import { ChartToolbar, filterPricesByPeriod, type ChartPeriod } from "./features/price-chart/ChartToolbar";
import { PriceChart, type ChartPointPosition } from "./features/price-chart/PriceChart";
import { usePriceChart } from "./features/price-chart/usePriceChart";
import { ReasonTooltip } from "./features/movement-explanation/ReasonTooltip";
import { useMovementExplanation } from "./features/movement-explanation/useMovementExplanation";
import { StockSelector } from "./features/stock-selector/StockSelector";
import { ArticleChecklist } from "./features/article-checklist/ArticleChecklist";
import { Card } from "./shared/components/Card";
import { MOCK_STOCKS } from "./mocks/stockData";
import type { PricePoint } from "./shared/types/stock";

const TOOLTIP_WIDTH = 290;

function changeClass(value: number): string {
  if (value > 0) return "value--positive";
  if (value < 0) return "value--negative";
  return "";
}

export default function App() {
  const [ticker, setTicker] = useState("005930");
  const [period, setPeriod] = useState<ChartPeriod>("all");
  const [selectedPoint, setSelectedPoint] = useState<PricePoint | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<ChartPointPosition | null>(null);
  const chartWrapperRef = useRef<HTMLDivElement>(null);

  const { prices, loading: pricesLoading, error: pricesError } = usePriceChart(ticker);
  const { status, data, error, explain } = useMovementExplanation();

  useEffect(() => {
    setSelectedPoint(null);
    setTooltipPosition(null);
  }, [ticker]);

  const visiblePrices = filterPricesByPeriod(prices, period);
  const latestPoint = prices[prices.length - 1] ?? null;
  const stockName = MOCK_STOCKS.find((stock) => stock.ticker === ticker)?.name ?? ticker;

  function handleSelectTicker(nextTicker: string) {
    setTicker(nextTicker);
  }

  function handleSelectPoint(point: PricePoint, position: ChartPointPosition) {
    setSelectedPoint(point);
    void explain(ticker, point.time, "1d");

    const wrapper = chartWrapperRef.current;
    const maxX = wrapper ? wrapper.clientWidth - TOOLTIP_WIDTH - 8 : position.x;
    const maxY = wrapper ? wrapper.clientHeight - 160 : position.y;
    setTooltipPosition({
      x: Math.max(8, Math.min(position.x + 16, maxX)),
      y: Math.max(8, Math.min(position.y - 32, maxY)),
    });
  }

  function handleCloseTooltip() {
    setSelectedPoint(null);
    setTooltipPosition(null);
  }

  return (
    <>
      <header className="app-header">
        <div>
          <h1>Stock Lens</h1>
          <p>차트에서 급등락 지점을 클릭하면 원인 후보를, 오른쪽에서 오늘의 기사 핵심을 확인하세요.</p>
        </div>
        <StockSelector selectedTicker={ticker} onSelect={handleSelectTicker} />
      </header>

      <div className="stock-quote">
        <span className="stock-quote__name">{stockName}</span>
        <span className="stock-quote__ticker">{ticker}</span>
        {latestPoint && (
          <>
            <span className="stock-quote__price">{latestPoint.close.toLocaleString()}원</span>
            <span className={`stock-quote__change ${changeClass(latestPoint.change_percent)}`}>
              {latestPoint.change_percent > 0 ? "▲" : latestPoint.change_percent < 0 ? "▼" : ""}{" "}
              {Math.abs(latestPoint.change_percent).toFixed(2)}%
            </span>
          </>
        )}
      </div>

      <div className="detail-grid">
        <Card title="주가 차트" className="detail-grid__chart">
          <ChartToolbar period={period} onChangePeriod={setPeriod} />
          {pricesError && <div className="error-banner">{pricesError}</div>}
          {pricesLoading ? (
            <p className="empty-state">가격 데이터를 불러오는 중입니다...</p>
          ) : (
            <>
              <p className="empty-state">급등·급락 지점을 누르면 원인 후보를 보여줘요</p>
              <div className="price-chart__wrapper" ref={chartWrapperRef}>
                <PriceChart
                  prices={visiblePrices}
                  selectedTime={selectedPoint?.time ?? null}
                  onSelectPoint={handleSelectPoint}
                />
                {tooltipPosition && (
                  <ReasonTooltip
                    status={status}
                    data={data}
                    error={error}
                    style={{ left: tooltipPosition.x, top: tooltipPosition.y }}
                    onClose={handleCloseTooltip}
                  />
                )}
              </div>
            </>
          )}
        </Card>

        <Card title="오늘의 체크리스트" className="detail-grid__checklist">
          <ArticleChecklist ticker={ticker} />
        </Card>
      </div>
    </>
  );
}
