#!/usr/bin/env bash
# Agentic Research Engine Deployment Script
# Enhanced with error handling and security checks
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

if [ $# -lt 2 ]; then
  log_error "Usage: $0 <environment> <image-tag>"
  log_error "Valid environments: staging, production, development"
  exit 1
fi

ENV="$1"
TAG="$2"

# Validate environment
case "$ENV" in
    staging|production|development)
        log_info "Deploying to environment: $ENV"
        ;;
    *)
        log_error "Invalid environment: $ENV"
        log_error "Valid environments: staging, production, development"
        exit 1
        ;;
esac

# Security check for production
if [[ "$ENV" == "production" ]]; then
    log_warning "Production deployment detected - running security checks..."
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        log_error "Uncommitted changes detected. Commit your changes before production deployment."
        exit 1
    fi
    
    # Verify we're on main branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$CURRENT_BRANCH" != "main" ]]; then
        log_error "Production deployments must be from main branch. Current: $CURRENT_BRANCH"
        exit 1
    fi
    
    log_success "Production security checks passed"
fi

# Pre-deployment checks
log_info "Running pre-deployment checks..."

# Check kubectl access
if ! kubectl cluster-info >/dev/null 2>&1; then
    log_error "Unable to connect to Kubernetes cluster"
    exit 1
fi

# Check namespace exists
if ! kubectl get namespace "$ENV" >/dev/null 2>&1; then
    log_warning "Namespace $ENV does not exist, creating..."
    kubectl create namespace "$ENV" || {
        log_error "Failed to create namespace $ENV"
        exit 1
    }
fi

# Detect currently active color from the service selector (defaults to blue)
log_info "Detecting current deployment color..."
CURRENT_COLOR=$(kubectl get svc agent-services -n "$ENV" -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "blue")
if [ "$CURRENT_COLOR" = "blue" ]; then
  NEW_COLOR="green"
else
  NEW_COLOR="blue"
fi

log_info "Current color: $CURRENT_COLOR, New color: $NEW_COLOR"

# Infrastructure deployment
log_info "Initializing Terraform..."
if [[ -d "infra/terraform" ]]; then
    terraform -chdir=infra/terraform init -input=false || {
        log_error "Terraform initialization failed"
        exit 1
    }
    
    log_info "Applying infrastructure changes..."
    terraform -chdir=infra/terraform apply -auto-approve \
      -var="kubeconfig=$HOME/.kube/config" \
      -var="namespace=$ENV" \
      -var="image_tag=$TAG" \
      -var="color=$NEW_COLOR" || {
        log_error "Terraform apply failed"
        exit 1
    }
    
    log_success "Infrastructure deployment completed"
else
    log_warning "No Terraform configuration found, skipping infrastructure deployment"
fi

# Wait for new deployment to become ready
log_info "Waiting for deployment to become ready..."
if kubectl get deployment/agent-services-$NEW_COLOR -n "$ENV" >/dev/null 2>&1; then
    kubectl rollout status deployment/agent-services-$NEW_COLOR -n "$ENV" --timeout=300s || {
        log_error "Deployment rollout failed or timed out"
        log_error "Rolling back..."
        kubectl rollout undo deployment/agent-services-$NEW_COLOR -n "$ENV" 2>/dev/null || true
        exit 1
    }
    log_success "Deployment is ready"
else
    log_error "Deployment agent-services-$NEW_COLOR not found in namespace $ENV"
    exit 1
fi

# Health check before traffic switch
log_info "Running health checks before traffic switch..."
SERVICE_IP=$(kubectl get svc agent-services-$NEW_COLOR -n "$ENV" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
if [[ -n "$SERVICE_IP" ]]; then
    log_info "Service IP: $SERVICE_IP"
    # Additional health checks could be added here
fi

# Shift traffic to the new deployment
log_info "Switching traffic to new deployment..."
if kubectl get svc agent-services -n "$ENV" >/dev/null 2>&1; then
    kubectl patch svc agent-services -n "$ENV" \
      -p "{\"spec\":{\"selector\":{\"app\":\"agent-services\",\"color\":\"$NEW_COLOR\"}}}" || {
        log_error "Failed to switch traffic to new deployment"
        exit 1
    }
    log_success "Traffic switched to new deployment"
else
    log_warning "Service agent-services not found, skipping traffic switch"
fi

# Wait a moment for traffic to stabilize
log_info "Waiting for traffic to stabilize..."
sleep 10

# Remove the old deployment after traffic switch
if kubectl get deployment/agent-services-$CURRENT_COLOR -n "$ENV" >/dev/null 2>&1; then
    log_info "Cleaning up old deployment..."
    kubectl delete deployment/agent-services-$CURRENT_COLOR -n "$ENV" || {
        log_warning "Failed to delete old deployment, manual cleanup may be required"
    }
    log_success "Old deployment cleaned up"
fi

# Final status report
log_success "🎉 Deployment completed successfully!"
log_success "Environment: $ENV"
log_success "Image Tag: $TAG"
log_success "Active Color: $NEW_COLOR"
log_info "Deployment timestamp: $(date -Iseconds)"
