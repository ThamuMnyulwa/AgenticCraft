# Roadmap and open items

## Not verified yet

1. **Part 2 against Google Cloud:** deploy, `async_stream_query` event parsing, `run_inference` with `session_inputs`, the shape of the custom metric input, and writing results to GCS. Checked against SDK source only.
2. **Model calls to `global` from an agent deployed in `europe-west1`.** Verified for Part 1 on a laptop, not yet from Agent Runtime.
3. **The service account roles** beyond `roles/aiplatform.user`. The extra roles are a least-privilege choice and not listed by the docs.
4. **The MLflow UI tab names** used in the run-of-show.

## Done since the first plan

- Part 1 verified end to end on 2026-10-04: Gemini on the Agent Platform (`global`), MLflow traces, Vertex judge, exactly one failing row (bicycles), quality gate passes.
- Remote Terraform state in `gs://oceanhub-dev-tfstate` (versioned, private), one prefix per stack.
- Gemini API key in Secret Manager, reused if it exists, else created.

## Phase 2: after the talk

| Item | Why | Notes |
|---|---|---|
| Workload Identity Federation for GitHub | Deploy from CI without JSON keys | Terraform manages the pool, the provider and a deployer service account with `iam.serviceAccountUser` on the agent SA |
| Dev and prod environments | Promote a tested agent | A tfvars file per environment, or one project each. CI deploys dev on merge and prod on a tagged release after the eval gate passes. |
| Per-agent identity | Recommended by the Agent Runtime setup docs | `identity_type: AGENT_IDENTITY` in the deploy config instead of a shared service account |
| Eval-runner Docker image | Continuous evaluation in production | Build in CI, push to Artifact Registry with `dev` and `prod` tags, run nightly as a Cloud Run Job against the deployed agent. This is where Docker becomes necessary. |
| Shared MLflow server | A team-wide view of traces and evals | MLflow on Cloud Run with Cloud SQL and a GCS artifact store, also containerised |
| One trace store | See Part 1 and Part 2 traces side by side | Send Agent Runtime OpenTelemetry traces to MLflow, which accepts OTLP |
| Workload Identity Federation for the CI eval job | The `evals` job is skipped until it exists | Terraform: pool, GitHub OIDC provider limited to this repo, CI service account with `roles/aiplatform.user`, then the three `GCP_*` repo variables |
