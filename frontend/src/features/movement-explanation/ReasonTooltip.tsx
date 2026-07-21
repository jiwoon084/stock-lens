import type { CSSProperties } from "react";

import type { MovementExplanationResponse, Source } from "../../shared/types/explanation";
import { ExplanationLoading } from "./ExplanationLoading";

type Status = "idle" | "loading" | "success" | "error";

interface ReasonTooltipProps {
  status: Status;
  data: MovementExplanationResponse | null;
  error: string | null;
  style: CSSProperties;
  onClose: () => void;
}

function dayLabel(sourceDate: string, selectedDate: string): string {
  const diffMs = new Date(`${sourceDate}T00:00:00`).getTime() - new Date(`${selectedDate}T00:00:00`).getTime();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "당일";
  return diffDays > 0 ? `+${diffDays}일` : `${diffDays}일`;
}

function linkedSources(sourceIds: string[], sources: Source[]): Source[] {
  const seen = new Set<string>();
  return sourceIds
    .map((id) => sources.find((source) => source.id === id))
    .filter((source): source is Source => {
      if (!source || seen.has(source.title)) return false;
      seen.add(source.title);
      return true;
    });
}

export function ReasonTooltip({ status, data, error, style, onClose }: ReasonTooltipProps) {
  if (status === "idle") return null;

  return (
    <div className="reason-tooltip" style={style}>
      <button type="button" className="reason-tooltip__close" onClick={onClose} aria-label="닫기">
        ×
      </button>

      {status === "loading" && <ExplanationLoading />}

      {status === "error" && <p className="reason-tooltip__error">{error ?? "분석 요청이 실패했습니다."}</p>}

      {status === "success" && data && (
        <>
          <p className="reason-tooltip__title">
            이날 왜 {data.direction === "up" ? "올랐을까" : data.direction === "down" ? "내렸을까" : "움직였을까"}? —
            원인 후보
          </p>
          <ol className="reason-tooltip__factors">
            {data.factors.map((factor) => {
              const linked = linkedSources(factor.source_ids, data.sources);
              return (
                <li key={factor.title}>
                  <span className="reason-tooltip__factor-title">{factor.title}</span>
                  {linked.length > 0 && (
                    <div className="reason-tooltip__evidence">
                      근거:{" "}
                      {linked.map((source, index) => (
                        <span key={source.id}>
                          {index > 0 && " · "}
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noreferrer"
                            className="reason-tooltip__evidence-link"
                          >
                            {source.title}
                          </a>{" "}
                          ({dayLabel(source.published_at.slice(0, 10), data.selected_date)})
                        </span>
                      ))}
                    </div>
                  )}
                </li>
              );
            })}
          </ol>
        </>
      )}
    </div>
  );
}
