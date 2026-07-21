import { useEffect, useState } from "react";

import { ChartToolbar, filterPricesByPeriod, type ChartPeriod } from "./features/price-chart/ChartToolbar";
import { ChartTypeToggle, type ChartType } from "./features/price-chart/ChartTypeToggle";
import { PriceChart } from "./features/price-chart/PriceChart";
import { SelectedPointInfo } from "./features/price-chart/SelectedPointInfo";
import { StockHeader } from "./features/price-chart/StockHeader";
import { usePriceChart } from "./features/price-chart/usePriceChart";
import { AIAnalysisPanel } from "./features/movement-explanation/AIAnalysisPanel";
import { useMovementExplanation } from "./features/movement-explanation/useMovementExplanation";
import { MarketEventsPanel } from "./features/market-events/MarketEventsPanel";
import { StockSelector } from "./features/stock-selector/StockSelector";
import { useStocks } from "./features/stock-selector/useStocks";
import { Card } from "./shared/components/Card";
import { LoadingSpinner } from "./shared/components/LoadingSpinner";
import type { LlmProvider } from "./shared/types/explanation";
import type { PricePoint } from "./shared/types/stock";

export default function App() {
  const [ticker, setTicker] = useState("005930");
  const [period, setPeriod] = useState<ChartPeriod>("all");
  const [chartType, setChartType] = useState<ChartType>("candle");
  const [llmProvider, setLlmProvider] = useState<LlmProvider>("solar");
  const [selectedPoint, setSelectedPoint] = useState<PricePoint | null>(null);

  const stocks = useStocks();
  const { prices, loading: pricesLoading, error: pricesError } = usePriceChart(ticker);
  const { status, data, error, explain, reset } = useMovementExplanation();

  useEffect(() => {
    setSelectedPoint(null);
    reset();
  }, [ticker, reset]);

  const visiblePrices = filterPricesByPeriod(prices, period);

  function handleSelectTicker(nextTicker: string) {
    setTicker(nextTicker);
  }

  function handleSelectPoint(point: PricePoint) {
    setSelectedPoint(point);
    void explain(ticker, point.time, "1d", llmProvider);
  }

  function handleRetry() {
    if (selectedPoint) void explain(ticker, selectedPoint.time, "1d", llmProvider);
  }

  function handleChangeProvider(provider: LlmProvider) {
    setLlmProvider(provider);
    if (selectedPoint) void explain(ticker, selectedPoint.time, "1d", provider);
  }

  return (
    <div className="page">
      <header className="app-topbar">
        <span className="app-topbar__logo">Stock Lens</span>
        <span className="app-topbar__tagline">차트에서 날짜를 선택하면 주가 변동 요인을 분석합니다</span>
      </header>

      <section className="stock-summary">
        <StockSelector stocks={stocks} selectedTicker={ticker} onSelect={handleSelectTicker} />
        <StockHeader stocks={stocks} ticker={ticker} prices={prices} />
      </section>

      <div className="workspace">
        <div className="workspace__main">
          <Card
            className="chart-card"
            title={
              <span className="chart-card__title-row">
                주가 차트
                <ChartTypeToggle chartType={chartType} onChange={setChartType} />
              </span>
            }
            actions={<ChartToolbar period={period} onChangePeriod={setPeriod} />}
          >
            {pricesError && <div className="error-banner">{pricesError}</div>}
            {pricesLoading ? (
              <LoadingSpinner label="가격 데이터를 불러오는 중입니다..." />
            ) : (
              <>
                <PriceChart
                  prices={visiblePrices}
                  selectedTime={selectedPoint?.time ?? null}
                  chartType={chartType}
                  onSelectPoint={handleSelectPoint}
                />
                <SelectedPointInfo point={selectedPoint} />
              </>
            )}
          </Card>

          <MarketEventsPanel
            prices={visiblePrices}
            selectedPoint={selectedPoint}
            status={status}
            data={data}
            error={error}
            onSelectPoint={handleSelectPoint}
            onRetry={handleRetry}
          />
        </div>

        <div className="workspace__side">
          <AIAnalysisPanel
            status={status}
            data={data}
            error={error}
            ticker={ticker}
            selectedDate={selectedPoint?.time ?? null}
            llmProvider={llmProvider}
            onChangeProvider={handleChangeProvider}
            onRetry={handleRetry}
          />
        </div>
      </div>
    </div>
  );
}
