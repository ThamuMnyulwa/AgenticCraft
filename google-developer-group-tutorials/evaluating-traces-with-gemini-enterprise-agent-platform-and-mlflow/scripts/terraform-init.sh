#!/usr/bin/env bash
# terraform init for one stack, with its state in the GCS bucket.
# Usage: scripts/terraform-init.sh <stack>   (a folder under terraform/)
#
# There is ONE bucket for all state. Each stack gets its own prefix (a folder
# in the bucket) named after its folder under terraform/, so stacks never
# share or overwrite a state file:
#
#   gs://<TF_STATE_BUCKET>/                          one bucket, e.g. oceanhub-dev-tfstate
#   └── agenticcraft/evaluating-traces/               this repo and demo
#       ├── gemini_api_key/default.tfstate            state of terraform/gemini_api_key
#       └── agent_platform/default.tfstate            state of terraform/agent_platform
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
STACK="${1:?usage: scripts/terraform-init.sh <stack>}"
[[ -d "terraform/${STACK}" ]] || { echo "No such stack: terraform/${STACK}" >&2; exit 1; }

set -a
# shellcheck source=/dev/null
source .env
set +a
BUCKET="${TF_STATE_BUCKET:-${GOOGLE_CLOUD_PROJECT}-tfstate}"

terraform -chdir="terraform/${STACK}" init -input=false -reconfigure \
  -backend-config="bucket=${BUCKET}" \
  -backend-config="prefix=agenticcraft/evaluating-traces/${STACK}"
