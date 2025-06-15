#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <environment> <image-tag>" >&2
  exit 1
fi

ENV="$1"
TAG="$2"

terraform -chdir=infra/terraform init -input=false
terraform -chdir=infra/terraform apply -auto-approve \
  -var="kubeconfig=$HOME/.kube/config" \
  -var="namespace=$ENV" \
  -var="image_tag=$TAG"

helm upgrade --install agent-services infra/helm/agent-services \
  --namespace "$ENV" --create-namespace \
  --set image.tag="$TAG" \
  --set color="$ENV"
