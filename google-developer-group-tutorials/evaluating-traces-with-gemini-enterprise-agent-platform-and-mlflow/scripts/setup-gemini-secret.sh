#!/usr/bin/env bash
# Make sure the Gemini API key is in Secret Manager, using Terraform (terraform/gemini_api_key).
#
#   already managed by this stack  -> keep managing it
#   exists in the project already  -> use it as data, create nothing
#   does not exist                 -> create a restricted API key and store it
#
# The key itself is never written to .env. The Python code reads it from Secret Manager.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
STACK=terraform/gemini_api_key

[[ -f .env ]] || cp .env.example .env
set -a
# shellcheck source=/dev/null
source .env
set +a
[[ -n "${GOOGLE_CLOUD_PROJECT:-}" && "$GOOGLE_CLOUD_PROJECT" != your-* ]] \
  || { echo "Set GOOGLE_CLOUD_PROJECT in .env first." >&2; exit 1; }
SECRET_ID="${GEMINI_SECRET_ID:-gemini-api-key}"

terraform -chdir="$STACK" init -input=false

if terraform -chdir="$STACK" state list 2>/dev/null | grep -q '^google_secret_manager_secret\.gemini_api_key'; then
  create_secret=true
  echo "Secret ${SECRET_ID} is managed by this stack."
elif gcloud secrets describe "$SECRET_ID" --project "$GOOGLE_CLOUD_PROJECT" >/dev/null 2>&1; then
  create_secret=false
  echo "Secret ${SECRET_ID} already exists in ${GOOGLE_CLOUD_PROJECT}. Using it, creating nothing."
else
  create_secret=true
  echo "Secret ${SECRET_ID} not found. Creating an API key and the secret."
fi

terraform -chdir="$STACK" apply -input=false \
  -var "project_id=${GOOGLE_CLOUD_PROJECT}" \
  -var "region=${GOOGLE_CLOUD_LOCATION:-europe-west1}" \
  -var "secret_id=${SECRET_ID}" \
  -var "create_secret=${create_secret}"

echo "Gemini API key: $(terraform -chdir="$STACK" output -raw secret_name) ($(terraform -chdir="$STACK" output -raw mode))"
