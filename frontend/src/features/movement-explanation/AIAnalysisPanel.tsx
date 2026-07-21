import type { MovementExplanationResponse } from "../../shared/types/explanation";
import { ExplanationLoading } from "./ExplanationLoading";
import { IssueChecklist } from "./IssueChecklist";
import type { ExplanationStatus } from "./useMovementExplanation";

const CONFIDENCE_LABEL: Record<MovementExplanationResponse["confidence"], string> = {
  low: "낮음",
  medium: "보통",
  high: "높음",
};

const STATUS_LABEL: Record<ExplanationStatus, string> = {
  idle: "대기 중",
  loading: "분석 중",
  success: "분석 완료",
  error: "분석 실패",
};

interface AIAnalysisPanelProps {
  status: ExplanationStatus;
  data: MovementExplanationResponse | null;
  error: string | null;
  ticker: string;
  selectedDate: string | null;
  onRetry: () => void;
}

export function AIAnalysisPanel({ status, data, error, ticker, selectedDate, onRetry }: AIAnalysisPanelProps) {
  return (
    <section className="ai-panel">
      <header className="ai-panel__header">
        <div>
          <h3 className="ai-panel__title">AI 분석 리포트</h3>
          <p className="ai-panel__subtitle">
            {selectedDate ? `${ticker} · ${selectedDate} 기준` : "날짜를 선택하면 리포트가 생성됩니다"}
          </p>
        </div>
        <span className={`ai-panel__status ai-panel__status--${status}`}>{STATUS_LABEL[status]}</span>
      </header>

      {status === "idle" && (
        <p className="empty-state">
          차트 또는 아래 이벤트 카드에서 날짜를 선택하면 AI 분석 리포트를 확인할 수 있어요.
        </p>
      )}

      {status === "loading" && !data && <ExplanationLoading />}

      {status === "loading" && data && (
        <div className="ai-panel__body ai-panel__body--dimmed">
          <p className="ai-panel__refresh-badge">새로운 분석을 불러오는 중...</p>
          <AIAnalysisContent data={data} />
        </div>
      )}

      {status === "error" && (
        <div className="error-banner">
          <p>{error ?? "분석 요청이 실패했습니다."}</p>
          <button type="button" className="retry-button" onClick={onRetry}>
            다시 시도
          </button>
        </div>
      )}

      {status === "success" && data && (
        <div className="ai-panel__body">
          <AIAnalysisContent data={data} />
        </div>
      )}
    </section>
  );
}

function AIAnalysisContent({ data }: { data: MovementExplanationResponse }) {
  const directionArrow = data.direction === "up" ? "▲" : data.direction === "down" ? "▼" : "-";
  const directionClass =
    data.direction === "up" ? "value--positive" : data.direction === "down" ? "value--negative" : "";

  return (
    <>
      <div className="ai-panel__headline-row">
        <span className={`ai-panel__direction ${directionClass}`}>
          {directionArrow} {data.change_percent > 0 ? "+" : ""}
          {data.change_percent.toFixed(2)}%
        </span>
        <span className="ai-panel__confidence">신뢰도 {CONFIDENCE_LABEL[data.confidence]}</span>
      </div>

      <p className="ai-panel__headline">{data.headline}</p>
      <p className="ai-panel__summary">{data.summary}</p>

      <IssueChecklist data={data} />

      {data.limitations.length > 0 && (
        <div className="ai-panel__limitations">
          <h4 className="ai-panel__limitations-title">분석의 한계</h4>
          <ul className="limitations-list">
            {data.limitations.map((limitation) => (
              <li key={limitation}>{limitation}</li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
