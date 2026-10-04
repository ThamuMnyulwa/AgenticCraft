# Roadmap and open items

## Not verified yet

These are checked against SDK source and docs, but not against a live project.

1. **Part 1 end to end**, and whether the spider row fails reliably.
2. **`gemini-3.5-flash` in `europe-west1` on Agent Platform.** A metadata check returned 403, which was inconclusive. If deploy or inference fails on the model, try `us-central1` or the global endpoint.
3. **Part 2 against Google Cloud:** deploy, `async_stream_query` event parsing, `run_inference` with `session_inputs`, the shape of the custom metric input, and writing results to GCS.
4. **The service account roles** beyond `roles/aiplatform.user`. The extra roles are a least-privilege choice and not listed by the docs.
5. **The MLflow UI tab names** used in the run-of-show.
6. **Billing on `oceanhub-dev`.** It was off at the last check, which blocks Secret Manager and Part 2.
7. **Whether a `gemini-api-key` secret already exists** in `oceanhub-dev`. It could not be listed without billing. `./demo.sh api-key` handles both cases.

## Phase 2: after the talk

| Item | Why | Notes |
|---|---|---|
| Remote Terraform state in GCS | CI/CD cannot use laptop-local state, and state holds the API key | A `backend "gcs"` block per stack, with a bucket created once by hand or a bootstrap stack |
| Workload Identity Federation for GitHub | Deploy from CI without JSON keys | Terraform manages the pool, the provider and a deployer service account with `iam.serviceAccountUser` on the agent SA |
| Dev and prod environments | Promote a tested agent | A tfvars file per environment, or one project each. CI deploys dev on merge and prod on a tagged release after the eval gate passes. |
| Per-agent identity | Recommended by the Agent Runtime setup docs | `identity_type: AGENT_IDENTITY` in the deploy config instead of a shared service account |
| Eval-runner Docker image | Continuous evaluation in production | Build in CI, push to Artifact Registry with `dev` and `prod` tags, run nightly as a Cloud Run Job against the deployed agent. This is where Docker becomes necessary. |
| Shared MLflow server | A team-wide view of traces and evals | MLflow on Cloud Run with Cloud SQL and a GCS artifact store, also containerised |
| One trace store | See Part 1 and Part 2 traces side by side | Send Agent Runtime OpenTelemetry traces to MLflow, which accepts OTLP |
| CI reads the key from Secret Manager | Drop the `GEMINI_API_KEY` GitHub secret | Needs Workload Identity Federation, with `roles/secretmanager.secretAccessor` on the `gemini-api-key` secret for the CI identity |
