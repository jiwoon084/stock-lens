import { useEffect, useState, type ReactNode } from "react";

import type { Factor, MovementExplanationResponse } from "../../shared/types/explanation";

interface IssueChecklistProps {
  data: MovementExplanationResponse;
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

export function IssueChecklist({ data }: IssueChecklistProps) {
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    setChecked(new Set());
    setExpanded(new Set());
  }, [data]);

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

  if (data.factors.length === 0) {
    return <p className="empty-state">확인된 주요 요인이 없습니다.</p>;
  }

  return (
    <div className="issue-checklist">
      <div className="issue-checklist__header">
        <h4 className="issue-checklist__title">주요 요인</h4>
        <span className="issue-checklist__count">{data.factors.length}개</span>
      </div>

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
                  {linkedSources.length > 0 && (
                    <button
                      type="button"
                      className="issue-checklist__expand-toggle"
                      onClick={() => toggleExpanded(key)}
                    >
                      출처 {linkedSources.length}건 {isExpanded ? "숨기기" : "보기"}
                    </button>
                  )}
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
    </div>
  );
}
