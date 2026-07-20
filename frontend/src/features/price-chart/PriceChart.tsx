import { createChart, type IChartApi, type ISeriesApi } from "lightweight-charts";
import { useEffect, useRef, useState } from "react";

import type { ExplanationStatus } from "../movement-explanation/useMovementExplanation";
import type { MovementExplanationResponse } from "../../shared/types/explanation";
import type { PricePoint } from "../../shared/types/stock";

interface PriceChartProps {
  prices: PricePoint[];
  selectedTime: string | null;
  onSelectPoint: (point: PricePoint) => void;
  explanationStatus: ExplanationStatus;
  explanationData: MovementExplanationResponse | null;
  explanationError: string | null;
}

interface Anchor {
  x: number;
  y: number;
  flipX: boolean;
  flipY: boolean;
}

export function PriceChart({
  prices,
  selectedTime,
  onSelectPoint,
  explanationStatus,
  explanationData,
  explanationError,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const pricesRef = useRef<PricePoint[]>(prices);
  const [anchor, setAnchor] = useState<Anchor | null>(null);

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
      if (!param.time || !param.point) return;
      const point = pricesRef.current.find((p) => p.time === param.time);
      if (!point) return;

      const width = containerRef.current?.clientWidth ?? 0;
      const height = containerRef.current?.clientHeight ?? 0;
      setAnchor({
        x: param.point.x,
        y: param.point.y,
        flipX: param.point.x > width / 2,
        flipY: param.point.y > height / 2,
      });
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
    setAnchor(null);
  }, [prices]);

  useEffect(() => {
    const handleResize = () => setAnchor(null);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

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

  return (
    <div className="price-chart__wrapper">
      <div className="price-chart__container" ref={containerRef} />
      {anchor && (
        <div
          className={`price-chart__popover ${anchor.flipX ? "price-chart__popover--flip-x" : ""} ${
            anchor.flipY ? "price-chart__popover--flip-y" : ""
          }`.trim()}
          style={{ left: anchor.x, top: anchor.y }}
        >
          {explanationStatus === "loading" && (
            <p className="price-chart__popover-loading">원인 분석 중...</p>
          )}
          {explanationStatus === "error" && (
            <p className="price-chart__popover-loading">{explanationError ?? "분석 실패"}</p>
          )}
          {explanationStatus === "success" && explanationData && (
            <>
              <p className="price-chart__popover-title">이날 왜 올랐을까? — 원인 후보</p>
              <ol className="price-chart__popover-list">
                {explanationData.factors.map((factor) => {
                  const source = explanationData.sources.find((s) => s.id === factor.source_ids[0]);
                  return (
                    <li key={factor.title}>
                      {factor.title}
                      {source ? ` — 근거: ${source.publisher}` : ""}
                    </li>
                  );
                })}
              </ol>
            </>
          )}
        </div>
      )}
    </div>
  );
}
