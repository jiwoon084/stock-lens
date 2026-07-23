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
  isIntradayView: boolean;
}

// Derived from the analysis response's own chart_card.price_change_text, NOT from
// selectedPoint.change_percent — for "오늘" that number comes from the frontend's independent
// useLivePrice poll, a different snapshot in time than whatever live quote the backend fetched
// when it built these same factors. Two separately-polled reads of a number that's still moving
// will occasionally disagree in sign; reading the direction back out of the same response that
// produced the factors guarantees the headline and the content always agree.
//
// "오늘"(isIntradayView)에는 방향(상승/하락) 자체를 아예 묻지 않는다 — 장이 안 끝나 등락이
// 확정되지 않은 값으로 "왜"를 주장하면 근거 내용의 방향성과 계속 어긋날 위험이 있어서, 백엔드도
// 이 경우 방향 판단 없이 사실만 전달하도록 바뀜(stock_analysis_system.txt의 is_intraday 분기).
function movementTitle(priceChangeText: string | null, isIntradayView: boolean): string {
  if (isIntradayView) return "오늘 확인된 소식";
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
  isIntradayView,
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
        <MovementSection
          title={movementTitle(priceChangeText, isIntradayView)}
          items={items}
          intradayNotice={intradayNotice}
        />
      )}
    </div>
  );
}
