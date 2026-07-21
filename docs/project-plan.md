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
2. **M1 — Real market data — blocked/deferred**: tried `pykrx` for real KRX price series;
   confirmed (via direct calls) that KRX changed its access policy around 2026-04
   (`feat: add KRX login/session support` in pykrx's own history) and unauthenticated requests
   now return unreliable data or errors. `KRX_ID`/`KRX_PW` are personal KRX account credentials,
   not an API key — scripting logins with them is a real account-safety/ToS concern, so this
   was deliberately not pursued further. Price data stays Mock. Revisit only with either a
   sanctioned KRX account for this purpose or a different real price-data source — real-time
   price isn't actually required for the product goal (explaining moves from disclosures), so
   this is low priority.
3. **M2 — Real retrieval — mostly done, DART only**: `retrieval_service.py` no longer returns
   hardcoded sources.
   - `data/step1_corpcode.py` → `step2_disclosures.py` fetch real DART corp codes and ~3 months
     of disclosures per sample ticker into `data/disclosures.json` (one-time snapshot, no
     scheduled refresh — MVP decision).
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
   - **Not done**: 자기주식취득결정 has zero real occurrences in the current 5-ticker sample so
     its formatter is unverified; other DART event-specific APIs (배당결정, 회사분할, 소송 등)
     aren't wired at all. 뉴스 and 증권사 리서치 리포트 (한경 컨센서스 등) — tier 2 in the
     priority model above — are entirely unconnected; source selection (crawling vs. a news API)
     hasn't been decided.
4. **M3 — Real LLM — not started**: `llm_service.py` now receives real DART text/structured
   data, but the summarization and 호재/유의/중립 labeling are still rule-based (impact is
   inferred purely from the day's price direction, not from reading the content — this is a
   known, documented limitation, visible in the UI's own limitations list). Wiring SOLAR (via
   `langchain-upstage`) or Gemini using `app/prompts/explain_movement.txt`, gated by
   `LLM_PROVIDER`, is still ahead. `backend/app/agent/` holds an early LangGraph skeleton
   (`state.py`/`nodes.py`/`graph.py`, still TODO stubs) for this.
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
