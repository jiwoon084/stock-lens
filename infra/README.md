# infra

This folder holds the GCE deployment setup: a reused VM (from an earlier course project) running
both containers via Docker Compose, not Cloud Run. See [gcp-setup.md](./gcp-setup.md) for the
one-time setup and [../docs/deployment.md](../docs/deployment.md) for the full reasoning.

- `gcp-setup.md` — one-time VM setup (placing the compose file/`.env`/data, registering GitHub
  Secrets, making the GHCR packages public).
- `gce/docker-compose.yml` — the actual file that lives on the VM at
  `~/stock-lens/docker-compose.yml`; `deploy.yml` only runs `docker compose pull && up -d`
  against it over SSH.
- `gce/.env.example` — shape of the `.env` that lives alongside it on the VM (placeholders only;
  real values are placed on the VM directly, never committed or passed through CI).
