#!/usr/bin/env bash
# Single entry point for the DevFest evals demo. Run ./demo.sh with no arguments for help.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
export MLFLOW_DISABLE_AGENT_HINT=1

MLFLOW_PORT=5000

BOLD=$'\033[1m'; BLUE=$'\033[34m'; GREEN=$'\033[32m'; RED=$'\033[31m'; RESET=$'\033[0m'
step() { echo; echo "${BOLD}${BLUE}==> $*${RESET}"; }
ok()   { echo "${GREEN}ok${RESET} $*"; }
die()  { echo "${RED}error:${RESET} $*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: ./demo.sh <command>

Part 1 (local MLflow; Gemini on the Agent Platform with your gcloud credentials)
  setup        uv sync and create .env from .env.example if missing
  api-key      optional AI Studio route: Gemini API key in Secret Manager, copied into .env
  mlflow-ui    start the MLflow UI on port ${MLFLOW_PORT} (reuses a running one)
  part1        create traces, then run the MLflow evaluation
  test         run the offline unit tests
  lint         ruff check --fix, ruff format and terraform fmt (same as pre-commit)

Part 2 (Google Cloud: Agent Runtime and the evaluation service)
  tf-bootstrap create the GCS bucket for Terraform state (once per project)
  infra-up     terraform init + apply in terraform/agent_platform/
  deploy       deploy the ADK agent to Agent Runtime
  traces       send queries to the deployed agent
  part2        run the Agent Platform evaluation
  infra-down   delete the deployed agent, then terraform destroy both stacks

  all          setup, tf-bootstrap, part1, infra-up, deploy, traces, part2
EOF
}

load_env() {
  [[ -f .env ]] || die ".env not found. Run ./demo.sh setup first."
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
}

require_cmd() { command -v "$1" >/dev/null 2>&1 || die "$1 is not installed. $2"; }

is_set() { local value="${!1:-}"; [[ -n "$value" && "$value" != your-* ]]; }

require_var() { is_set "$1" || die "$1 is not set. Edit .env and set it."; }

require_adc() {
  gcloud auth application-default print-access-token >/dev/null 2>&1 \
    || die "No application default credentials. Run: gcloud auth application-default login"
}

# preflight local: what Part 1 needs. preflight cloud: what Part 2 needs as well.
preflight() {
  step "Preflight ($1)"
  require_cmd uv "See https://docs.astral.sh/uv/"
  load_env
  # Both parts call Gemini through the Agent Platform with your gcloud credentials.
  require_cmd gcloud "See https://cloud.google.com/sdk/docs/install"
  require_var GOOGLE_CLOUD_PROJECT
  require_adc
  if [[ "$1" == cloud ]]; then
    require_cmd terraform "See https://developer.hashicorp.com/terraform/install"
    require_var GOOGLE_CLOUD_LOCATION
  fi
  ok "all checks passed"
}

cmd_setup() {
  step "Installing Python dependencies"
  require_cmd uv "See https://docs.astral.sh/uv/"
  uv sync
  if [[ ! -f .env ]]; then
    cp .env.example .env
    ok "created .env, now set GOOGLE_CLOUD_PROJECT in it"
  else
    ok ".env already exists"
  fi
}

cmd_mlflow_ui() {
  step "MLflow UI on http://localhost:${MLFLOW_PORT}"
  if curl -sf "http://localhost:${MLFLOW_PORT}/health" >/dev/null; then
    ok "already running"
    return
  fi
  # uv run (not uvx) so the server uses the same MLflow version that wrote mlflow.db.
  uv run mlflow server --backend-store-uri sqlite:///mlflow.db --port "$MLFLOW_PORT"
}

cmd_api_key() {
  step "Gemini API key in Secret Manager"
  require_cmd terraform "See https://developer.hashicorp.com/terraform/install"
  require_cmd gcloud "See https://cloud.google.com/sdk/docs/install"
  require_adc
  ./scripts/setup-gemini-secret.sh
}

cmd_part1() {
  preflight local
  step "Part 1: running the agent to create traces"
  uv run python -m part1_mlflow.run_agent
  step "Part 1: evaluating with MLflow"
  uv run python -m part1_mlflow.evaluate
}

cmd_lint() {
  step "Python: ruff check --fix and ruff format"
  uv run ruff check --fix .
  uv run ruff format .
  step "Terraform: fmt"
  require_cmd terraform "See https://developer.hashicorp.com/terraform/install"
  terraform fmt -recursive terraform
}

cmd_test() {
  step "Unit tests"
  uv run pytest -q
}

# Usage: tf <stack> <terraform args>, where stack is a folder under terraform/.
tf() { local stack="$1"; shift; terraform -chdir="terraform/${stack}" "$@"; }

tf_vars() {
  echo -var "project_id=${GOOGLE_CLOUD_PROJECT}" -var "region=${GOOGLE_CLOUD_LOCATION}"
}

cmd_tf_bootstrap() {
  step "Terraform state bucket"
  require_cmd gcloud "See https://cloud.google.com/sdk/docs/install"
  ./scripts/bootstrap-terraform-state.sh
}

cmd_infra_up() {
  preflight cloud
  step "Terraform: creating APIs, bucket and service account"
  ./scripts/terraform-init.sh agent_platform
  # shellcheck disable=SC2046
  tf agent_platform apply $(tf_vars)
}

cmd_deploy() {
  preflight cloud
  step "Deploying the ADK agent to Agent Runtime (takes a few minutes)"
  uv run python -m part2_agent_platform.deploy
}

cmd_traces() {
  preflight cloud
  step "Sending queries to the deployed agent"
  uv run python -m part2_agent_platform.generate_traces
}

cmd_part2() {
  preflight cloud
  step "Part 2: evaluating with the Agent Platform"
  uv run python -m part2_agent_platform.evaluate
}

cmd_infra_down() {
  preflight cloud
  step "Deleting the deployed agent"
  uv run python -m part2_agent_platform.teardown
  ./scripts/terraform-init.sh agent_platform
  ./scripts/terraform-init.sh gemini_api_key
  step "Terraform: destroying the Agent Platform stack"
  # shellcheck disable=SC2046
  tf agent_platform destroy $(tf_vars)
  step "Terraform: deleting the Gemini API key"
  # shellcheck disable=SC2046
  tf gemini_api_key destroy $(tf_vars)
}

cmd_all() {
  cmd_setup
  cmd_tf_bootstrap
  cmd_part1
  cmd_infra_up
  cmd_deploy
  cmd_traces
  cmd_part2
}

case "${1:-}" in
  setup)      cmd_setup ;;
  api-key)    cmd_api_key ;;
  mlflow-ui)  cmd_mlflow_ui ;;
  part1)      cmd_part1 ;;
  test)       cmd_test ;;
  lint)       cmd_lint ;;
  tf-bootstrap) cmd_tf_bootstrap ;;
  infra-up)   cmd_infra_up ;;
  deploy)     cmd_deploy ;;
  traces)     cmd_traces ;;
  part2)      cmd_part2 ;;
  infra-down) cmd_infra_down ;;
  all)        cmd_all ;;
  -h|--help|help|"") usage ;;
  *) usage; die "unknown command: $1" ;;
esac
