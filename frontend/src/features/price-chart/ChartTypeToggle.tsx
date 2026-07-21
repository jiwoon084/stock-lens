export type ChartType = "candle" | "line";

interface ChartTypeToggleProps {
  chartType: ChartType;
  onChange: (chartType: ChartType) => void;
}

export function ChartTypeToggle({ chartType, onChange }: ChartTypeToggleProps) {
  return (
    <div className="chart-type-toggle" role="group" aria-label="차트 형태 선택">
      <button
        type="button"
        className={`chart-type-toggle__button ${
          chartType === "candle" ? "chart-type-toggle__button--active" : ""
        }`.trim()}
        aria-pressed={chartType === "candle"}
        title="캔들 차트"
        onClick={() => onChange("candle")}
      >
        <CandleIcon />
      </button>
      <button
        type="button"
        className={`chart-type-toggle__button ${
          chartType === "line" ? "chart-type-toggle__button--active" : ""
        }`.trim()}
        aria-pressed={chartType === "line"}
        title="라인 차트"
        onClick={() => onChange("line")}
      >
        <LineIcon />
      </button>
    </div>
  );
}

function CandleIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <line x1="4" y1="1" x2="4" y2="15" stroke="currentColor" strokeWidth="1.2" />
      <rect x="2.25" y="5" width="3.5" height="6" rx="0.5" fill="currentColor" />
      <line x1="11.5" y1="1" x2="11.5" y2="15" stroke="currentColor" strokeWidth="1.2" />
      <rect x="9.75" y="3" width="3.5" height="4" rx="0.5" fill="currentColor" />
    </svg>
  );
}

function LineIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <polyline
        points="1.5,11 5,6.5 8,9 14.5,2.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="5" cy="6.5" r="1" fill="currentColor" />
      <circle cx="8" cy="9" r="1" fill="currentColor" />
    </svg>
  );
}
