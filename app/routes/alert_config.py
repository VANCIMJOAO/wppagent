"""
API endpoints para configuração de alertas
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.routes.admin_auth import get_current_admin_user
from app.monitoring.alerting_system import AlertRule, AlertSeverity, NotificationChannel, NotificationConfig, AlertManager
from app.models.database import AdminUser
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/alert-config", tags=["alert-config"])

# Modelos Pydantic
class AlertRuleRequest(BaseModel):
    name: str = Field(..., description="Nome da regra de alerta")
    metric_name: str = Field(..., description="Nome da métrica")
    condition: str = Field(..., description="Condição (gt, gte, lt, lte, eq, ne)")
    threshold: float = Field(..., description="Valor limite")
    duration: int = Field(..., description="Duração em segundos")
    severity: str = Field(..., description="Severidade (low, medium, high, critical)")
    description: str = Field(..., description="Descrição do alerta")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags adicionais")
    enabled: bool = Field(default=True, description="Se a regra está habilitada")

class AlertRuleResponse(BaseModel):
    name: str
    metric_name: str
    condition: str
    threshold: float
    duration: int
    severity: str
    description: str
    tags: Dict[str, str]
    enabled: bool

class NotificationConfigRequest(BaseModel):
    channel: str = Field(..., description="Canal (email, slack, webhook, console)")
    target: str = Field(..., description="Destino (email, webhook URL, etc)")
    min_severity: str = Field(..., description="Severidade mínima")
    rate_limit: int = Field(..., description="Rate limit em segundos")
    enabled: bool = Field(default=True, description="Se está habilitado")

class NotificationConfigResponse(BaseModel):
    channel: str
    target: str
    min_severity: str
    rate_limit: int
    enabled: bool

class AlertTestRequest(BaseModel):
    rule_name: str = Field(..., description="Nome da regra para testar")
    test_value: float = Field(..., description="Valor para testar")

class AlertTestResponse(BaseModel):
    triggered: bool
    message: str
    current_value: float
    threshold: float
    condition: str

# Instância global do AlertManager
alert_manager = AlertManager()

@router.get("/rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Obter todas as regras de alerta configuradas"""
    try:
        rules = []
        for rule in alert_manager.rules.values():
            rules.append(AlertRuleResponse(
                name=rule.name,
                metric_name=rule.metric_name,
                condition=rule.condition,
                threshold=rule.threshold,
                duration=rule.duration,
                severity=rule.severity.value,
                description=rule.description,
                tags=rule.tags,
                enabled=rule.enabled
            ))
        
        return rules
    except Exception as e:
        logger.error(f"Erro ao obter regras de alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    request: AlertRuleRequest,
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Criar nova regra de alerta"""
    try:
        # Validar severidade
        try:
            severity = AlertSeverity(request.severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Severidade inválida: {request.severity}")
        
        # Validar condição
        valid_conditions = ["gt", "gte", "lt", "lte", "eq", "ne"]
        if request.condition not in valid_conditions:
            raise HTTPException(status_code=400, detail=f"Condição inválida: {request.condition}")
        
        # Criar regra
        rule = AlertRule(
            name=request.name,
            metric_name=request.metric_name,
            condition=request.condition,
            threshold=request.threshold,
            duration=request.duration,
            severity=severity,
            description=request.description,
            tags=request.tags,
            enabled=request.enabled
        )
        
        # Adicionar ao gerenciador
        alert_manager.add_rule(rule)
        
        logger.info(f"Regra de alerta criada: {request.name}")
        
        return AlertRuleResponse(
            name=rule.name,
            metric_name=rule.metric_name,
            condition=rule.condition,
            threshold=rule.threshold,
            duration=rule.duration,
            severity=rule.severity.value,
            description=rule.description,
            tags=rule.tags,
            enabled=rule.enabled
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar regra de alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/rules/{rule_name}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_name: str,
    request: AlertRuleRequest,
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Atualizar regra de alerta existente"""
    try:
        if rule_name not in alert_manager.rules:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
        
        # Validar severidade
        try:
            severity = AlertSeverity(request.severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Severidade inválida: {request.severity}")
        
        # Validar condição
        valid_conditions = ["gt", "gte", "lt", "lte", "eq", "ne"]
        if request.condition not in valid_conditions:
            raise HTTPException(status_code=400, detail=f"Condição inválida: {request.condition}")
        
        # Remover regra antiga
        alert_manager.remove_rule(rule_name)
        
        # Criar nova regra
        rule = AlertRule(
            name=request.name,
            metric_name=request.metric_name,
            condition=request.condition,
            threshold=request.threshold,
            duration=request.duration,
            severity=severity,
            description=request.description,
            tags=request.tags,
            enabled=request.enabled
        )
        
        # Adicionar ao gerenciador
        alert_manager.add_rule(rule)
        
        logger.info(f"Regra de alerta atualizada: {request.name}")
        
        return AlertRuleResponse(
            name=rule.name,
            metric_name=rule.metric_name,
            condition=rule.condition,
            threshold=rule.threshold,
            duration=rule.duration,
            severity=rule.severity.value,
            description=rule.description,
            tags=rule.tags,
            enabled=rule.enabled
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar regra de alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/rules/{rule_name}")
async def delete_alert_rule(
    rule_name: str,
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Deletar regra de alerta"""
    try:
        if rule_name not in alert_manager.rules:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
        
        alert_manager.remove_rule(rule_name)
        
        logger.info(f"Regra de alerta deletada: {rule_name}")
        
        return {"message": "Regra deletada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar regra de alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications", response_model=List[NotificationConfigResponse])
async def get_notification_configs(
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Obter configurações de notificação"""
    try:
        configs = []
        for config in alert_manager.notification_service.configs:
            configs.append(NotificationConfigResponse(
                channel=config.channel.value,
                target=config.target,
                min_severity=config.min_severity.value,
                rate_limit=config.rate_limit,
                enabled=config.enabled
            ))
        
        return configs
    except Exception as e:
        logger.error(f"Erro ao obter configurações de notificação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications", response_model=NotificationConfigResponse)
async def create_notification_config(
    request: NotificationConfigRequest,
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Criar nova configuração de notificação"""
    try:
        # Validar canal
        try:
            channel = NotificationChannel(request.channel.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Canal inválido: {request.channel}")
        
        # Validar severidade
        try:
            min_severity = AlertSeverity(request.min_severity.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Severidade inválida: {request.min_severity}")
        
        # Criar configuração
        config = NotificationConfig(
            channel=channel,
            target=request.target,
            min_severity=min_severity,
            rate_limit=request.rate_limit,
            enabled=request.enabled
        )
        
        # Adicionar ao serviço
        alert_manager.notification_service.add_config(config)
        
        logger.info(f"Configuração de notificação criada: {request.channel}")
        
        return NotificationConfigResponse(
            channel=config.channel.value,
            target=config.target,
            min_severity=config.min_severity.value,
            rate_limit=config.rate_limit,
            enabled=config.enabled
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar configuração de notificação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test", response_model=AlertTestResponse)
async def test_alert_rule(
    request: AlertTestRequest,
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Testar regra de alerta com valor específico"""
    try:
        if request.rule_name not in alert_manager.rules:
            raise HTTPException(status_code=404, detail="Regra não encontrada")
        
        rule = alert_manager.rules[request.rule_name]
        triggered = rule.evaluate(request.test_value)
        
        message = f"Regra {'disparada' if triggered else 'não disparada'} com valor {request.test_value}"
        
        return AlertTestResponse(
            triggered=triggered,
            message=message,
            current_value=request.test_value,
            threshold=rule.threshold,
            condition=rule.condition
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao testar regra de alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_available_metrics(
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Obter lista de métricas disponíveis"""
    try:
        # Lista de métricas disponíveis no sistema
        metrics = [
            {
                "name": "system.cpu.usage_percent",
                "description": "Uso de CPU em percentual",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "system.memory.usage_percent",
                "description": "Uso de memória em percentual",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "system.disk.usage_percent",
                "description": "Uso de disco em percentual",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "api.response_time_ms",
                "description": "Tempo de resposta da API",
                "unit": "ms",
                "type": "histogram"
            },
            {
                "name": "api.error_rate",
                "description": "Taxa de erro da API",
                "unit": "%",
                "type": "gauge"
            },
            {
                "name": "whatsapp.messages.sent",
                "description": "Mensagens WhatsApp enviadas",
                "unit": "count",
                "type": "counter"
            },
            {
                "name": "whatsapp.messages.received",
                "description": "Mensagens WhatsApp recebidas",
                "unit": "count",
                "type": "counter"
            },
            {
                "name": "database.connections.active",
                "description": "Conexões ativas do banco",
                "unit": "count",
                "type": "gauge"
            },
            {
                "name": "redis.memory.usage",
                "description": "Uso de memória do Redis",
                "unit": "bytes",
                "type": "gauge"
            }
        ]
        
        return {"metrics": metrics}
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas disponíveis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_alert_system_status(
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """Obter status do sistema de alertas"""
    try:
        return {
            "enabled": alert_manager.running,
            "total_rules": len(alert_manager.rules),
            "active_rules": len([r for r in alert_manager.rules.values() if r.enabled]),
            "total_notifications": len(alert_manager.notification_service.configs),
            "active_alerts": len(alert_manager.active_alerts),
            "last_evaluation": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter status do sistema de alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
