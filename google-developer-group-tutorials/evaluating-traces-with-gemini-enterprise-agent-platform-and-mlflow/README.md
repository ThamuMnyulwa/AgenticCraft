# Evaluating traces with the Gemini Enterprise Agent Platform and MLflow

Demo repo for the DevFest talk "Evaluating Generative AI with the Gemini Enterprise Agent Platform".

One small travel assistant (two tools: `get_weather` and `calculator`), evaluated at two scales:

- **Part 1, local:** a Gemini agent traced with MLflow, scored with a Gemini LLM judge and a code check on the trace.
- **Part 2, cloud:** the same agent rebuilt with ADK, deployed to Agent Runtime with Cloud Trace, and scored by the Agent Platform evaluation service.

Both parts use the same five questions (`shared/eval_data.py`). One of them fails on purpose.

More detail lives in [`docs/`](docs/README.md): [architecture](docs/architecture.md), [setup](docs/setup.md), [development and CI/CD](docs/development.md), [decisions](docs/decisions.md) and [roadmap](docs/roadmap.md).

```
.
├── demo.sh                   # single entry point: ./demo.sh <command>
├── shared/                   # used by both parts
│   ├── config.py             # MODEL and SYSTEM_INSTRUCTION
│   ├── tools.py              # get_weather, calculator (fixed fake data)
│   └── eval_data.py          # 5 questions + expected tool, one fails on purpose
├── part1_mlflow/
│   ├── agent.py              # google-genai agent, traced with MLflow
│   ├── run_agent.py          # 3 questions to create traces
│   ├── scorers.py            # RelevanceToQuery (Gemini judge) + right_tool
│   └── evaluate.py           # mlflow.genai.evaluate
├── part2_agent_platform/
│   ├── agent/agent.py        # the same agent in ADK
│   ├── settings.py           # reads Terraform outputs
│   ├── deploy.py             # deploy to Agent Runtime with telemetry on
│   ├── generate_traces.py    # 7 questions to the deployed agent
│   ├── evaluate.py           # run_inference + evaluate, results to GCS
│   └── teardown.py           # delete the deployed agent
├── terraform/
│   ├── gemini_api_key/       # optional: Gemini API key in Secret Manager (AI Studio route)
│   └── agent_platform/       # APIs, bucket, service account for Part 2
├── scripts/
│   ├── bootstrap-terraform-state.sh  # creates the GCS state bucket, once per project
│   ├── terraform-init.sh             # terraform init for one stack against that bucket
│   └── setup-gemini-secret.sh        # picks reuse or create, then applies gemini_api_key
└── tests/                    # offline unit tests (./demo.sh test)
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python 3.14 is installed by uv automatically)
- [Terraform](https://developer.hashicorp.com/terraform/install) 1.16+ and the [gcloud CLI](https://cloud.google.com/sdk/docs/install), signed in with `gcloud auth application-default login`
- A Google Cloud project with billing, signed in with `gcloud auth application-default login`. Both parts call Gemini through the Agent Platform with those credentials, so no API key is needed.
- Part 2 also needs permission to create service accounts and grant roles (Owner, or Editor plus Project IAM Admin)

## Quick start

1. `./demo.sh setup` installs dependencies and creates `.env`. Set `GOOGLE_CLOUD_PROJECT` in it, then run `./demo.sh tf-bootstrap` once per project to create the Terraform state bucket.
2. `./demo.sh test` runs the offline tests (no credentials needed).
3. `./demo.sh mlflow-ui` in a second terminal, then open http://localhost:5000
4. `./demo.sh part1` creates traces and runs the evaluation.
5. For Part 2 (billing on): `./demo.sh infra-up && ./demo.sh deploy && ./demo.sh traces && ./demo.sh part2`.

Run `./demo.sh` with no arguments to list every command.

## Run of show: Part 1 live (10 minutes)

| Time | Do | Say |
|---|---|---|
| 0:00 | Show `shared/tools.py` and `part1_mlflow/agent.py` | Two fake tools, one Gemini agent. `mlflow.gemini.autolog()` plus `@mlflow.trace` is all the instrumentation. |
| 2:00 | `./demo.sh part1` | Three questions first, then the five-row evaluation. |
| 3:00 | MLflow UI: **Experiments**, then **devfest-evals**, then the **Traces** tab. Click the Cape Town trace. | One request is one trace: AGENT span, LLM span, TOOL span `get_weather`, LLM span. Show inputs and outputs on each span. |
| 5:00 | Show `part1_mlflow/scorers.py` | One LLM judge (Gemini judging Gemini) and one plain Python check that reads the trace. |
| 6:00 | MLflow UI: the **Evaluations** (evaluation runs) tab, open the newest run | Five rows, two scorers. Relevance passes everywhere. |
| 7:00 | Find the row "How many wheels do 2 bicycles have?" with `right_tool` = No. Open its trace. | The answer is correct (4) but there is no TOOL span. The judge says relevant, the trace says the agent skipped the calculator. The cause is one word in the system prompt: "complex arithmetic". A correct answer can hide the wrong behaviour, and only trace-level evaluation catches it. |
| 9:00 | Hand over to Part 2 slides | Same agent, same questions, now in the cloud. |

## Pre-talk checklist

- [ ] `./demo.sh test` passes.
- [ ] `./demo.sh part1` run at least once today, so the MLflow UI already has data if the network fails.
- [ ] Part 2 run ahead of time: `infra-up`, `deploy`, `traces`, `part2`. Deploys take several minutes, so never do them live.
- [ ] Screenshots: the Agent Platform evaluation results (from the `part2` output and the GCS results), the Cloud Trace list, and one trace drill-down showing the tool span.
- [ ] Backup screen recording of the Part 1 run of show.
- [ ] Laptop: `.env` filled in, MLflow UI running, font size up, notifications off.

## Fallback plan

- **No network:** play the Part 1 recording, then show the Part 2 screenshots.
- **Gemini rate limit or error in `part1`:** open the MLflow UI and walk through the run from the rehearsal.
- **The deliberate failure passes:** model behaviour can change. Open a trace from the rehearsal where it failed, and say this is exactly why we evaluate continuously.

## Costs and cleanup

- Part 1 is about 21 Gemini Flash calls per run (agent plus judge), roughly $0.05 to $0.30, billed to the Cloud billing account through the Agent Platform.
- Part 2 costs a little for Agent Runtime while the agent is deployed, plus Gemini calls for inference and the rubric metrics, and a few MB in Cloud Storage. Expect well under a few dollars for a rehearsal and the talk. Check the Agent Platform pricing page for current rates.
- **After the talk, run `./demo.sh infra-down`.** It deletes the deployed agent, destroys the bucket (including results) and the service account, then deletes the Gemini API key. Enabled APIs are left on.

## Notes

- Change the model in one place: `shared/config.py`. `MODEL_LOCATION` is `global` because `gemini-3.5-flash` is not served from `europe-west1`; the infra stays in `europe-west1`.
- `./demo.sh api-key` is optional. It keeps a Gemini API key in Secret Manager (reused if it exists) and copies it into `.env` for anyone who wants the AI Studio route. The demo code does not use it: on `oceanhub-dev` the AI Studio prepaid credits are empty, while the Agent Platform bills the Cloud billing account.
- The MLflow store is `mlflow.db` (SQLite) in this folder. `./demo.sh mlflow-ui` serves it with the same MLflow version that wrote it.
- `.env`, `mlflow.db`, Terraform state and `.agent_resource` are gitignored. The secret version is written with a write-only attribute, so it is not in Terraform state, but the API key resource still records the key string there. Terraform state lives in `gs://<project>-tfstate` (versioned, private, one prefix per stack), so treat read access to that bucket like access to the key.

## CI/CD

Defined at the AgenticCraft repo root.

- `.github/workflows/ci.yml`: gitleaks over the full git history, plus every pre-commit hook.
- `.github/workflows/gdg-evaluating-traces.yml`: runs when this folder changes, nightly, and on demand.
  - `tests`: `uv sync --locked` and `pytest` (offline).
  - `terraform`: `fmt -check` and `validate` for both stacks (no cloud credentials).
  - `evals`: runs the Part 1 evaluation with `--gate`. It fails if `right_tool` drops below 80% (so the one deliberate failure is allowed) or relevance below 100%, and uploads `mlflow.db` as an artifact. Signs in with Workload Identity Federation and is skipped until the repo variables `GCP_PROJECT_ID`, `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT` exist (see `docs/roadmap.md`).
- `.github/dependabot.yml`: weekly updates for actions, uv packages and the Terraform provider.

Formatting runs in three places, with the same rules everywhere (root `ruff.toml`):

- **On save:** `.vscode/settings.json` at the repo root runs ruff (fix, organise imports, format) and `terraform fmt` on save in VS Code or Antigravity. Install the recommended extensions when prompted.
- **On commit:** pre-commit runs `ruff check --fix`, `ruff format` and `terraform_fmt`. Run `uv tool install pre-commit && pre-commit install` once at the repo root.
- **On demand:** `./demo.sh lint`.

Locally, `./demo.sh part1` never fails on the gate, so a flaky row cannot break the live demo. Run `uv run python -m part1_mlflow.evaluate --gate` to see what CI sees.

Deploys are reproducible: `deploy.py` sends Agent Runtime the `agent-runtime` dependency group exported from `uv.lock`, so the cloud runs the exact versions that were tested.
