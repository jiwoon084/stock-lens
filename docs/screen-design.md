# Screen Design

Stock Lens is a single screen (no routing) implemented in `frontend/src/App.tsx`, composed of
four stacked cards.

```
┌─────────────────────────────────────────────────────────┐
│ Stock Lens                                               │
│ 차트에서 날짜를 선택하면 주가 변동 요인을 분석합니다.       │
├─────────────────────────────────────────────────────────┤
│ [종목 선택]                                              │
│  (삼성전자) (SK하이닉스) (NAVER) (카카오) (현대차)         │
├─────────────────────────────────────────────────────────┤
│ [주가 차트]                                              │
│  (1주) (2주) (1개월) (전체)                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │            candlestick chart (lightweight-charts)  │  │
│  │                     ↑ click a bar to select a date │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│ [선택한 날짜 정보]                                        │
│  날짜        종가        전일 대비 등락률   거래량 변화율   │
│  2026-07-17  84,400원    -2.65%            +236.58%      │
├─────────────────────────────────────────────────────────┤
│ [AI 분석]                                                │
│  (idle) 차트에서 날짜를 클릭하면 AI 분석을 요청합니다.      │
│  (loading) 변동 원인을 분석하는 중입니다...                │
│  (success) 헤드라인 / 요약 / 신뢰도 / 요인 카드 / 출처 목록 │
│            / 분석 한계                                    │
│  (error) 분석 요청이 실패했습니다. (<status>)              │
└─────────────────────────────────────────────────────────┘
```

## Component → state mapping

| Component | File | State it owns / reads |
|---|---|---|
| `StockSelector` | `features/stock-selector/StockSelector.tsx` | fetches stock list, calls `onSelect(ticker)` |
| `ChartToolbar` | `features/price-chart/ChartToolbar.tsx` | period (`1w`/`2w`/`1m`/`all`), filters prices client-side |
| `PriceChart` | `features/price-chart/PriceChart.tsx` | renders candlesticks, emits click → `PricePoint` |
| `SelectedPoint` | `features/price-chart/SelectedPoint.tsx` | pure display of the selected `PricePoint` |
| `ExplanationPanel` | `features/movement-explanation/ExplanationPanel.tsx` | pure display of `idle/loading/success/error` |

`App.tsx` owns `ticker`, `period`, and `selectedPoint` state, and the `useMovementExplanation`
hook's `status/data/error`. Selecting a chart point synchronously updates `selectedPoint` and
triggers the explanation request — there is no separate "요청" button.

## States explicitly covered

- Stock price loading (`usePriceChart` loading flag) and its own error fallback to mock data
- No point selected yet (`selected-point` empty state, `explanation-panel` idle state)
- Explanation loading (`ExplanationLoading`)
- Explanation success (headline, summary, confidence, factors, sources, limitations)
- Explanation error (`error-banner`, distinct from the price-loading error)

## Deliberately not designed

Login/account/portfolio screens, comparison view, and follow-up question UI are out of scope
(see `docs/requirements.md`) and have no corresponding screen.
