interface LoadingSpinnerProps {
  label?: string;
}

export function LoadingSpinner({ label = "불러오는 중..." }: LoadingSpinnerProps) {
  return (
    <div className="loading-spinner" role="status">
      <span className="loading-spinner__dot" />
      <span>{label}</span>
    </div>
  );
}
