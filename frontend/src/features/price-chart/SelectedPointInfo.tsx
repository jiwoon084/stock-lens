import type { PricePoint } from "../../shared/types/stock";

interface SelectedPointInfoProps {
  point: PricePoint | null;
}

export function SelectedPointInfo({ point }: SelectedPointInfoProps) {
  if (!point) {
    return (
      <p className="selected-point-info selected-point-info--empty">
        차트에서 날짜를 클릭하면 그날의 가격·등락률·거래량을 확인할 수 있어요.
      </p>
    );
  }

  const changeClass =
    point.change_percent > 0 ? "value--positive" : point.change_percent < 0 ? "value--negative" : "";

  return (
    <div className="selected-point-info">
      <span className="selected-point-info__date">{point.time}</span>
      <span className="selected-point-info__price">{point.close.toLocaleString()}원</span>
      <span className={`selected-point-info__change ${changeClass}`}>
        {point.change_percent > 0 ? "+" : ""}
        {point.change_percent.toFixed(2)}%
      </span>
      <span className="selected-point-info__volume">
        거래량 {point.volume.toLocaleString()} ({point.volume_change_percent > 0 ? "+" : ""}
        {point.volume_change_percent.toFixed(1)}%)
      </span>
    </div>
  );
}
