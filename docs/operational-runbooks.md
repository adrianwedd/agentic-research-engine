# Operational Runbooks - Agentic Research Engine

**Classification: CRITICAL - PRODUCTION OPERATIONS**  
**Last Updated: 2025-08-08**  
**Version: 1.0.0**

This document provides comprehensive operational procedures for the Agentic Research Engine production environment, including incident response, troubleshooting, and maintenance procedures.

## Table of Contents

1. [System Overview](#system-overview)
2. [Incident Response Procedures](#incident-response-procedures)
3. [Health Monitoring and Alerting](#health-monitoring-and-alerting)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Scaling Operations](#scaling-operations)
7. [Backup and Recovery](#backup-and-recovery)
8. [Security Incident Response](#security-incident-response)

## System Overview

### Architecture Components

- **Episodic Memory Service**: Port 8081, handles experience storage and retrieval
- **Reputation Service**: Port 8090, manages agent reputation and evaluations
- **Redis**: Port 6379, caching and session storage
- **Weaviate**: Port 8080, vector database for embeddings
- **Prometheus**: Port 9090, metrics collection
- **Grafana**: Port 3000, monitoring dashboards
- **Jaeger**: Port 16686, distributed tracing

### Service Dependencies

```
┌─────────────────────┐    ┌──────────────────┐
│  Episodic Memory    │────│      Redis       │
│     Service         │    │    (Cache)       │
└─────────────────────┘    └──────────────────┘
           │
           ▼
┌─────────────────────┐    ┌──────────────────┐
│     Weaviate        │    │   Reputation     │
│  (Vector Store)     │    │    Service       │
└─────────────────────┘    └──────────────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │   PostgreSQL     │
                           │   (Database)     │
                           └──────────────────┘
```

## Incident Response Procedures

### P0 (Critical) Incidents

**Definition**: Service completely unavailable or data corruption

**Response Time**: 15 minutes

**Escalation Path**: 
1. On-call engineer (immediate)
2. Senior engineer (15 minutes)
3. Engineering manager (30 minutes)
4. VP Engineering (1 hour)

#### Immediate Actions

1. **Acknowledge the incident**
   ```bash
   # Check overall system health
   kubectl get pods -n orchestrix-pilot
   kubectl get services -n orchestrix-pilot
   ```

2. **Assess impact and scope**
   ```bash
   # Check service health endpoints
   kubectl exec -n orchestrix-pilot deployment/episodic-memory -- curl -s http://localhost:8081/health
   kubectl exec -n orchestrix-pilot deployment/reputation-service -- curl -s http://localhost:8090/health
   ```

3. **Check monitoring dashboards**
   - Grafana: System Overview Dashboard
   - Prometheus: Alert Manager
   - Jaeger: Trace analysis for errors

4. **Communication**
   - Update status page
   - Notify stakeholders via Slack/Email
   - Create incident channel

### P1 (High) Incidents

**Definition**: Degraded performance or partial service unavailability

**Response Time**: 1 hour

#### Investigation Steps

1. **Performance Analysis**
   ```bash
   # Check resource usage
   kubectl top pods -n orchestrix-pilot
   kubectl top nodes
   ```

2. **Log Analysis**
   ```bash
   # Check recent logs for errors
   kubectl logs -n orchestrix-pilot deployment/episodic-memory --tail=100
   kubectl logs -n orchestrix-pilot deployment/reputation-service --tail=100
   ```

3. **Database Health**
   ```bash
   # Check Redis connectivity
   kubectl exec -n orchestrix-pilot deployment/redis -- redis-cli ping
   
   # Check Weaviate health
   kubectl exec -n orchestrix-pilot deployment/weaviate -- curl -s http://localhost:8080/v1/.well-known/ready
   ```

## Health Monitoring and Alerting

### Key Metrics to Monitor

#### Service Health Metrics
- **Uptime**: `up{job="episodic-memory"}`, `up{job="reputation-service"}`
- **Response Time**: `http_request_duration_seconds_bucket`
- **Error Rate**: `rate(http_requests_total{status=~"5.."}[5m])`
- **Request Rate**: `rate(http_requests_total[5m])`

#### Infrastructure Metrics
- **CPU Usage**: `container_cpu_usage_seconds_total`
- **Memory Usage**: `container_memory_usage_bytes`
- **Disk Usage**: `container_fs_usage_bytes`
- **Network Traffic**: `container_network_transmit_bytes_total`

#### Database Metrics
- **Redis Memory**: `redis_memory_used_bytes`
- **Redis Connections**: `redis_connected_clients`
- **Weaviate Query Time**: `weaviate_query_duration_ms`

### Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|---------|
| Service Down | up == 0 for 1m | P0 incident |
| High Error Rate | error rate > 5% for 2m | P1 incident |
| High Response Time | p95 > 2s for 2m | P1 incident |
| High Memory Usage | > 80% for 5m | Investigation |
| High CPU Usage | > 80% for 5m | Investigation |
| Redis Memory Full | > 90% | Scale or clear cache |
| Disk Space Low | > 85% | Add storage |

### Monitoring Commands

```bash
# Check all pods status
kubectl get pods -n orchestrix-pilot -o wide

# Check service endpoints
kubectl get endpoints -n orchestrix-pilot

# Check recent events
kubectl get events -n orchestrix-pilot --sort-by='.lastTimestamp' | tail -20

# Check resource quotas
kubectl describe resourcequota -n orchestrix-pilot

# Port forward to monitoring tools (for troubleshooting)
kubectl port-forward -n orchestrix-pilot svc/grafana 3000:3000
kubectl port-forward -n orchestrix-pilot svc/prometheus 9090:9090
kubectl port-forward -n orchestrix-pilot svc/jaeger-query 16686:16686
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Service Won't Start

**Symptoms**: Pod in CrashLoopBackOff state

**Investigation**:
```bash
# Check pod status and events
kubectl describe pod -n orchestrix-pilot <pod-name>

# Check logs
kubectl logs -n orchestrix-pilot <pod-name> --previous

# Check resource constraints
kubectl describe nodes
```

**Common Causes**:
- Missing secrets or configuration
- Resource limits too low
- Image pull failures
- Database connection issues

**Solutions**:
```bash
# Update secrets
kubectl get secrets -n orchestrix-pilot

# Increase resource limits
kubectl patch deployment <deployment-name> -n orchestrix-pilot -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"memory":"2Gi","cpu":"1000m"}}}]}}}}'

# Force image pull
kubectl rollout restart deployment/<deployment-name> -n orchestrix-pilot
```

#### 2. High Memory Usage

**Investigation**:
```bash
# Check memory usage by pod
kubectl top pods -n orchestrix-pilot --sort-by=memory

# Check memory limits
kubectl describe pods -n orchestrix-pilot | grep -A 5 "Limits:"

# Check for memory leaks in application logs
kubectl logs -n orchestrix-pilot deployment/episodic-memory | grep -i "memory\|leak\|oom"
```

**Solutions**:
```bash
# Restart high-memory pods
kubectl rollout restart deployment/<deployment-name> -n orchestrix-pilot

# Scale horizontally
kubectl scale deployment <deployment-name> --replicas=3 -n orchestrix-pilot

# Increase memory limits
kubectl patch deployment <deployment-name> -n orchestrix-pilot -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container-name>","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
```

#### 3. Database Connection Issues

**Redis Issues**:
```bash
# Check Redis pod status
kubectl get pods -n orchestrix-pilot -l app=redis

# Test Redis connectivity
kubectl exec -n orchestrix-pilot deployment/redis -- redis-cli ping

# Check Redis memory usage
kubectl exec -n orchestrix-pilot deployment/redis -- redis-cli info memory

# Check Redis logs
kubectl logs -n orchestrix-pilot deployment/redis
```

**Weaviate Issues**:
```bash
# Check Weaviate health
kubectl exec -n orchestrix-pilot deployment/weaviate -- curl -s http://localhost:8080/v1/.well-known/live

# Check Weaviate schema
kubectl exec -n orchestrix-pilot deployment/weaviate -- curl -s http://localhost:8080/v1/schema

# Check Weaviate logs
kubectl logs -n orchestrix-pilot deployment/weaviate
```

#### 4. Network Connectivity Issues

**Investigation**:
```bash
# Check network policies
kubectl get networkpolicy -n orchestrix-pilot

# Test service-to-service connectivity
kubectl run netshoot --image=nicolaka/netshoot --rm -i --restart=Never -n orchestrix-pilot -- sh

# Inside netshoot pod:
# nslookup episodic-memory.orchestrix-pilot.svc.cluster.local
# curl -v http://episodic-memory:8081/health
# curl -v http://reputation-service:8090/health
```

**Solutions**:
- Verify DNS resolution
- Check network policies
- Validate service configurations
- Check firewall rules

## Maintenance Procedures

### Scheduled Maintenance

#### Monthly Maintenance Window
- **Time**: First Sunday of month, 2:00 AM - 6:00 AM UTC
- **Duration**: 4 hours maximum
- **Communication**: 48 hours advance notice

#### Pre-Maintenance Checklist
- [ ] Notify stakeholders
- [ ] Update status page
- [ ] Backup critical data
- [ ] Prepare rollback plan
- [ ] Validate all changes in staging

#### Standard Maintenance Tasks

1. **Security Updates**
   ```bash
   # Update base images
   docker pull prom/prometheus:latest
   docker pull grafana/grafana:latest
   docker pull redis:7.0-alpine
   
   # Update Kubernetes manifests
   kubectl apply -f deployment/k8s/
   
   # Rolling update
   kubectl rollout restart deployment/episodic-memory -n orchestrix-pilot
   kubectl rollout restart deployment/reputation-service -n orchestrix-pilot
   ```

2. **Database Maintenance**
   ```bash
   # Redis maintenance
   kubectl exec -n orchestrix-pilot deployment/redis -- redis-cli BGREWRITEAOF
   
   # Check Redis fragmentation
   kubectl exec -n orchestrix-pilot deployment/redis -- redis-cli info memory
   ```

3. **Monitoring Maintenance**
   ```bash
   # Prune old Prometheus data (if needed)
   kubectl exec -n orchestrix-pilot deployment/prometheus -- promtool query range \
     --query='up' \
     --start=$(date -d '30 days ago' +%s) \
     --end=$(date +%s)
   
   # Clean up Grafana temp files
   kubectl exec -n orchestrix-pilot deployment/grafana -- find /tmp -type f -mtime +7 -delete
   ```

### Post-Maintenance Verification

```bash
# Health check all services
./deployment/scripts/health-check.sh

# Run smoke tests
./deployment/scripts/smoke-test.sh

# Check monitoring alerts
curl -s http://prometheus:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
```

## Scaling Operations

### Horizontal Scaling

#### Scale Up Services
```bash
# Scale episodic memory service
kubectl scale deployment episodic-memory --replicas=5 -n orchestrix-pilot

# Scale reputation service
kubectl scale deployment reputation-service --replicas=3 -n orchestrix-pilot

# Verify scaling
kubectl get pods -n orchestrix-pilot -l app=episodic-memory
```

#### Auto-scaling Configuration
```bash
# Apply HPA (if not already configured)
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: episodic-memory-hpa
  namespace: orchestrix-pilot
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: episodic-memory
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
```

### Vertical Scaling

#### Increase Resource Limits
```bash
# Update memory and CPU limits
kubectl patch deployment episodic-memory -n orchestrix-pilot -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "episodic-memory",
          "resources": {
            "limits": {"memory": "4Gi", "cpu": "2"},
            "requests": {"memory": "2Gi", "cpu": "1"}
          }
        }]
      }
    }
  }
}'
```

## Backup and Recovery

### Backup Procedures

#### Redis Backup
```bash
# Create Redis backup
kubectl exec -n orchestrix-pilot deployment/redis -- redis-cli BGSAVE

# Copy backup file
kubectl cp orchestrix-pilot/redis-pod:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb
```

#### Weaviate Backup
```bash
# Backup Weaviate data
kubectl exec -n orchestrix-pilot deployment/weaviate -- tar -czf /tmp/weaviate-backup.tar.gz /var/lib/weaviate

# Copy backup
kubectl cp orchestrix-pilot/weaviate-pod:/tmp/weaviate-backup.tar.gz ./weaviate-backup-$(date +%Y%m%d).tar.gz
```

#### Configuration Backup
```bash
# Backup all Kubernetes resources
kubectl get all,secrets,configmaps,pv,pvc -n orchestrix-pilot -o yaml > cluster-backup-$(date +%Y%m%d).yaml
```

### Recovery Procedures

#### Service Recovery
```bash
# Restore from backup
kubectl apply -f cluster-backup-YYYYMMDD.yaml

# Wait for services to come online
kubectl wait --for=condition=available deployment --all -n orchestrix-pilot --timeout=600s
```

#### Data Recovery
```bash
# Restore Redis data
kubectl cp ./redis-backup-YYYYMMDD.rdb orchestrix-pilot/redis-pod:/data/dump.rdb
kubectl rollout restart deployment/redis -n orchestrix-pilot

# Restore Weaviate data
kubectl cp ./weaviate-backup-YYYYMMDD.tar.gz orchestrix-pilot/weaviate-pod:/tmp/
kubectl exec -n orchestrix-pilot deployment/weaviate -- tar -xzf /tmp/weaviate-backup.tar.gz -C /
kubectl rollout restart deployment/weaviate -n orchestrix-pilot
```

## Security Incident Response

### Security Alert Response

#### Immediate Actions
1. **Isolate affected systems**
   ```bash
   # Apply restrictive network policy
   kubectl apply -f - <<EOF
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: emergency-lockdown
     namespace: orchestrix-pilot
   spec:
     podSelector: {}
     policyTypes:
     - Ingress
     - Egress
   EOF
   ```

2. **Preserve evidence**
   ```bash
   # Capture logs
   kubectl logs --all-containers -n orchestrix-pilot > security-incident-logs-$(date +%Y%m%d-%H%M%S).txt
   
   # Capture cluster state
   kubectl get all -n orchestrix-pilot -o yaml > security-incident-state-$(date +%Y%m%d-%H%M%S).yaml
   ```

3. **Assess impact**
   - Check access logs
   - Review authentication events
   - Analyze network traffic
   - Examine data integrity

#### Recovery Actions
```bash
# Rotate all secrets
kubectl delete secret application-secrets -n orchestrix-pilot
kubectl create secret generic application-secrets -n orchestrix-pilot \
  --from-literal=database-url="new-secure-database-url" \
  --from-literal=api-keys="new-secure-api-keys"

# Update deployment to use new secrets
kubectl rollout restart deployment --all -n orchestrix-pilot

# Remove lockdown policy after verification
kubectl delete networkpolicy emergency-lockdown -n orchestrix-pilot
```

### Security Hardening Checklist

- [ ] All secrets properly encrypted at rest
- [ ] Network policies restrict inter-pod communication
- [ ] RBAC properly configured with least privilege
- [ ] All containers run as non-root
- [ ] Security contexts properly configured
- [ ] Image vulnerability scanning enabled
- [ ] Admission controllers configured
- [ ] Audit logging enabled

---

## Emergency Contacts

**Primary On-Call**: [Configure based on your team]
**Secondary On-Call**: [Configure based on your team]
**Engineering Manager**: [Configure based on your team]
**Security Team**: [Configure based on your team]

## Additional Resources

- [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [Prometheus Alerting Documentation](https://prometheus.io/docs/alerting/latest/overview/)
- [Grafana Dashboard Documentation](https://grafana.com/docs/grafana/latest/dashboards/)
- [Application Architecture Documentation](./architecture/)

---

**Document Status**: Active  
**Next Review Date**: 2025-09-08  
**Document Owner**: Platform Engineering Team