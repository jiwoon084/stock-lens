import type { MovementExplanationResponse } from "../shared/types/explanation";

export const MOCK_EXPLANATION: MovementExplanationResponse = {
  ticker: "005930",
  selected_date: "2026-07-15",
  price: 84200,
  change_percent: 3.42,
  volume_change_percent: 81.3,
  direction: "up",
  headline: "실적 기대와 외국인 매수세가 주요 관련 요인으로 분석됩니다.",
  summary:
    "선택 시점 전후의 공개 자료를 종합하면 실적 기대와 반도체 업황 개선 전망이 상승과 관련된 주요 요인으로 확인됩니다.",
  confidence: "medium",
  factors: [
    {
      title: "실적 기대 상승",
      impact: "positive",
      description: "시장 전망치를 상회할 수 있다는 기대가 관련 기사에서 언급되었습니다.",
      source_ids: ["source-1", "source-2"],
    },
  ],
  sources: [
    {
      id: "source-1",
      type: "news",
      title: "삼성전자 실적 전망 관련 기사",
      publisher: "샘플 언론사",
      published_at: "2026-07-15T09:20:00+09:00",
      url: "https://example.com",
      excerpt: "실적 개선 기대가 확대되고 있다는 내용입니다.",
      summary_lines: ["실적 개선 기대가 확대되고 있어요."],
    },
  ],
  limitations: ["공개 자료만으로 가격 변동의 직접적인 인과관계를 확정할 수 없습니다."],
};
