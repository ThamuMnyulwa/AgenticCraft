variable "project_id" {
  description = "Google Cloud project that owns the API key."
  type        = string
}

variable "region" {
  description = "Default region for the provider. API keys themselves are global."
  type        = string
  default     = "europe-west1"
}
