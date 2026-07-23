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
  onSelectIntradayPoint?: (isoTime: string, price: number) => void;
  onSelectedPointCoordinate?: (coordinate: ChartCoordinate | null) => void;
}

type DailySeries = ISeriesApi<"Candlestick"> | ISeriesApi<"Area">;

const WON_PRICE_FORMAT = { type: "price" as const, precision: 0, minMove: 1 };
const UP_COLOR = "#d92b2b";
const DOWN_COLOR = "#1c64f2";

// lightweight-charts spaces bars uniformly by array index, not by real elapsed time — mixing
// day-granularity history with minute-granularity intraday ticks on one series would make 30
// same-day minute bars occupy as much width as 30 historical days. So "오늘" (isIntradayView) is
// a fully separate, homogeneous-granularity series/time-mode, never blended with the daily one.
function isoToUtcSeconds(iso: string): number {
  return Math.floor(Date.parse(iso) / 1000);
}

// Set once at chart creation and never swapped afterward — `chart.applyOptions({ timeScale:
// { tickMarkFormatter: undefined } })` does NOT actually clear a previously-set formatter (a
// real bug hit during development: switching away from the intraday view left this formatter
// active, which then threw "Invalid time value" trying to parse a daily date string as a
// number on every redraw, freezing the chart). Branching on the value's runtime type instead
// means one stable formatter handles both modes correctly, so there's nothing to swap.
function formatTick(time: Time): string {
  if (typeof time === "number") {
    return new Intl.DateTimeFormat("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Asia/Seoul",
    }).format(new Date(time * 1000));
  }
  if (typeof time === "string") {
    const [, month, day] = time.split("-");
    return `${Number(month)}/${Number(day)}`;
  }
  return `${time.month}/${time.day}`;
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
    upColor: UP_COLOR,
    downColor: DOWN_COLOR,
    borderVisible: false,
    wickUpColor: UP_COLOR,
    wickDownColor: DOWN_COLOR,
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
  // lightweight-charts colors each candle by comparing that bar's own open vs close by default —
  // a different metric from change_percent (close vs the PREVIOUS day's close), which is what
  // drives the "왜 올라갔나요/내려갔나요" headline and every displayed 등락률. The two can
  // disagree (e.g. a gap-up day that drifts down after the open still nets positive vs
  // yesterday), showing a blue/down-colored candle under an "왜 올라갔나요?" headline. Passing
  // an explicit per-point color keyed off change_percent keeps the candle and the headline
  // always driven by the same number.
  (series as ISeriesApi<"Candlestick">).setData(
    prices.map((point) => {
      const color = point.change_percent < 0 ? DOWN_COLOR : UP_COLOR;
      return {
        time: point.time,
        open: point.open,
        high: point.high,
        low: point.low,
        close: point.close,
        color,
        wickColor: color,
        borderColor: color,
      };
    }),
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
  onSelectIntradayPoint,
  onSelectedPointCoordinate,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<DailySeries | ISeriesApi<"Area"> | null>(null);
  const pricesRef = useRef<PricePoint[]>(prices);
  const intradayRef = useRef<IntradayPoint[]>(intradayPrices);
  const selectedTimeRef = useRef<string | null>(selectedTime);
  const onCoordinateRef = useRef(onSelectedPointCoordinate);
  const onSelectIntradayPointRef = useRef(onSelectIntradayPoint);
  const isIntradayViewRef = useRef(isIntradayView);
  // Exact clicked intraday timestamp, for precise popover positioning — `selectedTime` (shared
  // with the daily view) only carries a date, not a minute, so it can't pinpoint a spot on the
  // intraday line by itself.
  const selectedIntradayIsoRef = useRef<string | null>(null);
  // `visiblePrices`/`intradayPrices` are freshly-sliced arrays on every parent render (App.tsx
  // doesn't memoize them), so effects keyed on them re-run far more often than the data actually
  // changes. That's harmless on its own, but emitting a brand-new {x,y} object on every one of
  // those re-runs never lets React bail out of re-rendering (object identity always differs even
  // when the values don't) — which re-triggers the parent, which re-runs this effect again,
  // looping forever. Comparing by value before calling the callback breaks the cascade.
  const lastCoordinateRef = useRef<ChartCoordinate | null>(null);

  function emitCoordinate(next: ChartCoordinate | null) {
    const prev = lastCoordinateRef.current;
    const unchanged = prev === next || (prev !== null && next !== null && prev.x === next.x && prev.y === next.y);
    if (unchanged) return;
    lastCoordinateRef.current = next;
    onCoordinateRef.current?.(next);
  }

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
    onSelectIntradayPointRef.current = onSelectIntradayPoint;
  }, [onSelectIntradayPoint]);

  useEffect(() => {
    isIntradayViewRef.current = isIntradayView;
  }, [isIntradayView]);

  function updateSelectedPointCoordinate() {
    const chart = chartRef.current;
    const series = seriesRef.current;
    if (!chart || !series) {
      emitCoordinate(null);
      return;
    }

    if (isIntradayViewRef.current) {
      const iso = selectedIntradayIsoRef.current;
      const target = iso ? intradayRef.current.find((p) => p.time === iso) : undefined;
      if (!target) {
        emitCoordinate(null);
        return;
      }
      const x = chart.timeScale().timeToCoordinate(isoToUtcSeconds(target.time) as Time);
      const y = series.priceToCoordinate(target.price);
      emitCoordinate(x === null || y === null ? null : { x, y });
      return;
    }

    const time = selectedTimeRef.current;
    const point = time ? pricesRef.current.find((p) => p.time === time) : undefined;
    if (!point) {
      emitCoordinate(null);
      return;
    }
    const x = chart.timeScale().timeToCoordinate(point.time as Time);
    const y = series.priceToCoordinate(point.close);
    emitCoordinate(x === null || y === null ? null : { x, y });
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
      timeScale: { borderColor: "#e5e7eb", tickMarkFormatter: formatTick },
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
      if (!param.time) return;

      if (isIntradayViewRef.current) {
        const clicked = intradayRef.current.find((p) => isoToUtcSeconds(p.time) === param.time);
        if (!clicked) return;
        selectedIntradayIsoRef.current = clicked.time;
        onSelectIntradayPointRef.current?.(clicked.time, clicked.price);
        updateSelectedPointCoordinate();
        return;
      }

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
    selectedIntradayIsoRef.current = null;

    if (isIntradayView) {
      const series = createIntradaySeries(chart);
      seriesRef.current = series;
      applyIntradayData(series, intradayRef.current);
    } else {
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
