"""
Schemas para health check e monitoramento
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheckResponse(BaseModel):
    status: HealthStatus
    timestamp: str
    version: str = "1.0.0"
    

class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: int


class AppInfo(BaseModel):
    name: str = "WhatsApp Agent"
    version: str = "1.0.0"
    environment: str = "production"


class SystemHealth(BaseModel):
    database: HealthStatus
    redis: Optional[HealthStatus] = None
    whatsapp_api: HealthStatus
    

class DetailedHealthResponse(BaseModel):
    status: HealthStatus
    timestamp: str
    app_info: AppInfo
    system_metrics: SystemMetrics
    system_health: SystemHealth
    additional_info: Optional[Dict[str, Any]] = None
