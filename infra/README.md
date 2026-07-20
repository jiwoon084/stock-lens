# infra

This folder holds GCP-side setup notes and Cloud Run environment references. It does not
contain Terraform or any other infrastructure-as-code — resources are created manually or via
`gcloud`, following [gcp-setup.md](./gcp-setup.md) and [../docs/deployment.md](../docs/deployment.md).

- `gcp-setup.md` — one-time GCP project setup (APIs, Artifact Registry, Workload Identity
  Federation, Secret Manager).
- `cloud-run/` — example environment variable files for each Cloud Run service. These are
  references for what to configure in the Cloud Run console / `gcloud run deploy`, not files
  consumed automatically by any script.
