import { createChart, type IChartApi, type ISeriesApi } from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { PricePoint } from "../../shared/types/stock";

export interface ChartPointPosition {
  x: number;
  y: number;
}

interface PriceChartProps {
  prices: PricePoint[];
  selectedTime: string | null;
  onSelectPoint: (point: PricePoint, position: ChartPointPosition) => void;
}

export function PriceChart({ prices, selectedTime, onSelectPoint }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const pricesRef = useRef<PricePoint[]>(prices);
  const onSelectPointRef = useRef(onSelectPoint);

  useEffect(() => {
    pricesRef.current = prices;
  }, [prices]);

  useEffect(() => {
    onSelectPointRef.current = onSelectPoint;
  }, [onSelectPoint]);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: { background: { color: "transparent" }, textColor: "#5b6472" },
      grid: {
        vertLines: { color: "#eef0f3" },
        horzLines: { color: "#eef0f3" },
      },
      timeScale: { borderColor: "#e5e8ec" },
      rightPriceScale: { borderColor: "#e5e8ec" },
      autoSize: true,
      // 마우스 휠로 페이지를 스크롤하다 차트 위에서 의도치 않게 확대/축소·이동되는 것을 방지 —
      // 기간 탭(1주/2주/1개월/전체)으로만 범위를 바꾸도록 고정.
      handleScroll: false,
      handleScale: false,
    });

    const series = chart.addAreaSeries({
      lineColor: "#1f2937",
      lineWidth: 2,
      topColor: "rgba(15, 118, 110, 0.16)",
      bottomColor: "rgba(15, 118, 110, 0.01)",
    });

    chart.subscribeClick((param) => {
      if (!param.time || !param.point) return;
      const point = pricesRef.current.find((p) => p.time === param.time);
      if (point) onSelectPointRef.current(point, { x: param.point.x, y: param.point.y });
    });

    chartRef.current = chart;
    seriesRef.current = series;

    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!seriesRef.current) return;
    seriesRef.current.setData(
      prices.map((point) => ({
        time: point.time,
        value: point.close,
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
              position: "inBar",
              color: "#0f766e",
              shape: "circle",
            },
          ]
        : [],
    );
  }, [selectedTime]);

  return <div className="price-chart__container" ref={containerRef} />;
}
