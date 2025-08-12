"""
Sistema de Alertas para monitoramento do WhatsApp Agent
"""
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
import json

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Classe para representar um alerta"""
    id: str
    title: str
    message: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AlertManager:
    """Gerenciador de alertas do sistema"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_cooldown: Dict[str, datetime] = {}
        
        # Configurações de alerta
        self.severity_cooldowns = {
            "LOW": 3600,      # 1 hora
            "MEDIUM": 1800,   # 30 minutos
            "HIGH": 600,      # 10 minutos
            "CRITICAL": 300   # 5 minutos
        }
        
        self.email_config = {
            "enabled": settings.alert_email_enabled if hasattr(settings, 'alert_email_enabled') else False,
            "smtp_server": getattr(settings, 'smtp_server', 'localhost'),
            "smtp_port": getattr(settings, 'smtp_port', 587),
            "username": getattr(settings, 'smtp_username', ''),
            "password": getattr(settings, 'smtp_password', ''),
            "from_email": getattr(settings, 'alert_from_email', 'whatsapp-agent@localhost'),
            "to_emails": getattr(settings, 'alert_to_emails', '').split(',') if hasattr(settings, 'alert_to_emails') else []
        }
    
    async def create_alert(self, 
                          alert_id: str,
                          title: str,
                          message: str,
                          severity: str = "MEDIUM",
                          source: str = "system",
                          data: Optional[Dict[str, Any]] = None) -> Alert:
        """Cria um novo alerta"""
        
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity.upper(),
            timestamp=datetime.now(),
            source=source,
            data=data or {}
        )
        
        # Verificar se já existe um alerta ativo com o mesmo ID
        if alert_id in self.alerts and not self.alerts[alert_id].resolved:
            logger.debug(f"Alerta {alert_id} já existe e está ativo, atualizando...")
            existing_alert = self.alerts[alert_id]
            existing_alert.message = message
            existing_alert.data.update(data or {})
            return existing_alert
        
        # Adicionar novo alerta
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        logger.warning(f"Novo alerta criado: [{severity}] {title} - {message}")
        
        # Enviar notificação se necessário
        await self._send_notification(alert)
        
        return alert
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system"):
        """Resolve um alerta"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            logger.info(f"Alerta {alert_id} resolvido por {resolved_by}")
            
            # Remover da lista de alertas ativos
            del self.alerts[alert_id]
    
    async def _send_notification(self, alert: Alert):
        """Envia notificação do alerta"""
        
        # Verificar cooldown para evitar spam
        cooldown_key = f"{alert.source}_{alert.severity}"
        cooldown_seconds = self.severity_cooldowns.get(alert.severity, 1800)
        
        if cooldown_key in self.notification_cooldown:
            last_notification = self.notification_cooldown[cooldown_key]
            if datetime.now() - last_notification < timedelta(seconds=cooldown_seconds):
                logger.debug(f"Notificação em cooldown para {cooldown_key}")
                return
        
        # Atualizar cooldown
        self.notification_cooldown[cooldown_key] = datetime.now()
        
        # Enviar por email se configurado
        if self.email_config["enabled"]:
            await self._send_email_notification(alert)
        
        # Log da notificação
        logger.info(f"Notificação enviada para alerta: {alert.id}")
    
    async def _send_email_notification(self, alert: Alert):
        """Envia notificação por email"""
        try:
            if not self.email_config["to_emails"]:
                logger.warning("Nenhum email de destino configurado para alertas")
                return
            
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.email_config["from_email"]
            msg['To'] = ", ".join(self.email_config["to_emails"])
            msg['Subject'] = f"[WhatsApp Agent] {alert.severity} - {alert.title}"
            
            # Corpo do email
            body = f"""
            Alerta do WhatsApp Agent
            
            Severidade: {alert.severity}
            Título: {alert.title}
            Mensagem: {alert.message}
            Fonte: {alert.source}
            Timestamp: {alert.timestamp.isoformat()}
            
            Dados adicionais:
            {json.dumps(alert.data, indent=2, default=str)}
            
            ---
            Este é um alerta automático do sistema WhatsApp Agent.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar email
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                if self.email_config["username"]:
                    server.starttls()
                    server.login(self.email_config["username"], self.email_config["password"])
                
                server.send_message(msg)
            
            logger.info(f"Email de alerta enviado para: {', '.join(self.email_config['to_emails'])}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de alerta: {e}")
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """Obtém alertas ativos"""
        alerts = list(self.alerts.values())
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity.upper()]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Obtém histórico de alertas"""
        return sorted(self.alert_history[-limit:], key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de alertas"""
        active_alerts = list(self.alerts.values())
        
        stats = {
            "active_alerts": len(active_alerts),
            "total_alerts": len(self.alert_history),
            "alerts_by_severity": {},
            "alerts_by_source": {},
            "recent_alerts": len([
                alert for alert in self.alert_history 
                if alert.timestamp > datetime.now() - timedelta(hours=24)
            ])
        }
        
        # Contar por severidade
        for alert in active_alerts:
            severity = alert.severity
            stats["alerts_by_severity"][severity] = stats["alerts_by_severity"].get(severity, 0) + 1
        
        # Contar por fonte
        for alert in active_alerts:
            source = alert.source
            stats["alerts_by_source"][source] = stats["alerts_by_source"].get(source, 0) + 1
        
        return stats
    
    async def cleanup_old_alerts(self, max_age_days: int = 30):
        """Remove alertas antigos do histórico"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        original_count = len(self.alert_history)
        self.alert_history = [
            alert for alert in self.alert_history 
            if alert.timestamp > cutoff_date
        ]
        
        removed_count = original_count - len(self.alert_history)
        if removed_count > 0:
            logger.info(f"Removidos {removed_count} alertas antigos do histórico")


# Instância global do gerenciador de alertas
alert_manager = AlertManager()


# Funções de conveniência para criar alertas específicos
async def alert_whatsapp_api_error(error_details: Dict[str, Any]):
    """Cria alerta para erro na API do WhatsApp"""
    await alert_manager.create_alert(
        alert_id="whatsapp_api_error",
        title="Erro na API do WhatsApp",
        message=f"Falha na comunicação com a API do WhatsApp: {error_details.get('error', 'Erro desconhecido')}",
        severity="HIGH",
        source="whatsapp_service",
        data=error_details
    )


async def alert_database_connection_error(error_details: Dict[str, Any]):
    """Cria alerta para erro de conexão com banco"""
    await alert_manager.create_alert(
        alert_id="database_connection_error",
        title="Erro de Conexão com Banco de Dados",
        message="Falha na conexão com o banco de dados PostgreSQL",
        severity="CRITICAL",
        source="database",
        data=error_details
    )


async def alert_rate_limit_exceeded(client_info: Dict[str, Any]):
    """Cria alerta para rate limit excedido"""
    await alert_manager.create_alert(
        alert_id=f"rate_limit_{client_info.get('client_id', 'unknown')}",
        title="Rate Limit Excedido",
        message=f"Cliente {client_info.get('client_id')} excedeu o rate limit",
        severity="MEDIUM",
        source="rate_limiter",
        data=client_info
    )


async def alert_llm_service_error(error_details: Dict[str, Any]):
    """Cria alerta para erro no serviço LLM"""
    await alert_manager.create_alert(
        alert_id="llm_service_error",
        title="Erro no Serviço LLM",
        message="Falha na comunicação com o serviço de LLM (OpenAI)",
        severity="HIGH",
        source="llm_service",
        data=error_details
    )
