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
  priceChangeText: string | null;
  intradayNotice: string | null;
}

// Derived from the analysis response's own chart_card.price_change_text, NOT from
// selectedPoint.change_percent — for "오늘" that number comes from the frontend's independent
// useLivePrice poll, a different snapshot in time than whatever live quote the backend fetched
// when it built these same factors. Two separately-polled reads of a number that's still moving
// will occasionally disagree in sign; reading the direction back out of the same response that
// produced the factors guarantees the headline and the content always agree.
function movementTitle(priceChangeText: string | null): string {
  if (!priceChangeText) return "이날 왜 움직였나요?";
  if (priceChangeText.startsWith("-")) return "이날 왜 내려갔나요?";
  if (priceChangeText.startsWith("+")) return "이날 왜 올라갔나요?";
  return "이날 왜 움직였나요?";
}

export function ChartMovementPopover({
  status,
  items,
  error,
  coordinate,
  containerWidth,
  resetKey,
  priceChangeText,
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
        <MovementSection title={movementTitle(priceChangeText)} items={items} intradayNotice={intradayNotice} />
      )}
    </div>
  );
}
