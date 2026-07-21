# Screen Design

Stock Lens is a single screen (no routing) implemented in `frontend/src/App.tsx`, composed of a
top bar, a stock summary bar, and a two-column workspace: chart + market-events on the left,
an AI analysis report panel on the right (sticky). Light, Koyfin-inspired chrome; the events
panel below the chart borrows Perplexity Finance's "notable moves" card row.

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Stock Lens · 차트에서 날짜를 선택하면 주가 변동 요인을 분석합니다             │
├───────────────────────────────────────────────────────────────────────────┤
│ (삼성전자)(SK하이닉스)(NAVER)(카카오)(현대차)                                │
│ 삼성전자 KOSPI  005930                              84,400원  ▼ -2.65%     │
│                                                       업데이트 기준 ...     │
├───────────────────────────────────────────────┬─────────────────────────┤
│ [주가 차트]                    (1주)(2주)(1개월)(전체) │ AI 분석 리포트  [분석 완료]│
│ ┌─────────────────────────────────────────┐   │ 005930 · 2026-07-17 기준 │
│ │  candlestick chart (440px)                │   │ ▼ -2.65%    신뢰도 보통  │
│ │  클릭 시 마커로 선택 지점 표시              │   │ 헤드라인 ...            │
│ └─────────────────────────────────────────┘   │ 요약 문단 ...            │
│ 2026-07-17  84,400원  -2.65%  거래량 +236.6%   │ 주요 요인 3개            │
├───────────────────────────────────────────────┤ ☐ [유의] 자기주식처분... │
│ [주목할 만한 가격변동]                          │   출처 1건 보기          │
│ (07-13 ▼-2.1%)(07-15 ▲+3.4%)(07-17 ▼-2.65%)... │ 확인 완료 0/3            │
│  ← 가로 스크롤, 선택된 날짜는 강조                │ 분석의 한계 ...          │
│ 2026-07-17 관련 자료                           │                         │
│  [공시] 자기주식처분결과보고서 · DART · 삼성전자  │                         │
│  [공시] 주요사항보고서 ...                      │                         │
└───────────────────────────────────────────────┴─────────────────────────┘
```

## Component → state mapping

| Component | File | State it owns / reads |
|---|---|---|
| `useStocks` | `features/stock-selector/useStocks.ts` | fetches the sample stock list once, shared by `StockSelector` and `StockHeader` |
| `StockSelector` | `features/stock-selector/StockSelector.tsx` | receives `stocks` as a prop, calls `onSelect(ticker)` |
| `StockHeader` | `features/price-chart/StockHeader.tsx` | pure display of name/market/code + latest close, change, and "업데이트 기준" date, derived from `prices` (unfiltered by period) |
| `ChartToolbar` | `features/price-chart/ChartToolbar.tsx` | period (`1w`/`2w`/`1m`/`all`), filters prices client-side; rendered as the chart card's header action |
| `PriceChart` | `features/price-chart/PriceChart.tsx` | renders candlesticks, emits click → `PricePoint`, marks the selected time with a chart marker (no embedded popover) |
| `SelectedPointInfo` | `features/price-chart/SelectedPointInfo.tsx` | pure display strip under the chart: selected date's price/등락률/거래량, or an idle hint |
| `AIAnalysisPanel` | `features/movement-explanation/AIAnalysisPanel.tsx` | report container — idle/loading/error/success states, header (status pill + ticker/date), headline, summary, confidence, delegates factor list to `IssueChecklist`, renders limitations |
| `IssueChecklist` | `features/movement-explanation/IssueChecklist.tsx` | pure display of a given `data`'s factors, plus local (non-persisted) checkbox/expand state |
| `ExplanationLoading` | `features/movement-explanation/ExplanationLoading.tsx` | skeleton placeholder (shimmer bars) shown only on the *first* load for a ticker (no prior data to keep visible) |
| `MarketEventsPanel` | `features/market-events/MarketEventsPanel.tsx` | "주목할 만한 가격변동" card row (derived client-side from `prices` via `selectNotableMovements`, no extra API calls) + a "선택한 날짜의 관련 자료" sub-panel driven by the same explanation state as the AI panel |
| `EventCard` | `features/market-events/EventCard.tsx` | one notable-movement card (date/방향/등락률/거래량 변화); click reselects that date, same as clicking the chart |
| `SourceCard` | `features/market-events/SourceCard.tsx` | one `Source` (news/disclosure/report) card — type badge, date, title, excerpt, publisher, links out |

`App.tsx` owns `ticker`, `period`, and `selectedPoint` state, and the `useMovementExplanation`
hook's `status/data/error/reset`. Selecting a chart point *or* an event card synchronously
updates `selectedPoint` and triggers the same `explain()` call — there is no separate "요청"
button, and both entry points feed the same state so the chart marker, the selected event card,
and the AI panel's date all move together. Changing `ticker` resets both `selectedPoint` and the
explanation state (`reset()`), so no stale result from a previous stock lingers.

## States explicitly covered

- Stock price loading (`usePriceChart` loading flag, shown via `LoadingSpinner`) and its own
  error fallback to mock data (`error-banner` in the chart card)
- No point selected yet (idle): chart shows no marker, `SelectedPointInfo` shows a hint,
  `AIAnalysisPanel` shows a guidance message, `MarketEventsPanel` still shows the notable-moves
  row (computed from prices alone) with a hint in the sources sub-panel
- Explanation loading: if this is the *first* analysis for the ticker (`data` is still `null`),
  both `AIAnalysisPanel` and the events panel's sources sub-panel show a skeleton. If a previous
  result already exists (the user clicked a new point while one was showing), that previous
  content stays visible at reduced opacity with a small "새로운 분석/자료를 불러오는 중..." badge
  instead of disappearing — `useMovementExplanation` doesn't clear `data` on a new `explain()`
  call, and the UI takes advantage of that instead of blanking the panel.
- Explanation success — `AIAnalysisPanel` shows headline/summary/confidence/factor
  checklist/limitations; `MarketEventsPanel`'s sources sub-panel lists that date's
  `sources` as cards (empty state if `sources` is empty)
- Explanation error — `error-banner` + a "다시 시도" retry button in both `AIAnalysisPanel` and
  `MarketEventsPanel` (both call the same retry, which re-issues `explain()` for the current
  `selectedPoint`)

## Known limitations (deliberate, not bugs)

- "주목할 만한 가격변동" cards are computed purely from already-fetched price data
  (`Math.abs(change_percent)`, top N) — they don't carry a headline/자료유형/발행처 up front,
  because doing so would mean pre-fetching `/api/v1/explanations` for every notable date, which
  isn't part of the existing API contract and would multiply real DART calls. Those richer
  fields (자료 유형/발행처/발췌문) appear once a date is actually selected, in the
  "관련 자료" sub-panel below the card row, sourced from that date's `sources` response.
- Checkbox "확인 완료" state is local component state only — it resets whenever a new point is
  selected or the explanation reloads. Nothing is persisted.
- "호재/유의/중립" tags are a direct 3-way mapping of the existing `Factor.impact` field — there
  is no 4th category and no backend change.
- Glossary terms (수급/업황/컨센서스/잠정실적) are visually marked (dotted underline) with a
  native `title` tooltip only — clicking them does nothing yet.

## Deliberately not designed

Login/account/portfolio screens, comparison view, and follow-up question UI are out of scope
(see `docs/requirements.md`) and have no corresponding screen.
