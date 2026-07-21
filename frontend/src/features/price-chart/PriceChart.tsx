import { createChart, type IChartApi, type ISeriesApi } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { PricePoint } from "../../shared/types/stock";
import type { ChartType } from "./ChartTypeToggle";

interface PriceChartProps {
  prices: PricePoint[];
  selectedTime: string | null;
  chartType: ChartType;
  onSelectPoint: (point: PricePoint) => void;
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

export function PriceChart({ prices, selectedTime, chartType, onSelectPoint }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<PriceSeries | null>(null);
  const pricesRef = useRef<PricePoint[]>(prices);

  useEffect(() => {
    pricesRef.current = prices;
  }, [prices]);

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
    });

    chart.subscribeClick((param) => {
      if (!param.time) return;
      const point = pricesRef.current.find((p) => p.time === param.time);
      if (!point) return;
      onSelectPoint(point);
    });

    chartRef.current = chart;

    return () => {
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chartType]);

  useEffect(() => {
    if (!seriesRef.current) return;
    applyData(seriesRef.current, chartType, prices);
    chartRef.current?.timeScale().fitContent();
  }, [prices, chartType]);

  useEffect(() => {
    if (!seriesRef.current) return;
    applyMarkers(seriesRef.current, selectedTime);
  }, [selectedTime]);

  return <div className="price-chart__container" ref={containerRef} />;
}
