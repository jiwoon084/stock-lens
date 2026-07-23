import { HighlightedText } from "../../shared/components/HighlightedText";
import { AnalysisCaution } from "./AnalysisCaution";
import type { MovementItem, MovementStatus } from "../../types/stockAnalysis";

const STATUS_LABEL: Record<MovementStatus, string> = {
  confirmed: "공식 자료로 확인됐어요",
  reported: "언론에서 언급했어요",
  uncertain: "추가 확인이 필요해요",
  not_found: "관련 자료를 찾지 못했어요",
};

const EVIDENCE_TYPE_LABEL: Record<MovementItem["evidence_type"], string> = {
  official_disclosure: "회사 공식 공시",
  market_data: "시장 데이터",
  media_report: "언론 보도",
};

interface MovementSectionProps {
  title: string;
  items: MovementItem[];
  intradayNotice?: string | null;
}

export function MovementSection({ title, items, intradayNotice }: MovementSectionProps) {
  return (
    <section className="analysis-section">
      <h4 className="analysis-section__title">{title}</h4>
      {intradayNotice && <AnalysisCaution caution={intradayNotice} />}

      {items.length === 0 ? (
        <p className="empty-state">확인된 배경 정보가 아직 충분하지 않아요.</p>
      ) : (
        <ul className="movement-list">
          {items.map((item) => (
            <li key={item.title} className="movement-item">
              <div className="movement-item__heading">
                <span className={`movement-item__evidence-tag movement-item__evidence-tag--${item.evidence_type}`}>
                  {EVIDENCE_TYPE_LABEL[item.evidence_type]}
                </span>
                <span className={`movement-item__status movement-item__status--${item.status}`}>
                  {STATUS_LABEL[item.status]}
                </span>
              </div>
              <p className="movement-item__title">{item.title}</p>
              <p className="movement-item__description">
                <HighlightedText text={item.description} />
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
