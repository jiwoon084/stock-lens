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
  "interval": string   // e.g. "1d"; currently unused by the mock but part of the contract
}
```

**Request example**

```json
{ "ticker": "005930", "selected_date": "2026-07-15", "interval": "1d" }
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
  "headline": "관련 DART 공시 자료를 찾지 못했습니다.",
  "summary": "선택 시점(2026-07-17) 전후로 조회 가능한 DART 공시가 없어, 가격 변동과 관련지을 수 있는 공개 자료를 확인하지 못했습니다.",
  "confidence": "low",
  "factors": [],
  "sources": [],
  "limitations": [
    "DART 공시 검색 결과가 없어 요인을 도출할 수 없습니다.",
    "뉴스·리서치 리포트 등 다른 자료는 아직 연동되지 않았습니다."
  ]
}
```

**Error (404)** — unknown ticker

```json
{ "detail": "Unknown ticker: 999999" }
```

**Error (400)** — ticker is known but has no price data for `selected_date` (e.g. a weekend,
or a date outside the mock's 30-day window)

```json
{ "detail": "No price data for 005930 on 2020-01-01" }
```
