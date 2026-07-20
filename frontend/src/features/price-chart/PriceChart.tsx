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
      layout: { background: { color: "transparent" }, textColor: "#e6e8eb" },
      grid: {
        vertLines: { color: "#2a2e38" },
        horzLines: { color: "#2a2e38" },
      },
      timeScale: { borderColor: "#2a2e38" },
      rightPriceScale: { borderColor: "#2a2e38" },
      autoSize: true,
    });

    const series = chart.addCandlestickSeries({
      upColor: "#ef5350",
      downColor: "#4c8dff",
      borderVisible: false,
      wickUpColor: "#ef5350",
      wickDownColor: "#4c8dff",
    });

    chart.subscribeClick((param) => {
      if (!param.time) return;
      const point = pricesRef.current.find((p) => p.time === param.time);
      if (point) onSelectPoint(point);
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
              color: "#4c8dff",
              shape: "arrowDown",
              text: "선택",
            },
          ]
        : [],
    );
  }, [selectedTime]);

  return <div className="price-chart__container" ref={containerRef} />;
}
