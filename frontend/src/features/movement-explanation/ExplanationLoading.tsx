export function ExplanationLoading() {
  return (
    <div className="report-skeleton" role="status" aria-label="분석 결과를 불러오는 중입니다">
      <div className="report-skeleton__line report-skeleton__line--wide" />
      <div className="report-skeleton__line" />
      <div className="report-skeleton__line report-skeleton__line--short" />
      <div className="report-skeleton__block" />
      <div className="report-skeleton__block" />
      <div className="report-skeleton__block report-skeleton__block--short" />
    </div>
  );
}
