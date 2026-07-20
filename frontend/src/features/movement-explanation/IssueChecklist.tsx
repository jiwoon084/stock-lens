import { useEffect, useState, type ReactNode } from "react";

import type { Factor, MovementExplanationResponse } from "../../shared/types/explanation";
import { ExplanationLoading } from "./ExplanationLoading";
import type { ExplanationStatus } from "./useMovementExplanation";

interface IssueChecklistProps {
  status: ExplanationStatus;
  data: MovementExplanationResponse | null;
  error: string | null;
}

const IMPACT_TAG: Record<Factor["impact"], string> = {
  positive: "호재",
  negative: "유의",
  neutral: "중립",
};

const GLOSSARY_TERMS = ["수급", "업황", "컨센서스", "잠정실적"];
const GLOSSARY_TITLE = "용어 설명 기능은 준비 중입니다.";

function renderWithGlossary(text: string): ReactNode {
  const pattern = new RegExp(`(${GLOSSARY_TERMS.join("|")})`, "g");
  const parts = text.split(pattern);

  return parts.map((part, index) =>
    GLOSSARY_TERMS.includes(part) ? (
      <span key={index} className="glossary-term" title={GLOSSARY_TITLE}>
        {part}
      </span>
    ) : (
      part
    ),
  );
}

export function IssueChecklist({ status, data, error }: IssueChecklistProps) {
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    setChecked(new Set());
    setExpanded(new Set());
  }, [data]);

  if (status === "idle") {
    return <p className="empty-state">차트에서 날짜를 클릭하면 오늘의 체크리스트를 만들어드려요.</p>;
  }

  if (status === "loading") {
    return <ExplanationLoading />;
  }

  if (status === "error") {
    return <div className="error-banner">{error ?? "분석 요청이 실패했습니다."}</div>;
  }

  if (!data) return null;

  function toggleChecked(key: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toggleExpanded(key: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <div className="issue-checklist">
      <h4 className="issue-checklist__title">오늘의 체크리스트</h4>
      <p className="issue-checklist__subtitle">관심 종목 기사 핵심을 짚고 넘어가기</p>
      <p className="issue-checklist__summary">
        오늘 기사 {data.sources.length}건 → 핵심 이슈 {data.factors.length}개로 정리했어요
      </p>

      <ul className="issue-checklist__list">
        {data.factors.map((factor) => {
          const key = factor.title;
          const linkedSources = data.sources.filter((s) => factor.source_ids.includes(s.id));
          const isExpanded = expanded.has(key);

          return (
            <li key={key} className="issue-checklist__item">
              <div className="issue-checklist__row">
                <input
                  type="checkbox"
                  className="issue-checklist__checkbox"
                  checked={checked.has(key)}
                  onChange={() => toggleChecked(key)}
                  aria-label={`${factor.title} 확인 완료`}
                />
                <div className="issue-checklist__content">
                  <span className={`issue-tag issue-tag--${factor.impact}`}>{IMPACT_TAG[factor.impact]}</span>
                  <span className="issue-checklist__factor-title">{factor.title}</span>
                  <p className="issue-checklist__factor-desc">{renderWithGlossary(factor.description)}</p>
                  <button
                    type="button"
                    className="issue-checklist__expand-toggle"
                    onClick={() => toggleExpanded(key)}
                  >
                    출처 {linkedSources.length}건 {isExpanded ? "숨기기" : "보기"}
                  </button>
                  {isExpanded && (
                    <ul className="issue-checklist__sources">
                      {linkedSources.map((source) => (
                        <li key={source.id}>
                          <a href={source.url} target="_blank" rel="noreferrer">
                            {source.title}
                          </a>{" "}
                          · {source.publisher}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      <p className="issue-checklist__footer">
        확인 완료 {checked.size}/{data.factors.length}
      </p>

      <ul className="limitations-list">
        {data.limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
    </div>
  );
}
