export type ChartPeriod = "1w" | "2w" | "1m" | "all";

const PERIODS: { value: ChartPeriod; label: string }[] = [
  { value: "1w", label: "1주" },
  { value: "2w", label: "2주" },
  { value: "1m", label: "1개월" },
  { value: "all", label: "전체" },
];

interface ChartToolbarProps {
  period: ChartPeriod;
  onChangePeriod: (period: ChartPeriod) => void;
}

export function ChartToolbar({ period, onChangePeriod }: ChartToolbarProps) {
  return (
    <div className="chart-toolbar">
      {PERIODS.map((option) => (
        <button
          key={option.value}
          type="button"
          className={`chart-toolbar__button ${
            option.value === period ? "chart-toolbar__button--active" : ""
          }`.trim()}
          onClick={() => onChangePeriod(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function filterPricesByPeriod<T extends { time: string }>(prices: T[], period: ChartPeriod): T[] {
  if (period === "all") return prices;
  const days = period === "1w" ? 5 : period === "2w" ? 10 : 20;
  return prices.slice(-days);
}
