# Decisions and deviations

Every API was checked against the installed package source or the current official docs (October 2026). This is where the build differs from the original brief, and why.

## Platform and SDK

| Brief said | We did | Why |
|---|---|---|
| Agent Platform SDK, `client.evals.*` | `google-cloud-agentplatform` 2.3.0, `agentplatform.Client` | `vertexai.Client` now raises a deprecation warning pointing to `agentplatform.Client`. `client.runtimes` replaces `client.agent_engines`. |
| Cloud Trace telemetry | env var `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` | The SDK source treats `AdkApp(enable_tracing=...)` as the legacy switch. |
| `run_inference` + `evaluate` | Kept. We did not use `create_evaluation_run`. | `create_evaluation_run` adds a server-side multi-turn user simulator. Single-turn `run_inference` + `evaluate` is simpler and more predictable for a live talk. |
| One task-success and one tool-use metric | `FINAL_RESPONSE_QUALITY`, `TOOL_USE_QUALITY`, plus custom `right_tool` | The client SDK has no trajectory metrics yet (a TODO in its source), so `right_tool` is a custom metric, which also mirrors Part 1. |
| Print the console URL of the evaluation run | Print the GCS browser URL of the results | The SDK has no console-URL helper and the docs do not give a URL pattern. |
| `google-cloud-agentplatform` is the new SDK | Ship `google-cloud-aiplatform` (same version) next to it in the `agent-runtime` group | The first deploy crashed in `AdkApp.set_up()`: with telemetry on, `agentplatform.frameworks.adk` imports `google.cloud.aiplatform` in several places, and only `google-cloud-aiplatform` ships that module. The two packages share 64 `agentplatform/` files with identical hashes, so installing both is safe. Reproduced locally with the project number and telemetry on, then fixed. |
| One task-success and one tool-use metric (Part 2) | Plus our own judge, `travel_guidelines`, in both parts | Requested ("add a judge"). Same plain-English guideline in both parts. In Part 2 it is an `LLMMetric` with an explicit prompt that asks for JSON: with `MetricPromptBuilder` the judge answered in prose and the service failed to parse every row. A first guideline about "not inventing weather data" was dropped because the judge cannot see tool results and failed a correct answer. |
| `evaluation` extra is enough | Also depend on `google-cloud-bigquery` directly | `agentplatform.evals` always imports BigQuery, but the `evaluation` extra does not install it. This is a packaging bug in 2.3.0. |

## MLflow

| Brief said | We did | Why |
|---|---|---|
| `uvx mlflow server` | `uv run mlflow server --backend-store-uri sqlite:///mlflow.db` | `uvx` fetches the newest MLflow, which can disagree with the pinned version about the `mlflow.db` schema. |
| Nested LLM and tool spans | Tools wrapped with `mlflow.trace(span_type="TOOL")` | `mlflow.gemini.autolog()` records LLM calls only, not tool executions. |
| Gemini as judge model | `RelevanceToQuery(model="vertex_ai:/gemini-3.5-flash")` | `<provider>:/<model>` is the URI format in the MLflow source. The `vertex_ai` provider uses Application Default Credentials and reads `VERTEX_PROJECT` and `VERTEX_LOCATION`. |
| Latest packages | `google-genai` 2.28.0, `enterprise=True` | MLflow 3.16.1 declares Gemini autolog tested only up to `google-genai` 2.20.0. We checked that autolog still patches 2.28.0. Pin back to `<=2.20.0` if tracing misbehaves. |

## Repo and tooling

| Brief said | We did | Why |
|---|---|---|
| Repo `devfest-evals/` | `AgenticCraft/google-developer-group-tutorials/evaluating-traces-with-gemini-enterprise-agent-platform-and-mlflow/` | One hub repo for every talk. Per-folder CI uses path filters. The uv project is still named `devfest-evals`. |
| Python 3.12 | Python 3.14 | The latest Python. Agent Runtime accepts 3.10 to 3.14. |
| `infra/` | `terraform/` with two stacks | The Gemini API key has its own lifecycle (often shared and long-lived), separate from the Part 2 infra. |
| Gemini API key (AI Studio) via `GEMINI_API_KEY` | Agent Platform with Application Default Credentials, `location="global"` | The AI Studio prepaid credits on `oceanhub-dev` were empty (402). The Agent Platform bills the Cloud billing account at the same token price, both parts now use one platform, and no key is handled. The Secret Manager key stack stays as an optional AI Studio route. |
| Region with Agent Runtime and evaluation | `europe-west1` for infra, `global` for model calls | `europe-west1` was requested and supports both services. `gemini-3.5-flash` returns 404 in `europe-west1`, so model calls go to `global`. |
| "Exactly one row must fail on purpose" | "How many wheels do 2 bicycles have?" plus "complex arithmetic" in the instruction | Gemini 3.5 Flash used the calculator for every arithmetic question with a plain instruction, including the original spider question. The vague word "complex" is a realistic prompt bug; with it the bicycle row skipped the tool in 3 of 3 runs while the other four rows passed. |
| One preflight check | `preflight local` and `preflight cloud` | `part1` needs only a Gemini key (from the environment or Secret Manager), not the Part 2 tooling. |
| `eval_data.py` in Part 1 | `shared/eval_data.py` | Both parts score the same questions. |
| No Docker mentioned, later asked "where necessary" | No Docker | Agent Runtime builds its own container from source. Docker on stage would only add a failure point. See [roadmap.md](roadmap.md) for where Docker would be needed. |
| Terraform provider v7 | `hashicorp/google ~> 8.5` | v8 is current. No changes affect the resources used here. `disable_on_destroy = false` is set explicitly. |
