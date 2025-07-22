terraform {
  required_version = ">= 1.0.0"
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig
  }
}

resource "helm_release" "skilllib_vector_db" {
  name       = "skilllib-vector-db"
  namespace  = var.namespace
  repository = "https://weaviate.github.io/weaviate-helm"
  chart      = "weaviate"
  version    = var.weaviate_version

  values = [
    yamlencode({
      persistence = {
        enabled = true
        size    = var.storage_size
      }
      env = merge({
        QUERY_DEFAULTS_LIMIT = 20
        DEFAULT_VECTORIZER_MODULE = "none"
        DISABLE_TELEMETRY = "true"
      }, var.api_key != "" ? {
        AUTHENTICATION_APIKEY_ENABLED      = "true"
        AUTHENTICATION_APIKEY_ALLOWED_KEYS = var.api_key
        AUTHENTICATION_APIKEY_USERS        = "skilllib"
      } : {})
    })
  ]
}

output "endpoint" {
  value = "http://skilllib-vector-db.${var.namespace}.svc.cluster.local:8080"
}
