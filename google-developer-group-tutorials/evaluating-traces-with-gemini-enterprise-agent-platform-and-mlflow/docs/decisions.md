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
| `evaluation` extra is enough | Also depend on `google-cloud-bigquery` directly | `agentplatform.evals` always imports BigQuery, but the `evaluation` extra does not install it. This is a packaging bug in 2.3.0. |

## MLflow

| Brief said | We did | Why |
|---|---|---|
| `uvx mlflow server` | `uv run mlflow server --backend-store-uri sqlite:///mlflow.db` | `uvx` fetches the newest MLflow, which can disagree with the pinned version about the `mlflow.db` schema. |
| Nested LLM and tool spans | Tools wrapped with `mlflow.trace(span_type="TOOL")` | `mlflow.gemini.autolog()` records LLM calls only, not tool executions. |
| Gemini as judge model | `RelevanceToQuery(model="gemini:/gemini-3.5-flash")` | `<provider>:/<model>` is the URI format in the MLflow source. The `gemini` provider reads `GEMINI_API_KEY`. |
| Latest packages | `google-genai` 2.28.0 | MLflow 3.16.1 declares Gemini autolog tested only up to `google-genai` 2.20.0. We checked that autolog still patches 2.28.0. Pin back to `<=2.20.0` if tracing misbehaves. |

## Repo and tooling

| Brief said | We did | Why |
|---|---|---|
| Repo `devfest-evals/` | `AgenticCraft/google-developer-group-tutorials/evaluating-traces-with-gemini-enterprise-agent-platform-and-mlflow/` | One hub repo for every talk. Per-folder CI uses path filters. The uv project is still named `devfest-evals`. |
| Python 3.12 | Python 3.14 | The latest Python. Agent Runtime accepts 3.10 to 3.14. |
| `infra/` | `terraform/` with two stacks | The Gemini API key is created as code and works without billing. Part 2 needs billing. |
| Region with Agent Runtime and evaluation | `europe-west1` | Requested. Supported by both. |
| One preflight check | `preflight local` and `preflight cloud` | `part1` must work with only `GEMINI_API_KEY`. |
| `eval_data.py` in Part 1 | `shared/eval_data.py` | Both parts score the same questions. |
| No Docker mentioned, later asked "where necessary" | No Docker | Agent Runtime builds its own container from source. Docker on stage would only add a failure point. See [roadmap.md](roadmap.md) for where Docker would be needed. |
| Terraform provider v7 | `hashicorp/google ~> 8.5` | v8 is current. No changes affect the resources used here. `disable_on_destroy = false` is set explicitly. |
