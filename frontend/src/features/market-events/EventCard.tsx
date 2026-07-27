import { ChangeValue } from "../../shared/components/ChangeValue";
import type { PricePoint } from "../../shared/types/stock";

interface EventCardProps {
  point: PricePoint;
  selected: boolean;
  onSelect: (point: PricePoint) => void;
}

export function EventCard({ point, selected, onSelect }: EventCardProps) {
  return (
    <button
      type="button"
      className={`event-card ${selected ? "event-card--selected" : ""}`.trim()}
      onClick={() => onSelect(point)}
    >
      <span className="event-card__date">{point.time}</span>
      <ChangeValue value={point.change_percent} className="event-card__change" />
      <span className="event-card__volume">
        거래량 {point.volume_change_percent > 0 ? "+" : ""}
        {point.volume_change_percent.toFixed(1)}%
      </span>
    </button>
  );
}
