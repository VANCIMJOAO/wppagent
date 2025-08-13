"""
Prometheus Metrics Integration for WhatsApp Agent
Provides comprehensive monitoring and observability for production deployment
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info, 
    CollectorRegistry, generate_latest, 
    CONTENT_TYPE_LATEST
)
from fastapi import Response
import time
import psutil
import logging

logger = logging.getLogger(__name__)

# Create custom registry for our metrics
registry = CollectorRegistry()

# API Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=registry
)

# Webhook Metrics
webhook_messages_processed_total = Counter(
    'webhook_messages_processed_total',
    'Total webhook messages processed',
    ['status'],
    registry=registry
)

webhook_processing_duration_seconds = Histogram(
    'webhook_processing_duration_seconds',
    'Webhook processing duration in seconds',
    registry=registry
)

# Database Metrics
database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=registry
)

database_connections_idle = Gauge(
    'database_connections_idle',
    'Number of idle database connections',
    registry=registry
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    registry=registry
)

# System Metrics
process_resident_memory_bytes = Gauge(
    'process_resident_memory_bytes',
    'Resident memory size in bytes',
    registry=registry
)

process_cpu_seconds_total = Counter(
    'process_cpu_seconds_total',
    'Total user and system CPU time spent in seconds',
    registry=registry
)

# Rate Limiting Metrics
rate_limit_hits_total = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['limit_type'],
    registry=registry
)

# Business Metrics
lead_scoring_processed_total = Counter(
    'lead_scoring_processed_total',
    'Total leads processed through scoring',
    ['score_range'],
    registry=registry
)

lead_scoring_errors_total = Counter(
    'lead_scoring_errors_total',
    'Total lead scoring errors',
    ['error_type'],
    registry=registry
)

lead_scoring_duration_seconds = Histogram(
    'lead_scoring_duration_seconds',
    'Lead scoring processing duration in seconds',
    registry=registry
)

# Cache Metrics
cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate as a percentage',
    registry=registry
)

cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result'],
    registry=registry
)

# Application Info
app_info = Info(
    'whatsapp_agent_info',
    'WhatsApp Agent application information',
    registry=registry
)

class MetricsCollector:
    """Centralized metrics collection and reporting"""
    
    def __init__(self):
        self.start_time = time.time()
        self._last_cpu_time = 0
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Set application info
        app_info.info({
            'version': '2.0.0',
            'environment': 'production',
            'service': 'whatsapp-agent'
        })
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        try:
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        except Exception as e:
            logger.error(f"Error recording HTTP metrics: {e}")
    
    def record_webhook_processing(self, status: str, duration: float):
        """Record webhook processing metrics"""
        try:
            webhook_messages_processed_total.labels(status=status).inc()
            webhook_processing_duration_seconds.observe(duration)
        except Exception as e:
            logger.error(f"Error recording webhook metrics: {e}")
    
    def record_database_query(self, operation: str, duration: float):
        """Record database query metrics"""
        try:
            database_query_duration_seconds.labels(operation=operation).observe(duration)
        except Exception as e:
            logger.error(f"Error recording database metrics: {e}")
    
    def record_rate_limit_hit(self, limit_type: str):
        """Record rate limit hits"""
        try:
            rate_limit_hits_total.labels(limit_type=limit_type).inc()
        except Exception as e:
            logger.error(f"Error recording rate limit metrics: {e}")
    
    def record_lead_scoring(self, score: int, duration: float, error_type: str = None):
        """Record lead scoring metrics"""
        try:
            if error_type:
                lead_scoring_errors_total.labels(error_type=error_type).inc()
            else:
                # Categorize score ranges
                if score >= 80:
                    score_range = "high"
                elif score >= 60:
                    score_range = "medium"
                else:
                    score_range = "low"
                
                lead_scoring_processed_total.labels(score_range=score_range).inc()
                lead_scoring_duration_seconds.observe(duration)
        except Exception as e:
            logger.error(f"Error recording lead scoring metrics: {e}")
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operations"""
        try:
            cache_operations_total.labels(operation=operation, result=result).inc()
            
            # Update cache hit rate
            if result == "hit":
                self._cache_hits += 1
            elif result == "miss":
                self._cache_misses += 1
            
            total_ops = self._cache_hits + self._cache_misses
            if total_ops > 0:
                hit_rate = (self._cache_hits / total_ops) * 100
                cache_hit_rate.set(hit_rate)
        except Exception as e:
            logger.error(f"Error recording cache metrics: {e}")
    
    def update_database_connections(self, active: int, idle: int):
        """Update database connection counts"""
        try:
            database_connections_active.set(active)
            database_connections_idle.set(idle)
        except Exception as e:
            logger.error(f"Error updating database connection metrics: {e}")
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            process_resident_memory_bytes.set(memory_info.rss)
            
            # CPU usage
            cpu_times = process.cpu_times()
            current_cpu_time = cpu_times.user + cpu_times.system
            if self._last_cpu_time > 0:
                cpu_delta = current_cpu_time - self._last_cpu_time
                process_cpu_seconds_total._value._value += cpu_delta
            self._last_cpu_time = current_cpu_time
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        try:
            # Update system metrics before generating output
            self.update_system_metrics()
            return generate_latest(registry).decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return ""

# Global metrics collector instance
metrics_collector = MetricsCollector()

def get_metrics_response() -> Response:
    """Get metrics as FastAPI Response"""
    metrics_data = metrics_collector.get_metrics()
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )

# Context managers for timing operations
class timer:
    """Context manager for timing operations"""
    
    def __init__(self, callback):
        self.callback = callback
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.callback(duration)

def http_request_timer(method: str, endpoint: str):
    """Timer for HTTP requests"""
    return timer(lambda duration: metrics_collector.record_http_request(
        method, endpoint, 200, duration
    ))

def webhook_timer():
    """Timer for webhook processing"""
    return timer(lambda duration: metrics_collector.record_webhook_processing(
        "success", duration
    ))

def database_timer(operation: str):
    """Timer for database operations"""
    return timer(lambda duration: metrics_collector.record_database_query(
        operation, duration
    ))

def lead_scoring_timer():
    """Timer for lead scoring operations"""
    return timer(lambda duration: duration)  # Duration handled separately in record_lead_scoring
