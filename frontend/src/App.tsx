import { useCallback, useEffect, useRef, useState } from "react";

import { ChartToolbar, filterPricesByPeriod, type ChartPeriod } from "./features/price-chart/ChartToolbar";
import { ChartTypeToggle, type ChartType } from "./features/price-chart/ChartTypeToggle";
import { PriceChart, type ChartCoordinate } from "./features/price-chart/PriceChart";
import { SelectedPointInfo } from "./features/price-chart/SelectedPointInfo";
import { StockHeader } from "./features/price-chart/StockHeader";
import { useIntradayPrices } from "./features/price-chart/useIntradayPrices";
import { usePriceChart } from "./features/price-chart/usePriceChart";
import { useMovementExplanation } from "./features/movement-explanation/useMovementExplanation";
import { MarketEventsPanel } from "./features/market-events/MarketEventsPanel";
import { StockSelector } from "./features/stock-selector/StockSelector";
import { useStocks } from "./features/stock-selector/useStocks";
import { ChartSummaryCard } from "./components/analysis/ChartSummaryCard";
import { ChartMovementPopover } from "./components/analysis/ChartMovementPopover";
import { AnalysisDetailPanel } from "./components/analysis/AnalysisDetailPanel";
import { useStockAnalysis } from "./components/analysis/useStockAnalysis";
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
  const [pointCoordinate, setPointCoordinate] = useState<ChartCoordinate | null>(null);
  const [chartWidth, setChartWidth] = useState(0);
  const chartWrapperResizeObserverRef = useRef<ResizeObserver | null>(null);

  // A plain ref + a mount-only effect would miss this node — it doesn't exist yet while
  // pricesLoading is true, so it only appears after the initial render. A callback ref fires
  // whenever the node is actually attached/detached, which is what re-observing needs here.
  const chartWrapperRef = useCallback((node: HTMLDivElement | null) => {
    chartWrapperResizeObserverRef.current?.disconnect();
    chartWrapperResizeObserverRef.current = null;
    if (!node) return;

    setChartWidth(node.getBoundingClientRect().width);
    const observer = new ResizeObserver(([entry]) => setChartWidth(entry.contentRect.width));
    observer.observe(node);
    chartWrapperResizeObserverRef.current = observer;
  }, []);

  const stocks = useStocks();
  const { prices, loading: pricesLoading, error: pricesError } = usePriceChart(ticker);
  const intradayPrices = useIntradayPrices(ticker);
  const { status, data, error, explain, reset } = useMovementExplanation();
  const {
    status: analysisStatus,
    data: analysisData,
    error: analysisError,
    analyze,
    reset: resetAnalysis,
  } = useStockAnalysis();

  useEffect(() => {
    setSelectedPoint(null);
    reset();
    resetAnalysis();
  }, [ticker, reset, resetAnalysis]);

  const visiblePrices = filterPricesByPeriod(prices, period);
  const isIntradayView = period === "today";

  function handleSelectTicker(nextTicker: string) {
    setTicker(nextTicker);
  }

  function handleSelectPoint(point: PricePoint) {
    setSelectedPoint(point);
    void explain(ticker, point.time, "1d", llmProvider);
    void analyze(ticker, point.time);
  }

  function handleRetry() {
    if (selectedPoint) void explain(ticker, selectedPoint.time, "1d", llmProvider);
  }

  function handleRetryAnalysis() {
    if (selectedPoint) void analyze(ticker, selectedPoint.time);
  }

  function handleChangeProvider(provider: LlmProvider) {
    setLlmProvider(provider);
    if (selectedPoint) void explain(ticker, selectedPoint.time, "1d", provider);
  }

  function handleSelectPrimaryEvidence(sourceId: string) {
    document.getElementById(`source-${sourceId}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
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
                <div className="price-chart__wrapper" ref={chartWrapperRef}>
                  <PriceChart
                    prices={visiblePrices}
                    intradayPrices={intradayPrices}
                    isIntradayView={isIntradayView}
                    selectedTime={selectedPoint?.time ?? null}
                    chartType={chartType}
                    onSelectPoint={handleSelectPoint}
                    onSelectedPointCoordinate={setPointCoordinate}
                  />
                  <ChartMovementPopover
                    status={analysisStatus}
                    items={analysisData?.analysis.detail_panel.why_it_moved ?? []}
                    error={analysisError}
                    coordinate={pointCoordinate}
                    containerWidth={chartWidth}
                    resetKey={selectedPoint?.time ?? ""}
                  />
                </div>
                <SelectedPointInfo point={selectedPoint} />
                <ChartSummaryCard
                  status={analysisStatus}
                  chartCard={analysisData?.analysis.chart_card ?? null}
                  error={analysisError}
                  sources={analysisData?.sources ?? {}}
                  onSelectPrimaryEvidence={handleSelectPrimaryEvidence}
                />
              </>
            )}
          </Card>

          <MarketEventsPanel
            prices={visiblePrices}
            selectedPoint={selectedPoint}
            status={status}
            data={data}
            error={error}
            llmProvider={llmProvider}
            onChangeProvider={handleChangeProvider}
            onSelectPoint={handleSelectPoint}
            onRetry={handleRetry}
          />
        </div>

        <div className="workspace__side">
          <AnalysisDetailPanel
            status={analysisStatus}
            data={analysisData}
            error={analysisError}
            ticker={ticker}
            selectedDate={selectedPoint?.time ?? null}
            onRetry={handleRetryAnalysis}
          />
        </div>
      </div>
    </div>
  );
}
