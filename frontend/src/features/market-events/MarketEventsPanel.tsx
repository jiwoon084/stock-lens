import type { ExplanationStatus } from "../movement-explanation/useMovementExplanation";
import { LlmProviderToggle } from "../movement-explanation/LlmProviderToggle";
import type { LlmProvider, MovementExplanationResponse } from "../../shared/types/explanation";
import type { PricePoint } from "../../shared/types/stock";
import { Card } from "../../shared/components/Card";
import { EventCard } from "./EventCard";
import { SourceCard } from "./SourceCard";
import { selectNotableMovements } from "./marketEvents";

interface MarketEventsPanelProps {
  prices: PricePoint[];
  selectedPoint: PricePoint | null;
  status: ExplanationStatus;
  data: MovementExplanationResponse | null;
  error: string | null;
  llmProvider: LlmProvider;
  onChangeProvider: (provider: LlmProvider) => void;
  onSelectPoint: (point: PricePoint) => void;
  onRetry: () => void;
}

export function MarketEventsPanel({
  prices,
  selectedPoint,
  status,
  data,
  error,
  llmProvider,
  onChangeProvider,
  onSelectPoint,
  onRetry,
}: MarketEventsPanelProps) {
  const notable = selectNotableMovements(prices);

  return (
    <Card className="market-events" title="주목할 만한 가격변동">
      <p className="market-events__subtitle">
        변동이 컸던 거래일을 훑어보고, 클릭해서 관련 자료를 확인하세요.
      </p>

      {notable.length === 0 ? (
        <p className="empty-state">표시할 데이터가 없습니다.</p>
      ) : (
        <div className="event-card-row">
          {notable.map((point) => (
            <EventCard
              key={point.time}
              point={point}
              selected={selectedPoint?.time === point.time}
              onSelect={onSelectPoint}
            />
          ))}
        </div>
      )}

      <div className="market-events__sources">
        <div className="market-events__sources-header">
          <h4 className="market-events__sources-title">
            {selectedPoint ? `${selectedPoint.time} 관련 자료` : "관련 자료"}
          </h4>
          <LlmProviderToggle provider={llmProvider} onChange={onChangeProvider} />
        </div>

        {!selectedPoint && (
          <p className="empty-state">위 카드 또는 차트에서 날짜를 선택하면 관련 자료가 여기에 표시됩니다.</p>
        )}

        {selectedPoint && status === "loading" && !data && (
          <div className="source-card-list">
            <div className="source-card source-card--skeleton" />
            <div className="source-card source-card--skeleton" />
          </div>
        )}

        {selectedPoint && status === "loading" && data && (
          <>
            <p className="market-events__refresh-badge">새로운 자료를 불러오는 중...</p>
            <div className="source-card-list source-card-list--dimmed">
              {data.sources.map((source) => (
                <SourceCard key={source.id} source={source} />
              ))}
            </div>
          </>
        )}

        {selectedPoint && status === "error" && (
          <div className="error-banner">
            <p>{error ?? "관련 자료를 불러오지 못했습니다."}</p>
            <button type="button" className="retry-button" onClick={onRetry}>
              다시 시도
            </button>
          </div>
        )}

        {selectedPoint && status === "success" && data && (
          data.sources.length > 0 ? (
            <div className="source-card-list">
              {data.sources.map((source) => (
                <SourceCard key={source.id} source={source} />
              ))}
            </div>
          ) : (
            <p className="empty-state">관련 자료를 찾지 못했습니다.</p>
          )
        )}
      </div>
    </Card>
  );
}
