import { createChart, type IChartApi, type ISeriesApi, type Time } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { PricePoint } from "../../shared/types/stock";
import type { ChartType } from "./ChartTypeToggle";

export interface ChartCoordinate {
  x: number;
  y: number;
}

interface PriceChartProps {
  prices: PricePoint[];
  selectedTime: string | null;
  chartType: ChartType;
  onSelectPoint: (point: PricePoint) => void;
  onSelectedPointCoordinate?: (coordinate: ChartCoordinate | null) => void;
}

type PriceSeries = ISeriesApi<"Candlestick"> | ISeriesApi<"Area">;

const WON_PRICE_FORMAT = { type: "price" as const, precision: 0, minMove: 1 };

function createSeries(chart: IChartApi, chartType: ChartType): PriceSeries {
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

function applyData(series: PriceSeries, chartType: ChartType, prices: PricePoint[]) {
  if (chartType === "line") {
    (series as ISeriesApi<"Area">).setData(
      prices.map((point) => ({ time: point.time, value: point.close })),
    );
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

function applyMarkers(series: PriceSeries, selectedTime: string | null) {
  series.setMarkers(
    selectedTime
      ? [
          {
            time: selectedTime,
            position: "aboveBar",
            color: "#4f46e5",
            shape: "arrowDown",
            text: "선택",
          },
        ]
      : [],
  );
}

export function PriceChart({
  prices,
  selectedTime,
  chartType,
  onSelectPoint,
  onSelectedPointCoordinate,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<PriceSeries | null>(null);
  const pricesRef = useRef<PricePoint[]>(prices);
  const selectedTimeRef = useRef<string | null>(selectedTime);
  const onCoordinateRef = useRef(onSelectedPointCoordinate);

  useEffect(() => {
    pricesRef.current = prices;
  }, [prices]);

  useEffect(() => {
    selectedTimeRef.current = selectedTime;
  }, [selectedTime]);

  useEffect(() => {
    onCoordinateRef.current = onSelectedPointCoordinate;
  }, [onSelectedPointCoordinate]);

  function updateSelectedPointCoordinate() {
    const chart = chartRef.current;
    const series = seriesRef.current;
    const time = selectedTimeRef.current;
    const point = time ? pricesRef.current.find((p) => p.time === time) : undefined;

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
      // 기간 탭(1주/2주/1개월/전체)으로만 범위를 바꾸도록 고정.
      handleScroll: false,
      handleScale: false,
    });

    chart.subscribeClick((param) => {
      if (!param.time) return;
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

  // Swap the series whenever the chosen chart type changes (lightweight-charts has no
  // "change series type in place" API — remove and re-add, then replay data/markers/selection).
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    if (seriesRef.current) {
      chart.removeSeries(seriesRef.current);
    }
    const series = createSeries(chart, chartType);
    seriesRef.current = series;

    applyData(series, chartType, pricesRef.current);
    applyMarkers(series, selectedTime);
    chart.timeScale().fitContent();
    updateSelectedPointCoordinate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartType]);

  useEffect(() => {
    if (!seriesRef.current) return;
    applyData(seriesRef.current, chartType, prices);
    chartRef.current?.timeScale().fitContent();
    updateSelectedPointCoordinate();
  }, [prices, chartType]);

  useEffect(() => {
    if (!seriesRef.current) return;
    applyMarkers(seriesRef.current, selectedTime);
    updateSelectedPointCoordinate();
  }, [selectedTime]);

  return <div className="price-chart__container" ref={containerRef} />;
}
