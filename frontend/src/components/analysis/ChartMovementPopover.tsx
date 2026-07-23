import { useEffect, useState, type CSSProperties } from "react";

import { MovementSection } from "./MovementSection";
import type { StockAnalysisStatus } from "./useStockAnalysis";
import type { ChartCoordinate } from "../../features/price-chart/PriceChart";
import type { MovementItem } from "../../types/stockAnalysis";

interface ChartMovementPopoverProps {
  status: StockAnalysisStatus;
  items: MovementItem[];
  error: string | null;
  coordinate: ChartCoordinate | null;
  containerWidth: number;
  resetKey: string;
  changePercent: number | null;
  intradayNotice: string | null;
}

function movementTitle(changePercent: number | null): string {
  if (!changePercent) return "이날 왜 움직였나요?";
  return changePercent > 0 ? "이날 왜 올라갔나요?" : "이날 왜 내려갔나요?";
}

export function ChartMovementPopover({
  status,
  items,
  error,
  coordinate,
  containerWidth,
  resetKey,
  changePercent,
  intradayNotice,
}: ChartMovementPopoverProps) {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setDismissed(false);
  }, [resetKey]);

  if (dismissed || !coordinate || status === "idle") {
    return null;
  }

  const anchorFromRight = containerWidth > 0 && coordinate.x > containerWidth / 2;
  const style: CSSProperties = {
    top: Math.max(8, coordinate.y - 24),
    ...(anchorFromRight
      ? { right: Math.max(8, containerWidth - coordinate.x + 12) }
      : { left: coordinate.x + 12 }),
  };

  return (
    <div className="chart-movement-popover" style={style}>
      <button
        type="button"
        className="chart-movement-popover__close"
        onClick={() => setDismissed(true)}
        aria-label="닫기"
      >
        ✕
      </button>

      {status === "loading" && (
        <div className="report-skeleton" role="status" aria-label="분석 중">
          <div className="report-skeleton__line report-skeleton__line--wide" />
          <div className="report-skeleton__line report-skeleton__line--short" />
        </div>
      )}

      {status === "error" && <p className="empty-state">{error ?? "분석 요청이 실패했습니다."}</p>}

      {status === "success" && (
        <MovementSection title={movementTitle(changePercent)} items={items} intradayNotice={intradayNotice} />
      )}
    </div>
  );
}
