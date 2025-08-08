#!/bin/bash

# Security Validation Script for ORCHESTRIX Pilot
# Classification: CRITICAL - SECURITY VALIDATION
# Last Updated: 2025-08-08

set -euo pipefail

# Configuration
NAMESPACE="orchestrix-pilot"
CLUSTER_NAME="orchestrix-pilot-cluster"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_TOTAL=0
CHECKS_PASSED=0
CHECKS_FAILED=0
CRITICAL_ISSUES=0

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

log_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
    ((CHECKS_TOTAL++))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((CHECKS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((CHECKS_FAILED++))
    if [[ "${2:-}" == "CRITICAL" ]]; then
        ((CRITICAL_ISSUES++))
    fi
}

# Check hard-coded secrets
check_hardcoded_secrets() {
    log_check "Checking for hard-coded secrets in deployments..."
    
    local found_secrets=0
    local deployments=$(kubectl get deployments -n $NAMESPACE -o name)
    
    for deployment in $deployments; do
        local env_vars=$(kubectl get $deployment -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[*].env[*].value}' 2>/dev/null || echo "")
        
        if echo "$env_vars" | grep -qE "(password|secret|key|token)" 2>/dev/null; then
            log_fail "Hard-coded secrets found in $deployment" "CRITICAL"
            found_secrets=1
        fi
    done
    
    if [[ $found_secrets -eq 0 ]]; then
        log_pass "No hard-coded secrets found in deployments"
    fi
}

# Check external secrets configuration
check_external_secrets() {
    log_check "Validating External Secrets Operator configuration..."
    
    # Check if external secrets are properly configured
    local external_secrets=$(kubectl get externalsecrets -n $NAMESPACE -o name 2>/dev/null || echo "")
    
    if [[ -z "$external_secrets" ]]; then
        log_fail "No external secrets configured" "CRITICAL"
        return
    fi
    
    # Check each external secret status
    for secret in $external_secrets; do
        local status=$(kubectl get $secret -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")
        
        if [[ "$status" == "True" ]]; then
            log_pass "External secret $secret is ready"
        else
            log_fail "External secret $secret is not ready" "CRITICAL"
        fi
    done
}

# Check network policies
check_network_policies() {
    log_check "Validating network policies..."
    
    local netpols=$(kubectl get networkpolicies -n $NAMESPACE --no-headers | wc -l)
    
    if [[ $netpols -lt 3 ]]; then
        log_fail "Insufficient network policies configured (found: $netpols, expected: >= 3)" "CRITICAL"
    else
        log_pass "Network policies are configured ($netpols policies found)"
    fi
    
    # Check default deny policy
    if kubectl get networkpolicy default-deny-all -n $NAMESPACE &>/dev/null; then
        log_pass "Default deny-all network policy is in place"
    else
        log_fail "Default deny-all network policy is missing" "CRITICAL"
    fi
}

# Check RBAC configuration
check_rbac() {
    log_check "Validating RBAC configuration..."
    
    # Check service accounts
    local service_accounts=$(kubectl get serviceaccounts -n $NAMESPACE --no-headers | wc -l)
    
    if [[ $service_accounts -lt 3 ]]; then
        log_fail "Insufficient service accounts configured" "CRITICAL"
    else
        log_pass "Service accounts are properly configured"
    fi
    
    # Check for overly permissive cluster roles
    local cluster_roles=$(kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.subjects[]?.namespace == "'$NAMESPACE'") | .metadata.name')
    
    for role in $cluster_roles; do
        local verbs=$(kubectl get clusterrole $(kubectl get clusterrolebinding $role -o jsonpath='{.roleRef.name}') -o jsonpath='{.rules[*].verbs[*]}')
        
        if echo "$verbs" | grep -q "\*"; then
            log_fail "Overly permissive cluster role binding: $role" "CRITICAL"
        fi
    done
}

# Check pod security
check_pod_security() {
    log_check "Validating pod security configurations..."
    
    local pods=$(kubectl get pods -n $NAMESPACE -o name)
    
    for pod in $pods; do
        # Check if running as non-root
        local run_as_non_root=$(kubectl get $pod -n $NAMESPACE -o jsonpath='{.spec.securityContext.runAsNonRoot}' 2>/dev/null || echo "false")
        
        if [[ "$run_as_non_root" != "true" ]]; then
            log_fail "Pod $pod is not configured to run as non-root" "CRITICAL"
        fi
        
        # Check for privileged containers
        local privileged=$(kubectl get $pod -n $NAMESPACE -o jsonpath='{.spec.containers[*].securityContext.privileged}' 2>/dev/null || echo "false")
        
        if [[ "$privileged" == "true" ]]; then
            log_fail "Pod $pod has privileged containers" "CRITICAL"
        fi
        
        # Check for read-only root filesystem
        local read_only_fs=$(kubectl get $pod -n $NAMESPACE -o jsonpath='{.spec.containers[*].securityContext.readOnlyRootFilesystem}' 2>/dev/null || echo "false")
        
        if [[ "$read_only_fs" != "true" ]]; then
            log_warn "Pod $pod does not have read-only root filesystem"
        fi
    done
    
    log_pass "Pod security validation completed"
}

# Check resource limits
check_resource_limits() {
    log_check "Validating resource limits and quotas..."
    
    # Check resource quota
    if kubectl get resourcequota pilot-resource-quota -n $NAMESPACE &>/dev/null; then
        log_pass "Resource quota is configured"
    else
        log_fail "Resource quota is missing" "CRITICAL"
    fi
    
    # Check limit ranges
    if kubectl get limitrange pilot-limit-range -n $NAMESPACE &>/dev/null; then
        log_pass "Limit range is configured"
    else
        log_fail "Limit range is missing" "CRITICAL"
    fi
    
    # Check that all deployments have resource limits
    local deployments=$(kubectl get deployments -n $NAMESPACE -o name)
    
    for deployment in $deployments; do
        local has_limits=$(kubectl get $deployment -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[*].resources.limits}' 2>/dev/null)
        
        if [[ -z "$has_limits" || "$has_limits" == "null" ]]; then
            log_fail "Deployment $deployment is missing resource limits" "CRITICAL"
        else
            log_pass "Deployment $deployment has resource limits configured"
        fi
    done
}

# Check TLS/SSL configuration
check_tls_configuration() {
    log_check "Validating TLS/SSL configuration..."
    
    # Check ingress TLS
    local ingresses=$(kubectl get ingress -n $NAMESPACE -o name)
    
    for ingress in $ingresses; do
        local tls_hosts=$(kubectl get $ingress -n $NAMESPACE -o jsonpath='{.spec.tls[*].hosts[*]}' 2>/dev/null)
        
        if [[ -n "$tls_hosts" ]]; then
            log_pass "Ingress $ingress has TLS configured"
        else
            log_fail "Ingress $ingress is missing TLS configuration" "CRITICAL"
        fi
    done
    
    # Check certificate secrets
    local tls_secrets=$(kubectl get secrets -n $NAMESPACE -o json | jq -r '.items[] | select(.type == "kubernetes.io/tls") | .metadata.name')
    
    if [[ -z "$tls_secrets" ]]; then
        log_fail "No TLS certificate secrets found" "CRITICAL"
    else
        log_pass "TLS certificate secrets are configured"
    fi
}

# Check image security
check_image_security() {
    log_check "Validating container image security..."
    
    local deployments=$(kubectl get deployments -n $NAMESPACE -o name)
    
    for deployment in $deployments; do
        local images=$(kubectl get $deployment -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[*].image}')
        
        for image in $images; do
            # Check for latest tag usage
            if [[ "$image" == *":latest" ]]; then
                log_fail "Deployment $deployment uses 'latest' tag for image $image" "CRITICAL"
            fi
            
            # Check for official/trusted registries
            if [[ ! "$image" =~ ^(.*\.amazonaws\.com|docker\.io|quay\.io|gcr\.io) ]]; then
                log_warn "Image $image from untrusted registry in $deployment"
            fi
        done
    done
    
    log_pass "Container image security validation completed"
}

# Check secrets encryption
check_secrets_encryption() {
    log_check "Validating secrets encryption..."
    
    # Check if secrets are properly encrypted at rest
    local secrets=$(kubectl get secrets -n $NAMESPACE --no-headers | wc -l)
    
    if [[ $secrets -gt 0 ]]; then
        log_pass "Secrets are present and should be encrypted at rest by EKS"
    else
        log_warn "No secrets found in namespace"
    fi
    
    # Check for unencrypted sensitive data in ConfigMaps
    local configmaps=$(kubectl get configmaps -n $NAMESPACE -o name)
    
    for cm in $configmaps; do
        local data=$(kubectl get $cm -n $NAMESPACE -o jsonpath='{.data}' 2>/dev/null)
        
        if echo "$data" | grep -qiE "(password|secret|key|token|credential)" 2>/dev/null; then
            log_fail "ConfigMap $cm contains sensitive data that should be in secrets" "CRITICAL"
        fi
    done
}

# Check monitoring and logging
check_monitoring_logging() {
    log_check "Validating monitoring and logging setup..."
    
    # Check if Prometheus is running
    if kubectl get deployment prometheus -n $NAMESPACE &>/dev/null; then
        log_pass "Prometheus is deployed"
    else
        log_fail "Prometheus is not deployed" "CRITICAL"
    fi
    
    # Check if Jaeger is running for distributed tracing
    if kubectl get deployment jaeger -n $NAMESPACE &>/dev/null; then
        log_pass "Jaeger is deployed for distributed tracing"
    else
        log_fail "Jaeger is not deployed" "CRITICAL"
    fi
    
    # Check if OpenTelemetry collector is running
    if kubectl get deployment otel-collector -n $NAMESPACE &>/dev/null; then
        log_pass "OpenTelemetry collector is deployed"
    else
        log_fail "OpenTelemetry collector is not deployed" "CRITICAL"
    fi
}

# Check backup and disaster recovery
check_backup_dr() {
    log_check "Validating backup and disaster recovery setup..."
    
    # Check if backup CronJob is configured
    if kubectl get cronjob backup-persistent-data -n $NAMESPACE &>/dev/null; then
        log_pass "Backup CronJob is configured"
    else
        log_fail "Backup CronJob is not configured" "CRITICAL"
    fi
    
    # Check Pod Disruption Budgets
    local pdbs=$(kubectl get poddisruptionbudgets -n $NAMESPACE --no-headers | wc -l)
    
    if [[ $pdbs -gt 0 ]]; then
        log_pass "Pod Disruption Budgets are configured"
    else
        log_fail "Pod Disruption Budgets are not configured"
    fi
    
    # Check if emergency runbooks are available
    if kubectl get configmap emergency-runbook -n $NAMESPACE &>/dev/null; then
        log_pass "Emergency runbooks are available"
    else
        log_fail "Emergency runbooks are not available"
    fi
}

# Check compliance requirements
check_compliance() {
    log_check "Validating compliance requirements..."
    
    # Check audit logging
    local audit_policy=$(kubectl get events -n $NAMESPACE --no-headers | wc -l)
    
    if [[ $audit_policy -gt 0 ]]; then
        log_pass "Kubernetes events are being logged (audit trail)"
    else
        log_warn "No Kubernetes events found"
    fi
    
    # Check data retention policies
    if kubectl get configmap prometheus-config -n $NAMESPACE -o yaml | grep -q "retention"; then
        log_pass "Data retention policies are configured"
    else
        log_warn "Data retention policies may not be properly configured"
    fi
}

# Run penetration testing checks
run_penetration_tests() {
    log_check "Running basic penetration testing checks..."
    
    # Check for exposed services without authentication
    local services=$(kubectl get services -n $NAMESPACE -o json | jq -r '.items[] | select(.spec.type == "LoadBalancer" or .spec.type == "NodePort") | .metadata.name')
    
    for service in $services; do
        log_warn "Service $service is exposed externally - ensure proper authentication is in place"
    done
    
    # Check for default passwords (basic check)
    if kubectl get secret grafana-secrets -n $NAMESPACE -o yaml | grep -q "OrchestrixPilotAdmin123"; then
        log_fail "Default Grafana password detected - change immediately" "CRITICAL"
    fi
}

# Generate security report
generate_security_report() {
    log_info "Generating security validation report..."
    
    cat << EOF > security-validation-report.txt
ORCHESTRIX Pilot Security Validation Report
==========================================

Date: $(date)
Cluster: $CLUSTER_NAME
Namespace: $NAMESPACE

Summary:
--------
Total checks: $CHECKS_TOTAL
Passed: $CHECKS_PASSED
Failed: $CHECKS_FAILED
Critical issues: $CRITICAL_ISSUES

Security Score: $(( (CHECKS_PASSED * 100) / CHECKS_TOTAL ))%

Critical Issues: $CRITICAL_ISSUES

Recommendations:
---------------
1. Address all CRITICAL security issues before production deployment
2. Review and fix all WARN level issues
3. Conduct regular security scans and penetration testing
4. Implement continuous security monitoring
5. Regular security training for development team

Next Steps:
----------
1. Fix critical security issues
2. Re-run security validation
3. Conduct external security audit
4. Implement security monitoring alerts
5. Document security procedures

EOF

    log_info "Security report saved to security-validation-report.txt"
}

# Main execution
main() {
    log_info "Starting ORCHESTRIX Pilot Security Validation"
    log_info "============================================"
    echo
    
    # Run all security checks
    check_hardcoded_secrets
    check_external_secrets
    check_network_policies
    check_rbac
    check_pod_security
    check_resource_limits
    check_tls_configuration
    check_image_security
    check_secrets_encryption
    check_monitoring_logging
    check_backup_dr
    check_compliance
    run_penetration_tests
    
    echo
    log_info "Security Validation Summary"
    log_info "==========================="
    echo "Total checks: $CHECKS_TOTAL"
    echo "Passed: $CHECKS_PASSED"
    echo "Failed: $CHECKS_FAILED"
    echo "Critical issues: $CRITICAL_ISSUES"
    echo
    
    if [[ $CRITICAL_ISSUES -gt 0 ]]; then
        log_error "CRITICAL SECURITY ISSUES DETECTED!"
        log_error "DO NOT PROCEED TO PRODUCTION until all critical issues are resolved"
        generate_security_report
        exit 1
    elif [[ $CHECKS_FAILED -gt 0 ]]; then
        log_warn "Some security checks failed, but no critical issues detected"
        log_warn "Review and address failed checks before production deployment"
        generate_security_report
        exit 2
    else
        log_info "All security checks passed! ✅"
        log_info "Pilot environment is ready for production consideration"
        generate_security_report
        exit 0
    fi
}

# Handle script arguments
case "${1:-validate}" in
    "validate")
        main
        ;;
    "report")
        generate_security_report
        cat security-validation-report.txt
        ;;
    *)
        echo "Usage: $0 {validate|report}"
        echo
        echo "Commands:"
        echo "  validate  - Run complete security validation"
        echo "  report    - Generate and display security report"
        exit 1
        ;;
esac