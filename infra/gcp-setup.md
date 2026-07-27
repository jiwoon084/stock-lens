# GCE One-Time Setup

These steps are not automated by CI/CD and must be run once before `.github/workflows/deploy.yml`
can succeed. See [../docs/deployment.md](../docs/deployment.md) for the full reasoning (why
port 80 only, why the backend isn't exposed directly, why `.env`/`data/` live on the VM instead
of in the pipeline); this file is the quick command reference.

## 1. Confirm the VM

```bash
ssh <username>@<vm-external-ip> "docker --version && docker compose version"
```

Reused from an earlier course project's VM — Docker and the Compose plugin are already there.
Only port 80, port 8000 (already used by that project's own container), and 22 are open at the
firewall.

## 2. Place the compose file, env, and data on the VM

```bash
ssh <username>@<vm-external-ip> "mkdir -p ~/stock-lens/data"
scp infra/gce/docker-compose.yml <username>@<vm-external-ip>:~/stock-lens/docker-compose.yml
scp .env <username>@<vm-external-ip>:~/stock-lens/.env   # real values, based on infra/gce/.env.example's shape
scp data/*.json <username>@<vm-external-ip>:~/stock-lens/data/
```

## 3. Register GitHub repository Secrets

```bash
gh secret set GCE_HOST --body "<vm-external-ip>"
gh secret set GCE_USERNAME --body "<username>"
gh secret set GCE_SSH_KEY < path/to/private_key
```

## 4. First deploy + make GHCR packages public

Push to `main` (or `gh workflow run deploy.yml`) once. This creates the
`stock-lens-backend`/`stock-lens-frontend` GHCR packages under the repo owner. Then, on GitHub
(profile → Packages → each package → Package settings → Danger Zone), set visibility to
**Public** so the VM can `docker compose pull` without its own registry credential. Every deploy
after that is just a push to `main`.
