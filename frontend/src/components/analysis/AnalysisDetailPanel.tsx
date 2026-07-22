import { AnalysisCaution } from "./AnalysisCaution";
import { RecommendedMaterials } from "./RecommendedMaterials";
import { WatchChecklist } from "./WatchChecklist";
import type { StockAnalysisStatus } from "./useStockAnalysis";
import type { StockAnalysisResponse } from "../../types/stockAnalysis";

const STATUS_LABEL: Record<StockAnalysisStatus, string> = {
  idle: "대기 중",
  loading: "분석 중",
  success: "분석 완료",
  error: "분석 실패",
};

function _isAllEmpty(data: StockAnalysisResponse): boolean {
  const panel = data.analysis.detail_panel;
  return panel.what_to_watch.length === 0 && panel.recommended_materials.length === 0;
}

interface AnalysisDetailPanelProps {
  status: StockAnalysisStatus;
  data: StockAnalysisResponse | null;
  error: string | null;
  ticker: string;
  selectedDate: string | null;
  onRetry: () => void;
}

export function AnalysisDetailPanel({ status, data, error, ticker, selectedDate, onRetry }: AnalysisDetailPanelProps) {
  return (
    <section className="ai-panel">
      <header className="ai-panel__header">
        <div>
          <h3 className="ai-panel__title">오늘의 체크리스트</h3>
          <p className="ai-panel__subtitle">
            {selectedDate ? `${ticker} · ${selectedDate} 기준` : "날짜를 선택하면 체크리스트가 생성됩니다"}
          </p>
        </div>
        <span className={`ai-panel__status ai-panel__status--${status}`}>{STATUS_LABEL[status]}</span>
      </header>

      {status === "idle" && (
        <p className="empty-state">차트 또는 아래 이벤트 카드에서 날짜를 선택하면 체크리스트를 확인할 수 있어요.</p>
      )}

      {status === "loading" && (
        <div className="report-skeleton" role="status" aria-label="분석 결과를 불러오는 중입니다">
          <div className="report-skeleton__line report-skeleton__line--wide" />
          <div className="report-skeleton__line" />
          <div className="report-skeleton__block" />
          <div className="report-skeleton__block report-skeleton__block--short" />
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
          {_isAllEmpty(data) ? (
            <p className="empty-state">이 날짜에는 설명에 활용할 공식 공시나 관련 뉴스가 충분하지 않아요.</p>
          ) : (
            <>
              <WatchChecklist items={data.analysis.detail_panel.what_to_watch} resetKey={selectedDate ?? ""} />
              <RecommendedMaterials materials={data.analysis.detail_panel.recommended_materials} sources={data.sources} />
            </>
          )}
          <AnalysisCaution caution={data.analysis.detail_panel.caution} />
        </div>
      )}
    </section>
  );
}
