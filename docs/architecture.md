# Architecture

## Runtime request flow

```mermaid
flowchart LR
    Browser["사용자 브라우저"]
    Web["Cloud Run: stock-lens-web (Nginx + React SPA)"]
    Api["Cloud Run: stock-lens-api (FastAPI)"]
    LLM["SOLAR / Gemini (not yet wired — mock today)"]
    Dart["DART Open API (실제 — 공시목록/본문/구조화 이벤트)"]
    Krx["data.go.kr 금융위원회_주식시세정보 (실제 — 있으면 사용, 없으면 mock)"]
    News["뉴스 / 증권사 리서치 리포트 (not yet wired — mock today)"]

    Browser -->|HTTPS| Web
    Browser -->|HTTPS, VITE_API_BASE_URL| Api
    Api --> LLM
    Api -->|실시간 호출, DART_API_KEY 필요| Dart
    Api -->|실시간 호출, KRX_API_KEY 있으면 사용| Krx
    Api --> News
```

`app/services/retrieval_service.py`는 이제 목업이 아니라 **실제 DART 데이터**를 쓴다: 종목별
공시 목록은 `data/step1_corpcode.py`/`step2_disclosures.py`로 미리 받아둔 스냅샷(`data/disclosures.json`,
약 3개월치, 재실행 스케줄 없음)이고, 요청이 들어올 때마다 그중 선택 날짜와 가까운 공시에 대해
DART의 `document.xml`(본문) 또는 구조화 이벤트 API(`tsstkDpDecsn`/`piicDecsn`, `data/step3_major_events.py`)를
실시간으로 호출한다. 즉 백엔드는 이제 요청 경로에서 실제로 외부(DART)로 나간다 — Cloud Run에
배포할 때 아웃바운드 네트워크와 `DART_API_KEY`(Secret Manager)가 필요하다.

`app/services/market_data_service.py`도 마찬가지로 `KRX_API_KEY`가 설정돼 있으면
`app/services/krx_price_client.py`를 통해 data.go.kr의 금융위원회_주식시세정보를 요청마다
실시간으로 호출한다 (같은 날 반복 호출은 in-process `lru_cache`로 막음). DART 공시 스냅샷과
달리 일별 시세는 매일 바뀌는 데이터라 스냅샷 방식이 맞지 않아 미리 받아두지 않는다. 키가
없거나 호출이 실패하면 예외 없이 mock 시세로 폴백한다 — DART처럼 "빈 결과"가 아니라 mock으로
폴백하는 이유는, 차트가 아예 빈 상태가 되는 것보다 그럴듯한 mock 시세가 더 나은 제품 상태이기
때문이다.

반면 `app/services/llm_service.py`(요약/호재·유의 판단)와 뉴스/컨센서스는 여전히 mock/미연동이다
— llm_service는 실제 DART 공시 텍스트를 받아서 조합하지만, 그 조합·판단 로직 자체는 규칙 기반이고
실제 LLM 호출은 없다. 이 부분이 M3(및 뉴스 연동)의 남은 범위다 — `docs/project-plan.md` 참고.

## Deployment pipeline

```mermaid
flowchart LR
    Dev["Developer push to main"]
    GHA["GitHub Actions"]
    AR["Artifact Registry (stock-lens repo)"]
    CRWeb["Cloud Run: stock-lens-web"]
    CRApi["Cloud Run: stock-lens-api"]

    Dev --> GHA
    GHA -->|docker build/push backend & frontend, tag=github.sha| AR
    AR -->|gcloud run deploy| CRWeb
    AR -->|gcloud run deploy| CRApi
    GHA -.->|Workload Identity Federation, no JSON keys| AR
```

`ci.yml` runs lint/build/test/docker-build on every PR and push to `main`, but never deploys.
`deploy.yml` is the only workflow that pushes images and deploys, and only runs on push to
`main` or manual `workflow_dispatch`. See `docs/deployment.md` for what must be configured
before `deploy.yml` can succeed.

## Backend internal layering

```mermaid
flowchart TD
    Routes["api/routes/* (HTTP only)"]
    Schemas["schemas/* (Pydantic request/response models)"]
    Services["services/* (market data, retrieval, LLM, explanation orchestration)"]
    Config["core/config.py (env vars)"]

    Routes --> Schemas
    Routes --> Services
    Services --> Config
```

`explanation_service.explain_movement()` is the only place that calls `market_data_service`,
`retrieval_service`, and `llm_service` together — routes never call more than one service
directly, and never contain business logic themselves.

## Stock-analysis pipeline (POST /api/analysis/date)

`stock_analysis_service.analyze_date()` no longer runs this as one procedural function — it
builds and invokes a LangGraph `StateGraph` (`app/agent/graph.py`) with four sequential nodes
(`app/agent/nodes.py`, state shape in `app/agent/state.py`):

```mermaid
flowchart LR
    A["fetch_market_data"] --> B["retrieve_evidence"] --> C["build_llm_input"] --> D["generate_analysis"]
```

Each node is a thin wrapper around helpers that already lived in `stock_analysis_service.py`
(and stay there, unit-tested directly) — the graph adds explicit orchestration, not new
business rules. `TickerNotFoundError`/`DateNotFoundError` raised inside `fetch_market_data`
propagate out of `graph.invoke()` and are translated back to `UnknownTickerError`/
`UnknownDateError` at the `analyze_date()` boundary, so the HTTP-level 404 behavior is
unchanged.

`retrieve_evidence` calls `retrieval_service.get_related_documents()`, which now ranks
candidates by a **date + semantic-similarity hybrid score** instead of date proximity alone:
the selected date's price movement is turned into a short query string, embedded via
Upstage's `solar-embedding-1-large-query` model, and compared (cosine similarity) against each
disclosure/news candidate's title embedded via `solar-embedding-1-large-passage`
(`app/services/embedding_client.py`). This lets a semantically relevant but older disclosure
outrank a closer-dated but unrelated one — see `backend/tests/test_retrieval_service.py`.
Routine disclosures (`_is_routine`) are still deprioritized ahead of any ranking. If
`SOLAR_API_KEY` is unset or the embedding call fails, ranking falls back to the exact original
date-only order — same fallback philosophy as `market_data_service`/`llm_service`.
