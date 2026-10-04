#!/usr/bin/env bash
# terraform init for one stack, with its state in the GCS bucket.
# Usage: scripts/terraform-init.sh <stack>   (a folder under terraform/)
# Each stack gets its own prefix, so the stacks never share a state file.
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
