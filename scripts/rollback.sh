#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <environment>" >&2
  exit 1
fi

ENV="$1"
CURRENT_COLOR=$(kubectl get svc agent-services -n "$ENV" -o jsonpath='{.spec.selector.color}')
if [ "$CURRENT_COLOR" = "blue" ]; then
  PREV_COLOR="green"
else
  PREV_COLOR="blue"
fi

if kubectl get deployment/agent-services-$PREV_COLOR -n "$ENV" >/dev/null 2>&1; then
  kubectl patch svc agent-services -n "$ENV" \
    -p "{\"spec\":{\"selector\":{\"app\":\"agent-services\",\"color\":\"$PREV_COLOR\"}}}"
  kubectl delete deployment/agent-services-$CURRENT_COLOR -n "$ENV"
else
  echo "Rollback failed: deployment agent-services-$PREV_COLOR does not exist" >&2
  exit 1
fi
