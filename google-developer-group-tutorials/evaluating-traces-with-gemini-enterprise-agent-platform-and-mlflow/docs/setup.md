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
- Billing must be linked before `./demo.sh api-key` (Secret Manager requires it) and Part 2. Check with `gcloud billing projects describe <project-id>`, then link with `gcloud billing projects link <project-id> --billing-account=<id>`.
- To run Terraform you need Owner, or Editor plus Project IAM Admin.

## `.env`

Created by `./demo.sh setup` from `.env.example`, and never committed (gitignored, and blocked by a pre-commit hook).

| Variable | Needed for | Set by |
|---|---|---|
| `GEMINI_SECRET_ID` | Name of the Secret Manager secret with the Gemini key | defaults to `gemini-api-key` |
| `GEMINI_API_KEY` | Optional override. Leave empty to read from Secret Manager. | you, only if you want to skip Secret Manager (for example a project without billing) |
| `GOOGLE_CLOUD_PROJECT` | Terraform, Part 2 | you |
| `GOOGLE_CLOUD_LOCATION` | Terraform, Part 2 | defaults to `europe-west1` |

## First run, in order

```bash
./demo.sh setup        # uv sync, create .env
# edit .env: GOOGLE_CLOUD_PROJECT
./demo.sh api-key      # Gemini key in Secret Manager: reuse if it exists, else create
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

## Repository secret for CI

The `evals` CI job needs the key as a GitHub secret:

```bash
gh secret set GEMINI_API_KEY --repo ThamuMnyulwa/AgenticCraft
```
