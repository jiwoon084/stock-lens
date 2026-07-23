export interface GlossaryEntry {
  term: string;
  definition: string;
}

// Curated for terms that actually show up in this repo's disclosure/news data (data/disclosures.json,
// data/news.json) — not a general finance dictionary. Longest term first isn't required here;
// HighlightedText sorts by length itself so overlapping entries (e.g. a future "자기주식" vs
// "자기주식처분") always match the more specific one.
export const GLOSSARY: GlossaryEntry[] = [
  {
    term: "자기주식처분",
    definition: "회사가 갖고 있던 자기 주식을 다시 시장에 파는 것이에요. 보통 직원 보상이나 자금 확보 목적으로 이뤄져요.",
  },
  {
    term: "유상증자",
    definition:
      "회사가 새 주식을 발행해서 투자자에게 돈을 받고 파는 것이에요. 회사엔 자금이 들어오지만, 기존 주주의 지분 비율은 줄어들 수 있어요.",
  },
  {
    term: "공정공시",
    definition: "특정 투자자에게만 알려주면 불공평하니, 중요한 정보를 모든 투자자에게 동시에 공개하도록 하는 제도예요.",
  },
  {
    term: "잠정실적",
    definition: "아직 확정되지 않은, 회사가 미리 발표하는 실적 수치예요. 나중에 정식 발표에서 조금 달라질 수 있어요.",
  },
  {
    term: "거래량",
    definition: "일정 기간 동안 그 주식이 사고팔린 주식 수예요. 거래량이 많으면 그만큼 관심이 몰렸다는 뜻이에요.",
  },
  {
    term: "시가총액",
    definition: "현재 주가에 전체 발행 주식 수를 곱한 값이에요. 회사의 전체 가치를 나타내는 대표적인 지표예요.",
  },
  {
    term: "공급계약",
    definition: "회사가 다른 회사에 물건이나 서비스를 공급하기로 맺은 계약이에요. 계약 규모가 크면 주가에 영향을 줄 수 있어요.",
  },
  {
    term: "특수관계인",
    definition: "회사의 임원, 대주주, 그 가족처럼 회사와 특별히 가까운 관계에 있는 사람이나 회사를 뜻해요.",
  },
  {
    term: "액면가",
    definition: "주식이 처음 발행될 때 정해진 기준 가격이에요. 실제 거래되는 시장 가격과는 다를 수 있어요.",
  },
  {
    term: "위탁증거금",
    definition: "주식을 살 때 증권사에 미리 맡겨두는 보증금 같은 돈이에요.",
  },
  {
    term: "배당",
    definition: "회사가 벌어들인 이익 일부를 주주에게 나눠주는 것이에요.",
  },
  {
    term: "자기주식취득",
    definition: "회사가 시장에서 자기 회사 주식을 다시 사들이는 것이에요(\"자기주식처분\"의 반대예요).",
  },
  {
    term: "영업이익",
    definition: "회사가 본업으로 벌어들인 이익이에요.",
  },
  {
    term: "순이익",
    definition: "영업이익에서 이자·세금 등을 다 뺀, 최종적으로 남은 이익이에요.",
  },
  {
    term: "풍문",
    definition: "아직 확인 안 된 소문이나 보도예요. 회사가 사실인지 아닌지 해명하는 공시도 있어요.",
  },
  {
    term: "최대주주",
    definition: "회사 주식을 가장 많이 갖고 있는 사람이나 회사예요. 보통 회사를 실질적으로 이끄는 대주주를 뜻해요.",
  },
  {
    term: "대량보유",
    definition:
      "한 사람이나 회사가 특정 기업 주식을 5% 이상 갖게 되면 그 사실을 공시해야 하는 제도예요(흔히 \"5%룰\"이라고 불러요).",
  },
  {
    term: "전환가액",
    definition: "전환사채(나중에 주식으로 바꿀 수 있는 채권)를 실제 주식으로 바꿀 때 적용되는 가격이에요.",
  },
  {
    term: "적자",
    definition: "회사가 번 돈보다 쓴 돈이 더 많아서 손해를 본 상태예요. 반대말은 흑자예요.",
  },
  {
    term: "실적발표",
    definition: "회사가 일정 기간(분기·반기·연간) 경영 성과를 공식적으로 발표하는 것이에요.",
  },
];
