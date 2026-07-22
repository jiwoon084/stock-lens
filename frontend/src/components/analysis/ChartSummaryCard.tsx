import type { ChartCard, SourceMetadata } from "../../types/stockAnalysis";
import type { StockAnalysisStatus } from "./useStockAnalysis";

interface ChartSummaryCardProps {
  status: StockAnalysisStatus;
  chartCard: ChartCard | null;
  error: string | null;
  sources: Record<string, SourceMetadata>;
  onSelectPrimaryEvidence?: (sourceId: string) => void;
}

export function ChartSummaryCard({ status, chartCard, error, sources, onSelectPrimaryEvidence }: ChartSummaryCardProps) {
  if (status === "idle") {
    return (
      <p className="chart-summary-card chart-summary-card--empty">
        차트에서 날짜를 클릭하면 그날의 AI 요약을 확인할 수 있어요.
      </p>
    );
  }

  if (status === "loading") {
    return (
      <div className="chart-summary-card chart-summary-card--loading" role="status" aria-label="분석 요약을 불러오는 중입니다">
        <div className="report-skeleton__line report-skeleton__line--short" />
        <div className="report-skeleton__line report-skeleton__line--wide" />
        <div className="report-skeleton__line" />
      </div>
    );
  }

  if (status === "error") {
    return <p className="chart-summary-card chart-summary-card--empty">{error ?? "요약을 불러오지 못했어요."}</p>;
  }

  if (!chartCard) {
    return null;
  }

  const changeClass = chartCard.price_change_text.trim().startsWith("-") ? "value--negative" : "value--positive";
  const primarySource = chartCard.primary_evidence ? sources[chartCard.primary_evidence.source_id] : undefined;

  return (
    <div className="chart-summary-card">
      <div className="chart-summary-card__headline-row">
        <span className="chart-summary-card__date">{chartCard.selected_date}</span>
        <span className={`chart-summary-card__change ${changeClass}`}>{chartCard.price_change_text}</span>
      </div>

      <p className="chart-summary-card__summary">{chartCard.one_line_summary}</p>

      {chartCard.quick_facts.length > 0 && (
        <dl className="chart-summary-card__quick-facts">
          {chartCard.quick_facts.map((fact) => (
            <div className="chart-summary-card__quick-fact" key={fact.label}>
              <dt>{fact.label}</dt>
              <dd>{fact.value}</dd>
            </div>
          ))}
        </dl>
      )}

      {chartCard.primary_evidence && (
        <button
          type="button"
          className="chart-summary-card__evidence-badge"
          onClick={() => onSelectPrimaryEvidence?.(chartCard.primary_evidence!.source_id)}
          title={primarySource?.title ?? chartCard.primary_evidence.label}
        >
          [{chartCard.primary_evidence.label}]
        </button>
      )}
    </div>
  );
}
