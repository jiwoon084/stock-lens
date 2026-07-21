import type { ChecklistItem } from "../../shared/types/checklist";

const TAG_LABEL: Record<ChecklistItem["tag"], string> = {
  positive: "호재",
  negative: "악재",
  earnings: "실적",
  caution: "유의",
  neutral: "중립",
};

interface ChecklistItemRowProps {
  item: ChecklistItem;
  checked: boolean;
  onToggle: (id: string) => void;
}

export function ChecklistItemRow({ item, checked, onToggle }: ChecklistItemRowProps) {
  return (
    <label className={`checklist-item ${checked ? "checklist-item--checked" : ""}`.trim()}>
      <input
        type="checkbox"
        className="checklist-item__checkbox"
        checked={checked}
        onChange={() => onToggle(item.id)}
      />
      <div className="checklist-item__body">
        <div className="checklist-item__heading">
          <span className={`checklist-tag checklist-tag--${item.tag}`}>{TAG_LABEL[item.tag]}</span>
          <span className="checklist-item__headline">{item.headline}</span>
        </div>
        <p className="checklist-item__description">
          {item.description} 출처 {item.source_count}건
          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className="checklist-item__link"
              onClick={(event) => event.stopPropagation()}
            >
              원문 보기 ↗
            </a>
          )}
        </p>
      </div>
    </label>
  );
}
