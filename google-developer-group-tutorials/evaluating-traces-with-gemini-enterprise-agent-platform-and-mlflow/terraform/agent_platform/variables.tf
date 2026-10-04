variable "project_id" {
  description = "Google Cloud project to deploy the demo into."
  type        = string
}

variable "region" {
  description = "Region for Agent Runtime and evaluation. europe-west1 supports both."
  type        = string
  default     = "europe-west1"
}
