#!/usr/bin/env bash
# Create a Gemini API key with Terraform (terraform/gemini_api_key) and save it to .env.
# Safe to re-run: Terraform reuses the existing key. Works on projects without billing.
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

terraform -chdir="$STACK" init -input=false
terraform -chdir="$STACK" apply -input=false \
  -var "project_id=${GOOGLE_CLOUD_PROJECT}" -var "region=${GOOGLE_CLOUD_LOCATION:-europe-west1}"

key="$(terraform -chdir="$STACK" output -raw gemini_api_key)"

# Replace the GEMINI_API_KEY line in .env (or add it) without printing the key.
tmp="$(mktemp)"
grep -v '^GEMINI_API_KEY=' .env > "$tmp" || true
echo "GEMINI_API_KEY=${key}" >> "$tmp"
mv "$tmp" .env
chmod 600 .env

echo "Saved GEMINI_API_KEY to .env (key ${key:0:6}...)"
