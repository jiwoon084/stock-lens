import type { PricePoint } from "../../shared/types/stock";

interface SelectedPointProps {
  point: PricePoint | null;
}

function changeClass(value: number): string {
  if (value > 0) return "value--positive";
  if (value < 0) return "value--negative";
  return "";
}

export function SelectedPoint({ point }: SelectedPointProps) {
  if (!point) {
    return <p className="empty-state">차트에서 날짜를 선택하면 상세 정보가 표시됩니다.</p>;
  }

  return (
    <div className="selected-point">
      <div className="selected-point__item">
        <span className="selected-point__label">날짜</span>
        <span className="selected-point__value">{point.time}</span>
      </div>
      <div className="selected-point__item">
        <span className="selected-point__label">종가</span>
        <span className="selected-point__value">{point.close.toLocaleString()}원</span>
      </div>
      <div className="selected-point__item">
        <span className="selected-point__label">전일 대비 등락률</span>
        <span className={`selected-point__value ${changeClass(point.change_percent)}`}>
          {point.change_percent > 0 ? "+" : ""}
          {point.change_percent.toFixed(2)}%
        </span>
      </div>
      <div className="selected-point__item">
        <span className="selected-point__label">거래량 변화율</span>
        <span className={`selected-point__value ${changeClass(point.volume_change_percent)}`}>
          {point.volume_change_percent > 0 ? "+" : ""}
          {point.volume_change_percent.toFixed(2)}%
        </span>
      </div>
    </div>
  );
}
