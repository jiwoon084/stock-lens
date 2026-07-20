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

Returns a mock movement-explanation response, shaped identically to what a future
SOLAR/Gemini-backed response will return (see `app/services/llm_service.py` and
`app/prompts/explain_movement.txt`).

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

**Success (200)**

```json
{
  "ticker": "005930",
  "selected_date": "2026-07-15",
  "price": 84200,
  "change_percent": 3.42,
  "volume_change_percent": 81.3,
  "direction": "up",
  "headline": "실적 기대와 외국인 매수세가 주요 관련 요인으로 분석됩니다.",
  "summary": "선택 시점 전후의 공개 자료를 종합하면 실적 기대와 반도체 업황 개선 전망이 상승과 관련된 주요 요인으로 확인됩니다.",
  "confidence": "medium",
  "factors": [
    {
      "title": "실적 기대 상승",
      "impact": "positive",
      "description": "시장 전망치를 상회할 수 있다는 기대가 관련 기사에서 언급되었습니다.",
      "source_ids": ["source-1", "source-2"]
    }
  ],
  "sources": [
    {
      "id": "source-1",
      "type": "news",
      "title": "삼성전자 실적 전망 관련 기사",
      "publisher": "샘플 언론사",
      "published_at": "2026-07-15T09:20:00+09:00",
      "url": "https://example.com",
      "excerpt": "실적 개선 기대가 확대되고 있다는 내용입니다."
    }
  ],
  "limitations": ["공개 자료만으로 가격 변동의 직접적인 인과관계를 확정할 수 없습니다."]
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
