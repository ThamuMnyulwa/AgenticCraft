# The Gemini API key lives in Secret Manager.
# create_secret = true:  create a key (restricted to the Gemini API) and store it.
# create_secret = false: use a secret that already exists, read as data. Nothing is created.
# scripts/setup-gemini-secret.sh picks the mode by checking what already exists.
terraform {
  required_version = ">= 1.16"

  # State lives in the shared GCS state bucket, under the prefix
  # agenticcraft/evaluating-traces/gemini_api_key. The bucket is shared by all stacks;
  # the prefix is per stack. Both are passed at init time by scripts/terraform-init.sh.
  backend "gcs" {}
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.5"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region

  # Bill API quota to this project. Needed when running with user credentials
  # (gcloud auth application-default login): some APIs, like API Keys, reject
  # calls that do not name a quota project.
  user_project_override = true
  billing_project       = var.project_id
}

resource "google_project_service" "apis" {
  for_each = toset([
    "apikeys.googleapis.com",
    "generativelanguage.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_apikeys_key" "gemini" {
  count        = var.create_secret ? 1 : 0
  name         = "devfest-gemini-key"
  display_name = "DevFest evals demo (Gemini API only)"

  restrictions {
    api_targets {
      service = "generativelanguage.googleapis.com"
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "gemini_api_key" {
  count     = var.create_secret ? 1 : 0
  secret_id = var.secret_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "gemini_api_key" {
  count  = var.create_secret ? 1 : 0
  secret = google_secret_manager_secret.gemini_api_key[0].id

  # Write-only: the value is sent to Secret Manager but not saved in Terraform state.
  # Bump the version number to push a new key.
  secret_data_wo         = google_apikeys_key.gemini[0].key_string
  secret_data_wo_version = 1
}

# Existing secret: fail early if it has no readable version, without copying the value into state.
data "google_secret_manager_secret_version" "existing" {
  count             = var.create_secret ? 0 : 1
  secret            = var.secret_id
  fetch_secret_data = false

  depends_on = [google_project_service.apis]
}
