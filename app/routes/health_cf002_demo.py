"""
🔧 CF002 - Health Check Demo Routes para Response Wrapper
========================================================

Demonstra diferentes tipos de response com padronização automática.
Ideal para testes frontend e validação do wrapper.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/health-demo", tags=["CF002 Health Demo"])


@router.get("/simple")
async def simple_health_cf002():
    """CF002 - Health check simples com wrapper automático"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "whats_agent",
    }


@router.get("/detailed")
async def detailed_health_cf002():
    """CF002 - Health check detalhado com métricas"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "whats_agent",
        "version": "1.0.0",
        "uptime_seconds": 3600,
        "database": {"status": "connected", "latency_ms": 45},
        "memory": {"used_mb": 128, "available_mb": 512},
    }


@router.get("/database-error")
async def database_error_demo_cf002():
    """CF002 - Simula erro de banco padronizado"""
    raise HTTPException(status_code=503, detail="Database connection timeout")


@router.get("/unauthorized")
async def unauthorized_demo_cf002():
    """CF002 - Simula erro de autorização"""
    raise HTTPException(
        status_code=401, detail="Authentication token is invalid or expired"
    )


@router.get("/metrics")
async def metrics_demo_cf002():
    """CF002 - Métricas do sistema com wrapper"""
    return {
        "requests_total": 1234,
        "requests_per_minute": 56,
        "average_response_time_ms": 120,
        "error_rate_percent": 0.5,
        "active_sessions": 89,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/test-notification")
async def test_notification_cf002(notification_data: Dict[str, Any]):
    """CF002 - Teste de notificação com wrapper POST"""
    return {
        "notification_id": "notif_123456",
        "message": notification_data.get("message", "Test notification"),
        "sent_at": datetime.now().isoformat(),
        "status": "sent",
        "recipient": notification_data.get("recipient", "test@example.com"),
    }
