import type { ChecklistResponse } from "../shared/types/checklist";

const SAMSUNG_CHECKLIST: ChecklistResponse = {
  ticker: "005930",
  date: "2026-07-20",
  total_article_count: 14,
  items: [
    {
      id: "chk-1",
      tag: "positive",
      headline: "HBM 공급계약 체결 보도",
      description: "대형 고객사와 차세대 메모리 공급 합의.",
      source_count: 3,
      url: "",
    },
    {
      id: "chk-2",
      tag: "earnings",
      headline: "3분기 잠정실적 발표 예정",
      description: "컨센서스 대비 개선 전망. 발표일 확인 필요.",
      source_count: 5,
      url: "",
    },
    {
      id: "chk-3",
      tag: "caution",
      headline: "환율·업황 변동성 언급",
      description: "일부 리포트가 하반기 리스크 요인 지적.",
      source_count: 4,
      url: "",
    },
    {
      id: "chk-4",
      tag: "neutral",
      headline: "신규 라인 증설 계획 보도",
      description: "사실 전달 성격. 중복 기사 다수 묶음.",
      source_count: 2,
      url: "",
    },
  ],
};

const DEFAULT_CHECKLIST: Omit<ChecklistResponse, "ticker"> = {
  date: "2026-07-20",
  total_article_count: 9,
  items: [
    {
      id: "chk-1",
      tag: "positive",
      headline: "주요 거래처向 공급 확대 보도",
      description: "관련 업계 매체에서 긍정적으로 평가.",
      source_count: 3,
      url: "",
    },
    {
      id: "chk-2",
      tag: "earnings",
      headline: "분기 실적 발표 예정",
      description: "시장 컨센서스와 비교 필요.",
      source_count: 4,
      url: "",
    },
    {
      id: "chk-3",
      tag: "caution",
      headline: "업황 관련 유의 요인 언급",
      description: "일부 자료가 리스크 요인으로 지적.",
      source_count: 2,
      url: "",
    },
  ],
};

export function generateMockChecklist(ticker: string): ChecklistResponse {
  if (ticker === SAMSUNG_CHECKLIST.ticker) return SAMSUNG_CHECKLIST;
  return { ticker, ...DEFAULT_CHECKLIST };
}
