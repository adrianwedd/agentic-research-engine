variable "kubeconfig" {
  description = "Path to kubeconfig"
  type        = string
}

variable "namespace" {
  description = "Target namespace for the vector database"
  type        = string
  default     = "ltm"
}

variable "qdrant_version" {
  description = "Helm chart version to deploy"
  type        = string
  default     = "0.6.2"
}

variable "api_key" {
  description = "Admin API key for qdrant"
  type        = string
  sensitive   = true
}
