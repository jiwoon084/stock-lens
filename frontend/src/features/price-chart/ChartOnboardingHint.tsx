interface ChartOnboardingHintProps {
  visible: boolean;
  onDismiss: () => void;
}

// 2차 멘토링 피드백("차트를 클릭하면 상세 정보를 볼 수 있다는 점을 명확히 알려줄 필요가 있다")
// 반영 — 기존엔 상단 태그라인/차트 아래 보조 텍스트뿐이라 눈에 잘 안 띄었음. 첫 방문자에게만
// 보이는 배너로 승격하고, 실제로 클릭하는 순간(App.tsx) 또는 닫기 버튼으로 다시 안 뜨게 함.
export function ChartOnboardingHint({ visible, onDismiss }: ChartOnboardingHintProps) {
  if (!visible) return null;

  return (
    <div className="chart-onboarding-hint" role="status">
      <span className="chart-onboarding-hint__icon" aria-hidden="true">
        👆
      </span>
      <span className="chart-onboarding-hint__text">
        차트에서 날짜를 클릭해보세요 — 그날의 AI 분석과 관련 자료를 바로 볼 수 있어요
      </span>
      <button
        type="button"
        className="chart-onboarding-hint__close"
        onClick={onDismiss}
        aria-label="안내 닫기"
      >
        ✕
      </button>
    </div>
  );
}
