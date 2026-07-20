# Project Plan

## Goal

Ship a working boilerplate for Stock Lens: a service where a user picks a sample stock, views
its price chart, clicks a date, and gets an AI-style explanation of the price movement around
that date. At this stage the priority is **structure and contracts**, not real AI — analysis is
returned by a mock service shaped exactly like the future real response.

## Scope for this iteration

In scope:
- Correct monorepo structure (frontend / backend / infra / docs / data / scripts)
- Mock-data-driven core interaction (stock select → chart → click → explanation)
- Frontend/backend API contract (snake_case at the boundary, matching types)
- Local execution via Docker Compose
- Dockerfiles structured for GCP Cloud Run
- GitHub Actions CI (lint/build/test/docker build) and CD skeleton (WIF-based deploy)

Out of scope (explicitly excluded):
- Login, sign-up, account linking, portfolio, orders, payments, admin pages
- Real news crawling, real RAG/retrieval, real LLM calls (SOLAR/Gemini)
- Terraform, Kubernetes, Redis, Celery, Kafka, PostgreSQL, an auth server

## Milestones

1. **M0 — Monorepo boilerplate (this iteration)**: structure, mock APIs, working local/Docker
   run, CI/CD skeleton. Done when `docker compose up --build` serves a clickable chart with a
   mock AI panel.
2. **M1 — Real market data**: replace `market_data_service.py`'s generator with a real price
   data source (see `scripts/prepare_market_data.py` for where a real fetch would plug in).
3. **M2 — Real retrieval**: replace `retrieval_service.py` with an actual document
   store/search (see `scripts/ingest_documents.py` and `data/samples/documents/`).
4. **M3 — Real LLM**: wire `llm_service.py` to SOLAR or Gemini using `app/prompts/explain_movement.txt`,
   gated by `LLM_PROVIDER`.
5. **M4 — GCP deployment**: complete the one-time setup in `infra/gcp-setup.md`, then let
   `.github/workflows/deploy.yml` run for real.

## Non-goals

Anything in "explicitly excluded" above is a non-goal for the foreseeable roadmap covered by
this document, not just this iteration, unless a future decision reopens it.
