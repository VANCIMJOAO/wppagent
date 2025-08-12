"""
Sistema de Health Checks e Alertas
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import httpx
from app.config import settings
from app.utils.logger import get_logger
from app.database import AsyncSessionLocal
logger = get_logger(__name__)
from app.services.retry_handler import retry_handler
from app.services.alert_manager import (
    alert_manager, 
    alert_whatsapp_api_error, 
    alert_database_connection_error,
    alert_llm_service_error
)
from sqlalchemy import text

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """Sistema de health checks para monitorar componentes"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self.alert_thresholds = {
            "database_response_time": 5.0,  # seconds
            "api_response_time": 10.0,  # seconds
            "error_rate": 10.0,  # percentage
            "circuit_breaker_failures": 5
        }
    
    async def check_database_health(self) -> HealthCheck:
        """Verifica saúde do banco de dados"""
        start_time = datetime.now()
        
        try:
            async with AsyncSessionLocal() as db:
                # Query simples para testar conectividade
                result = await db.execute(text("SELECT 1"))
                result.fetchone()
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Resolver alerta se estava com problema
                await alert_manager.resolve_alert("database_connection_error")
                
                if response_time > self.alert_thresholds["database_response_time"]:
                    return HealthCheck(
                        name="database",
                        status=HealthStatus.DEGRADED,
                        message=f"Database responding slowly: {response_time:.2f}s",
                        timestamp=datetime.now(),
                        response_time=response_time
                    )
                
                return HealthCheck(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection OK",
                    timestamp=datetime.now(),
                    response_time=response_time
                )
                
        except Exception as e:
            # Criar alerta para problema de banco
            await alert_database_connection_error({
                "error": str(e),
                "response_time": (datetime.now() - start_time).total_seconds()
            })
            
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def check_whatsapp_api_health(self) -> HealthCheck:
        """Verifica saúde da API do WhatsApp"""
        start_time = datetime.now()
        
        try:
            # Testar endpoint de saúde da Meta API
            health_url = f"https://graph.facebook.com/{settings.meta_api_version}/me"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    health_url,
                    headers={"Authorization": f"Bearer {settings.meta_access_token}"},
                    timeout=30.0
                )
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    if response_time > self.alert_thresholds["api_response_time"]:
                        return HealthCheck(
                            name="whatsapp_api",
                            status=HealthStatus.DEGRADED,
                            message=f"WhatsApp API responding slowly: {response_time:.2f}s",
                            timestamp=datetime.now(),
                            response_time=response_time
                        )
                    
                    return HealthCheck(
                        name="whatsapp_api",
                        status=HealthStatus.HEALTHY,
                        message="WhatsApp API connection OK",
                        timestamp=datetime.now(),
                        response_time=response_time,
                        details={"token_valid": True}
                    )
                    
                elif response.status_code == 401:
                    return HealthCheck(
                        name="whatsapp_api",
                        status=HealthStatus.UNHEALTHY,
                        message="Invalid or expired WhatsApp access token",
                        timestamp=datetime.now(),
                        details={"token_valid": False}
                    )
                    
                else:
                    return HealthCheck(
                        name="whatsapp_api",
                        status=HealthStatus.DEGRADED,
                        message=f"WhatsApp API returned {response.status_code}",
                        timestamp=datetime.now(),
                        details={"status_code": response.status_code}
                    )
                    
        except Exception as e:
            return HealthCheck(
                name="whatsapp_api",
                status=HealthStatus.UNHEALTHY,
                message=f"WhatsApp API connection failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def check_openai_api_health(self) -> HealthCheck:
        """Verifica saúde da API do OpenAI"""
        start_time = datetime.now()
        
        try:
            # Testar endpoint simples da OpenAI
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    timeout=30.0
                )
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    return HealthCheck(
                        name="openai_api",
                        status=HealthStatus.HEALTHY,
                        message="OpenAI API connection OK",
                        timestamp=datetime.now(),
                        response_time=response_time
                    )
                elif response.status_code == 401:
                    return HealthCheck(
                        name="openai_api",
                        status=HealthStatus.UNHEALTHY,
                        message="Invalid OpenAI API key",
                        timestamp=datetime.now()
                    )
                else:
                    return HealthCheck(
                        name="openai_api",
                        status=HealthStatus.DEGRADED,
                        message=f"OpenAI API returned {response.status_code}",
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            return HealthCheck(
                name="openai_api",
                status=HealthStatus.UNHEALTHY,
                message=f"OpenAI API connection failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def check_circuit_breakers(self) -> HealthCheck:
        """Verifica estado dos circuit breakers"""
        try:
            # Verificar circuit breakers do retry handler
            whatsapp_status = retry_handler.get_circuit_breaker_status("whatsapp_api")
            
            if whatsapp_status.get("state") == "open":
                return HealthCheck(
                    name="circuit_breakers",
                    status=HealthStatus.UNHEALTHY,
                    message="WhatsApp API circuit breaker is OPEN",
                    timestamp=datetime.now(),
                    details=whatsapp_status
                )
            elif whatsapp_status.get("failure_count", 0) > 0:
                return HealthCheck(
                    name="circuit_breakers",
                    status=HealthStatus.DEGRADED,
                    message=f"WhatsApp API has {whatsapp_status.get('failure_count')} failures",
                    timestamp=datetime.now(),
                    details=whatsapp_status
                )
            else:
                return HealthCheck(
                    name="circuit_breakers",
                    status=HealthStatus.HEALTHY,
                    message="All circuit breakers normal",
                    timestamp=datetime.now(),
                    details=whatsapp_status
                )
                
        except Exception as e:
            return HealthCheck(
                name="circuit_breakers",
                status=HealthStatus.UNHEALTHY,
                message=f"Circuit breaker check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Executa todos os health checks"""
        logger.info("Executando health checks...")
        
        # Executar checks em paralelo
        checks = await asyncio.gather(
            self.check_database_health(),
            self.check_whatsapp_api_health(),
            self.check_openai_api_health(),
            self.check_circuit_breakers(),
            return_exceptions=True
        )
        
        results = {}
        check_names = ["database", "whatsapp_api", "openai_api", "circuit_breakers"]
        
        for i, check in enumerate(checks):
            if isinstance(check, Exception):
                results[check_names[i]] = HealthCheck(
                    name=check_names[i],
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(check)}",
                    timestamp=datetime.now()
                )
            else:
                results[check.name] = check
                self.checks[check.name] = check
        
        return results
    
    def get_overall_status(self, checks: Dict[str, HealthCheck]) -> HealthStatus:
        """Determina status geral do sistema"""
        statuses = [check.status for check in checks.values()]
        
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def should_alert(self, check: HealthCheck) -> bool:
        """Determina se deve disparar alerta"""
        # Só alertar se status mudou ou se está unhealthy há mais de 5 minutos
        previous = self.checks.get(check.name)
        
        if not previous:
            return check.status != HealthStatus.HEALTHY
        
        # Se status mudou para pior
        if (check.status == HealthStatus.UNHEALTHY and 
            previous.status != HealthStatus.UNHEALTHY):
            return True
        
        # Se está unhealthy há mais de 5 minutos
        if (check.status == HealthStatus.UNHEALTHY and
            datetime.now() - previous.timestamp > timedelta(minutes=5)):
            return True
        
        return False
    
    async def send_alert(self, check: HealthCheck):
        """Envia alerta (implementar conforme necessidade)"""
        alert_message = f"""
🚨 ALERTA - WhatsApp Agent

Componente: {check.name}
Status: {check.status.value.upper()}
Mensagem: {check.message}
Horário: {check.timestamp.strftime('%d/%m/%Y %H:%M:%S')}

Detalhes: {check.details if check.details else 'N/A'}
        """.strip()
        
        logger.error(f"ALERT: {alert_message}")
        
        # Aqui você pode implementar:
        # - Envio por email
        # - Webhook para Slack/Discord
        # - Push notification
        # - SMS
        
        # Exemplo: enviar para log específico de alertas
        alert_logger = logging.getLogger("alerts")
        alert_logger.critical(alert_message)


# Instância global
health_checker = HealthChecker()
