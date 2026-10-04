# Setup

## Tools

| Tool | Version used | Install |
|---|---|---|
| uv | 0.12.23 | `curl -LsSf https://astral.sh/uv/install.sh \| sh`, update with `uv self update` |
| Python | 3.14.8 | uv installs it automatically from `.python-version` |
| Terraform | 1.16.5 | [Install guide](https://developer.hashicorp.com/terraform/install). This laptop has it in `~/.local/bin`, which comes before `/usr/local/bin` on the PATH. |
| gcloud CLI | any recent | [Install guide](https://cloud.google.com/sdk/docs/install) |
| pre-commit | latest | `uv tool install pre-commit`, then `pre-commit install` at the AgenticCraft root |

## Google Cloud sign-in

gcloud needs two separate sign-ins:

```bash
gcloud auth login                                   # for the gcloud CLI itself
gcloud auth application-default login               # for Terraform and the Python SDKs
gcloud auth application-default set-quota-project <project-id>
gcloud config set project <project-id>
```

## Project

- The demo uses `oceanhub-dev`, set as `GOOGLE_CLOUD_PROJECT` in `.env`.
- Billing must be linked (Gemini on the Agent Platform, Secret Manager and Part 2 all need it). Check with `gcloud billing projects describe <project-id>`. `oceanhub-dev` is linked to My Billing Account.
- To run Terraform you need Owner, or Editor plus Project IAM Admin.

## `.env`

Created by `./demo.sh setup` from `.env.example`, and never committed (gitignored, and blocked by a pre-commit hook).

| Variable | Needed for | Set by |
|---|---|---|
| `GEMINI_SECRET_ID` | Optional AI Studio route: Secret Manager secret with a Gemini API key | defaults to `gemini-api-key` |
| `GEMINI_API_KEY` | Optional AI Studio route: local copy of the key. Not used by the demo code. | `./demo.sh api-key` |
| `GOOGLE_CLOUD_PROJECT` | Terraform, Part 2 | you |
| `GOOGLE_CLOUD_LOCATION` | Terraform, Part 2 | defaults to `europe-west1` |
| `TF_STATE_BUCKET` | Terraform state bucket | defaults to `<project>-tfstate`. This project uses `oceanhub-dev-tfstate`. |

## First run, in order

```bash
./demo.sh setup        # uv sync, create .env
# edit .env: GOOGLE_CLOUD_PROJECT
./demo.sh tf-bootstrap # once per project: GCS bucket for Terraform state
./demo.sh test         # offline tests
./demo.sh mlflow-ui    # second terminal, http://localhost:5000
./demo.sh part1        # traces + MLflow evaluation

# Part 2, billing on
./demo.sh infra-up     # shows the plan, asks before applying
./demo.sh deploy       # several minutes
./demo.sh traces
./demo.sh part2

# afterwards
./demo.sh infra-down   # agent, bucket, service account and API key
```

## Terraform state

- Both stacks use a GCS backend in `gs://<TF_STATE_BUCKET>`, one prefix each: `agenticcraft/evaluating-traces/gemini_api_key` and `agenticcraft/evaluating-traces/agent_platform`.
- `scripts/bootstrap-terraform-state.sh` creates the bucket with versioning, uniform access and public access prevention. It runs outside Terraform because a backend cannot create itself, and it is safe to re-run.
- `scripts/terraform-init.sh <stack>` runs `terraform init` with the bucket and prefix. `demo.sh` and the key script always go through it.
- To roll back a bad apply, restore an older version of `default.tfstate` from the bucket (`gcloud storage ls -a gs://<bucket>/agenticcraft/evaluating-traces/<stack>/`).
- The GCS backend locks state during runs, so two people cannot apply at once.

## CI access to Google Cloud

The `evals` CI job calls Gemini on the Agent Platform, so it needs a Google Cloud identity. It uses Workload Identity Federation (no keys) and is skipped until these repository variables exist:

```bash
gh variable set GCP_PROJECT_ID --body oceanhub-dev
gh variable set GCP_WORKLOAD_IDENTITY_PROVIDER --body projects/<number>/locations/global/workloadIdentityPools/<pool>/providers/<provider>
gh variable set GCP_SERVICE_ACCOUNT --body <ci-sa>@oceanhub-dev.iam.gserviceaccount.com
```

Creating the pool, provider and CI service account (with `roles/aiplatform.user`) is on the [roadmap](roadmap.md).
