import { useEffect, useState } from "react";

import { HighlightedText } from "../../shared/components/HighlightedText";
import type { WatchItem } from "../../types/stockAnalysis";

interface WatchChecklistProps {
  items: WatchItem[];
  resetKey: string;
}

export function WatchChecklist({ items, resetKey }: WatchChecklistProps) {
  const [checked, setChecked] = useState<Set<string>>(new Set());

  useEffect(() => {
    setChecked(new Set());
  }, [resetKey]);

  function toggle(title: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      return next;
    });
  }

  return (
    <section className="analysis-section">
      <h4 className="analysis-section__title">앞으로 지켜볼 신호</h4>
      <p className="analysis-section__subtitle">앞으로 발표될 내용에서 확인하세요</p>

      {items.length === 0 ? (
        <p className="empty-state">지금은 추가로 확인할 항목이 없어요.</p>
      ) : (
        <ul className="watch-checklist">
          {items.map((item) => (
            <li key={item.title} className="watch-checklist__item">
              <input
                type="checkbox"
                className="watch-checklist__checkbox"
                checked={checked.has(item.title)}
                onChange={() => toggle(item.title)}
                aria-label={`${item.title} 확인 완료`}
              />
              <div className="watch-checklist__content">
                <p className={`watch-checklist__title ${checked.has(item.title) ? "watch-checklist__title--done" : ""}`}>
                  {item.title}
                </p>
                <p className="watch-checklist__description">
                  <HighlightedText text={item.description} />
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
