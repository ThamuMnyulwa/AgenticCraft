# A Gemini API key as code. The same kind of key AI Studio creates,
# restricted so it can only call the Gemini API. Needs no billing.
terraform {
  required_version = ">= 1.16"
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
}

resource "google_project_service" "apis" {
  for_each = toset([
    "apikeys.googleapis.com",
    "generativelanguage.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_apikeys_key" "gemini" {
  name         = "devfest-gemini-key"
  display_name = "DevFest evals demo (Gemini API only)"

  restrictions {
    api_targets {
      service = "generativelanguage.googleapis.com"
    }
  }

  depends_on = [google_project_service.apis]
}
