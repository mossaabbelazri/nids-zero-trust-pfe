variable "project_id" {
  description = "L'ID de ton projet GCP"
  type        = string
  # Remplace par ton vrai ID de projet
  default     = "zero-trust-mlops-pfe" 
}

variable "region" {
  description = "La region de deploiement"
  type        = string
  default     = "europe-west1"
}