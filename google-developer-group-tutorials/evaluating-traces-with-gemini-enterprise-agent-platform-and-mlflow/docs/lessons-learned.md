# Lessons learned

Everything that cost time while building this demo (October 2026), so the next talk does not repeat it. Each entry is: what we saw, why, and what we did. Versions: MLflow 3.16.1, google-genai 2.28.0, google-cloud-agentplatform 2.3.0, google-adk 2.11.0, Terraform google provider 8.5.0, Python 3.14.

## Gemini Enterprise Agent Platform (Part 2)

### SDK and packaging

- **Vertex AI was renamed.** Since April 2026 it is the Gemini Enterprise Agent Platform. Use `google-cloud-agentplatform` and `agentplatform.Client`; `vertexai.Client` still works but warns that it is deprecated. `client.runtimes` replaces `client.agent_engines`.
- **The deployed agent crashed on start.** With telemetry on, `agentplatform.frameworks.adk` imports `google.cloud.aiplatform` in several places, but only the older `google-cloud-aiplatform` package ships it. Fix: ship `google-cloud-aiplatform` (same version) in the `agent-runtime` dependency group. The two packages share 64 `agentplatform/` files with identical hashes, so installing both is safe. Reproduce locally with `GOOGLE_CLOUD_PROJECT=<number>` and `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`, then `AdkApp(...).set_up()`.
- **`agentplatform.evals` failed to import.** It always imports BigQuery, but the `evaluation` extra does not install it. Fix: depend on `google-cloud-bigquery` directly.
- **Signatures differ from some docs.** `client.runtimes.create` takes keyword arguments only, and `AgentInfo.load_from_agent` takes one argument. Introspect the installed SDK (`inspect.signature`) instead of copying snippets.

### Models, regions and billing

- **`gemini-3.5-flash` returned 404 in `europe-west1`.** It is only served from the `global` endpoint. Keep the infra regional and send model calls to `global`: `genai.Client(enterprise=True, location="global")`, and in ADK `Gemini(model=..., client_kwargs={"enterprise": True, "location": "global"})`.
- **The AI Studio key returned 402 "prepayment credits are depleted".** The Gemini API (AI Studio) has its own prepaid billing, separate from the Cloud billing account. Calling the same model through the Agent Platform with Application Default Credentials bills the Cloud account at about the same token price and needs no key.
- **Billing was off on the project.** It was linked to a closed trial account. Closed billing accounts cannot be deleted (Google keeps them for audit); unlink their projects instead. Credits and payment methods are only visible in the console, not via `gcloud` or the API.
- **429 RESOURCE_EXHAUSTED** happens on the `global` endpoint after many calls. Both MLflow and ADK retry with backoff, which looks like a hang. This is the most likely cause of the evaluation runs that "stalled" for minutes.

### Terraform

- **API Keys returned 403 "requires a quota project" with user credentials.** Set `user_project_override = true` and `billing_project = var.project_id` in the provider block.
- **`terraform apply -input=false` without `-auto-approve` fails** instead of asking. Scripts pass `"$@"` so a human gets the prompt and automation can add `--auto-approve`. For reviewed changes, use `plan -out=x.tfplan` then `apply x.tfplan`.
- **Remote state needs a bucket that exists first.** A backend cannot create its own bucket, so `scripts/bootstrap-terraform-state.sh` creates it once (versioning on, public access prevention). One bucket, one prefix per stack.
- **"Import if it exists, else create" cannot be done with `count` alone.** A data lookup would make Terraform destroy its own resource on the second run. The script decides (in state, exists outside state, missing) and passes `create_secret`.
- **Write-only attributes** (`secret_data_wo`) keep a secret version out of state, but the API key resource still stores `key_string` in state.

### Tracing

- **No traces anywhere, while the Telemetry API returned HTTP 200.** `observability.googleapis.com` was disabled. Trace Explorer showed "error fetching project provision state". Enabling the Observability API fixed both Trace Explorer and the agent's Traces tab (traces sent before that were lost).
- **The old Cloud Trace v1 API cannot see the new trace storage.** `GET /v1/projects/.../traces/<id>` returned 404 for traces that the console shows. Check in the console, not with v1.
- **Telemetry switch:** set `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` on the deployment. `AdkApp(enable_tracing=...)` is the legacy flag.
- **Prompt-response logging:** set `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`. `SPAN_AND_EVENT` did not change anything. `AdkApp.set_up()` forces `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`, so content shows up in the log events linked to spans, not as span attributes. Only traffic after the change carries content.
- **Redeploying created a new agent each time.** `deploy.py` now calls `client.runtimes.update(name=...)` when `.agent_resource` exists, which keeps the agent ID.

### Evaluation

- **`tool_use_quality` scored 0.33 to 0.67 and said "no tools are provided".** `run_inference` against a deployed agent fills `agent_data` without the agents' tool definitions, and `evaluate()` ignores `agent_info` when a row already has `agent_data`. Fix: copy `AgentInfo.load_from_agent(root_agent).agents` into every row's `agent_data`. After that it scored 1.0.
- **`tool_use_quality` errors (400) on a row with no tool calls.** That row is left out of the metric. Explain it rather than hide it: it is the bicycle row.
- **A custom `LLMMetric` built with `MetricPromptBuilder` failed on every row with "Error parsing JSON".** The judge answered in prose. Fix: an explicit prompt that asks for `{"score": ..., "explanation": ...}` (`{{` and `}}` are literal braces). Google's eval skill also says to always set `judge_model`.
- **A judge can only judge what it sees.** A guideline about "not inventing weather data" failed a correct answer, because the judge sees the question and answer but not the tool results. Write guidelines that are checkable from those two alone, and leave tool behaviour to trace checks.
- **Custom Python metrics run locally only.** `types.Metric(custom_function=...)` works in `evaluate()`, but not in managed runs (the service cannot run your code).
- **Managed evaluation runs:** `create_evaluation_run` with `agent=` would start a multi-turn user simulator. Passing `agent=` plus rows already answered by `run_inference` (keep its `candidate_name`) makes the service only score them and labels the run with the agent ID. Without an experiment, every run creates a new one; reuse one with `evaluation_experiment=`.
- **Open issue: runs created from the SDK do not appear in the console.** The Evaluation page and the agent's Evaluation tab list "experiments", and SDK experiments (which only exist in the v1beta1 API) never showed, whether in `europe-west1`, `us-central1` or `global`, linked to the agent or not. The docs and Google's eval skill do not cover it. What we show instead: the `part2` table, the HTML report, and the agent's Traces tab.
- **The agent's Evaluation tab lists experiments and online monitors only.** Online monitors (continuous scoring of live traffic) have no SDK or Terraform support yet; set them up in the console. A custom judge can be registered for the console with `google_vertex_ai_evaluation_metric`.
- **The console's "Enable APIs" banner** asked for 23 APIs. Enabling them through Terraform keeps the setup reproducible.

## MLflow (Part 1)

- **Gemini autolog is only tested up to `google-genai` 2.20.0** in MLflow 3.16.1. It still patched 2.28.0 correctly.
- **Autolog records LLM calls, not tool calls.** Wrap the tools with `mlflow.trace(span_type="TOOL")` so they show as TOOL spans, and run the tool loop yourself so every step is visible.
- **Judge model URIs are `<provider>:/<model>`.** `gemini:/...` reads `GEMINI_API_KEY`; `vertex_ai:/...` uses Application Default Credentials plus `VERTEX_PROJECT` and `VERTEX_LOCATION`.
- **`result_df` uses a `request` column**, not `inputs`.
- **The Judges page lists registered scorers only.** Scorers passed to `evaluate()` score the run but are not saved. `scorer.register()` saves LLM judges; `@scorer` code cannot be registered outside Databricks.
- **The Review page lists review queues** (`mlflow.genai.review_queues`, experimental, works locally), not assessments on traces. Labeling sessions, and `title` / `overwrite` on label schemas, are Databricks-only.
- **Sessions:** `mlflow.update_current_trace(session_id=..., user=...)` inside the traced function.
- **Datasets:** `create_dataset` plus `merge_records` (idempotent, matches on inputs); pass the dataset to `evaluate()` so runs link to it.
- **`uvx mlflow server` pulls the newest MLflow,** which can disagree with the pinned version about the `mlflow.db` schema. Use `uv run mlflow server`.
- **No network calls at import time.** Creating the Gemini client or fetching a key on import made the offline tests call Google. Create clients lazily (`functools.cache`) and fetch secrets in `setup()`.

## Designing the deliberate failure

- **Gemini 3.5 Flash follows instructions well.** With "Use the calculator tool for arithmetic" it used the calculator for every question, including "How many legs do 3 spiders have?". A demo needs a failure that is reliable.
- **A realistic prompt bug works:** "Use the calculator tool for *complex* arithmetic". "How many wheels do 2 bicycles have?" then skipped the tool in 3 of 3 runs, while the other four rows kept using their tools. Test candidates several times (temperature 0 is not fully deterministic with thinking models).
- **The story it tells:** the answer is right and every judge passes it; only the trace shows the missing tool call.

## Repo, CI and tooling

- **`pre-commit run --all-files` skips untracked files.** Run `pre-commit run --files $(git ls-files --others --exclude-standard)` on new work before the first commit.
- **A `# shellcheck source=` directive applies to the next command only.** Put it directly above `source`, not above `set -a; source ...`.
- **GitHub Actions did not start: "account is locked due to a billing issue".** Check annotations, not just job status. Also, `push` plus `pull_request` runs every workflow twice on a PR; limit `push` to `main`.
- **Old tools block "latest everything".** uv 0.7.3 could not install Python 3.14.8 (`uv self update` fixed it); Terraform in `/usr/local/bin` needed sudo, so 1.16.5 went to `~/.local/bin`, which is earlier on the PATH.
- **Ignore `*.tfvars` repo-wide,** but keep `.terraform.lock.hcl` and `*.tfvars.example` tracked.
- **Console links:** a URL wrapped in parentheses can pick up the `)` and point at a project that does not exist. Put links on their own line.
- **Google's agent skills** (`npx skills add google/skills`) are worth installing for Agent Platform work; `agent-platform-eval-flywheel` covers metrics, dataset shapes and the HTML report used here.
