output "secret_name" {
  description = "Read the key with: gcloud secrets versions access latest --secret=<secret_id>"
  value = (
    var.create_secret
    ? google_secret_manager_secret.gemini_api_key[0].name
    : "projects/${var.project_id}/secrets/${var.secret_id}"
  )
}

output "mode" {
  value = var.create_secret ? "created" : "existing"
}
