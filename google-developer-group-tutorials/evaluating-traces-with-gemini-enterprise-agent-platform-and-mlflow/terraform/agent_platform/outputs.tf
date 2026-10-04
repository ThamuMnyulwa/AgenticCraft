output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "bucket_name" {
  value = google_storage_bucket.demo.name
}

output "agent_service_account_email" {
  value = google_service_account.agent.email
}
