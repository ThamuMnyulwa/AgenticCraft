terraform {
  required_version = ">= 1.16"

  # State lives in the shared GCS state bucket, under the prefix
  # agenticcraft/evaluating-traces/agent_platform. The bucket is shared by all stacks;
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

# APIs listed on the Agent Runtime setup page, plus IAM and Service Usage for this config.
locals {
  apis = [
    "agentidentity.googleapis.com", # Agent Platform console: agent identity
    "agentregistry.googleapis.com", # Agent Platform console: Agent Registry
    "aiplatform.googleapis.com",
    "apphub.googleapis.com",           # the agent's Topology view in the console
    "apptopology.googleapis.com",      # the agent's Topology view in the console
    "cloudapiregistry.googleapis.com", # Agent Platform console: API registry
    "cloudresourcemanager.googleapis.com",
    "cloudtrace.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "observability.googleapis.com", # trace storage and Trace Explorer for telemetry.googleapis.com
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "telemetry.googleapis.com",
  ]

  agent_roles = [
    "roles/aiplatform.user",                   # call Gemini and the Agent Platform APIs
    "roles/cloudtrace.agent",                  # write traces
    "roles/logging.logWriter",                 # write logs
    "roles/monitoring.metricWriter",           # write metrics
    "roles/serviceusage.serviceUsageConsumer", # use enabled APIs in this project
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  service            = each.value
  disable_on_destroy = false
}

# One bucket for agent staging files and evaluation results.
resource "google_storage_bucket" "demo" {
  name                        = "${var.project_id}-devfest-evals"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true # demo only: lets terraform destroy remove results too

  depends_on = [google_project_service.apis]
}

# The identity the deployed agent runs as.
resource "google_service_account" "agent" {
  account_id   = "devfest-agent"
  display_name = "DevFest evals demo agent"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "agent" {
  for_each = toset(local.agent_roles)
  project  = var.project_id
  role     = each.value
  member   = google_service_account.agent.member
}

resource "google_storage_bucket_iam_member" "agent_bucket" {
  bucket = google_storage_bucket.demo.name
  role   = "roles/storage.objectUser"
  member = google_service_account.agent.member
}
