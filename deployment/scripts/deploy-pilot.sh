#!/bin/bash

# ORCHESTRIX Pilot Deployment Script
# Classification: CRITICAL - DEPLOYMENT AUTOMATION
# Last Updated: 2025-08-08

set -euo pipefail

# Configuration
ENVIRONMENT="pilot"
AWS_REGION="us-west-2"
CLUSTER_NAME="orchestrix-pilot-cluster"
NAMESPACE="orchestrix-pilot"
TERRAFORM_DIR="$(dirname "$0")/../terraform"
K8S_DIR="$(dirname "$0")/../k8s"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    local tools=("terraform" "kubectl" "aws" "helm")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check Terraform version
    local tf_version=$(terraform version -json | jq -r .terraform_version)
    if [[ $(echo -e "1.0.0\n$tf_version" | sort -V | head -n1) != "1.0.0" ]]; then
        log_error "Terraform version 1.0.0 or higher is required (found: $tf_version)"
        exit 1
    fi
    
    log_info "Prerequisites check passed ✓"
}

# Deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    terraform init
    
    # Validate configuration
    terraform validate
    
    # Plan deployment
    terraform plan -var="environment=$ENVIRONMENT" -var="aws_region=$AWS_REGION" -out=tfplan
    
    # Apply if plan looks good
    read -p "Do you want to apply the Terraform plan? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        terraform apply tfplan
        log_info "Infrastructure deployment completed ✓"
    else
        log_warn "Infrastructure deployment cancelled"
        exit 0
    fi
    
    # Get outputs
    CLUSTER_ENDPOINT=$(terraform output -raw cluster_endpoint)
    DATABASE_ENDPOINT=$(terraform output -raw database_endpoint)
    
    log_info "Cluster endpoint: $CLUSTER_ENDPOINT"
}

# Configure kubectl
configure_kubectl() {
    log_info "Configuring kubectl for EKS cluster..."
    
    aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"
    
    # Test connectivity
    if kubectl cluster-info &> /dev/null; then
        log_info "Kubectl configuration successful ✓"
    else
        log_error "Failed to connect to Kubernetes cluster"
        exit 1
    fi
}

# Install cluster add-ons
install_cluster_addons() {
    log_info "Installing cluster add-ons..."
    
    # Install External Secrets Operator
    helm repo add external-secrets https://charts.external-secrets.io
    helm repo update
    
    helm upgrade --install external-secrets external-secrets/external-secrets \
        --namespace external-secrets-system \
        --create-namespace \
        --set installCRDs=true \
        --wait
    
    # Install NGINX Ingress Controller
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo update
    
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        --namespace ingress-nginx \
        --create-namespace \
        --set controller.service.type=LoadBalancer \
        --set controller.metrics.enabled=true \
        --wait
    
    # Install cert-manager
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    
    helm upgrade --install cert-manager jetstack/cert-manager \
        --namespace cert-manager \
        --create-namespace \
        --version v1.13.0 \
        --set installCRDs=true \
        --wait
    
    # Install Istio (for service mesh)
    curl -L https://istio.io/downloadIstio | sh -
    export PATH="$PWD/istio-*/bin:$PATH"
    istioctl install --set values.defaultRevision=default -y
    
    log_info "Cluster add-ons installation completed ✓"
}

# Deploy application
deploy_application() {
    log_info "Deploying application components..."
    
    cd "$K8S_DIR"
    
    # Create namespace and RBAC
    kubectl apply -f namespace.yaml
    
    # Wait for namespace to be ready
    kubectl wait --for=condition=Ready namespace/$NAMESPACE --timeout=60s
    
    # Deploy external secrets
    kubectl apply -f external-secrets.yaml
    
    # Wait for secrets to be created
    log_info "Waiting for secrets to be populated..."
    kubectl wait --for=condition=Ready externalsecret/application-secrets -n $NAMESPACE --timeout=300s
    
    # Deploy monitoring stack
    kubectl apply -f monitoring-stack.yaml
    
    # Deploy application services
    kubectl apply -f secure-deployment.yaml
    
    # Deploy API gateway
    kubectl apply -f api-gateway.yaml
    
    # Deploy disaster recovery components
    kubectl apply -f disaster-recovery.yaml
    
    log_info "Application deployment completed ✓"
}

# Wait for deployments
wait_for_deployments() {
    log_info "Waiting for all deployments to be ready..."
    
    local deployments=(
        "episodic-memory"
        "reputation-service" 
        "prometheus"
        "grafana"
        "jaeger"
        "otel-collector"
    )
    
    for deployment in "${deployments[@]}"; do
        log_info "Waiting for $deployment..."
        kubectl rollout status deployment/$deployment -n $NAMESPACE --timeout=600s
    done
    
    # Wait for StatefulSets
    kubectl rollout status statefulset/weaviate -n $NAMESPACE --timeout=600s
    
    log_info "All deployments are ready ✓"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check pod status
    kubectl get pods -n $NAMESPACE
    
    # Check service endpoints
    local services=("episodic-memory" "reputation-service" "weaviate" "prometheus" "grafana")
    
    for service in "${services[@]}"; do
        local endpoint=$(kubectl get svc $service -n $NAMESPACE -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}')
        log_info "Testing $service at $endpoint..."
        
        # Port forward and test
        kubectl port-forward svc/$service 8080:${endpoint##*:} -n $NAMESPACE &
        local pf_pid=$!
        sleep 5
        
        if curl -f -s -o /dev/null --max-time 10 "http://localhost:8080/health" 2>/dev/null || \
           curl -f -s -o /dev/null --max-time 10 "http://localhost:8080/" 2>/dev/null; then
            log_info "$service health check passed ✓"
        else
            log_warn "$service health check failed"
        fi
        
        kill $pf_pid 2>/dev/null || true
        sleep 2
    done
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Get Grafana admin password
    local grafana_password=$(kubectl get secret grafana-secrets -n $NAMESPACE -o jsonpath='{.data.admin-password}' | base64 -d)
    
    log_info "Grafana admin password: $grafana_password"
    log_info "Grafana URL: http://$(kubectl get svc grafana -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'):3000"
    log_info "Prometheus URL: http://$(kubectl get svc prometheus -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'):9090"
    log_info "Jaeger URL: http://$(kubectl get svc jaeger-query -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'):16686"
    
    # Import Grafana dashboards
    log_info "Consider importing pre-built dashboards for application monitoring"
}

# Display deployment summary
display_summary() {
    log_info "Deployment Summary"
    echo "=================="
    echo
    echo "Environment: $ENVIRONMENT"
    echo "Namespace: $NAMESPACE"
    echo "Cluster: $CLUSTER_NAME"
    echo "Region: $AWS_REGION"
    echo
    echo "Services deployed:"
    kubectl get svc -n $NAMESPACE
    echo
    echo "Deployments status:"
    kubectl get deployments -n $NAMESPACE
    echo
    echo "Next steps:"
    echo "1. Configure DNS for pilot-api.orchestrix.ai"
    echo "2. Update OAuth2 proxy configuration with OIDC details"
    echo "3. Import Grafana dashboards"
    echo "4. Configure alerting rules"
    echo "5. Run security scan and penetration testing"
    echo
    echo "Emergency contacts and runbooks are available in the disaster-recovery ConfigMap"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f "$TERRAFORM_DIR/tfplan" 2>/dev/null || true
}

# Main execution
main() {
    log_info "Starting ORCHESTRIX Pilot Deployment"
    log_info "===================================="
    
    trap cleanup EXIT
    
    check_prerequisites
    deploy_infrastructure
    configure_kubectl
    install_cluster_addons
    deploy_application
    wait_for_deployments
    run_health_checks
    setup_monitoring
    display_summary
    
    log_info "Pilot deployment completed successfully! 🎉"
    log_warn "Remember to run security validation before proceeding to production"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "destroy")
        log_warn "Destroying pilot environment..."
        read -p "Are you sure you want to destroy the pilot environment? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kubectl delete namespace $NAMESPACE --wait=true
            cd "$TERRAFORM_DIR" && terraform destroy -auto-approve
            log_info "Pilot environment destroyed"
        fi
        ;;
    "status")
        kubectl get all -n $NAMESPACE
        ;;
    "logs")
        kubectl logs -f deployment/${2:-episodic-memory} -n $NAMESPACE
        ;;
    *)
        echo "Usage: $0 {deploy|destroy|status|logs [service]}"
        exit 1
        ;;
esac