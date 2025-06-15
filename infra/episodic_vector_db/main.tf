terraform {
  required_version = ">= 1.0.0"
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig
  }
}

resource "helm_release" "episodic_vector_db" {
  name       = "episodic-vector-db"
  namespace  = var.namespace
  repository = "https://qdrant.github.io/qdrant-helm"
  chart      = "qdrant"
  version    = var.qdrant_version

  set_sensitive {
    name  = "apiKey"
    value = var.api_key
  }

  values = [
    yamlencode({
      persistence = {
        enabled = true
        size    = "20Gi"
      }
    })
  ]
}

output "endpoint" {
  value = "http://episodic-vector-db.${var.namespace}.svc.cluster.local:6333"
}
