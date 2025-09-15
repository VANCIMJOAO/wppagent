"""
API endpoints para o sistema de alertas
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.routes.admin_auth import get_current_admin_user
from app.services.alert_system import AlertSeverity, AlertType, alert_manager

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    id: str
    type: str
    severity: str
    title: str
    message: str
    timestamp: datetime
    data: Dict
    resolved: bool


class AlertSummaryResponse(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int
    by_type: Dict[str, int]


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filtrar por severidade"),
    current_user=Depends(get_current_admin_user),
):
    """
    Obter lista de alertas ativos
    """
    try:
        alerts = alert_manager.get_active_alerts(severity=severity)

        return [
            AlertResponse(
                id=alert.id,
                type=alert.type.value,
                severity=alert.severity.value,
                title=alert.title,
                message=alert.message,
                timestamp=alert.timestamp,
                data=alert.data,
                resolved=alert.resolved,
            )
            for alert in alerts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar alertas: {str(e)}")


@router.get("/summary", response_model=AlertSummaryResponse)
async def get_alerts_summary(current_user=Depends(get_current_admin_user)):
    """
    Obter resumo dos alertas
    """
    try:
        summary = alert_manager.get_alert_summary()
        return AlertSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter resumo: {str(e)}")


@router.post("/resolve/{alert_id}")
async def resolve_alert(alert_id: str, current_user=Depends(get_current_admin_user)):
    """
    Resolver um alerta específico
    """
    try:
        await alert_manager.resolve_alert(alert_id)
        return {"message": f"Alerta {alert_id} resolvido com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao resolver alerta: {str(e)}"
        )


@router.post("/test")
async def create_test_alert(current_user=Depends(get_current_admin_user)):
    """
    Criar alerta de teste (apenas para desenvolvimento)
    """
    try:
        import random

        alert_id = f"test_alert_{int(datetime.now().timestamp())}"
        severities = list(AlertSeverity)
        types = list(AlertType)

        await alert_manager.create_alert(
            alert_id=alert_id,
            alert_type=random.choice(types),
            severity=random.choice(severities),
            title="Alerta de Teste",
            message=f"Este é um alerta de teste criado em {datetime.now()}",
            data={"test": True, "created_by": current_user.get("username", "test")},
        )

        return {"message": f"Alerta de teste {alert_id} criado com sucesso"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao criar alerta de teste: {str(e)}"
        )


@router.delete("/clear-resolved")
async def clear_resolved_alerts(current_user=Depends(get_current_admin_user)):
    """
    Limpar alertas resolvidos
    """
    try:
        await alert_manager.clear_resolved_alerts()
        return {"message": "Alertas resolvidos limpos com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar alertas: {str(e)}")


@router.get("/health")
async def get_system_health():
    """
    Endpoint público para verificar saúde do sistema de alertas
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
            "status": status,
            "alerts_summary": summary,
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "timestamp": datetime.utcnow()}
