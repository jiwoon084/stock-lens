import { useEffect, useState } from "react";

import { ChartToolbar, filterPricesByPeriod, type ChartPeriod } from "./features/price-chart/ChartToolbar";
import { PriceChart } from "./features/price-chart/PriceChart";
import { SelectedPoint } from "./features/price-chart/SelectedPoint";
import { usePriceChart } from "./features/price-chart/usePriceChart";
import { ExplanationPanel } from "./features/movement-explanation/ExplanationPanel";
import { useMovementExplanation } from "./features/movement-explanation/useMovementExplanation";
import { StockSelector } from "./features/stock-selector/StockSelector";
import { Card } from "./shared/components/Card";
import type { PricePoint } from "./shared/types/stock";

export default function App() {
  const [ticker, setTicker] = useState("005930");
  const [period, setPeriod] = useState<ChartPeriod>("all");
  const [selectedPoint, setSelectedPoint] = useState<PricePoint | null>(null);

  const { prices, loading: pricesLoading, error: pricesError } = usePriceChart(ticker);
  const { status, data, error, explain } = useMovementExplanation();

  useEffect(() => {
    setSelectedPoint(null);
  }, [ticker]);

  const visiblePrices = filterPricesByPeriod(prices, period);

  function handleSelectTicker(nextTicker: string) {
    setTicker(nextTicker);
  }

  function handleSelectPoint(point: PricePoint) {
    setSelectedPoint(point);
    void explain(ticker, point.time, "1d");
  }

  return (
    <>
      <header className="app-header">
        <h1>Stock Lens</h1>
        <p>차트에서 날짜를 선택하면 주가 변동 요인을 분석합니다.</p>
      </header>

      <Card title="종목 선택">
        <StockSelector selectedTicker={ticker} onSelect={handleSelectTicker} />
      </Card>

      <Card title="주가 차트">
        <ChartToolbar period={period} onChangePeriod={setPeriod} />
        {pricesError && <div className="error-banner">{pricesError}</div>}
        {pricesLoading ? (
          <p className="empty-state">가격 데이터를 불러오는 중입니다...</p>
        ) : (
          <PriceChart
            prices={visiblePrices}
            selectedTime={selectedPoint?.time ?? null}
            onSelectPoint={handleSelectPoint}
          />
        )}
      </Card>

      <Card title="선택한 날짜 정보">
        <SelectedPoint point={selectedPoint} />
      </Card>

      <Card title="AI 분석">
        <ExplanationPanel status={status} data={data} error={error} />
      </Card>
    </>
  );
}
