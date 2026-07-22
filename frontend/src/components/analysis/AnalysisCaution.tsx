interface AnalysisCautionProps {
  caution: string;
}

export function AnalysisCaution({ caution }: AnalysisCautionProps) {
  if (!caution) return null;

  return (
    <p className="analysis-caution">
      <span className="analysis-caution__icon" aria-hidden="true">
        ⚠
      </span>
      {caution}
    </p>
  );
}
