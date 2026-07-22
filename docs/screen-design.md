# Screen Design

Stock Lens is a single screen (no routing) implemented in `frontend/src/App.tsx`, composed of a
top bar, a stock summary bar, and a two-column workspace: chart + market-events on the left, a
"오늘의 체크리스트" panel on the right (sticky). Light, Koyfin-inspired chrome; the events panel
below the chart borrows Perplexity Finance's "notable moves" card row.

⚠️ Updated 2026-07-22 (CLAUDE.md section 10) — clicking a chart point now populates **three**
separate areas from **two** separate backend calls: the older `POST /api/v1/explanations` still
feeds `MarketEventsPanel`'s "관련 자료" list and its `LlmProviderToggle`, while a newer
`POST /api/analysis/date` feeds a popover anchored to the clicked point, a small summary card
under the chart, and the right-side panel (renamed from "AI 분석 리포트"). The diagram below
only shows the right-side panel's *current* content; see the component table for the popover/
summary card.

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Stock Lens · 차트에서 날짜를 선택하면 주가 변동 요인을 분석합니다             │
├───────────────────────────────────────────────────────────────────────────┤
│ (삼성전자)(SK하이닉스)(NAVER)(카카오)(현대차)                                │
│ 삼성전자 KOSPI  005930                              84,400원  ▼ -2.65%     │
│                                                       업데이트 기준 ...     │
├───────────────────────────────────────────────┬─────────────────────────┤
│ [주가 차트]                    (1주)(2주)(1개월)(전체) │ 오늘의 체크리스트 [완료]  │
│ ┌─────────────────────────────────────────┐   │ 005930 · 2026-07-17 기준 │
│ │  candlestick chart (440px)                │   │ 앞으로 확인할 내용        │
│ │  클릭 지점에 팝오버: "이날 왜 움직였나요?"    │   │ ☐ 계약 내용이 실적에...   │
│ └─────────────────────────────────────────┘   │ 더 읽어볼 자료           │
│ 2026-07-17  84,400원  -2.65%  거래량 +236.6%   │ [공시] 주요사항보고서 ... │
│ (요약 카드) -2.65%, 한줄요약, 핵심수치, 근거배지  │   원문 보기              │
├───────────────────────────────────────────────┤ 주의: 공개된 정보만으로... │
│ [주목할 만한 가격변동]           분석 모델(SOLAR)(Gemini)│                  │
│ (07-13 ▼-2.1%)(07-15 ▲+3.4%)(07-17 ▼-2.65%)... │                         │
│  ← 가로 스크롤, 선택된 날짜는 강조                │                         │
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
| `ChartTypeToggle` | `features/price-chart/ChartTypeToggle.tsx` | candle/line switch (icon buttons next to the chart card title); swaps the lightweight-charts series in place, keeps zoom + selection marker |
| `PriceChart` | `features/price-chart/PriceChart.tsx` | renders candlesticks or a line/area series depending on `chartType`, emits click → `PricePoint`, marks the selected time with a chart marker, and exposes the selected point's pixel coordinate via `onSelectedPointCoordinate` (for the popover below) |
| `SelectedPointInfo` | `features/price-chart/SelectedPointInfo.tsx` | pure display strip under the chart: selected date's price/등락률/거래량, or an idle hint |
| `ChartMovementPopover` | `components/analysis/ChartMovementPopover.tsx` | floating box anchored to the clicked chart point (flips left/right to stay inside the chart), renders `MovementSection` inside; dismissible, re-appears on the next point selection |
| `MovementSection` | `components/analysis/MovementSection.tsx` | "이날 왜 움직였나요?" — pure display of `why_it_moved` items (evidence-type tag + status label + title/description); used only inside the popover now |
| `ChartSummaryCard` | `components/analysis/ChartSummaryCard.tsx` | small card under the chart: selected date, price-change text, one-line AI summary, up to 2 quick facts, a clickable primary-evidence badge that scrolls to that source in `RecommendedMaterials` |
| `AnalysisDetailPanel` | `components/analysis/AnalysisDetailPanel.tsx` | the right-side panel, titled "오늘의 체크리스트" — idle/loading/error/success states, header (status pill + ticker/date), renders `WatchChecklist` + `RecommendedMaterials` + `AnalysisCaution` |
| `WatchChecklist` | `components/analysis/WatchChecklist.tsx` | "앞으로 확인할 내용" — checkbox list of `what_to_watch` items, local (non-persisted) checked state, resets when the selected date changes |
| `RecommendedMaterials` | `components/analysis/RecommendedMaterials.tsx` | "더 읽어볼 자료" — cards combining `recommended_materials` (LLM description/topics) with the backend's `sources` map (real title/url/publisher/date); `id="source-{id}"` on each card is the scroll target for `ChartSummaryCard`'s evidence badge |
| `AnalysisCaution` | `components/analysis/AnalysisCaution.tsx` | one-line caution sentence at the bottom of the panel |
| `useStockAnalysis` | `components/analysis/useStockAnalysis.ts` | hook backing all of the above — calls `POST /api/analysis/date`, clears previous data immediately on a new call so a stale date's result is never shown as if it were current |
| `AIAnalysisPanel` / `IssueChecklist` / `ExplanationLoading` | `features/movement-explanation/` | still exist and still work (backed by `useMovementExplanation` / `/api/v1/explanations`), but **not rendered directly in `App.tsx` anymore** — superseded by the components above for the main report. `LlmProviderToggle` from this same folder is still rendered, just relocated (see next row) |
| `MarketEventsPanel` | `features/market-events/MarketEventsPanel.tsx` | "주목할 만한 가격변동" card row (derived client-side from `prices` via `selectNotableMovements`) + `LlmProviderToggle` (SOLAR/Gemini picker for `/api/v1/explanations`, moved here from the old AI panel) + a "관련 자료" sub-panel driven by `useMovementExplanation`'s state |
| `EventCard` | `features/market-events/EventCard.tsx` | one notable-movement card (date/방향/등락률/거래량 변화); click reselects that date, same as clicking the chart |
| `SourceCard` | `features/market-events/SourceCard.tsx` | one `Source` (news/disclosure/report) card — type badge, date, title, excerpt, publisher, links out |

There is no separate "오늘의 체크리스트" *news* panel anymore — `ArticleChecklist` and its whole
backend slice (`checklist.py` route/schema/service) were deliberately removed (redundant with the
factor checklist, no disagreement between sessions on this one — see CLAUDE.md section 4/7). The
*current* "오늘의 체크리스트" title refers to `AnalysisDetailPanel` above, a renamed/trimmed
version of the old AI analysis panel — same name, different feature, don't confuse the two.

`App.tsx` owns `ticker`, `period`, `chartType`, `llmProvider`, `selectedPoint`,
`pointCoordinate`, and `chartWidth` state, plus both `useMovementExplanation`'s
`status/data/error/reset` and `useStockAnalysis`'s `status/data/error/reset`. Selecting a chart
point *or* an event card synchronously updates `selectedPoint` and triggers **both**
`explain()` (old, feeds `MarketEventsPanel`) and `analyze()` (new, feeds the popover/summary
card/side panel) — there is no separate "요청" button. This means one click issues two backend
LLM calls; see CLAUDE.md section 10's TODO list re: merging them later. Changing `ticker` resets
both hooks' state, so no stale result from a previous stock lingers. `chartWidth` is measured via
a callback ref on the chart wrapper (a plain `useRef` + mount-only `useEffect` would miss the
node while `pricesLoading` is still true — see the "실제 버그" note in CLAUDE.md section 10).

## States explicitly covered

- Stock price loading (`usePriceChart` loading flag, shown via `LoadingSpinner`) and its own
  error fallback to mock data (`error-banner` in the chart card)
- No point selected yet (idle): chart shows no marker and no popover, `SelectedPointInfo` and
  `ChartSummaryCard` show hints, `AnalysisDetailPanel` shows a guidance message,
  `MarketEventsPanel` still shows the notable-moves row (computed from prices alone) with a hint
  in the sources sub-panel
- Loading, two different behaviors by design: the **old** `/api/v1/explanations` state
  (`useMovementExplanation`) does *not* clear `data` on a new `explain()` call, so
  `MarketEventsPanel`'s sources sub-panel keeps showing the previous result dimmed with a
  "새로운 자료를 불러오는 중..." badge. The **new** `/api/analysis/date` state
  (`useStockAnalysis`) clears `data` to `null` immediately on `analyze()`, so
  `ChartMovementPopover`/`ChartSummaryCard`/`AnalysisDetailPanel` show a skeleton instead of a
  stale previous date's result — this was an explicit product requirement (never let one date's
  analysis look like it belongs to another).
- Analysis success — `ChartMovementPopover` shows `why_it_moved` next to the clicked point,
  `ChartSummaryCard` shows the one-line summary/quick facts/evidence badge,
  `AnalysisDetailPanel` shows `what_to_watch`/`recommended_materials`/caution (or a single
  "자료가 충분하지 않다" message if both are empty); separately, `MarketEventsPanel`'s sources
  sub-panel lists that date's `/api/v1/explanations` `sources` as cards
- Error — `error-banner` + "다시 시도" retry buttons, one pair per feature (`AnalysisDetailPanel`
  re-issues `analyze()`, `MarketEventsPanel` re-issues `explain()` — they're independent, so one
  can fail while the other succeeds)

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
