# GCP One-Time Setup

These steps are not automated by CI/CD and must be run once per GCP project before
`.github/workflows/deploy.yml` can succeed. See [../docs/deployment.md](../docs/deployment.md)
for the full walkthrough; this file is the quick command reference.

## 1. Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  secretmanager.googleapis.com \
  --project "$GCP_PROJECT_ID"
```

## 2. Create the Artifact Registry repository

```bash
gcloud artifacts repositories create stock-lens \
  --repository-format=docker \
  --location="$GCP_REGION" \
  --project "$GCP_PROJECT_ID"
```

## 3. Set up Workload Identity Federation

Create a Workload Identity Pool + Provider trusted by this GitHub repository, and a deploy
service account impersonated via that provider. No service account JSON key is created or
stored — GitHub Actions authenticates via OIDC (`google-github-actions/auth@v2`).

## 4. Create Secret Manager secrets

```bash
printf '%s' "$SOLAR_API_KEY" | gcloud secrets create SOLAR_API_KEY --data-file=- --project "$GCP_PROJECT_ID"
printf '%s' "$GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=- --project "$GCP_PROJECT_ID"
printf '%s' "$DART_API_KEY" | gcloud secrets create DART_API_KEY --data-file=- --project "$GCP_PROJECT_ID"
```

Grant the backend Cloud Run runtime service account `roles/secretmanager.secretAccessor` on
all three secrets. `DART_API_KEY` is the one actually in use today (SOLAR/GEMINI are still
unused placeholders) — see `docs/deployment.md` for a packaging gap around it (the DART
disclosure snapshot isn't in the deploy image yet).

## 5. Configure GitHub Repository Variables

See [../docs/deployment.md](../docs/deployment.md) for the full list of required variables.
