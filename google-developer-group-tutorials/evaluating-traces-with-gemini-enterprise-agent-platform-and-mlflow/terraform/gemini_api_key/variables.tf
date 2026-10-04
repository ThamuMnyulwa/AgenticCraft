variable "project_id" {
  description = "Google Cloud project that owns the API key and the secret."
  type        = string
}

variable "region" {
  description = "Default region for the provider. API keys and auto-replicated secrets are global."
  type        = string
  default     = "europe-west1"
}

variable "secret_id" {
  description = "Secret Manager secret that holds the Gemini API key. Must match GEMINI_SECRET_ID in .env."
  type        = string
  default     = "gemini-api-key"
}

variable "create_secret" {
  description = "true creates the key and secret. false uses an existing secret named secret_id."
  type        = bool
  default     = true
}
