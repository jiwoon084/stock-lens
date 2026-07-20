import type { Factor } from "../../shared/types/explanation";

const IMPACT_LABEL: Record<Factor["impact"], string> = {
  positive: "긍정적",
  negative: "부정적",
  neutral: "중립",
};

export function FactorCard({ factor }: { factor: Factor }) {
  return (
    <div className="factor-card">
      <div className="factor-card__title">
        {factor.title} · {IMPACT_LABEL[factor.impact]}
      </div>
      <p>{factor.description}</p>
    </div>
  );
}
