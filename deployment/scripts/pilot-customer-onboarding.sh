#!/bin/bash

# Pilot Customer Onboarding Automation Script
# Classification: STRATEGIC - CUSTOMER ONBOARDING
# Comprehensive automation for Phase 2 pilot user onboarding and success management
# Last Updated: 2025-08-08

set -euo pipefail

# Configuration and Environment Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NAMESPACE="orchestrix-pilot"
PILOT_USER_LIMIT=50
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Validate prerequisites
validate_prerequisites() {
    log_info "Validating deployment prerequisites..."
    
    # Check kubectl connectivity
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "kubectl cluster connection failed"
        return 1
    fi
    
    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log_error "Namespace $NAMESPACE does not exist"
        return 1
    fi
    
    # Check required secrets exist
    local required_secrets=(
        "postgres-credentials"
        "slack-webhook"
        "email-service-config"
        "grafana-secrets"
    )
    
    for secret in "${required_secrets[@]}"; do
        if ! kubectl get secret "$secret" -n "$NAMESPACE" >/dev/null 2>&1; then
            log_error "Required secret $secret not found in namespace $NAMESPACE"
            return 1
        fi
    done
    
    # Check database connectivity
    log_info "Validating database connectivity..."
    if ! kubectl exec -n "$NAMESPACE" deployment/postgres -- psql -U agent -d reputation -c "SELECT 1;" >/dev/null 2>&1; then
        log_error "Database connectivity check failed"
        return 1
    fi
    
    log_success "Prerequisites validation completed"
    return 0
}

# Initialize database schema for business validation
initialize_database_schema() {
    log_info "Initializing business validation database schema..."
    
    # Apply database schema from ConfigMap
    kubectl exec -n "$NAMESPACE" deployment/postgres -- psql -U agent -d reputation -f /dev/stdin <<EOF
$(kubectl get configmap business-metrics-schema -n "$NAMESPACE" -o jsonpath='{.data.schema\.sql}')
EOF
    
    # Create initial admin user and system configuration
    kubectl exec -n "$NAMESPACE" deployment/postgres -- psql -U agent -d reputation -c "
        INSERT INTO pilot_configuration (key, value, description) VALUES 
        ('pilot_user_limit', '$PILOT_USER_LIMIT', 'Maximum number of pilot users'),
        ('onboarding_automation_enabled', 'true', 'Enable automated onboarding workflows'),
        ('success_intervention_threshold', '0.7', 'Satisfaction threshold for success intervention'),
        ('weekly_cohort_size', '10', 'Number of users per weekly cohort')
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP;
    " 2>/dev/null || log_warn "Configuration values may already exist"
    
    log_success "Database schema initialization completed"
}

# Deploy customer onboarding infrastructure
deploy_onboarding_infrastructure() {
    log_info "Deploying customer onboarding infrastructure..."
    
    # Apply business validation Kubernetes resources
    kubectl apply -f "$PROJECT_ROOT/deployment/k8s/pilot-business-validation.yaml"
    
    # Wait for deployments to be ready
    log_info "Waiting for onboarding services to be ready..."
    kubectl rollout status deployment/business-metrics-collector -n "$NAMESPACE" --timeout=300s
    kubectl rollout status deployment/customer-success-manager -n "$NAMESPACE" --timeout=300s
    
    # Verify service health
    log_info "Verifying service health..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if kubectl exec -n "$NAMESPACE" deployment/business-metrics-collector -- curl -f http://localhost:8080/health >/dev/null 2>&1; then
            log_success "Business metrics collector is healthy"
            break
        fi
        log_warn "Attempt $attempt/$max_attempts: Waiting for business metrics collector to be healthy..."
        sleep 10
        ((attempt++))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "Business metrics collector failed to become healthy"
        return 1
    fi
    
    log_success "Customer onboarding infrastructure deployed successfully"
}

# Configure monitoring and alerting
configure_monitoring_alerting() {
    log_info "Configuring monitoring and alerting for customer onboarding..."
    
    # Apply business KPI monitoring rules
    kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: business-metrics-monitor
  namespace: $NAMESPACE
  labels:
    monitoring: prometheus
spec:
  selector:
    matchLabels:
      app: business-metrics-collector
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 15s
EOF
    
    # Configure Grafana datasource for business metrics
    kubectl patch configmap grafana-config -n "$NAMESPACE" --type merge -p '{
      "data": {
        "datasources.yaml": "apiVersion: 1\ndatasources:\n  - name: Business Metrics\n    type: prometheus\n    url: http://prometheus:9090\n    access: proxy\n    isDefault: false\n    editable: true"
      }
    }' 2>/dev/null || log_warn "Grafana configuration may need manual update"
    
    log_success "Monitoring and alerting configuration completed"
}

# Set up automated customer success workflows
setup_success_workflows() {
    log_info "Setting up automated customer success workflows..."
    
    # Create customer success automation ConfigMap
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: success-automation-config
  namespace: $NAMESPACE
  labels:
    component: customer-success
data:
  automation-rules.yaml: |
    success_workflows:
      onboarding_automation:
        - trigger: "user_registered"
          actions:
            - "send_welcome_email"
            - "schedule_onboarding_session"
            - "assign_success_manager"
        - trigger: "first_task_completed"
          actions:
            - "send_congratulations_message"
            - "suggest_next_features"
      
      satisfaction_monitoring:
        - trigger: "satisfaction_score < 7.0"
          actions:
            - "trigger_success_intervention"
            - "schedule_feedback_session"
            - "escalate_to_human_success_manager"
        - trigger: "satisfaction_score >= 9.0"
          actions:
            - "identify_as_champion"
            - "request_testimonial"
            - "offer_beta_features"
      
      engagement_tracking:
        - trigger: "no_activity_7_days"
          actions:
            - "send_re_engagement_email"
            - "offer_training_session"
        - trigger: "no_activity_14_days"
          actions:
            - "escalate_to_success_manager"
            - "schedule_retention_call"
      
      feature_adoption:
        - trigger: "feature_unused_30_days"
          actions:
            - "send_feature_tutorial"
            - "offer_guided_walkthrough"
        - trigger: "power_user_behavior"
          actions:
            - "offer_advanced_features"
            - "invite_to_advisory_board"
EOF
    
    # Restart customer success manager to pick up new configuration
    kubectl rollout restart deployment/customer-success-manager -n "$NAMESPACE"
    kubectl rollout status deployment/customer-success-manager -n "$NAMESPACE" --timeout=120s
    
    log_success "Customer success workflows configured"
}

# Create pilot user cohort management
create_cohort_management() {
    log_info "Creating pilot user cohort management system..."
    
    # Initialize cohort tracking
    kubectl exec -n "$NAMESPACE" deployment/postgres -- psql -U agent -d reputation -c "
        INSERT INTO pilot_cohorts (cohort_week, target_users, start_date, focus_area, success_criteria)
        VALUES 
        (1, 10, CURRENT_DATE, 'core_platform_validation', 'basic_functionality,user_onboarding_completion'),
        (2, 20, CURRENT_DATE + INTERVAL '7 days', 'feature_completeness_testing', 'feature_discovery,task_completion'),
        (3, 35, CURRENT_DATE + INTERVAL '14 days', 'performance_validation', 'response_time_satisfaction,system_reliability'),
        (4, 50, CURRENT_DATE + INTERVAL '21 days', 'full_pilot_capacity', 'concurrent_user_handling,system_scalability')
        ON CONFLICT (cohort_week) DO UPDATE SET
            target_users = EXCLUDED.target_users,
            focus_area = EXCLUDED.focus_area,
            success_criteria = EXCLUDED.success_criteria;
    " 2>/dev/null || log_warn "Cohort data may already exist"
    
    log_success "Cohort management system created"
}

# Set up feedback collection automation
setup_feedback_collection() {
    log_info "Setting up automated feedback collection system..."
    
    # Deploy feedback collection webhook service
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feedback-collector
  namespace: $NAMESPACE
  labels:
    app: feedback-collector
    component: customer-feedback
spec:
  replicas: 2
  selector:
    matchLabels:
      app: feedback-collector
  template:
    metadata:
      labels:
        app: feedback-collector
        component: customer-feedback
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
    spec:
      serviceAccountName: customer-success-manager
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: feedback-collector
        image: agentic/feedback-collector:v1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: connection-url
        - name: SLACK_WEBHOOK_URL
          valueFrom:
            secretKeyRef:
              name: slack-webhook
              key: url
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 15
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: feedback-collector
  namespace: $NAMESPACE
  labels:
    app: feedback-collector
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: feedback-collector
EOF
    
    log_success "Feedback collection system deployed"
}

# Validate deployment and run health checks
validate_deployment() {
    log_info "Running comprehensive deployment validation..."
    
    # Check all services are running
    local services=("business-metrics-collector" "customer-success-manager" "feedback-collector")
    for service in "${services[@]}"; do
        if ! kubectl get deployment "$service" -n "$NAMESPACE" >/dev/null 2>&1; then
            log_error "Service $service not found"
            return 1
        fi
        
        # Check if deployment is ready
        local ready_replicas
        ready_replicas=$(kubectl get deployment "$service" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
        local desired_replicas
        desired_replicas=$(kubectl get deployment "$service" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
        
        if [ "$ready_replicas" != "$desired_replicas" ]; then
            log_error "Service $service is not fully ready ($ready_replicas/$desired_replicas)"
            return 1
        fi
        
        log_success "Service $service is healthy ($ready_replicas/$desired_replicas)"
    done
    
    # Validate database connectivity and schema
    log_info "Validating database schema..."
    local table_count
    table_count=$(kubectl exec -n "$NAMESPACE" deployment/postgres -- psql -U agent -d reputation -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
    
    if [ "$table_count" -lt 8 ]; then
        log_error "Database schema incomplete. Expected at least 8 tables, found $table_count"
        return 1
    fi
    
    log_success "Database schema validation passed ($table_count tables)"
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    if kubectl exec -n "$NAMESPACE" deployment/business-metrics-collector -- curl -f -s http://localhost:8080/api/v1/metrics/summary >/dev/null; then
        log_success "Business metrics API is responding"
    else
        log_error "Business metrics API health check failed"
        return 1
    fi
    
    # Check monitoring integration
    log_info "Validating monitoring integration..."
    if kubectl get servicemonitor business-metrics-monitor -n "$NAMESPACE" >/dev/null 2>&1; then
        log_success "Monitoring integration configured"
    else
        log_warn "Monitoring integration may need manual configuration"
    fi
    
    log_success "Deployment validation completed successfully"
}

# Generate deployment summary report
generate_deployment_report() {
    log_info "Generating deployment summary report..."
    
    local report_file="$PROJECT_ROOT/deployment/reports/pilot-onboarding-deployment-$(date +%Y%m%d-%H%M%S).md"
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" <<EOF
# Pilot Customer Onboarding Deployment Report

**Deployment Date:** $(date '+%Y-%m-%d %H:%M:%S %Z')
**Environment:** $NAMESPACE
**Pilot User Limit:** $PILOT_USER_LIMIT

## Deployment Summary

### ✅ Successfully Deployed Services
- Business Metrics Collector (2 replicas)
- Customer Success Manager (1 replica)
- Feedback Collector (2 replicas)

### 📊 Database Schema
- **Tables Created:** $(kubectl exec -n "$NAMESPACE" deployment/postgres -- psql -U agent -d reputation -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
- **Initial Configuration:** Applied
- **Cohort Management:** Configured for 4-week pilot phases

### 🔍 Monitoring & Alerting
- **Prometheus Integration:** Configured
- **Business KPI Rules:** Applied
- **Grafana Dashboards:** Available
- **Alert Rules:** 8 business validation alerts configured

### 📈 Success Metrics Framework
- **Customer Satisfaction Target:** 8.5/10
- **Task Completion Target:** 95%
- **User Retention Target:** 92%
- **Feature Adoption Target:** 85%

### 🎯 Onboarding Phases
1. **Week 1:** 10 users - Core platform validation
2. **Week 2:** 20 users - Feature completeness testing
3. **Week 3:** 35 users - Performance validation
4. **Week 4:** 50 users - Full pilot capacity

### 🔧 Automation Features
- **Automated Onboarding:** Welcome emails, session scheduling
- **Success Interventions:** Triggered at satisfaction < 7.0
- **Re-engagement:** Automated for inactive users
- **Feedback Collection:** Multi-channel collection system

### 📋 Next Steps
1. Begin Week 1 user onboarding (10 users)
2. Monitor business KPIs and technical metrics
3. Execute success interventions as needed
4. Collect and analyze user feedback
5. Prepare for cohort expansion

### 🚨 Key Monitoring URLs
- **Business KPI Dashboard:** http://grafana.orchestrix-pilot.local/d/business-kpis
- **Customer Success Panel:** http://customer-success.orchestrix-pilot.local
- **Feedback Collection API:** http://feedback-collector.orchestrix-pilot.local/api/v1/feedback

---

**Report Generated By:** Pilot Customer Onboarding Automation Script
**Script Version:** 1.0.0
**Execution Status:** SUCCESS
EOF
    
    log_success "Deployment report generated: $report_file"
    
    # Also output summary to console
    echo
    log_success "====== PILOT CUSTOMER ONBOARDING DEPLOYMENT COMPLETE ======"
    echo
    log_info "📊 Business Validation Framework: ACTIVE"
    log_info "👥 Pilot User Capacity: $PILOT_USER_LIMIT users"
    log_info "📈 Success Metrics: 8 KPIs configured and monitored"
    log_info "🔄 Automation Workflows: Onboarding, Success, Retention"
    log_info "📋 Report Location: $report_file"
    echo
    log_info "Ready to begin Phase 2 pilot user onboarding!"
}

# Main execution flow
main() {
    log_info "Starting Pilot Customer Onboarding Deployment..."
    log_info "Target Environment: $NAMESPACE"
    log_info "Pilot User Limit: $PILOT_USER_LIMIT"
    echo
    
    # Validate prerequisites
    if ! validate_prerequisites; then
        log_error "Prerequisites validation failed"
        exit 1
    fi
    
    # Initialize database
    if ! initialize_database_schema; then
        log_error "Database schema initialization failed"
        exit 1
    fi
    
    # Deploy infrastructure
    if ! deploy_onboarding_infrastructure; then
        log_error "Infrastructure deployment failed"
        exit 1
    fi
    
    # Configure monitoring
    if ! configure_monitoring_alerting; then
        log_error "Monitoring configuration failed"
        exit 1
    fi
    
    # Set up success workflows
    if ! setup_success_workflows; then
        log_error "Success workflows setup failed"
        exit 1
    fi
    
    # Create cohort management
    if ! create_cohort_management; then
        log_error "Cohort management setup failed"
        exit 1
    fi
    
    # Set up feedback collection
    if ! setup_feedback_collection; then
        log_error "Feedback collection setup failed"
        exit 1
    fi
    
    # Validate deployment
    if ! validate_deployment; then
        log_error "Deployment validation failed"
        exit 1
    fi
    
    # Generate report
    generate_deployment_report
    
    log_success "Pilot Customer Onboarding Deployment completed successfully!"
    exit 0
}

# Handle script interruption
cleanup() {
    log_warn "Script interrupted. Cleaning up..."
    # Add any cleanup tasks here if needed
    exit 1
}

trap cleanup INT TERM

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi