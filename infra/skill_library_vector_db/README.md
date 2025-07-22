# SkillLibrary Vector Store

This directory contains Terraform configuration for deploying a Weaviate vector database to power the SkillLibrary. The setup relies on the Helm provider so that the database can be installed in any Kubernetes cluster using a single `terraform apply`.

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
  -var="namespace=ltm"
```

The service endpoint will be output after apply as `skilllib-vector-db.<namespace>.svc.cluster.local:8080`.

Configure the LTM service to connect by setting the following environment variables:

- `WEAVIATE_URL` – endpoint of the Weaviate instance.
- `WEAVIATE_API_KEY` – API key if authentication is enabled (optional).

### Configuration Variables
- `storage_size` - Persistent volume size for data (default `10Gi`).
- `api_key` - Optional admin API key for Weaviate.

