import type { LlmProvider } from "../../shared/types/explanation";

const PROVIDERS: { value: LlmProvider; label: string }[] = [
  { value: "solar", label: "SOLAR" },
  { value: "gemini", label: "Gemini" },
];

interface LlmProviderToggleProps {
  provider: LlmProvider;
  onChange: (provider: LlmProvider) => void;
}

export function LlmProviderToggle({ provider, onChange }: LlmProviderToggleProps) {
  return (
    <div className="llm-provider-toggle" role="group" aria-label="분석 모델 선택">
      <span className="llm-provider-toggle__label">분석 모델</span>
      {PROVIDERS.map((option) => (
        <button
          key={option.value}
          type="button"
          className={`llm-provider-toggle__button ${
            option.value === provider ? "llm-provider-toggle__button--active" : ""
          }`.trim()}
          aria-pressed={option.value === provider}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
