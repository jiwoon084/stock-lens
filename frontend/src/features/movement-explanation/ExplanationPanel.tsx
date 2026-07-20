import type { MovementExplanationResponse } from "../../shared/types/explanation";
import { ExplanationLoading } from "./ExplanationLoading";
import { FactorCard } from "./FactorCard";
import { SourceList } from "./SourceList";

type Status = "idle" | "loading" | "success" | "error";

interface ExplanationPanelProps {
  status: Status;
  data: MovementExplanationResponse | null;
  error: string | null;
}

const CONFIDENCE_LABEL: Record<MovementExplanationResponse["confidence"], string> = {
  low: "낮음",
  medium: "중간",
  high: "높음",
};

export function ExplanationPanel({ status, data, error }: ExplanationPanelProps) {
  if (status === "idle") {
    return <p className="empty-state">차트에서 날짜를 클릭하면 AI 분석을 요청합니다.</p>;
  }

  if (status === "loading") {
    return <ExplanationLoading />;
  }

  if (status === "error") {
    return <div className="error-banner">{error ?? "분석 요청이 실패했습니다."}</div>;
  }

  if (!data) return null;

  return (
    <div>
      <h4 className="explanation-panel__headline">{data.headline}</h4>
      <p className="explanation-panel__summary">{data.summary}</p>
      <p className="empty-state">분석 신뢰도: {CONFIDENCE_LABEL[data.confidence]}</p>

      <h5>주요 요인</h5>
      {data.factors.map((factor) => (
        <FactorCard key={factor.title} factor={factor} />
      ))}

      <h5>출처</h5>
      <SourceList sources={data.sources} />

      <h5>분석 한계</h5>
      <ul className="limitations-list">
        {data.limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
    </div>
  );
}
