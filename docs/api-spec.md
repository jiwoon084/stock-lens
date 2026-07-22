# API Spec

Base URL (local): `http://localhost:8000` (via Docker Compose backend service, mapped from
container port 8080). All request/response bodies use snake_case field names — the frontend
TypeScript types in `frontend/src/shared/types/` mirror these fields exactly, so no
case-conversion layer exists at the API boundary.

---

## GET /health

Liveness check.

**Response schema**

```
{ "status": string }
```

**Success (200)**

```json
{ "status": "ok" }
```

---

## GET /api/v1/stocks

Returns the sample stock universe (currently 5 tickers, hardcoded in
`app/services/market_data_service.py`).

**Response schema**

```
[{ "ticker": string, "name": string, "market": string }, ...]
```

**Success (200)**

```json
[
  { "ticker": "005930", "name": "삼성전자", "market": "KOSPI" },
  { "ticker": "000660", "name": "SK하이닉스", "market": "KOSPI" }
]
```

---

## GET /api/v1/stocks/{ticker}/prices

Returns a mock daily OHLCV series (30 trading days ending 2026-07-17) for the given ticker.

**Response schema**

```
[{
  "time": "YYYY-MM-DD",
  "open": number, "high": number, "low": number, "close": number,
  "volume": integer,
  "change_percent": number,       // vs previous trading day's close
  "volume_change_percent": number // vs previous trading day's volume
}, ...]
```

**Success (200)**

```json
[
  {
    "time": "2026-07-17",
    "open": 86800.0,
    "high": 86800.0,
    "low": 84200.0,
    "close": 84400.0,
    "volume": 10905123,
    "change_percent": -2.65,
    "volume_change_percent": 236.58
  }
]
```

**Error (404)** — unknown ticker

```json
{ "detail": "Unknown ticker: 999999" }
```

---

## POST /api/v1/explanations

Returns a movement-explanation response. `factors`/`sources` are now built from **real DART
disclosures** (see `app/services/retrieval_service.py` and `docs/project-plan.md` M2) when a
`data/disclosures.json` snapshot exists for the ticker/date — otherwise (e.g. in a Docker image
without `data/` mounted, or a date/ticker with no nearby disclosures) they come back empty and
`headline`/`summary` say so honestly rather than inventing content. `headline`/`summary`/
`confidence`/impact labeling are still rule-based (see `app/services/llm_service.py`) — not a
real LLM call yet. Because sources are fetched live from DART per request, **the exact response
content is not fully deterministic** and depends on `DART_API_KEY` being set and DART being
reachable; only the schema shape below is guaranteed.

**Request schema**

```
{
  "ticker": string,
  "selected_date": "YYYY-MM-DD",
  "interval": string,               // e.g. "1d"; currently unused but part of the contract
  "llm_provider": "solar" | "gemini" // optional, defaults to "solar" if omitted
}
```

`llm_provider` picks which real LLM writes the analysis (see `app/services/solar_client.py` /
`gemini_client.py`) — falls back to the deterministic rule-based response if that provider's
API key is unset or the call fails, so a missing key or provider outage never causes a 4xx/5xx.
An unrecognized value (anything other than `"solar"`/`"gemini"`) returns **422** (FastAPI's
standard request-validation error). This is a per-request user choice, not automatic routing —
see CLAUDE.md section 9 before changing this (reverted to auto-routing and back twice already).

**Request example**

```json
{ "ticker": "005930", "selected_date": "2026-07-15", "interval": "1d", "llm_provider": "gemini" }
```

**Response schema**

```
{
  "ticker": string,
  "selected_date": "YYYY-MM-DD",
  "price": number,
  "change_percent": number,
  "volume_change_percent": number,
  "direction": "up" | "down" | "flat",
  "headline": string,
  "summary": string,
  "confidence": "low" | "medium" | "high",
  "factors": [{
    "title": string,
    "impact": "positive" | "negative" | "neutral",
    "description": string,
    "source_ids": string[]
  }],
  "sources": [{
    "id": string, "type": string, "title": string, "publisher": string,
    "published_at": string (ISO 8601), "url": string, "excerpt": string
  }],
  "limitations": string[]
}
```

**Success (200)** — real example captured against actual DART data for Samsung Electronics
(자기주식처분결정 has a structured DART API, so its `excerpt` is a clean labeled summary rather
than raw document text — see `app/services/retrieval_service.py`'s `_format_structured_excerpt`):

```json
{
  "ticker": "005930",
  "selected_date": "2026-07-17",
  "price": 84400.0,
  "change_percent": -2.65,
  "volume_change_percent": 236.58,
  "direction": "down",
  "headline": "'자기주식처분결과보고서' 공시가 이 시점 가격 변동과 관련이 있을 수 있습니다.",
  "summary": "선택 시점(2026-07-17) 전후 5건의 DART 공시 중 등락률 -2.65%, 거래량 변화 +236.58%와 시점상 가까운 3건을 관련 요인으로 정리했습니다.",
  "confidence": "medium",
  "factors": [
    {
      "title": "주요사항보고서(자기주식처분결정)",
      "impact": "negative",
      "description": "처분목적: 임원 등 성과급의 자기주식 지급 / 처분주식수: 1,132,477주 / 처분가액: 1주당 285,000원, 총 322,755,945,000원 / 처분기간: 2026년 07월 13일 ~ 2026년 07월 13일",
      "source_ids": ["20260713000395"]
    }
  ],
  "sources": [
    {
      "id": "20260713000395",
      "type": "disclosure",
      "title": "주요사항보고서(자기주식처분결정)",
      "publisher": "DART · 삼성전자",
      "published_at": "2026-07-13T00:00:00+09:00",
      "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260713000395",
      "excerpt": "처분목적: 임원 등 성과급의 자기주식 지급 / 처분주식수: 1,132,477주 / 처분가액: 1주당 285,000원, 총 322,755,945,000원 / 처분기간: 2026년 07월 13일 ~ 2026년 07월 13일"
    }
  ],
  "limitations": [
    "공시 제목과 접수일만으로 가격 변동의 직접적인 인과관계를 확정할 수 없습니다.",
    "호재/유의/중립 표시는 실제 공시 내용을 분석한 것이 아니라, 등락 방향에 따른 단순 추정입니다.",
    "뉴스·리서치 리포트 등 다른 자료는 아직 연동되지 않았습니다."
  ]
}
```

**Success (200) — no matching disclosures found** (e.g. `DART_API_KEY` unset, `data/disclosures.json`
missing, or no disclosure near the selected date for that ticker — honest empty result, not a
fabricated one):

```json
{
  "ticker": "005930",
  "selected_date": "2026-07-17",
  "price": 84400.0,
  "change_percent": -2.65,
  "volume_change_percent": 236.58,
  "direction": "down",
  "headline": "관련 공시·뉴스 자료를 찾지 못했습니다.",
  "summary": "선택 시점(2026-07-17) 전후로 조회 가능한 DART 공시나 뉴스가 없어, 가격 변동과 관련지을 수 있는 공개 자료를 확인하지 못했습니다.",
  "confidence": "low",
  "factors": [],
  "sources": [],
  "limitations": ["관련 공시·뉴스 검색 결과가 없어 요인을 도출할 수 없습니다."]
}
```

**Error (404)** — unknown ticker

```json
{ "detail": "Unknown ticker: 999999" }
```

**Error (400)** — ticker is known but has no price data for `selected_date` (e.g. a weekend,
or a date outside the currently-available range — 250 trading days/~1 year when `KRX_API_KEY`
is set, 30 for the offline mock fallback)

```json
{ "detail": "No price data for 005930 on 2020-01-01" }
```

---

## POST /api/analysis/date

Newer, separate endpoint (2026-07-22) powering the chart-point popover, the small summary card
under the chart, and the sidebar "오늘의 체크리스트" panel. Does not touch or replace
`/api/v1/explanations` above — that one still powers the SOLAR/Gemini toggle and "관련 자료"
list inside `MarketEventsPanel`. See `app/schemas/stock_analysis.py` for the full Pydantic
models and CLAUDE.md section 10 for the full design writeup.

**Request schema**

```
{ "ticker": string, "selected_date": "YYYY-MM-DD" }
```

**Response schema** (abridged — see `app/schemas/stock_analysis.py` for exact field types/enums)

```
{
  "analysis": {
    "chart_card": {
      "selected_date": string, "price_change_text": string, "one_line_summary": string,
      "quick_facts": [{ "label": string, "value": string }],       // max 2
      "primary_evidence": { "label": string, "source_id": string } | null
    },
    "detail_panel": {
      "why_it_moved": [{ "title", "description", "status", "evidence_type", "evidence_level",
                          "source_ids": [string] }],                // max 2
      "what_to_watch": [{ "title", "description", "signal_type", "source_ids": [string] }],  // max 3
      "recommended_materials": [{ "source_id", "description",
                                    "information_to_verify": [string] }],  // max 2, topics max 3
      "caution": string
    }
  },
  "sources": { "<source_id>": { "source_id", "source_type", "title", "url", "publisher", "published_at" } }
}
```

Provider is fixed by env var `LLM_PROVIDER` (default `solar`) — no per-request field, no
user-facing toggle yet (see `app/services/llm/factory.py`). Every LLM-produced field is
re-validated against the backend-built candidates before being returned (source_ids must exist
in the input context, `quick_facts`/`what_to_watch` must exactly match a candidate,
`information_to_verify` must be a subset of that source's `available_topics`) — anything that
doesn't match is dropped, never trusted as-is. On repeated validation failure or no
disclosures/news at all for the date, falls back to a deterministic response built directly
from the backend candidates (no LLM call).

**Errors**: same 404 (`Unknown ticker`) / 400 (`No price data for ...`) shape as
`/api/v1/explanations` above.
