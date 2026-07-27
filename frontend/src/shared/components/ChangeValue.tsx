export function getChangeTone(value: number): "positive" | "negative" | "neutral" {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

export function getChangeArrow(value: number): string {
  return value > 0 ? "▲" : value < 0 ? "▼" : "-";
}

interface ChangeValueProps {
  value: number;
  showArrow?: boolean;
  className?: string;
}

export function ChangeValue({ value, showArrow = true, className }: ChangeValueProps) {
  return (
    <span className={`value--${getChangeTone(value)} ${className ?? ""}`.trim()}>
      {showArrow && `${getChangeArrow(value)} `}
      {value > 0 ? "+" : ""}
      {value.toFixed(2)}%
    </span>
  );
}
