import { createChart, type IChartApi, type ISeriesApi } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { PricePoint } from "../../shared/types/stock";

interface PriceChartProps {
  prices: PricePoint[];
  selectedTime: string | null;
  onSelectPoint: (point: PricePoint) => void;
}

export function PriceChart({ prices, selectedTime, onSelectPoint }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const pricesRef = useRef<PricePoint[]>(prices);

  useEffect(() => {
    pricesRef.current = prices;
  }, [prices]);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: { background: { color: "transparent" }, textColor: "#4b5563" },
      grid: {
        vertLines: { color: "#eef0f3" },
        horzLines: { color: "#eef0f3" },
      },
      timeScale: { borderColor: "#e5e7eb" },
      rightPriceScale: { borderColor: "#e5e7eb" },
      autoSize: true,
    });

    const series = chart.addCandlestickSeries({
      upColor: "#d92b2b",
      downColor: "#1c64f2",
      borderVisible: false,
      wickUpColor: "#d92b2b",
      wickDownColor: "#1c64f2",
    });

    chart.subscribeClick((param) => {
      if (!param.time) return;
      const point = pricesRef.current.find((p) => p.time === param.time);
      if (!point) return;
      onSelectPoint(point);
    });

    chartRef.current = chart;
    seriesRef.current = series;

    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    seriesRef.current.setData(
      prices.map((point) => ({
        time: point.time,
        open: point.open,
        high: point.high,
        low: point.low,
        close: point.close,
      })),
    );
    chartRef.current?.timeScale().fitContent();
  }, [prices]);

  useEffect(() => {
    if (!seriesRef.current) return;
    seriesRef.current.setMarkers(
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
  }, [selectedTime]);

  return <div className="price-chart__container" ref={containerRef} />;
}
