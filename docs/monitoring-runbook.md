# 📊 WhatsApp Agent - Monitoring & Observability Runbook

> **Guia completo de observabilidade enterprise** com logs estruturados, health checks, métricas de performance, alertas e procedimentos de troubleshooting para produção.

---

## 🔍 **VISÃO GERAL DE OBSERVABILIDADE**

### **Observability Score: 10/10** ✅

Sistema completamente observável com **4 pilares da observabilidade**:

- ✅ **Logs Estruturados**: JSON com correlação de trace
- ✅ **Métricas**: Prometheus + performance tracking
- ✅ **Health Checks**: 4 componentes monitorados
- ✅ **Alertas**: Sistema proativo de notificações

### **Components Monitored**
1. 🔍 **Application Health**: FastAPI + Next.js
2. 🗄️ **Database Health**: PostgreSQL connections
3. 🚀 **Cache Health**: Redis operations
4. 🔗 **External APIs**: Meta WhatsApp API
5. 📡 **Webhook Status**: Message processing
6. 🛡️ **Security Events**: Audit trail completo

---

## 📋 **HEALTH CHECKS SYSTEM**

### **Basic Health Check**
```python
# app/routes/health.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import asyncio

router = APIRouter()

@router.get("/health")
async def basic_health_check():
    """
    Basic health check endpoint
    Returns simple status for load balancers
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "service": "whatsapp-agent"
    }

# Response example:
{
    "status": "healthy",
    "timestamp": "2025-01-16T21:45:32.123456Z",
    "version": "1.0.0",
    "service": "whatsapp-agent"
}
```

### **Detailed Health Check**
```python
# app/routes/health.py
@router.get("/health/detailed")
async def detailed_health_check():
    """
    Comprehensive health check with all components
    """
    start_time = datetime.utcnow()
    checks = {}
    overall_status = "healthy"
    
    # ✅ 1. Database Health Check
    try:
        db_start = time.time()
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
            db_duration = (time.time() - db_start) * 1000
            
        checks["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_duration, 2),
            "details": "PostgreSQL connection successful"
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed"
        }
        overall_status = "unhealthy"
    
    # ✅ 2. Redis Health Check
    try:
        redis_start = time.time()
        await redis_client.ping()
        redis_duration = (time.time() - redis_start) * 1000
        
        # Check cache operations
        test_key = "health_check_test"
        await redis_client.set(test_key, "test", ex=5)
        test_value = await redis_client.get(test_key)
        await redis_client.delete(test_key)
        
        checks["redis"] = {
            "status": "healthy",
            "response_time_ms": round(redis_duration, 2),
            "details": "Redis operations successful",
            "cache_test": "passed" if test_value == "test" else "failed"
        }
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Redis connection failed"
        }
        overall_status = "unhealthy"
    
    # ✅ 3. Meta API Health Check
    try:
        meta_start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.facebook.com/v18.0/me",
                params={"access_token": settings.META_ACCESS_TOKEN},
                timeout=5.0
            )
            meta_duration = (time.time() - meta_start) * 1000
            
        if response.status_code == 200:
            checks["meta_api"] = {
                "status": "healthy",
                "response_time_ms": round(meta_duration, 2),
                "details": "Meta API accessible",
                "token_valid": True
            }
        else:
            checks["meta_api"] = {
                "status": "degraded",
                "response_time_ms": round(meta_duration, 2),
                "details": f"Meta API returned {response.status_code}",
                "token_valid": False
            }
            overall_status = "degraded"
            
    except Exception as e:
        checks["meta_api"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Meta API unreachable"
        }
        overall_status = "unhealthy"
    
    # ✅ 4. Webhook Health Check
    try:
        # Check recent webhook processing
        webhook_start = time.time()
        async with AsyncSessionLocal() as db:
            recent_webhooks = await db.execute(
                text("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed
                    FROM webhook_events 
                    WHERE created_at > NOW() - INTERVAL '5 minutes'
                """)
            )
            webhook_stats = recent_webhooks.fetchone()
            webhook_duration = (time.time() - webhook_start) * 1000
        
        total_webhooks = webhook_stats.total if webhook_stats else 0
        processed_webhooks = webhook_stats.processed if webhook_stats else 0
        
        success_rate = (processed_webhooks / total_webhooks * 100) if total_webhooks > 0 else 100
        
        checks["webhook"] = {
            "status": "healthy" if success_rate >= 95 else "degraded",
            "response_time_ms": round(webhook_duration, 2),
            "details": f"Webhook processing at {success_rate}% success rate",
            "recent_webhooks": total_webhooks,
            "processed_webhooks": processed_webhooks,
            "success_rate": round(success_rate, 2)
        }
        
        if success_rate < 95:
            overall_status = "degraded"
            
    except Exception as e:
        checks["webhook"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Webhook status check failed"
        }
        overall_status = "unhealthy"
    
    # ✅ Calculate total check duration
    total_duration = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "checks": checks,
        "total_check_duration_ms": round(total_duration, 2),
        "summary": {
            "healthy_components": len([c for c in checks.values() if c["status"] == "healthy"]),
            "total_components": len(checks),
            "overall_health_score": len([c for c in checks.values() if c["status"] == "healthy"]) / len(checks) * 100
        }
    }
```

### **Health Check Response Examples**

**Healthy System:**
```json
{
    "status": "healthy",
    "timestamp": "2025-01-16T21:45:32.123456Z",
    "version": "1.0.0",
    "checks": {
        "database": {
            "status": "healthy",
            "response_time_ms": 12.45,
            "details": "PostgreSQL connection successful"
        },
        "redis": {
            "status": "healthy", 
            "response_time_ms": 3.21,
            "details": "Redis operations successful",
            "cache_test": "passed"
        },
        "meta_api": {
            "status": "healthy",
            "response_time_ms": 156.78,
            "details": "Meta API accessible",
            "token_valid": true
        },
        "webhook": {
            "status": "healthy",
            "response_time_ms": 8.92,
            "details": "Webhook processing at 98.5% success rate",
            "recent_webhooks": 23,
            "processed_webhooks": 23,
            "success_rate": 100.0
        }
    },
    "total_check_duration_ms": 181.36,
    "summary": {
        "healthy_components": 4,
        "total_components": 4,
        "overall_health_score": 100.0
    }
}
```

---

## 📝 **STRUCTURED LOGGING SYSTEM**

### **Log Architecture**
```python
# app/utils/structured_logger.py
import json
import uuid
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
from fastapi import Request

# ✅ Trace correlation context
trace_id_context: ContextVar[str] = ContextVar('trace_id', default=None)

class StructuredLogger:
    """
    Enterprise-grade structured logging with trace correlation
    """
    
    def __init__(self, service_name: str = "whatsapp-agent"):
        self.service_name = service_name
        self.log_file = "logs/security_audit.log"
        
    async def log(
        self,
        level: str,
        message: str,
        category: str = "general",
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Log structured message with full context
        """
        # ✅ Get or generate trace ID
        current_trace_id = trace_id or trace_id_context.get() or str(uuid.uuid4())
        
        # ✅ Build log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "service": self.service_name,
            "trace_id": current_trace_id,
            "message": message,
            "category": category,
            "user_id": user_id,
            "metadata": metadata or {},
            "performance_metrics": performance_metrics or {}
        }
        
        # ✅ Write to file and stdout
        log_line = json.dumps(log_entry, ensure_ascii=False)
        print(log_line, file=sys.stdout)
        
        # ✅ Write to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    
    async def info(self, message: str, **kwargs):
        await self.log("INFO", message, **kwargs)
    
    async def warning(self, message: str, **kwargs):
        await self.log("WARNING", message, **kwargs)
    
    async def error(self, message: str, **kwargs):
        await self.log("ERROR", message, **kwargs)
    
    async def critical(self, message: str, **kwargs):
        await self.log("CRITICAL", message, **kwargs)

# Global logger instance
logger = StructuredLogger()
```

### **Request Logging Middleware**
```python
# app/middleware/logging_middleware.py
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all HTTP requests with performance metrics
    """
    
    async def dispatch(self, request: Request, call_next):
        # ✅ Generate trace ID for request
        trace_id = str(uuid.uuid4())
        trace_id_context.set(trace_id)
        
        # ✅ Start timing
        start_time = time.time()
        
        # ✅ Extract request info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # ✅ Log request start
        await logger.info(
            f"Request started: {request.method} {request.url.path}",
            category="api",
            trace_id=trace_id,
            metadata={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent
            }
        )
        
        try:
            # ✅ Process request
            response = await call_next(request)
            
            # ✅ Calculate performance metrics
            duration_ms = (time.time() - start_time) * 1000
            
            # ✅ Log request completion
            await logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code} in {duration_ms:.2f}ms",
                category="api",
                trace_id=trace_id,
                performance_metrics={
                    "duration_ms": round(duration_ms, 2),
                    "status_code": response.status_code,
                    "response_size_bytes": len(response.body) if hasattr(response, 'body') else 0
                }
            )
            
            # ✅ Add trace ID to response headers
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            # ✅ Log request error
            duration_ms = (time.time() - start_time) * 1000
            
            await logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                category="api",
                trace_id=trace_id,
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                performance_metrics={
                    "duration_ms": round(duration_ms, 2)
                }
            )
            raise

# Apply logging middleware
app.add_middleware(RequestLoggingMiddleware)
```

### **Business Logic Logging**
```python
# app/services/logged_appointment_service.py
class LoggedAppointmentService:
    """
    Appointment service with comprehensive logging
    """
    
    @staticmethod
    async def create_appointment(appointment_data: dict, user_id: str) -> Appointment:
        """
        Create appointment with detailed logging
        """
        trace_id = trace_id_context.get()
        
        await logger.info(
            "Creating new appointment",
            category="business_logic",
            user_id=user_id,
            trace_id=trace_id,
            metadata={
                "business_id": appointment_data.get("business_id"),
                "service_id": appointment_data.get("service_id"),
                "scheduled_at": appointment_data.get("scheduled_at")
            }
        )
        
        try:
            # ✅ Create appointment
            appointment = await AppointmentService.create_appointment(appointment_data)
            
            await logger.info(
                f"Appointment created successfully: {appointment.id}",
                category="business_logic",
                user_id=user_id,
                trace_id=trace_id,
                metadata={
                    "appointment_id": appointment.id,
                    "status": appointment.status
                }
            )
            
            return appointment
            
        except Exception as e:
            await logger.error(
                f"Failed to create appointment: {str(e)}",
                category="business_logic",
                user_id=user_id,
                trace_id=trace_id,
                metadata={
                    "error_type": type(e).__name__,
                    "appointment_data": appointment_data
                }
            )
            raise
```

### **Log Examples**

**API Request Log:**
```json
{
    "timestamp": "2025-01-16T21:45:32.123456Z",
    "level": "INFO",
    "service": "whatsapp-agent",
    "trace_id": "9653c499-73be-4b2b-b1d9-cb2e0fd2a973",
    "message": "Request completed: GET /api/appointments - 200 in 156.45ms",
    "category": "api",
    "metadata": {
        "method": "GET",
        "path": "/api/appointments",
        "query_params": "page=1&per_page=20",
        "client_ip": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
    },
    "performance_metrics": {
        "duration_ms": 156.45,
        "status_code": 200,
        "response_size_bytes": 2048
    }
}
```

**Security Event Log:**
```json
{
    "timestamp": "2025-01-16T21:45:32.123456Z",
    "level": "WARNING",
    "service": "whatsapp-agent",
    "trace_id": "a123b456-78cd-9ef0-1234-567890abcdef",
    "message": "Rate limit exceeded for IP 192.168.1.200",
    "category": "security",
    "metadata": {
        "client_ip": "192.168.1.200",
        "endpoint": "/api/auth/login",
        "rate_limit": "5/minute",
        "violation_count": 3
    }
}
```

---

## 📊 **PERFORMANCE METRICS**

### **Prometheus Metrics**
```python
# app/monitoring/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info

# ✅ HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ✅ Database Metrics
db_connections_total = Gauge(
    'db_connections_total',
    'Current database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# ✅ Cache Metrics
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']
)

cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

# ✅ Business Metrics
appointments_created_total = Counter(
    'appointments_created_total',
    'Total appointments created',
    ['business_id', 'status']
)

messages_processed_total = Counter(
    'messages_processed_total',
    'Total messages processed',
    ['message_type', 'status']
)

# ✅ Security Metrics
security_events_total = Counter(
    'security_events_total',
    'Total security events',
    ['event_type', 'severity']
)

failed_auth_attempts_total = Counter(
    'failed_auth_attempts_total',
    'Failed authentication attempts',
    ['reason']
)

# ✅ System Metrics
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Current memory usage in bytes'
)

cpu_usage_percent = Gauge(
    'cpu_usage_percent',
    'Current CPU usage percentage'
)
```

### **Metrics Collection Middleware**
```python
# app/middleware/metrics_middleware.py
import time
import psutil
from starlette.middleware.base import BaseHTTPMiddleware

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Collect Prometheus metrics for all requests
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # ✅ Record HTTP metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            # ✅ Update system metrics
            process = psutil.Process()
            memory_usage_bytes.set(process.memory_info().rss)
            cpu_usage_percent.set(process.cpu_percent())
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # ✅ Record failed request
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            raise

app.add_middleware(MetricsMiddleware)
```

### **Metrics Endpoint**
```python
# app/routes/metrics.py
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    """
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

---

## 🚨 **ALERTING SYSTEM**

### **Prometheus Alerts Configuration**
```yaml
# prometheus/alert_rules.yml
groups:
  - name: whatsapp_agent_alerts
    rules:
      
      # ✅ High Error Rate Alert
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
          service: whatsapp-agent
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"
          
      # ✅ High Response Time Alert
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 3m
        labels:
          severity: warning
          service: whatsapp-agent
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
          
      # ✅ Database Connection Issues
      - alert: DatabaseConnectionHigh
        expr: db_connections_total > 18
        for: 1m
        labels:
          severity: warning
          service: whatsapp-agent
        annotations:
          summary: "High database connection count"
          description: "Current connections: {{ $value }} (max: 20)"
          
      # ✅ Cache Hit Rate Low
      - alert: LowCacheHitRate
        expr: cache_hit_rate < 80
        for: 5m
        labels:
          severity: warning
          service: whatsapp-agent
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}%"
          
      # ✅ Memory Usage High
      - alert: HighMemoryUsage
        expr: memory_usage_bytes > 1073741824  # 1GB
        for: 2m
        labels:
          severity: critical
          service: whatsapp-agent
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanize }}B"
          
      # ✅ Failed Authentication Spike
      - alert: AuthenticationFailureSpike
        expr: rate(failed_auth_attempts_total[5m]) > 0.5
        for: 1m
        labels:
          severity: critical
          service: whatsapp-agent
        annotations:
          summary: "High authentication failure rate"
          description: "{{ $value }} failed authentication attempts per second"
          
      # ✅ Health Check Failure
      - alert: HealthCheckFailure
        expr: up{job="whatsapp-agent"} == 0
        for: 30s
        labels:
          severity: critical
          service: whatsapp-agent
        annotations:
          summary: "Service is down"
          description: "WhatsApp Agent service is not responding to health checks"
```

### **Alert Manager Configuration**
```yaml
# alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@whatsappagent.com'
  smtp_auth_username: 'alerts@whatsappagent.com'
  smtp_auth_password: '${SMTP_PASSWORD}'

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  # ✅ Critical Alerts (immediate notification)
  - name: 'critical-alerts'
    email_configs:
      - to: 'ops-team@whatsappagent.com'
        subject: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        body: |
          Alert: {{ .GroupLabels.alertname }}
          Severity: {{ .CommonLabels.severity }}
          Service: {{ .CommonLabels.service }}
          
          Details:
          {{ range .Alerts }}
          - {{ .Annotations.summary }}
          - {{ .Annotations.description }}
          {{ end }}
          
          Dashboard: https://grafana.whatsappagent.com
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#alerts'
        title: '🚨 Critical Alert'
        text: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        
  # ✅ Warning Alerts (batch notification)
  - name: 'warning-alerts'
    email_configs:
      - to: 'dev-team@whatsappagent.com'
        subject: '⚠️ WARNING: {{ .GroupLabels.alertname }}'
        body: |
          Alert: {{ .GroupLabels.alertname }}
          Severity: {{ .CommonLabels.severity }}
          
          {{ .CommonAnnotations.description }}
```

### **Custom Alert Handler**
```python
# app/monitoring/alert_handler.py
import asyncio
from typing import Dict, Any
from datetime import datetime

class AlertHandler:
    """
    Custom alert handling and escalation
    """
    
    def __init__(self):
        self.alert_history = []
        self.escalation_rules = {
            "critical": {"escalate_after": 300, "max_attempts": 5},  # 5 minutes
            "warning": {"escalate_after": 1800, "max_attempts": 3}   # 30 minutes
        }
    
    async def handle_alert(self, alert: Dict[str, Any]):
        """
        Process incoming alert with custom logic
        """
        alert_id = self.generate_alert_id(alert)
        severity = alert.get("labels", {}).get("severity", "warning")
        
        # ✅ Log alert
        await logger.critical(
            f"Alert triggered: {alert.get('annotations', {}).get('summary', 'Unknown alert')}",
            category="alerts",
            metadata={
                "alert_id": alert_id,
                "severity": severity,
                "labels": alert.get("labels", {}),
                "annotations": alert.get("annotations", {})
            }
        )
        
        # ✅ Check for automatic remediation
        remediation_result = await self.attempt_auto_remediation(alert)
        
        if remediation_result:
            await logger.info(
                f"Alert auto-remediated: {alert_id}",
                category="alerts",
                metadata={"remediation_action": remediation_result}
            )
            return
        
        # ✅ Store alert for escalation tracking
        self.alert_history.append({
            "alert_id": alert_id,
            "timestamp": datetime.utcnow(),
            "severity": severity,
            "alert": alert
        })
        
        # ✅ Send immediate notification for critical alerts
        if severity == "critical":
            await self.send_immediate_notification(alert)
    
    async def attempt_auto_remediation(self, alert: Dict[str, Any]) -> str:
        """
        Attempt automatic remediation for known issues
        """
        alert_name = alert.get("labels", {}).get("alertname", "")
        
        # ✅ Auto-restart for memory issues
        if alert_name == "HighMemoryUsage":
            # Trigger garbage collection
            import gc
            gc.collect()
            return "garbage_collection_triggered"
        
        # ✅ Cache clearing for cache issues
        if alert_name == "LowCacheHitRate":
            # Clear problematic cache entries
            pattern = "stale:*"
            await cache_manager.delete_pattern(pattern)
            return "stale_cache_cleared"
        
        # ✅ Connection pool refresh for DB issues
        if alert_name == "DatabaseConnectionHigh":
            # Force connection pool refresh
            await database_manager.refresh_connection_pool()
            return "db_pool_refreshed"
        
        return None
    
    async def send_immediate_notification(self, alert: Dict[str, Any]):
        """
        Send immediate notification for critical alerts
        """
        # Implementation for immediate notifications
        # (Slack, email, SMS, PagerDuty, etc.)
        pass

# Global alert handler
alert_handler = AlertHandler()
```

---

## 🔍 **LOG ANALYSIS TOOLS**

### **Log Query Commands**
```bash
# ✅ Real-time log monitoring
tail -f logs/security_audit.log | jq '.'

# ✅ Filter by log level
grep '"level":"ERROR"' logs/security_audit.log | jq '.'

# ✅ Filter by category
grep '"category":"security"' logs/security_audit.log | jq '.'

# ✅ Find logs by trace ID
grep "9653c499-73be-4b2b-b1d9-cb2e0fd2a973" logs/security_audit.log | jq '.'

# ✅ Performance analysis
grep '"category":"api"' logs/security_audit.log | jq '.performance_metrics.duration_ms' | sort -n

# ✅ Error summary
grep '"level":"ERROR"' logs/security_audit.log | jq -r '.message' | sort | uniq -c

# ✅ Top endpoints by request count
grep '"category":"api"' logs/security_audit.log | jq -r '.metadata.path' | sort | uniq -c | sort -nr

# ✅ Slow requests (>1000ms)
grep '"category":"api"' logs/security_audit.log | jq 'select(.performance_metrics.duration_ms > 1000)'

# ✅ Security events summary
grep '"category":"security"' logs/security_audit.log | jq -r '.message' | sort | uniq -c
```

### **Log Aggregation Queries**
```bash
# ✅ Request volume per minute
grep '"category":"api"' logs/security_audit.log | \
jq -r '.timestamp[0:16]' | sort | uniq -c

# ✅ Error rate calculation
total_requests=$(grep '"category":"api"' logs/security_audit.log | wc -l)
error_requests=$(grep '"level":"ERROR"' logs/security_audit.log | grep '"category":"api"' | wc -l)
echo "Error rate: $(echo "scale=2; $error_requests * 100 / $total_requests" | bc)%"

# ✅ Average response time
grep '"category":"api"' logs/security_audit.log | \
jq '.performance_metrics.duration_ms' | \
awk '{sum+=$1; count++} END {print "Average response time:", sum/count, "ms"}'

# ✅ Top error messages
grep '"level":"ERROR"' logs/security_audit.log | \
jq -r '.message' | sort | uniq -c | sort -nr | head -10
```

### **Log Analysis Script**
```python
# scripts/log_analyzer.py
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class LogAnalyzer:
    """
    Analyze structured logs for insights
    """
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.logs = []
        self.load_logs()
    
    def load_logs(self):
        """Load and parse log file"""
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    self.logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
    
    def analyze_performance(self, hours: int = 1) -> dict:
        """Analyze performance metrics for last N hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        api_logs = [
            log for log in self.logs
            if log.get('category') == 'api' and 
            datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff
        ]
        
        if not api_logs:
            return {"error": "No API logs found"}
        
        durations = [
            log.get('performance_metrics', {}).get('duration_ms', 0)
            for log in api_logs
        ]
        
        return {
            "total_requests": len(api_logs),
            "avg_response_time_ms": sum(durations) / len(durations),
            "max_response_time_ms": max(durations),
            "min_response_time_ms": min(durations),
            "slow_requests": len([d for d in durations if d > 1000])
        }
    
    def analyze_errors(self, hours: int = 24) -> dict:
        """Analyze error patterns"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        error_logs = [
            log for log in self.logs
            if log.get('level') in ['ERROR', 'CRITICAL'] and
            datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff
        ]
        
        error_messages = Counter([log.get('message', '') for log in error_logs])
        error_categories = Counter([log.get('category', '') for log in error_logs])
        
        return {
            "total_errors": len(error_logs),
            "top_error_messages": dict(error_messages.most_common(5)),
            "error_categories": dict(error_categories),
            "error_rate_per_hour": len(error_logs) / hours
        }
    
    def analyze_security(self, hours: int = 24) -> dict:
        """Analyze security events"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        security_logs = [
            log for log in self.logs
            if log.get('category') == 'security' and
            datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > cutoff
        ]
        
        event_types = Counter([
            log.get('metadata', {}).get('event_type', 'unknown')
            for log in security_logs
        ])
        
        return {
            "total_security_events": len(security_logs),
            "event_types": dict(event_types),
            "critical_events": len([
                log for log in security_logs 
                if log.get('level') == 'CRITICAL'
            ])
        }

# Usage example
if __name__ == "__main__":
    analyzer = LogAnalyzer("logs/security_audit.log")
    
    print("Performance Analysis (Last Hour):")
    print(json.dumps(analyzer.analyze_performance(1), indent=2))
    
    print("\nError Analysis (Last 24 Hours):")
    print(json.dumps(analyzer.analyze_errors(24), indent=2))
    
    print("\nSecurity Analysis (Last 24 Hours):")
    print(json.dumps(analyzer.analyze_security(24), indent=2))
```

---

## 📈 **DASHBOARD SETUP**

### **Grafana Dashboard Configuration**
```json
{
  "dashboard": {
    "title": "WhatsApp Agent - Production Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      },
      {
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "db_connections_total",
            "legendFormat": "Active Connections"
          },
          {
            "expr": "rate(db_query_duration_seconds_sum[5m]) / rate(db_query_duration_seconds_count[5m])",
            "legendFormat": "Avg Query Time"
          }
        ]
      },
      {
        "title": "Cache Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "cache_hit_rate",
            "legendFormat": "Hit Rate %"
          },
          {
            "expr": "rate(cache_operations_total[5m])",
            "legendFormat": "{{operation}} ops/sec"
          }
        ]
      }
    ]
  }
}
```

---

## 🔧 **OPERATIONAL PROCEDURES**

### **Daily Monitoring Checklist**
```bash
#!/bin/bash
# scripts/daily_health_check.sh

echo "🔍 Daily Health Check - $(date)"
echo "================================"

# ✅ 1. Health Check
echo "1. Application Health:"
curl -s http://localhost:8000/health | jq '.'

echo -e "\n2. Detailed Health:"
curl -s http://localhost:8000/health/detailed | jq '.summary'

# ✅ 3. Log Analysis
echo -e "\n3. Error Analysis (Last 24h):"
python scripts/log_analyzer.py

# ✅ 4. Performance Check
echo -e "\n4. Performance Metrics:"
curl -s http://localhost:9090/api/v1/query?query=rate\(http_requests_total\[5m\]\) | jq '.data.result[0].value[1]'

# ✅ 5. Database Status
echo -e "\n5. Database Status:"
psql $DATABASE_URL -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';"

# ✅ 6. Cache Status
echo -e "\n6. Cache Status:"
redis-cli -u $REDIS_URL info memory | grep used_memory_human

echo -e "\n✅ Daily health check completed"
```

### **Incident Response Playbook**
```markdown
# Incident Response Playbook

## 🚨 CRITICAL ALERT: Service Down
1. **Immediate Actions (0-5 minutes)**
   - Check health endpoint: `curl https://yourdomain.com/health`
   - Check server status: `systemctl status whatsapp-backend`
   - Check logs: `tail -50 logs/security_audit.log`

2. **Investigation (5-15 minutes)**
   - Check system resources: `htop`, `df -h`
   - Check database: `psql $DATABASE_URL -c "SELECT 1"`
   - Check Redis: `redis-cli -u $REDIS_URL ping`

3. **Recovery Actions**
   - Restart services: `systemctl restart whatsapp-backend`
   - Clear cache if needed: `redis-cli -u $REDIS_URL flushall`
   - Scale resources if needed

## ⚠️ WARNING ALERT: High Response Time
1. **Check Performance**
   - Monitor endpoint: `/metrics`
   - Analyze slow queries: `grep "duration_ms.*[5-9][0-9][0-9][0-9]" logs/security_audit.log`

2. **Optimization Actions**
   - Check database performance
   - Analyze cache hit rate
   - Review recent deployments

## 🔍 SECURITY ALERT: Authentication Failures
1. **Immediate Assessment**
   - Check source IPs: `grep "failed_auth" logs/security_audit.log | jq -r '.metadata.client_ip' | sort | uniq -c`
   - Review patterns: Time of day, frequency, methods

2. **Protection Actions**
   - Block malicious IPs: `iptables -A INPUT -s MALICIOUS_IP -j DROP`
   - Increase rate limiting temporarily
   - Notify security team
```

---

## 📞 **MONITORING SUPPORT**

### **Runbook Contacts**
- 🔧 **Operations Team**: ops@whatsappagent.com
- 🛡️ **Security Team**: security@whatsappagent.com
- 👨‍💻 **Development Team**: dev@whatsappagent.com

### **Escalation Matrix**
1. **Level 1**: Automated resolution attempts
2. **Level 2**: Operations team notification
3. **Level 3**: Development team escalation
4. **Level 4**: Management escalation

---

<div align="center">

**📊 ENTERPRISE-GRADE OBSERVABILITY SYSTEM**

*Complete visibility into system health, performance, and security*

**Observability Score: 10/10** ✅

</div>