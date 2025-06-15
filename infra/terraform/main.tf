terraform {
  required_version = ">= 1.0.0"
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig
  }
}

variable "kubeconfig" {
  description = "Path to kubeconfig file"
  type        = string
}

variable "namespace" {
  description = "Target namespace"
  type        = string
  default     = "staging"
}

variable "image_tag" {
  description = "Image tag to deploy"
  type        = string
}

resource "helm_release" "agent_services" {
  name       = "agent-services"
  namespace  = var.namespace
  chart      = "../helm/agent-services"
  values     = [
    yamlencode({
      image = {
        repository = "agentic/research-engine"
        tag        = var.image_tag
      }
      color = var.namespace == "production" ? "green" : "blue"
    })
  ]
}
