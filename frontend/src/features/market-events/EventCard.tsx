import type { PricePoint } from "../../shared/types/stock";

interface EventCardProps {
  point: PricePoint;
  selected: boolean;
  onSelect: (point: PricePoint) => void;
}

export function EventCard({ point, selected, onSelect }: EventCardProps) {
  const arrow = point.change_percent > 0 ? "▲" : point.change_percent < 0 ? "▼" : "-";
  const changeClass =
    point.change_percent > 0 ? "value--positive" : point.change_percent < 0 ? "value--negative" : "";

  return (
    <button
      type="button"
      className={`event-card ${selected ? "event-card--selected" : ""}`.trim()}
      onClick={() => onSelect(point)}
    >
      <span className="event-card__date">{point.time}</span>
      <span className={`event-card__change ${changeClass}`}>
        {arrow} {point.change_percent > 0 ? "+" : ""}
        {point.change_percent.toFixed(2)}%
      </span>
      <span className="event-card__volume">
        거래량 {point.volume_change_percent > 0 ? "+" : ""}
        {point.volume_change_percent.toFixed(1)}%
      </span>
    </button>
  );
}
