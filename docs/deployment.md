# Deployment

`.github/workflows/deploy.yml` builds both Docker images, pushes them to GitHub Container
Registry (GHCR), then SSHes into a GCE VM to pull and restart them via
`infra/gce/docker-compose.yml`. Not Cloud Run — the team decided early on to reuse the GCE VM
from a previous course project (MathMate) rather than stand up Cloud Run + Workload Identity
Federation, but `deploy.yml` stayed Cloud Run boilerplate for a while before this was actually
implemented. Command reference lives in `infra/gcp-setup.md`.

## 1. The VM

One VM (`ai-assistant`, `asia-northeast3-c`) already runs one other course project's container
(`lumi-agent`, bound to host port 8000) — this deploy must not collide with that. Docker and the
Compose plugin are already installed on it (reused from that project).

**Firewall**: only port 80 (HTTP), port 8000 (already used by `lumi-agent`), and 22 (SSH) are
open — confirmed empirically (`curl` to 80 gets "connection refused" = firewall lets the packet
through but nothing's listening yet; `curl` to 8001/443 times out = firewall drops it). This
project's backend is therefore **not exposed on its own port at all** — see "Single port,
proxied" below.

## 2. Single port, proxied (not two open ports)

Because only port 80 is open, the two services can't each get their own external port the way
the local `compose.yaml` does. Instead:

- The backend container binds `127.0.0.1:8001:8080` on the VM — reachable only from the VM
  itself (for the health check step in `deploy.yml`, or manual debugging over SSH), never from
  the internet.
- The frontend image is built with `VITE_API_BASE_URL=` (empty/relative) instead of a real host,
  so the SPA calls `/api/...` on its own origin. `frontend/nginx.conf` proxies `location /api/`
  to `http://backend:8080` over the Compose network. One public port, no CORS to configure
  (same-origin), and the backend is never directly reachable from outside the VM.

## 3. `infra/gce/docker-compose.yml` and its `.env`

This file lives on the VM at `~/stock-lens/docker-compose.yml` — it's the same file committed
here, not something `deploy.yml` generates. `deploy.yml` only ever runs `docker compose pull &&
docker compose up -d` against it over SSH; it doesn't write or edit it.

It reads a `~/stock-lens/.env` on the VM (see `infra/gce/.env.example` for the shape) for the
non-secret `GHCR_OWNER`/`ALLOWED_ORIGINS`/`LLM_PROVIDER` and the actual API keys
(`SOLAR_API_KEY`, `GEMINI_API_KEY`, `DART_API_KEY`, `KRX_API_KEY`, `KIS_APP_KEY`,
`KIS_APP_SECRET`, `KIS_ACCOUNT_NO`). This `.env` is placed on the VM once, out of band (scp from
a local `.env` that already has real values) — `deploy.yml` never touches it, so rotating a key
means editing it on the VM and restarting the containers, not pushing to GitHub.

**Known gap, same as before**: `backend/Dockerfile` only copies `app/` — `data/disclosures.json`
etc. aren't baked into the image. `docker-compose.yml` mounts `./data:/app/data:ro` from the
VM's `~/stock-lens/data/`, which (like `.env`) is placed on the VM once, out of band (`scp` the
local `data/*.json` files up) and persists across deploys — `deploy.yml` doesn't touch it either.
Refreshing this data (e.g. after re-running `data/step2_disclosures.py` locally) is a manual
`scp` for now.

## 4. GHCR image visibility

`deploy.yml` authenticates to GHCR with the ephemeral `GITHUB_TOKEN` to *push* images — that
works automatically, no setup needed. But the VM needs to *pull* them too, and giving the VM its
own long-lived registry credential is one more secret to manage. Simpler: once the first push
creates the `stock-lens-backend`/`stock-lens-frontend` packages, set their visibility to
**Public** in GitHub → your profile → Packages → (each package) → Package settings. They're just
built artifacts (no secrets baked in — API keys are injected at container runtime via `.env`,
never at image-build time), so there's no real exposure from this.

## 5. GitHub repository Secrets

Set these under Settings → Secrets and variables → Actions → **Secrets**:

| Secret | Value |
|---|---|
| `GCE_HOST` | the VM's external IP (changes if the VM is ever recreated, not just stopped/started — see `.env`'s comment) |
| `GCE_USERNAME` | SSH username on the VM |
| `GCE_SSH_KEY` | private key matching a public key already in the VM's `~/.ssh/authorized_keys` |

That's the entire secret surface `deploy.yml` needs — no GCP service account, no Workload
Identity Federation, no Artifact Registry. The API keys live only in the VM's own `.env` (§3),
never in GitHub.

## 6. First-time VM setup (once, out of band — not automated)

1. Confirm Docker + Compose plugin are on the VM (`docker --version && docker compose version`).
2. `mkdir -p ~/stock-lens/data` on the VM.
3. `scp` `infra/gce/docker-compose.yml` to `~/stock-lens/docker-compose.yml`.
4. `scp` a real `.env` (based on `infra/gce/.env.example`, with actual keys) to
   `~/stock-lens/.env`.
5. `scp` the local `data/*.json` files to `~/stock-lens/data/`.
6. Make the two GHCR packages public (§4) after the first `deploy.yml` run creates them.
7. Push to `main` (or run `deploy.yml` via `workflow_dispatch`).

## 7. Rollback

Images are tagged with both `:latest` and `:${{ github.sha }}`. To roll back, SSH in and:

```bash
cd ~/stock-lens
docker compose pull  # or edit docker-compose.yml to pin an old :<sha> tag temporarily
docker compose up -d
```

There's no automated rollback step in `deploy.yml` — manual, same reasoning as the old Cloud Run
doc: not worth scripting until it's needed often enough to hurt.
