"""
🚨 OM003 - Sistema Básico de Alertas para Observabilidade
========================================================

Implementa:
- Regras de alerta configuráveis
- Avaliação de métricas contra thresholds
- Integração com health check detalhado
- Logging estruturado de alertas

Alertas implementados:
- webhook_failure_rate > 10%
- message_processing_delay > 5000ms
- database_connection_errors > 0
- redis_unavailable == true

Autor: GitHub Copilot
Data: 2025-09-12
Status: OM003 Implementation - Basic Alert System
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.structured_apm import get_structured_logger

logger = get_structured_logger(__name__)
router = APIRouter(prefix="/health", tags=["Health Monitoring"])


class BasicAlertManager:
    """🚨 OM003 - Sistema básico de alertas"""

    def __init__(self):
        self.alert_rules = {
            "webhook_failure_rate": {
                "condition": "webhook_failure_rate > 10",
                "threshold": 10.0,
                "severity": "warning",
                "description": "Taxa de falha do webhook está alta (>10%)",
                "recommended_action": "Verificar logs do webhook e conectividade com Meta API",
            },
            "message_processing_delay": {
                "condition": "avg_processing_time > 5000",
                "threshold": 5000.0,  # 5 segundos
                "severity": "critical",
                "description": "Tempo de processamento de mensagens muito alto (>5s)",
                "recommended_action": "Verificar performance do banco e otimizar queries",
            },
            "database_connection": {
                "condition": "db_connection_errors > 0",
                "threshold": 0,
                "severity": "critical",
                "description": "Erros de conexão com banco de dados detectados",
                "recommended_action": "Verificar conectividade PostgreSQL e pool de conexões",
            },
            "redis_unavailable": {
                "condition": "redis_health == 0",
                "threshold": 0,
                "severity": "warning",
                "description": "Redis/Cache indisponível ou degradado",
                "recommended_action": "Verificar status do Redis e configuração de cache",
            },
            "appointments_creation_rate": {
                "condition": "appointments_per_hour < 1",
                "threshold": 1,
                "severity": "info",
                "description": "Taxa de criação de agendamentos baixa (<1/hora)",
                "recommended_action": "Verificar fluxo de agendamentos e campanhas ativas",
            },
            "meta_api_connectivity": {
                "condition": "meta_api_errors > 0",
                "threshold": 0,
                "severity": "critical",
                "description": "Erros de conectividade com Meta API (WhatsApp)",
                "recommended_action": "Verificar token de acesso e status da API do WhatsApp",
            },
        }

    async def evaluate_alerts(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """🚨 Avaliar métricas contra regras de alerta"""
        active_alerts = []

        logger.info(
            "🚨 OM003 - Avaliando alertas",
            metadata={
                "metrics_count": len(metrics),
                "rules_count": len(self.alert_rules),
            },
            category="alert_evaluation",
        )

        for alert_name, rule in self.alert_rules.items():
            try:
                if await self._should_fire_alert(alert_name, rule, metrics):
                    metric_name = self._extract_metric_name(rule["condition"])
                    current_value = metrics.get(metric_name, 0)

                    alert = {
                        "name": alert_name,
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "recommended_action": rule.get(
                            "recommended_action", "Verificar logs do sistema"
                        ),
                        "metric_name": metric_name,
                        "current_value": current_value,
                        "threshold": rule["threshold"],
                        "condition": rule["condition"],
                        "fired_at": datetime.utcnow().isoformat(),
                        "alert_id": f"om003_{alert_name}_{int(datetime.utcnow().timestamp())}",
                    }
                    active_alerts.append(alert)

                    # Log alerta com severidade apropriada
                    if rule["severity"] == "critical":
                        logger.error(
                            f"🚨 CRITICAL ALERT: {alert_name}",
                            metadata=alert,
                            category="alert_fired",
                        )
                    elif rule["severity"] == "warning":
                        logger.warning(
                            f"⚠️ WARNING ALERT: {alert_name}",
                            metadata=alert,
                            category="alert_fired",
                        )
                    else:
                        logger.info(
                            f"ℹ️ INFO ALERT: {alert_name}",
                            metadata=alert,
                            category="alert_fired",
                        )

            except Exception as e:
                logger.error(
                    f"❌ OM003 Erro ao avaliar alerta {alert_name}: {str(e)}",
                    metadata={"alert_name": alert_name, "error": str(e)},
                    category="alert_error",
                )

        logger.info(
            f"🚨 OM003 Avaliação completa: {len(active_alerts)} alertas ativos",
            metadata={"active_alerts_count": len(active_alerts)},
            category="alert_evaluation",
        )

        return active_alerts

    async def _should_fire_alert(
        self, alert_name: str, rule: Dict, metrics: Dict[str, float]
    ) -> bool:
        """🚨 Verificar se alerta deve ser disparado"""
        metric_name = self._extract_metric_name(rule["condition"])
        current_value = metrics.get(metric_name, 0)
        threshold = rule["threshold"]

        # Lógica de comparação baseada na condição
        if ">" in rule["condition"]:
            return current_value > threshold
        elif "<" in rule["condition"]:
            return current_value < threshold
        elif "==" in rule["condition"]:
            return current_value == threshold
        elif "!=" in rule["condition"]:
            return current_value != threshold
        elif ">=" in rule["condition"]:
            return current_value >= threshold
        elif "<=" in rule["condition"]:
            return current_value <= threshold

        return False

    def _extract_metric_name(self, condition: str) -> str:
        """🚨 Extrair nome da métrica da condição"""
        # Pega a primeira palavra antes do operador
        return condition.split()[0]

    def get_alert_summary(self, active_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """🚨 Gerar resumo dos alertas ativos"""
        if not active_alerts:
            return {
                "status": "healthy",
                "total_alerts": 0,
                "by_severity": {},
                "message": "Nenhum alerta ativo",
            }

        # Contar por severidade
        severity_counts = {}
        for alert in active_alerts:
            severity = alert["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Determinar status geral
        if severity_counts.get("critical", 0) > 0:
            overall_status = "critical"
        elif severity_counts.get("warning", 0) > 0:
            overall_status = "warning"
        else:
            overall_status = "info"

        return {
            "status": overall_status,
            "total_alerts": len(active_alerts),
            "by_severity": severity_counts,
            "message": f"{len(active_alerts)} alertas ativos ({overall_status} severity)",
        }


# Integração com health check
@router.get("/alerts")
async def get_active_alerts(db: AsyncSession = Depends(get_db)):
    """🚨 OM003 - Endpoint para alertas ativos"""
    alert_manager = BasicAlertManager()

    try:
        # Coletar métricas atuais via health check detalhado
        from app.routes.health_detailed import detailed_health_check

        health_data = await detailed_health_check(db)

        # Converter health data para métricas de alerta
        metrics = await _convert_health_to_metrics(health_data)

        # Avaliar alertas
        active_alerts = await alert_manager.evaluate_alerts(metrics)

        # Gerar resumo
        alert_summary = alert_manager.get_alert_summary(active_alerts)

        result = {
            "alerts": active_alerts,
            "summary": alert_summary,
            "total_active": len(active_alerts),
            "evaluated_at": datetime.utcnow().isoformat(),
            "metrics_snapshot": metrics,
            "evaluation_time_ms": 0,  # TODO: medir tempo de avaliação
        }

        logger.info(
            f"🚨 OM003 Alertas avaliados: {len(active_alerts)} ativos",
            metadata={
                "total_alerts": len(active_alerts),
                "status": alert_summary["status"],
            },
            category="alerts_endpoint",
        )

        return result

    except Exception as e:
        logger.error(
            f"❌ OM003 Erro ao avaliar alertas: {str(e)}",
            metadata={"error": str(e)},
            category="alerts_error",
        )

        return {
            "alerts": [],
            "summary": {
                "status": "error",
                "message": f"Erro ao avaliar alertas: {str(e)}",
            },
            "total_active": 0,
            "evaluated_at": datetime.utcnow().isoformat(),
            "error": str(e),
        }


async def _convert_health_to_metrics(health_data: Dict[str, Any]) -> Dict[str, float]:
    """🚨 Converter dados de health check para métricas de alerta"""
    components = health_data.get("components", {})

    metrics = {
        # Webhook metrics
        "webhook_failure_rate": components.get("webhook", {}).get(
            "blocked_percentage", 0
        ),
        "avg_processing_time": components.get("webhook", {}).get("response_time_ms", 0),
        # Database metrics
        "db_connection_errors": (
            1 if components.get("database", {}).get("status") != "healthy" else 0
        ),
        # Redis metrics
        "redis_health": (
            1 if components.get("redis", {}).get("status") == "healthy" else 0
        ),
        # Meta API metrics
        "meta_api_errors": (
            1 if components.get("meta_api", {}).get("status") != "healthy" else 0
        ),
        # Business metrics
        "appointments_per_hour": components.get("database", {}).get(
            "appointments_count", 0
        )
        / 24,  # Estimativa
        # Performance metrics
        "total_response_time": health_data.get("performance", {}).get(
            "total_check_time_ms", 0
        ),
    }

    return metrics


@router.get("/alerts/summary")
async def get_alert_summary(db: AsyncSession = Depends(get_db)):
    """🚨 OM003 - Resumo rápido de alertas para dashboard"""
    try:
        alert_response = await get_active_alerts(db)

        return {
            "status": alert_response["summary"]["status"],
            "total_alerts": alert_response["total_active"],
            "critical_count": alert_response["summary"]["by_severity"].get(
                "critical", 0
            ),
            "warning_count": alert_response["summary"]["by_severity"].get("warning", 0),
            "info_count": alert_response["summary"]["by_severity"].get("info", 0),
            "last_evaluated": alert_response["evaluated_at"],
        }

    except Exception as e:
        logger.error(
            f"❌ OM003 Erro no resumo de alertas: {str(e)}", category="alerts_summary"
        )

        return {
            "status": "error",
            "total_alerts": 0,
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "error": str(e),
            "last_evaluated": datetime.utcnow().isoformat(),
        }
