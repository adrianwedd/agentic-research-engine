#!/bin/bash

# Production Deployment Script - Agentic Research Engine
# Classification: CRITICAL - PRODUCTION DEPLOYMENT
# Last Updated: 2025-08-08
# 
# This script provides comprehensive production deployment automation with
# validation, rollback capabilities, and operational safety checks.

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$(dirname "${SCRIPT_DIR}")")"
readonly NAMESPACE="${NAMESPACE:-orchestrix-pilot}"
readonly ENVIRONMENT="${ENVIRONMENT:-production}"
readonly SERVICE_VERSION="${SERVICE_VERSION:-v1.0.0}"
readonly TIMEOUT="${TIMEOUT:-600}"
readonly LOG_FILE="${LOG_FILE:-/tmp/production-deploy-$(date +%Y%m%d-%H%M%S).log}"

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $*${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*${NC}" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $*${NC}" | tee -a "$LOG_FILE"
}

# Pre-flight checks
check_prerequisites() {
    log "Performing pre-flight checks..."
    
    # Check required tools
    local required_tools=("kubectl" "docker" "helm")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is required but not installed"
        fi
    done
    
    # Check Kubernetes connectivity
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
    fi
    
    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log "Creating namespace $NAMESPACE..."
        kubectl create namespace "$NAMESPACE"
    fi
    
    # Check required secrets exist
    local required_secrets=("application-secrets" "grafana-secrets")
    for secret in "${required_secrets[@]}"; do
        if ! kubectl get secret "$secret" -n "$NAMESPACE" &> /dev/null; then
            error "Required secret '$secret' not found in namespace '$NAMESPACE'"
        fi
    done
    
    success "Pre-flight checks completed successfully"
}

# Build and push Docker images
build_and_push_images() {
    log "Building and pushing Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build the main application image
    docker build -t "agentic/research-engine:$SERVICE_VERSION" .
    
    # Tag for production registry (replace with your registry)
    local registry="${DOCKER_REGISTRY:-docker.io}"
    docker tag "agentic/research-engine:$SERVICE_VERSION" "$registry/agentic/research-engine:$SERVICE_VERSION"
    
    # Push to registry
    log "Pushing image to registry..."
    docker push "$registry/agentic/research-engine:$SERVICE_VERSION"
    
    success "Docker images built and pushed successfully"
}

# Apply Kubernetes configurations
deploy_infrastructure() {
    log "Deploying infrastructure components..."
    
    cd "$PROJECT_ROOT/deployment/k8s"
    
    # Apply namespace first
    kubectl apply -f namespace.yaml
    
    # Apply monitoring stack
    log "Deploying monitoring stack..."
    kubectl apply -f monitoring-stack.yaml
    kubectl wait --for=condition=available --timeout="${TIMEOUT}s" deployment/prometheus -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout="${TIMEOUT}s" deployment/grafana -n "$NAMESPACE"
    kubectl wait --for=condition=available --timeout="${TIMEOUT}s" deployment/jaeger -n "$NAMESPACE"
    
    # Apply external secrets if available
    if [[ -f external-secrets.yaml ]]; then
        log "Deploying external secrets operator configuration..."
        kubectl apply -f external-secrets.yaml
    fi
    
    success "Infrastructure components deployed successfully"
}

# Deploy application services
deploy_services() {
    log "Deploying application services..."
    
    cd "$PROJECT_ROOT/deployment/k8s"
    
    # Update image tags in deployment
    sed -i.bak "s|agentic/research-engine:.*|agentic/research-engine:${SERVICE_VERSION}|g" secure-deployment.yaml
    
    # Apply the main deployment
    kubectl apply -f secure-deployment.yaml
    
    # Wait for deployments to be ready
    local deployments=("episodic-memory" "reputation-service" "weaviate" "redis")
    for deployment in "${deployments[@]}"; do
        log "Waiting for $deployment to be ready..."
        kubectl wait --for=condition=available --timeout="${TIMEOUT}s" deployment/"$deployment" -n "$NAMESPACE" || {
            error "Deployment $deployment failed to become ready"
        }
    done
    
    success "Application services deployed successfully"
}

# Validate deployment
validate_deployment() {
    log "Validating deployment..."
    
    # Check pod health
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | grep -E "(episodic-memory|reputation-service)" | awk '{print $1}')
    
    for pod in $pods; do
        log "Checking health of pod: $pod"
        
        # Wait for pod to be ready
        kubectl wait --for=condition=ready --timeout=120s pod/"$pod" -n "$NAMESPACE" || {
            error "Pod $pod is not ready"
        }
        
        # Check health endpoints
        local service_name
        service_name=$(echo "$pod" | cut -d'-' -f1-2)
        
        case "$service_name" in
            "episodic-memory")
                validate_service_health "$pod" 8081 "/health" "/ready"
                ;;
            "reputation-service")
                validate_service_health "$pod" 8090 "/health" "/ready"
                ;;
        esac
    done
    
    # Check service connectivity
    log "Validating service connectivity..."
    validate_service_connectivity
    
    success "Deployment validation completed successfully"
}

# Validate individual service health
validate_service_health() {
    local pod="$1"
    local port="$2"
    local health_path="$3"
    local ready_path="$4"
    
    log "Validating health endpoints for $pod..."
    
    # Health check
    kubectl exec -n "$NAMESPACE" "$pod" -- curl -sf "http://localhost:${port}${health_path}" > /dev/null || {
        error "Health check failed for $pod"
    }
    
    # Readiness check
    kubectl exec -n "$NAMESPACE" "$pod" -- curl -sf "http://localhost:${port}${ready_path}" > /dev/null || {
        error "Readiness check failed for $pod"
    }
    
    log "Health validation successful for $pod"
}

# Validate service-to-service connectivity
validate_service_connectivity() {
    log "Testing service-to-service connectivity..."
    
    # Get service endpoints
    local episodic_ip
    local reputation_ip
    
    episodic_ip=$(kubectl get svc episodic-memory -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    reputation_ip=$(kubectl get svc reputation-service -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
    
    # Test from within cluster using a temporary pod
    kubectl run connectivity-test --image=curlimages/curl:latest --rm -i --restart=Never -n "$NAMESPACE" -- sh -c "
        curl -sf http://${episodic_ip}:8081/health &&
        curl -sf http://${reputation_ip}:8090/health
    " || {
        error "Service connectivity validation failed"
    }
    
    log "Service connectivity validation successful"
}

# Rollback deployment if needed
rollback_deployment() {
    local previous_version="$1"
    warn "Initiating rollback to version: $previous_version"
    
    cd "$PROJECT_ROOT/deployment/k8s"
    
    # Update image tags for rollback
    sed -i.bak "s|agentic/research-engine:.*|agentic/research-engine:${previous_version}|g" secure-deployment.yaml
    
    # Apply rollback
    kubectl apply -f secure-deployment.yaml
    
    # Wait for rollback to complete
    local deployments=("episodic-memory" "reputation-service")
    for deployment in "${deployments[@]}"; do
        log "Rolling back $deployment..."
        kubectl rollout status deployment/"$deployment" -n "$NAMESPACE" --timeout="${TIMEOUT}s" || {
            error "Rollback failed for $deployment"
        }
    done
    
    warn "Rollback completed to version: $previous_version"
}

# Setup monitoring and alerting
setup_monitoring() {
    log "Setting up monitoring and alerting..."
    
    # Port-forward to access Grafana (for initial setup only)
    # In production, use proper ingress/load balancer
    
    local grafana_pod
    grafana_pod=$(kubectl get pods -n "$NAMESPACE" -l app=grafana --no-headers -o custom-columns=":metadata.name" | head -n1)
    
    if [[ -n "$grafana_pod" ]]; then
        log "Grafana pod: $grafana_pod"
        log "To access Grafana, run: kubectl port-forward -n $NAMESPACE $grafana_pod 3000:3000"
        log "Default credentials: admin / (check grafana-secrets)"
    fi
    
    # Check Prometheus targets
    local prometheus_pod
    prometheus_pod=$(kubectl get pods -n "$NAMESPACE" -l app=prometheus --no-headers -o custom-columns=":metadata.name" | head -n1)
    
    if [[ -n "$prometheus_pod" ]]; then
        log "Prometheus pod: $prometheus_pod"
        log "To access Prometheus, run: kubectl port-forward -n $NAMESPACE $prometheus_pod 9090:9090"
    fi
    
    success "Monitoring setup completed"
}

# Performance and load testing
run_smoke_tests() {
    log "Running smoke tests..."
    
    # Basic smoke tests to ensure services are responding
    local episodic_svc="episodic-memory.${NAMESPACE}.svc.cluster.local"
    local reputation_svc="reputation-service.${NAMESPACE}.svc.cluster.local"
    
    kubectl run smoke-test --image=curlimages/curl:latest --rm -i --restart=Never -n "$NAMESPACE" -- sh -c "
        echo 'Testing episodic memory service...' &&
        curl -sf http://${episodic_svc}:8081/health &&
        echo 'Testing reputation service...' &&
        curl -sf http://${reputation_svc}:8090/health &&
        echo 'All smoke tests passed!'
    " || {
        error "Smoke tests failed"
    }
    
    success "Smoke tests completed successfully"
}

# Generate deployment report
generate_deployment_report() {
    log "Generating deployment report..."
    
    local report_file="/tmp/deployment-report-$(date +%Y%m%d-%H%M%S).txt"
    
    cat > "$report_file" << EOF
# Production Deployment Report
Date: $(date)
Namespace: $NAMESPACE
Environment: $ENVIRONMENT
Version: $SERVICE_VERSION

## Deployed Services
$(kubectl get deployments -n "$NAMESPACE" -o wide)

## Service Status
$(kubectl get services -n "$NAMESPACE" -o wide)

## Pod Status
$(kubectl get pods -n "$NAMESPACE" -o wide)

## Resource Usage
$(kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "Metrics server not available")

## Events
$(kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -n 20)
EOF
    
    log "Deployment report generated: $report_file"
    success "Deployment completed successfully!"
}

# Cleanup function
cleanup() {
    log "Performing cleanup..."
    # Add any cleanup operations here
}

# Signal handlers
trap cleanup EXIT
trap 'error "Script interrupted"' INT TERM

# Main execution
main() {
    log "Starting production deployment for Agentic Research Engine"
    log "Environment: $ENVIRONMENT, Version: $SERVICE_VERSION, Namespace: $NAMESPACE"
    
    # Store previous deployment for rollback capability
    local previous_version=""
    if kubectl get deployment episodic-memory -n "$NAMESPACE" &> /dev/null; then
        previous_version=$(kubectl get deployment episodic-memory -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d':' -f2)
        log "Previous deployment version detected: $previous_version"
    fi
    
    # Execute deployment steps
    check_prerequisites
    build_and_push_images
    deploy_infrastructure
    deploy_services
    
    # Validation with rollback on failure
    if ! validate_deployment; then
        if [[ -n "$previous_version" ]]; then
            rollback_deployment "$previous_version"
        else
            error "Deployment validation failed and no previous version available for rollback"
        fi
    fi
    
    run_smoke_tests
    setup_monitoring
    generate_deployment_report
    
    success "Production deployment completed successfully!"
    log "Deployment log saved to: $LOG_FILE"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi