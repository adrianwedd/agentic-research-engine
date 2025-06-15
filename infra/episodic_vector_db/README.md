# Episodic Vector Database

This directory contains Terraform configuration for deploying a Qdrant vector database to power the Episodic Memory service. The setup relies on the Helm provider so that the database can be installed in any Kubernetes cluster using a single `terraform apply`.

## Prerequisites
- A reachable Kubernetes cluster
- `terraform` (>= 1.0)
- Access credentials and kubeconfig path supplied via variables

## Usage
Run the following commands, supplying sensitive values via environment variables or `-var` flags:

```bash
terraform init
terraform apply \
  -var="kubeconfig=$KUBECONFIG" \
  -var="namespace=ltm" \
  -var="api_key=$(SECRET_API_KEY)"
```

The `api_key` variable is marked as sensitive so it is never written to generated manifests. The service endpoint will be output after apply as `episodic-vector-db.<namespace>.svc.cluster.local:6333`.
