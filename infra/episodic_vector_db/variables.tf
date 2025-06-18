variable "kubeconfig" {
  description = "Path to kubeconfig"
  type        = string
}

variable "namespace" {
  description = "Target namespace for the vector database"
  type        = string
  default     = "ltm"
}

variable "milvus_version" {
  description = "Helm chart version to deploy"
  type        = string
  default     = "4.0.5"
}
