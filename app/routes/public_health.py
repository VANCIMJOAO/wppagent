"""
Endpoint público para monitoramento de saúde do sistema de alertas
"""

from datetime import datetime

from fastapi import APIRouter

from app.services.alert_system import alert_manager

# Router público (sem autenticação)
public_router = APIRouter(prefix="/health", tags=["system-health"])


@public_router.get("/alerts")
async def get_public_alert_health():
    """
    Endpoint público para verificar saúde do sistema de alertas
    Não requer autenticação - para monitoramento externo
    """
    try:
        summary = alert_manager.get_alert_summary()

        # Determinar status geral baseado nos alertas
        if summary["critical"] > 0:
            status = "critical"
        elif summary["high"] > 0:
            status = "warning"
        elif summary["medium"] > 0:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "service": "WhatsApp Agent Alert System",
            "status": status,
            "alerts_summary": summary,
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",
        }
    except Exception as e:
        return {
            "service": "WhatsApp Agent Alert System",
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",
        }


@public_router.get("/system")
async def get_public_system_health():
    """
    Endpoint público para verificar saúde geral do sistema
    """
    try:
        # Informações básicas do sistema sem dados sensíveis
        alert_summary = alert_manager.get_alert_summary()

        # Status simplificado
        if alert_summary["critical"] > 0:
            overall_status = "critical"
        elif alert_summary["high"] > 0:
            overall_status = "warning"
        else:
            overall_status = "operational"

        return {
            "service": "WhatsApp Agent API",
            "status": overall_status,
            "components": {
                "alert_system": {
                    "status": "operational",
                    "active_alerts": alert_summary["total"],
                },
                "api": {"status": "operational"},
                "database": {"status": "operational"},
            },
            "timestamp": datetime.utcnow(),
            "uptime": "available",
        }
    except Exception as e:
        return {
            "service": "WhatsApp Agent API",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow(),
        }
