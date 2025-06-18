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
  repository = "https://milvus-io.github.io/milvus-helm"
  chart      = "milvus"
  version    = var.milvus_version

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
  value = "tcp://episodic-vector-db.${var.namespace}.svc.cluster.local:19530"
}
