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
  repository = "https://weaviate.github.io/weaviate-helm"
  chart      = "weaviate"
  version    = var.weaviate_version

  values = [
    yamlencode({
      persistence = {
        enabled = true
        size    = "20Gi"
      }
      env = {
        QUERY_DEFAULTS_LIMIT    = 20
        DEFAULT_VECTORIZER_MODULE = "none"
        DISABLE_TELEMETRY      = "true"
      }
    })
  ]
}

output "endpoint" {
  value = "http://episodic-vector-db.${var.namespace}.svc.cluster.local:8080"
}
