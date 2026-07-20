# Architecture

## Runtime request flow

```mermaid
flowchart LR
    Browser["사용자 브라우저"]
    Web["Cloud Run: stock-lens-web (Nginx + React SPA)"]
    Api["Cloud Run: stock-lens-api (FastAPI)"]
    LLM["SOLAR / Gemini (not yet wired — mock today)"]
    Docs["문서 데이터 (news / disclosures / reports — mock today)"]

    Browser -->|HTTPS| Web
    Browser -->|HTTPS, VITE_API_BASE_URL| Api
    Api --> LLM
    Api --> Docs
```

Today, the "LLM" and "문서 데이터" boxes are `app/services/llm_service.py` and
`app/services/retrieval_service.py` returning hardcoded mock data — no outbound network calls
happen from the backend yet. The diagram shows the target shape once M2/M3 in
`docs/project-plan.md` land.

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
