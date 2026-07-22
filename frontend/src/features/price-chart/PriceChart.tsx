import { createChart, type IChartApi, type ISeriesApi, type Time } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { IntradayPoint, PricePoint } from "../../shared/types/stock";
import type { ChartType } from "./ChartTypeToggle";

export interface ChartCoordinate {
  x: number;
  y: number;
}

interface PriceChartProps {
  prices: PricePoint[];
  intradayPrices?: IntradayPoint[];
  isIntradayView?: boolean;
  selectedTime: string | null;
  chartType: ChartType;
  onSelectPoint: (point: PricePoint) => void;
  onSelectedPointCoordinate?: (coordinate: ChartCoordinate | null) => void;
}

type DailySeries = ISeriesApi<"Candlestick"> | ISeriesApi<"Area">;

const WON_PRICE_FORMAT = { type: "price" as const, precision: 0, minMove: 1 };

// lightweight-charts spaces bars uniformly by array index, not by real elapsed time — mixing
// day-granularity history with minute-granularity intraday ticks on one series would make 30
// same-day minute bars occupy as much width as 30 historical days. So "오늘" (isIntradayView) is
// a fully separate, homogeneous-granularity series/time-mode, never blended with the daily one.
function isoToUtcSeconds(iso: string): number {
  return Math.floor(Date.parse(iso) / 1000);
}

function formatIntradayTick(time: Time): string {
  return new Intl.DateTimeFormat("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Seoul",
  }).format(new Date((time as number) * 1000));
}

function createDailySeries(chart: IChartApi, chartType: ChartType): DailySeries {
  if (chartType === "line") {
    return chart.addAreaSeries({
      lineColor: "#4f46e5",
      lineWidth: 2,
      topColor: "rgba(79, 70, 229, 0.16)",
      bottomColor: "rgba(79, 70, 229, 0.01)",
      priceLineVisible: false,
      priceFormat: WON_PRICE_FORMAT,
    });
  }
  return chart.addCandlestickSeries({
    upColor: "#d92b2b",
    downColor: "#1c64f2",
    borderVisible: false,
    wickUpColor: "#d92b2b",
    wickDownColor: "#1c64f2",
    priceLineVisible: false,
    priceFormat: WON_PRICE_FORMAT,
  });
}

function createIntradaySeries(chart: IChartApi): ISeriesApi<"Area"> {
  return chart.addAreaSeries({
    lineColor: "#16a34a",
    lineWidth: 2,
    topColor: "rgba(22, 163, 74, 0.16)",
    bottomColor: "rgba(22, 163, 74, 0.01)",
    priceLineVisible: false,
    priceFormat: WON_PRICE_FORMAT,
  });
}

function applyDailyData(series: DailySeries, chartType: ChartType, prices: PricePoint[]) {
  if (chartType === "line") {
    (series as ISeriesApi<"Area">).setData(prices.map((point) => ({ time: point.time, value: point.close })));
    return;
  }
  (series as ISeriesApi<"Candlestick">).setData(
    prices.map((point) => ({
      time: point.time,
      open: point.open,
      high: point.high,
      low: point.low,
      close: point.close,
    })),
  );
}

function applyIntradayData(series: ISeriesApi<"Area">, intradayPrices: IntradayPoint[]) {
  series.setData(intradayPrices.map((point) => ({ time: isoToUtcSeconds(point.time) as Time, value: point.price })));
}

function applyMarkers(series: DailySeries, selectedTime: string | null) {
  series.setMarkers(
    selectedTime
      ? [{ time: selectedTime as Time, position: "aboveBar", color: "#4f46e5", shape: "arrowDown", text: "선택" }]
      : [],
  );
}

export function PriceChart({
  prices,
  intradayPrices = [],
  isIntradayView = false,
  selectedTime,
  chartType,
  onSelectPoint,
  onSelectedPointCoordinate,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<DailySeries | ISeriesApi<"Area"> | null>(null);
  const pricesRef = useRef<PricePoint[]>(prices);
  const intradayRef = useRef<IntradayPoint[]>(intradayPrices);
  const selectedTimeRef = useRef<string | null>(selectedTime);
  const onCoordinateRef = useRef(onSelectedPointCoordinate);
  const isIntradayViewRef = useRef(isIntradayView);

  useEffect(() => {
    pricesRef.current = prices;
  }, [prices]);

  useEffect(() => {
    intradayRef.current = intradayPrices;
  }, [intradayPrices]);

  useEffect(() => {
    selectedTimeRef.current = selectedTime;
  }, [selectedTime]);

  useEffect(() => {
    onCoordinateRef.current = onSelectedPointCoordinate;
  }, [onSelectedPointCoordinate]);

  useEffect(() => {
    isIntradayViewRef.current = isIntradayView;
  }, [isIntradayView]);

  function updateSelectedPointCoordinate() {
    const chart = chartRef.current;
    const series = seriesRef.current;
    const time = selectedTimeRef.current;
    const point = !isIntradayViewRef.current && time ? pricesRef.current.find((p) => p.time === time) : undefined;

    if (!chart || !series || !point) {
      onCoordinateRef.current?.(null);
      return;
    }

    const x = chart.timeScale().timeToCoordinate(point.time as Time);
    const y = series.priceToCoordinate(point.close);
    onCoordinateRef.current?.(x === null || y === null ? null : { x, y });
  }

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: { background: { color: "transparent" }, textColor: "#6b7280", fontSize: 12 },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: "#f0f1f4" },
      },
      crosshair: {
        vertLine: { color: "#d1d5db", width: 1, style: 1, labelBackgroundColor: "#4b5563" },
        horzLine: { color: "#d1d5db", width: 1, style: 1, labelBackgroundColor: "#4b5563" },
      },
      timeScale: { borderColor: "#e5e7eb" },
      rightPriceScale: { borderColor: "#e5e7eb" },
      localization: {
        priceFormatter: (price: number) => Math.round(price).toLocaleString("ko-KR"),
      },
      autoSize: true,
      // 마우스 휠로 페이지를 스크롤하다 차트 위에서 의도치 않게 확대/축소·이동되는 것을 방지 —
      // 기간 탭(오늘/1주/2주/1개월/전체)으로만 범위를 바꾸도록 고정.
      handleScroll: false,
      handleScale: false,
    });

    chart.subscribeClick((param) => {
      if (isIntradayViewRef.current || !param.time) return;
      const point = pricesRef.current.find((p) => p.time === param.time);
      if (!point) return;
      onSelectPoint(point);
    });

    chartRef.current = chart;

    const resizeObserver = new ResizeObserver(() => updateSelectedPointCoordinate());
    resizeObserver.observe(containerRef.current);

    const handleVisibleTimeRangeChange = () => updateSelectedPointCoordinate();
    chart.timeScale().subscribeVisibleTimeRangeChange(handleVisibleTimeRangeChange);

    return () => {
      chart.timeScale().unsubscribeVisibleTimeRangeChange(handleVisibleTimeRangeChange);
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Recreate the series whenever chart type or intraday/daily mode changes — lightweight-charts
  // has no "change series type in place" API, and the two modes use different time formats/tick
  // labeling entirely (see the module comment above).
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    if (seriesRef.current) {
      chart.removeSeries(seriesRef.current);
      seriesRef.current = null;
    }

    if (isIntradayView) {
      chart.applyOptions({ timeScale: { tickMarkFormatter: formatIntradayTick } });
      const series = createIntradaySeries(chart);
      seriesRef.current = series;
      applyIntradayData(series, intradayRef.current);
    } else {
      chart.applyOptions({ timeScale: { tickMarkFormatter: undefined } });
      const series = createDailySeries(chart, chartType);
      seriesRef.current = series;
      applyDailyData(series, chartType, pricesRef.current);
      applyMarkers(series, selectedTimeRef.current);
    }

    chart.timeScale().fitContent();
    updateSelectedPointCoordinate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartType, isIntradayView]);

  useEffect(() => {
    if (!seriesRef.current) return;
    if (isIntradayView) {
      applyIntradayData(seriesRef.current as ISeriesApi<"Area">, intradayPrices);
    } else {
      applyDailyData(seriesRef.current as DailySeries, chartType, prices);
    }
    chartRef.current?.timeScale().fitContent();
    updateSelectedPointCoordinate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prices, intradayPrices, chartType, isIntradayView]);

  useEffect(() => {
    if (!seriesRef.current || isIntradayView) return;
    applyMarkers(seriesRef.current as DailySeries, selectedTime);
    updateSelectedPointCoordinate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTime]);

  return <div className="price-chart__container" ref={containerRef} />;
}
