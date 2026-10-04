#!/usr/bin/env bash
# Create the GCS bucket that holds Terraform state for every stack in terraform/.
# Run once per project. Safe to re-run: an existing bucket is left as it is.
# This bucket is created outside Terraform on purpose: a backend cannot create itself.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env ]] || cp .env.example .env
set -a
# shellcheck source=/dev/null
source .env
set +a
[[ -n "${GOOGLE_CLOUD_PROJECT:-}" && "$GOOGLE_CLOUD_PROJECT" != your-* ]] \
  || { echo "Set GOOGLE_CLOUD_PROJECT in .env first." >&2; exit 1; }

BUCKET="${TF_STATE_BUCKET:-${GOOGLE_CLOUD_PROJECT}-tfstate}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-europe-west1}"

if gcloud storage buckets describe "gs://${BUCKET}" >/dev/null 2>&1; then
  echo "State bucket gs://${BUCKET} already exists."
else
  gcloud storage buckets create "gs://${BUCKET}" \
    --project "$GOOGLE_CLOUD_PROJECT" \
    --location "$LOCATION" \
    --uniform-bucket-level-access \
    --public-access-prevention
  echo "Created state bucket gs://${BUCKET}."
fi

# Versioning keeps every previous state file, so a bad apply can be rolled back.
gcloud storage buckets update "gs://${BUCKET}" --versioning >/dev/null
echo "Versioning is on for gs://${BUCKET}."
