# Project Plan

## Goal

Ship a working boilerplate for Stock Lens: a service where a user picks a sample stock, views
its price chart, clicks a date, and gets an AI-style explanation of the price movement around
that date. The initial iteration prioritized **structure and contracts** over real AI — analysis
was returned by a mock service shaped exactly like the future real response. That structure phase
is done; the current phase is replacing the mock pieces with real data, DART first.

## Scope for the initial iteration (M0, done)

In scope:
- Correct monorepo structure (frontend / backend / infra / docs / data / scripts)
- Mock-data-driven core interaction (stock select → chart → click → explanation)
- Frontend/backend API contract (snake_case at the boundary, matching types)
- Local execution via Docker Compose
- Dockerfiles structured for GCP Cloud Run
- GitHub Actions CI (lint/build/test/docker build) and CD skeleton (WIF-based deploy)

Out of scope (explicitly excluded) at that time:
- Login, sign-up, account linking, portfolio, orders, payments, admin pages
- Real news crawling, real RAG/retrieval, real LLM calls (SOLAR/Gemini)
- Terraform, Kubernetes, Redis, Celery, Kafka, PostgreSQL, an auth server

The "no real retrieval" line has since been superseded for DART specifically — see M2 below.
Login/account/portfolio/payments/admin and the infra exclusions (Terraform/K8s/Redis/etc.) are
still non-goals with no plan to revisit them.

## Data source priority (decided)

When asked whether DART is credible enough and whether news/community sentiment should also
feed the analysis, the agreed tiering was:

1. **DART (사실)** — highest credibility, legally-mandated disclosure, primary source
2. **뉴스 / 증권사 리서치 리포트 (해석)** — lower credibility than DART but fills the "왜 시장이
   반응했는지" gap DART alone doesn't answer
3. **커뮤니티 여론** — explicitly **not** included; noise risk conflicts with the "누락 없이
   정확하게" goal. Revisit only if there's a specific reason to add a clearly-labeled
   "시장 반응/화제성" signal, never blended into "원인" as if it were fact.

## Milestones

1. **M0 — Monorepo boilerplate — done**: structure, mock APIs, working local/Docker run, CI/CD
   skeleton.
2. **M1 — Real market data — done, via data.go.kr**: `pykrx` was tried first and
   deferred (see below); resumed instead with **금융위원회_주식시세정보**
   (`GetStockSecuritiesInfoService/getStockPriceInfo` on data.go.kr) — a proper service-key API,
   not a personal-account login, so the ToS/account-safety concern that blocked `pykrx` doesn't
   apply here.
   - `app/services/krx_price_client.py` calls the API live per request (`beginBasDt`/`endBasDt`
     date-range query by `likeSrtnCd`), with an in-process `lru_cache` keyed by
     (ticker, today's date) so repeated requests on the same day don't re-hit the API. Unlike
     DART's disclosures (historical facts, fetched once into `data/disclosures.json` — see M2),
     daily prices change every trading day, so a one-time snapshot would just be another frozen
     mock; this is deliberately *not* a `data/step*.py` snapshot script.
   - `market_data_service.get_price_series()` tries the real client only when `KRX_API_KEY` is
     set, and falls back to the existing deterministic mock generator
     (`_generate_mock_price_series`) on any failure (missing key, network error, unexpected
     response shape, non-`"00"` `resultCode`) — this is an intentional difference from DART's
     "honest empty result" pattern: an empty price series breaks the chart entirely, whereas
     mock prices keep the product usable while still being obviously a placeholder.
   - Old `pykrx` finding, still true and why it wasn't reused: KRX changed its access policy
     around 2026-04 (`feat: add KRX login/session support` in pykrx's own history) and
     unauthenticated requests now return unreliable data or errors; `KRX_ID`/`KRX_PW` are
     personal KRX account credentials, not an API key, so scripting logins with them was
     deliberately not pursued.
   - **Verified 2026-07-21** against a real `KRX_API_KEY`: `srtnCd`/`itmsNm` in the response
     match the requested ticker exactly (e.g. `005930`/`삼성전자`, no `likeSrtnCd` over-matching),
     and `krx_price_client.py`'s field mapping (`basDt`/`mkp`/`hipr`/`lopr`/`clpr`/`fltRt`/`trqu`/
     `mrktCtg`) parses real responses correctly end to end through
     `GET /api/v1/stocks/{ticker}/prices`.
3. **M2 — Real retrieval — done, DART + Naver News**: `retrieval_service.py` no longer returns
   hardcoded sources.
   - `data/step1_corpcode.py` → `step2_disclosures.py` fetch real DART corp codes and ~1 year of
     disclosures per sample ticker into `data/disclosures.json` (one-time snapshot, chunked by
     90-day windows with pagination since Open DART limits both, no scheduled refresh — MVP
     decision).
   - `retrieval_service.py` ranks disclosures by date-proximity to the selected date, with
     routine/administrative filing types (e.g. individual executives reporting personal trades)
     deprioritized — not discarded.
   - Body text: DART's `document.xml` is fetched live per disclosure and parsed (DART's own
     dart4.xsd XML, skipping the COVER boilerplate; falls back to lenient HTML tag-stripping for
     filing types that come back as plain HTML instead — both observed in real data).
   - Structured fields: `data/step3_major_events.py` fetches DART's dedicated structured APIs
     (`tsstkDpDecsn` 자기주식처분결정, `piicDecsn` 유상증자결정) for the two event types that
     appeared in the real sample data; those give clean labeled fields (처분목적/처분가액,
     증자방식/신주수 등) and take priority over the raw-text excerpt when available.
   - **뉴스 연동 완료**: `data/step5_news.py`가 네이버 뉴스 검색 API로 종목별 실제 기사를
     `data/news.json`에 저장 (`NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET` 필요, 없으면 스크립트만
     못 돌리는 것이고 서비스 자체는 안 죽음). `retrieval_service.get_related_documents()`가
     공시(최대 `DISCLOSURE_SLOTS`=3자리 우선)와 뉴스를 합쳐서 최대 5건을 반환 — 한쪽이 모자라면
     다른 쪽이 채움.
   - **Not done**: 자기주식취득결정 has zero real occurrences in the current 5-ticker sample so
     its formatter is unverified; other DART event-specific APIs (배당결정, 회사분할, 소송 등)
     aren't wired at all. 증권사 리서치 리포트(한경 컨센서스 등)는 여전히 미연동.
4. **M3 — Real LLM — done, SOLAR + Gemini (user-selectable)**: `llm_service.py` dispatches on a
   per-request `llm_provider` field (`"solar"` | `"gemini"`, default `"solar"`) — see
   `app/services/solar_client.py` / `gemini_client.py`. Both call their provider's native REST
   API directly with `requests` (no SDK) and enforce a JSON-schema-constrained response, so the
   model's output always parses into `Factor`/`limitations` cleanly. **A parallel branch has
   twice tried an automatic difficulty-based/fallback routing scheme instead (most recently
   2026-07-22) — deliberately reverted both times, most recently confirmed directly with the
   user in the same session that built the feature below.** See CLAUDE.md section 9 before
   touching this again — this has now flip-flopped three times and the team needs to sync in
   person before it changes a fourth. If a per-request pick is ever not enough (e.g. need
   automatic retry across providers), the auto-routing branch's `_providers_for()` pattern is
   preserved in git history (`e258fd0`/`2de919d`/`6a290b4` and later reverts) as a starting point.
   - Falls back to a deterministic, source-grounded rule-based response (each factor built from
     an actual retrieved document's title/excerpt, not templated text) if the chosen provider's
     key is missing, or the call fails for any reason — verified by unit tests
     (`test_solar_client.py`, `test_gemini_client.py`, `test_llm_service.py`) that never hit the
     network, plus real end-to-end calls against both providers (see below).
   - **Verified against real keys, both providers**: SOLAR via `solar-pro2`
     (`https://api.upstage.ai/v1/chat/completions`, OpenAI-compatible). Gemini required two
     rounds of empirical fixing — a freshly created API key 404'd on the dated model name
     `gemini-2.5-flash` ("no longer available to new users"), and separately a different key hit
     429 "prepayment credits are depleted" on `gemini-3.5-flash` (that model is paid-only, not on
     the free tier). `gemini-flash-latest` (a Google-maintained alias that always points at their
     current free-tier Flash model) resolved both — see `gemini_client.py` docstring.
   - Anti-hallucination: `app/prompts/explain_movement.txt` tags every retrieved document with
     its real `[id]` and instructs the model to only cite ids it was actually shown; `llm_service.
     _sanitize_factors()` additionally strips any cited id that doesn't match a real source as a
     backstop, in case a model ignores the instruction.
   - `backend/app/agent/` held an early, untouched LangGraph skeleton until 2026-07-23 — see
     M3.6 below, it's no longer a stub.
4b. **M3.5 — separate `POST /api/analysis/date` endpoint (2026-07-22)**: powers a chart-point
    popover, a small summary card under the chart, and the "오늘의 체크리스트" sidebar panel —
    see `docs/api-spec.md` and CLAUDE.md section 10. Has its own provider layer
    (`app/services/llm/`) fixed by env var `LLM_PROVIDER` (no user-facing toggle yet); completely
    independent of the M3 dispatcher above, do not conflate the two when resolving future merges.
4c. **M3.6 — semantic retrieval + LangGraph pipeline (2026-07-23)**: `retrieval_service.py`
    reranks candidates by a date-proximity + SOLAR-embedding-similarity hybrid score
    (`app/services/embedding_client.py`, `solar-embedding-1-large-query`/`-passage`), falling
    back to the original date-only order when `SOLAR_API_KEY` is unset or a call fails.
    `stock_analysis_service.analyze_date()` now builds and runs the previously-unused
    `app/agent/` LangGraph skeleton (`fetch_market_data` → `retrieve_evidence` →
    `build_llm_input` → `generate_analysis`) instead of one procedural function — each node
    wraps existing, still-independently-tested helpers, so no business logic moved. See
    CLAUDE.md section 11 and `docs/architecture.md`. Still open: `explain()`/`analyze()` still
    call retrieval and the LLM independently (no dedup), and the graph has no branching/retry
    policy beyond what `_generate_result()` already did.
5. **M4 — GCP deployment — not started**: complete the one-time setup in `infra/gcp-setup.md`,
   then let `.github/workflows/deploy.yml` run for real. Now also needs `DART_API_KEY` in Secret
   Manager (same pattern as SOLAR/GEMINI) and confirmation that the Cloud Run backend has
   outbound internet access, since M2 made the backend call out to DART live per request.

Separately, the frontend UI was redesigned (2-column layout: ticker header + chart with a
click-anchored popover on the left, a checklist-style panel — checkboxes, impact tags, expandable
sources, read-progress — on the right) to match a product mockup. This was a presentation-layer
change only; it consumes the same API contract and rides on whatever M1–M3 currently provide.
See `docs/screen-design.md` for the current layout.

## Non-goals

Login/account/portfolio/orders/payments/admin pages, and the infra exclusions (Terraform,
Kubernetes, Redis, Celery, Kafka, PostgreSQL, an auth server) remain non-goals for the
foreseeable roadmap, not just one iteration, unless a future decision reopens them. Community
sentiment as a "cause" source is also a deliberate non-goal (see priority model above).
