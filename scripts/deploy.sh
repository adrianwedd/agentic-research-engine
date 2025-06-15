#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <environment> <image-tag>" >&2
  exit 1
fi

ENV="$1"
TAG="$2"

# Detect currently active color from the service selector (defaults to blue)
CURRENT_COLOR=$(kubectl get svc agent-services -n "$ENV" -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "blue")
if [ "$CURRENT_COLOR" = "blue" ]; then
  NEW_COLOR="green"
else
  NEW_COLOR="blue"
fi

terraform -chdir=infra/terraform init -input=false
terraform -chdir=infra/terraform apply -auto-approve \
  -var="kubeconfig=$HOME/.kube/config" \
  -var="namespace=$ENV" \
  -var="image_tag=$TAG" \
  -var="color=$NEW_COLOR"

# Wait for new deployment to become ready
kubectl rollout status deployment/agent-services-$NEW_COLOR -n "$ENV"

# Shift traffic to the new deployment
kubectl patch svc agent-services -n "$ENV" \
  -p "{\"spec\":{\"selector\":{\"app\":\"agent-services\",\"color\":\"$NEW_COLOR\"}}}"

# Remove the old deployment after traffic switch
if kubectl get deployment/agent-services-$CURRENT_COLOR -n "$ENV" >/dev/null 2>&1; then
  kubectl delete deployment/agent-services-$CURRENT_COLOR -n "$ENV"
fi
