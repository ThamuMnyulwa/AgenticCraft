output "gemini_api_key" {
  description = "Read with: terraform output -raw gemini_api_key"
  value       = google_apikeys_key.gemini.key_string
  sensitive   = true
}
