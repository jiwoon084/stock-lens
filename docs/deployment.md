# Deployment

`.github/workflows/deploy.yml` cannot run successfully yet — it needs a GCP project and GitHub
repository variables that don't exist by default. This document lists what to set up once,
and the order to do it in. Command reference lives in `infra/gcp-setup.md`.

## 1. Enable GCP APIs

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  iamcredentials.googleapis.com secretmanager.googleapis.com --project "$GCP_PROJECT_ID"
```

## 2. Create the Artifact Registry repository

One Docker repository holds both images (`backend`, `frontend`), tagged by name inside it:

```bash
gcloud artifacts repositories create stock-lens --repository-format=docker \
  --location="$GCP_REGION" --project "$GCP_PROJECT_ID"
```

## 3. Reserve the two Cloud Run services

`stock-lens-web` and `stock-lens-api` are created by the first successful `gcloud run deploy`
in `deploy.yml` — there's no separate manual creation step, but the service account running
the deploy needs `roles/run.admin` in advance.

## 4. Set up Workload Identity Federation

No service account JSON key is ever created or stored. Instead:

1. Create a Workload Identity Pool and an OIDC provider trusted for this specific GitHub repo
   (restrict to `repository == "<org>/stock-lens"` at minimum).
2. Create a deploy service account (e.g. `stock-lens-deployer@$GCP_PROJECT_ID.iam.gserviceaccount.com`)
   with `roles/run.admin`, `roles/artifactregistry.writer`, and `roles/iam.serviceAccountUser`
   (to act as the backend runtime service account below).
3. Allow the Workload Identity provider to impersonate that service account.
4. Note the full provider resource name and service account email — they become
   `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_DEPLOY_SERVICE_ACCOUNT` below.

## 5. Create a backend runtime service account + Secret Manager secrets

```bash
gcloud iam service-accounts create stock-lens-api-runtime --project "$GCP_PROJECT_ID"

printf '%s' "$SOLAR_API_KEY" | gcloud secrets create SOLAR_API_KEY --data-file=- --project "$GCP_PROJECT_ID"
printf '%s' "$GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=- --project "$GCP_PROJECT_ID"
printf '%s' "$DART_API_KEY" | gcloud secrets create DART_API_KEY --data-file=- --project "$GCP_PROJECT_ID"
printf '%s' "$KRX_API_KEY" | gcloud secrets create KRX_API_KEY --data-file=- --project "$GCP_PROJECT_ID"

gcloud secrets add-iam-policy-binding SOLAR_API_KEY \
  --member="serviceAccount:stock-lens-api-runtime@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" --project "$GCP_PROJECT_ID"
# repeat for GEMINI_API_KEY, DART_API_KEY, and KRX_API_KEY
```

Real keys are never committed — only `SOLAR_API_KEY=` / `GEMINI_API_KEY=` / `DART_API_KEY=` /
`KRX_API_KEY=` placeholders exist in `.env.example`, and `deploy.yml` injects them via
`--set-secrets`, not plain env vars.

**All four are actually used today** — `DART_API_KEY`/`KRX_API_KEY` for real disclosures/prices
(`app/services/retrieval_service.py`, `app/services/krx_price_client.py`), and
`SOLAR_API_KEY`/`GEMINI_API_KEY` for the real SOLAR/Gemini call the frontend's
`LlmProviderToggle` picks per-request in `app/services/llm_service.py` (M3, see
`docs/project-plan.md`; CLAUDE.md section 9 — not automatic routing, don't "fix" this without
reading that section first). Every one of them degrades gracefully if missing:
`/api/v1/explanations` falls back to a rule-based/mock response, `/api/v1/stocks/{ticker}/prices`
falls back to mock prices — nothing 500s on a missing key. The newer `POST /api/analysis/date`
(CLAUDE.md section 10) reuses the same `SOLAR_API_KEY`/`GEMINI_API_KEY` secrets but picks a
provider from env var `LLM_PROVIDER` instead of a per-request field.

**Known gap**: `backend/Dockerfile` only copies `app/` into the image — `data/disclosures.json`
(the DART snapshot) is not baked in, and there's no volume mount in production the way
`compose.yaml` mounts `./data` locally. Until that's addressed, a Cloud Run deploy of the
current backend will have `DART_API_KEY` working for live per-request calls (document body,
structured events) but no disclosure *list* to rank against, so it'll behave like the "no
related disclosures found" case for every request. Decide how the snapshot ships (bake into the
image at build time, a mounted volume/GCS bucket, or move list-fetching to be live too) before
relying on this in a real deployment.

## 6. GitHub Repository Variables

Set these under Settings → Secrets and variables → Actions → **Variables** (not Secrets —
none of these are credentials; auth is via WIF):

| Variable | Example |
|---|---|
| `GCP_PROJECT_ID` | `stock-lens-prod` |
| `GCP_REGION` | `asia-northeast3` |
| `GCP_ARTIFACT_REPOSITORY` | `stock-lens` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/123/locations/global/workloadIdentityPools/gh/providers/gh-provider` |
| `GCP_DEPLOY_SERVICE_ACCOUNT` | `stock-lens-deployer@stock-lens-prod.iam.gserviceaccount.com` |
| `FRONTEND_SERVICE_NAME` | `stock-lens-web` |
| `BACKEND_SERVICE_NAME` | `stock-lens-api` |
| `BACKEND_PUBLIC_URL` | `https://stock-lens-api-xxxxx.a.run.app` |
| `BACKEND_RUNTIME_SERVICE_ACCOUNT` | `stock-lens-api-runtime@stock-lens-prod.iam.gserviceaccount.com` |
| `ALLOWED_ORIGINS` | `https://stock-lens-web-xxxxx.a.run.app` |

## 7. First deploy order

`BACKEND_PUBLIC_URL` doesn't exist until the backend has deployed once, and frontend build
needs it as a build arg. So the very first deploy is a two-pass process:

1. Run `deploy.yml` once (`workflow_dispatch` is fine) with `BACKEND_PUBLIC_URL` left blank or
   pointed at a placeholder — this creates `stock-lens-api` and prints its real `*.a.run.app` URL.
2. Set `BACKEND_PUBLIC_URL` to that real URL, and update backend's `ALLOWED_ORIGINS` variable
   to the frontend's real URL once it exists (same chicken-and-egg — frontend URL is also only
   known after its first deploy).
3. Re-run `deploy.yml`. From then on, every push to `main` redeploys both with the same URLs.

## 8. CORS

The backend reads `ALLOWED_ORIGINS` (comma-separated) at startup (`app/core/config.py`) and
passes it to `CORSMiddleware`. Locally this is `http://localhost:5173`. In Cloud Run it must be
the frontend's `*.a.run.app` URL — a mismatch here is the most common cause of a working
`curl` but a broken browser fetch.

## 9. Rollback

Cloud Run keeps every revision. To roll back:

```bash
gcloud run services update-traffic stock-lens-api --to-revisions=<previous-revision>=100 \
  --region "$GCP_REGION" --project "$GCP_PROJECT_ID"
```

Because images are tagged with `${{ github.sha }}`, redeploying an old commit's image is also
just `gcloud run deploy <service> --image ...backend:<old-sha>`. There is no automated
rollback step in `deploy.yml` — it's a manual `gcloud` command until that's needed often
enough to script.
