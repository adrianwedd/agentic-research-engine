variable "kubeconfig" {
  description = "Path to kubeconfig"
  type        = string
}

variable "namespace" {
  description = "Target namespace for the vector database"
  type        = string
  default     = "ltm"
}

variable "weaviate_version" {
  description = "Helm chart version to deploy"
  type        = string
  default     = "17.4.5"
}

variable "storage_size" {
  description = "Persistent volume size"
  type        = string
  default     = "10Gi"
}

variable "api_key" {
  description = "Optional admin API key"
  type        = string
  default     = ""
}
