# Screen Design

Stock Lens is a single screen (no routing) implemented in `frontend/src/App.tsx`, composed of a
header/stock-selector strip followed by a 2-column layout: chart on the left, a checklist-style
AI panel on the right.

```
┌─────────────────────────────────────────────────────────┐
│ Stock Lens                                               │
│ 차트에서 날짜를 선택하면 주가 변동 요인을 분석합니다.       │
├─────────────────────────────────────────────────────────┤
│ [종목 선택]                                              │
│  (삼성전자) (SK하이닉스) (NAVER) (카카오) (현대차)         │
├───────────────────────────────────────┬───────────────────┤
│ 삼성전자 005930          84,400원      │ [오늘의 체크리스트]│
│                    ▼ 2,300 (-2.65%)   │ 관심 종목 기사 핵심│
├───────────────────────────────────────┤ 을 짚고 넘어가기   │
│ [주가 차트]                           │                   │
│  (1주) (2주) (1개월) (전체)            │ 오늘 기사 3건 →    │
│  ┌─────────────────────────────────┐  │ 핵심 이슈 2개로    │
│  │  candlestick chart               │  │ 정리했어요        │
│  │  클릭 시 그 자리에 팝오버:         │  │                   │
│  │  "이날 왜 올랐을까? — 원인 후보"   │  │ ☐ [호재] 실적 기대│
│  │  1. 실적 기대 상승 — 근거: ...    │  │   상승 ...        │
│  │  2. 수급 개선 — 근거: ...         │  │   출처 2건 보기    │
│  └─────────────────────────────────┘  │ ☐ [긍정] 수급 개선│
│                                        │   ...             │
│                                        │ 확인 완료 0/2      │
│                                        │ (분석 한계 목록)   │
└───────────────────────────────────────┴───────────────────┘
```

## Component → state mapping

| Component | File | State it owns / reads |
|---|---|---|
| `useStocks` | `features/stock-selector/useStocks.ts` | fetches the sample stock list once, shared by `StockSelector` and `StockHeader` |
| `StockSelector` | `features/stock-selector/StockSelector.tsx` | receives `stocks` as a prop, calls `onSelect(ticker)` |
| `StockHeader` | `features/price-chart/StockHeader.tsx` | pure display of latest close + change, derived from `prices` (unfiltered by period) |
| `ChartToolbar` | `features/price-chart/ChartToolbar.tsx` | period (`1w`/`2w`/`1m`/`all`), filters prices client-side |
| `PriceChart` | `features/price-chart/PriceChart.tsx` | renders candlesticks, emits click → `PricePoint`, and renders a pixel-anchored popover using the same explanation state as the checklist |
| `IssueChecklist` | `features/movement-explanation/IssueChecklist.tsx` | pure display of `idle/loading/success/error`, plus local (non-persisted) checkbox/expand state |

`App.tsx` owns `ticker`, `period`, and `selectedPoint` state, and the `useMovementExplanation`
hook's `status/data/error/reset`. Selecting a chart point synchronously updates `selectedPoint`
and triggers the explanation request — there is no separate "요청" button. Changing `ticker`
resets both `selectedPoint` and the explanation state (`reset()`), so no stale result from a
previous stock lingers in the popover or checklist.

## States explicitly covered

- Stock price loading (`usePriceChart` loading flag) and its own error fallback to mock data
- No point selected yet (`price-chart` popover hidden, `issue-checklist` idle state)
- Explanation loading (`ExplanationLoading`, reused by both the popover and the checklist)
- Explanation success — popover shows a condensed factor list anchored to the clicked candle;
  checklist shows the full breakdown (tag, description, expandable sources, limitations)
- Explanation error (`error-banner` in the checklist, a short inline message in the popover)

## Known limitations (deliberate, not bugs)

- The popover is pixel-anchored to the clicked candle. Changing the period filter or resizing
  the window invalidates that anchor, so the popover hides itself (re-click to reopen) rather
  than drifting to the wrong spot.
- Checkbox "확인 완료" state is local component state only — it resets whenever a new point is
  selected or the explanation reloads. Nothing is persisted.
- "호재/유의/중립" tags are a direct 3-way mapping of the existing `Factor.impact` field — there
  is no 4th category and no backend change.
- Glossary terms (수급/업황/컨센서스/잠정실적) are visually marked (dotted underline) with a
  native `title` tooltip only — clicking them does nothing yet.

## Deliberately not designed

Login/account/portfolio screens, comparison view, and follow-up question UI are out of scope
(see `docs/requirements.md`) and have no corresponding screen.
