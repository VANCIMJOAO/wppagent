"""
Sistema de Alertas Automáticos para Produção
==========================================

Implementa sistema completo de alertas para:
- Falhas de sistema
- Performance degradada
- Problemas de negócio
- Alertas de segurança
- Notificações por múltiplos canais
"""

import asyncio
import smtplib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from pathlib import Path

from app.services.production_logger import alerts_logger, log_security_event
from app.utils.logger import get_logger
from app.config import settings
logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Níveis de severidade de alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Categorias de alertas"""
    SYSTEM = "system"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SECURITY = "security"
    EXTERNAL = "external"


@dataclass
class Alert:
    """Estrutura de um alerta"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    category: AlertCategory
    timestamp: datetime
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['category'] = self.category.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data


class AlertChannel:
    """Canal de notificação de alertas"""
    
    async def send(self, alert: Alert) -> bool:
        """Enviar alerta (implementar em subclasses)"""
        raise NotImplementedError


class EmailAlertChannel(AlertChannel):
    """Canal de alerta por email"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str,
                 from_email: str, to_emails: List[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    async def send(self, alert: Alert) -> bool:
        """Enviar alerta por email"""
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Corpo do email
            body = f"""
            ALERTA DO SISTEMA WHATSAPP AGENT
            ================================
            
            Severidade: {alert.severity.value.upper()}
            Categoria: {alert.category.value}
            Timestamp: {alert.timestamp.strftime('%d/%m/%Y %H:%M:%S')}
            
            Título: {alert.title}
            
            Mensagem:
            {alert.message}
            
            Metadados:
            {json.dumps(alert.metadata, indent=2, ensure_ascii=False)}
            
            ID do Alerta: {alert.id}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            alerts_logger.info(f"Email alert sent successfully: {alert.id}")
            return True
            
        except Exception as e:
            alerts_logger.error(f"Failed to send email alert: {e}", exc_info=True)
            return False


class SlackAlertChannel(AlertChannel):
    """Canal de alerta para Slack"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send(self, alert: Alert) -> bool:
        """Enviar alerta para Slack"""
        try:
            # Mapear cores por severidade
            color_map = {
                AlertSeverity.LOW: "#36a64f",      # Verde
                AlertSeverity.MEDIUM: "#ffcc00",   # Amarelo
                AlertSeverity.HIGH: "#ff6600",     # Laranja
                AlertSeverity.CRITICAL: "#ff0000"  # Vermelho
            }
            
            # Criar payload do Slack
            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#cccccc"),
                        "title": f"🚨 {alert.title}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severidade",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Categoria",
                                "value": alert.category.value,
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
                                "short": True
                            },
                            {
                                "title": "ID",
                                "value": alert.id,
                                "short": True
                            }
                        ],
                        "footer": "WhatsApp Agent",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            # Enviar via webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
            
            alerts_logger.info(f"Slack alert sent successfully: {alert.id}")
            return True
            
        except Exception as e:
            alerts_logger.error(f"Failed to send Slack alert: {e}", exc_info=True)
            return False


class WhatsAppAlertChannel(AlertChannel):
    """Canal de alerta via WhatsApp"""
    
    def __init__(self, phone_number: str, api_token: str):
        self.phone_number = phone_number
        self.api_token = api_token
    
    async def send(self, alert: Alert) -> bool:
        """Enviar alerta via WhatsApp"""
        try:
            # Só enviar alertas críticos via WhatsApp
            if alert.severity != AlertSeverity.CRITICAL:
                return True
            
            message = f"""
🚨 *ALERTA CRÍTICO*
Sistema: WhatsApp Agent

*{alert.title}*

{alert.message}

Timestamp: {alert.timestamp.strftime('%d/%m/%Y %H:%M:%S')}
ID: {alert.id}
            """.strip()
            
            # Implementar envio via API do WhatsApp
            # (adaptar conforme sua API)
            payload = {
                "phone": self.phone_number,
                "message": message,
                "token": self.api_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.whatsapp.com/send",  # URL da sua API
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
            
            alerts_logger.info(f"WhatsApp alert sent successfully: {alert.id}")
            return True
            
        except Exception as e:
            alerts_logger.error(f"Failed to send WhatsApp alert: {e}", exc_info=True)
            return False


class ProductionAlertManager:
    """
    Gerenciador de alertas para produção
    """
    
    def __init__(self, storage_path: str = "logs/alerts"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Alertas ativos
        self.active_alerts: Dict[str, Alert] = {}
        
        # Histórico de alertas
        self.alert_history: List[Alert] = []
        
        # Canais de notificação
        self.channels: List[AlertChannel] = []
        
        # Configurações de cooldown por severidade
        self.cooldown_periods = {
            AlertSeverity.LOW: timedelta(hours=1),
            AlertSeverity.MEDIUM: timedelta(minutes=30),
            AlertSeverity.HIGH: timedelta(minutes=10),
            AlertSeverity.CRITICAL: timedelta(minutes=5)
        }
        
        # Último alerta por tipo (para cooldown)
        self.last_alert_by_type: Dict[str, datetime] = {}
        self._initialized = False
        
        # Inicializar canais
        self._setup_channels()
        
        # Nota: Alertas persistidos serão carregados quando necessário
        # Para evitar problemas de event loop na inicialização
    
    async def initialize(self):
        """Inicializar sistema de alertas de forma assíncrona"""
        if not self._initialized:
            await self._load_persisted_alerts()
            self._initialized = True
    
    def _setup_channels(self):
        """Configurar canais de notificação"""
        try:
            # Canal de email se configurado
            if hasattr(settings, 'alert_email_enabled') and settings.alert_email_enabled:
                email_channel = EmailAlertChannel(
                    smtp_host=getattr(settings, 'smtp_host', 'localhost'),
                    smtp_port=getattr(settings, 'smtp_port', 587),
                    username=getattr(settings, 'smtp_username', ''),
                    password=getattr(settings, 'smtp_password', ''),
                    from_email=getattr(settings, 'alert_from_email', 'alerts@whatsapp-agent.com'),
                    to_emails=getattr(settings, 'alert_to_emails', '').split(',')
                )
                self.channels.append(email_channel)
            
            # Canal Slack se configurado
            if hasattr(settings, 'slack_webhook_url') and settings.slack_webhook_url:
                slack_channel = SlackAlertChannel(settings.slack_webhook_url)
                self.channels.append(slack_channel)
            
            # Canal WhatsApp se configurado
            if hasattr(settings, 'alert_whatsapp_phone') and settings.alert_whatsapp_phone:
                whatsapp_channel = WhatsAppAlertChannel(
                    phone_number=settings.alert_whatsapp_phone,
                    api_token=getattr(settings, 'whatsapp_api_token', '')
                )
                self.channels.append(whatsapp_channel)
                
        except Exception as e:
            alerts_logger.error(f"Error setting up alert channels: {e}", exc_info=True)
    
    async def _load_persisted_alerts(self):
        """Carregar alertas persistidos"""
        try:
            alerts_file = self.storage_path / "active_alerts.json"
            if alerts_file.exists():
                with open(alerts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for alert_data in data:
                    alert = Alert(
                        id=alert_data['id'],
                        title=alert_data['title'],
                        message=alert_data['message'],
                        severity=AlertSeverity(alert_data['severity']),
                        category=AlertCategory(alert_data['category']),
                        timestamp=datetime.fromisoformat(alert_data['timestamp']),
                        metadata=alert_data['metadata'],
                        resolved=alert_data['resolved']
                    )
                    self.active_alerts[alert.id] = alert
                    
        except Exception as e:
            alerts_logger.error(f"Error loading persisted alerts: {e}", exc_info=True)
    
    async def _persist_alerts(self):
        """Persistir alertas ativos"""
        try:
            alerts_file = self.storage_path / "active_alerts.json"
            data = [alert.to_dict() for alert in self.active_alerts.values()]
            
            with open(alerts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            alerts_logger.error(f"Error persisting alerts: {e}", exc_info=True)
    
    def _should_send_alert(self, alert_type: str, severity: AlertSeverity) -> bool:
        """Verificar se deve enviar alerta (cooldown)"""
        if alert_type not in self.last_alert_by_type:
            return True
        
        last_alert_time = self.last_alert_by_type[alert_type]
        cooldown_period = self.cooldown_periods[severity]
        
        return datetime.now(timezone.utc) - last_alert_time > cooldown_period
    
    def add_alert(self, alert_id: str, message: str, severity: str, metadata: dict = None):
        """Método síncrono para adicionar alerta (wrapper)"""
        try:
            # Garantir inicialização mínima
            if not hasattr(self, '_initialized'):
                self._initialized = False
            
            # Mapear severidade
            severity_map = {
                'low': AlertSeverity.LOW,
                'medium': AlertSeverity.MEDIUM,
                'high': AlertSeverity.HIGH,
                'critical': AlertSeverity.CRITICAL
            }
            
            severity_obj = severity_map.get(severity.lower(), AlertSeverity.MEDIUM)
            
            # Criar alerta simples
            alert = Alert(
                id=alert_id,
                title=f"Alert: {alert_id}",
                message=message,
                severity=severity_obj,
                category=AlertCategory.SYSTEM,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            # Adicionar aos alertas ativos se não existe
            if not hasattr(self, 'active_alerts'):
                self.active_alerts = {}
            if not hasattr(self, 'alert_history'):
                self.alert_history = []
                
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            return alert
            
        except Exception as e:
            logger.error("Error adding alert: {e}")
            return None

    async def create_alert(self, 
                          alert_id: str,
                          title: str,
                          message: str,
                          severity: AlertSeverity,
                          category: AlertCategory,
                          metadata: Optional[Dict[str, Any]] = None) -> Alert:
        """Criar novo alerta"""
        try:
            alert = Alert(
                id=alert_id,
                title=title,
                message=message,
                severity=severity,
                category=category,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            # Verificar cooldown
            alert_type = f"{category.value}_{severity.value}"
            if not self._should_send_alert(alert_type, severity):
                alerts_logger.debug(f"Alert {alert_id} suppressed due to cooldown")
                return alert
            
            # Adicionar aos alertas ativos
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Atualizar último alerta
            self.last_alert_by_type[alert_type] = alert.timestamp
            
            # Log do alerta
            alerts_logger.warning(
                f"Alert created: {title}",
                extra_data={
                    'alert_id': alert_id,
                    'severity': severity.value,
                    'category': category.value,
                    'message': message,
                    'metadata': metadata
                }
            )
            
            # Log de segurança se aplicável
            if category == AlertCategory.SECURITY:
                log_security_event("alert_created", {
                    'alert_id': alert_id,
                    'title': title,
                    'severity': severity.value
                }, severity.value.upper())
            
            # Enviar notificações
            await self._send_notifications(alert)
            
            # Persistir alertas
            await self._persist_alerts()
            
            return alert
            
        except Exception as e:
            alerts_logger.error(f"Error creating alert: {e}", exc_info=True)
            raise
    
    async def _send_notifications(self, alert: Alert):
        """Enviar notificações para todos os canais"""
        for channel in self.channels:
            try:
                await channel.send(alert)
            except Exception as e:
                alerts_logger.error(f"Error sending notification via {type(channel).__name__}: {e}")
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system"):
        """Resolver um alerta"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now(timezone.utc)
                alert.resolved_by = resolved_by
                
                # Remover dos alertas ativos
                del self.active_alerts[alert_id]
                
                alerts_logger.info(
                    f"Alert resolved: {alert.title}",
                    extra_data={
                        'alert_id': alert_id,
                        'resolved_by': resolved_by,
                        'duration_minutes': (alert.resolved_at - alert.timestamp).total_seconds() / 60
                    }
                )
                
                # Persistir mudanças
                await self._persist_alerts()
                
        except Exception as e:
            alerts_logger.error(f"Error resolving alert {alert_id}: {e}", exc_info=True)
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Obter alertas ativos"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Obter estatísticas de alertas"""
        try:
            active_alerts = list(self.active_alerts.values())
            
            stats = {
                'active_count': len(active_alerts),
                'total_history': len(self.alert_history),
                'by_severity': {},
                'by_category': {},
                'recent_alerts': len([
                    alert for alert in self.alert_history
                    if alert.timestamp > datetime.now(timezone.utc) - timedelta(hours=24)
                ])
            }
            
            # Contar por severidade
            for alert in active_alerts:
                severity = alert.severity.value
                stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # Contar por categoria
            for alert in active_alerts:
                category = alert.category.value
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            return stats
            
        except Exception as e:
            alerts_logger.error(f"Error generating alert stats: {e}", exc_info=True)
            return {}
    
    # === ALERTAS PRÉ-DEFINIDOS ===
    
    async def alert_system_down(self, component: str, error_message: str):
        """Alerta de sistema fora do ar"""
        await self.create_alert(
            alert_id=f"system_down_{component}",
            title=f"Sistema {component} fora do ar",
            message=f"O componente {component} está indisponível: {error_message}",
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SYSTEM,
            metadata={'component': component, 'error': error_message}
        )
    
    async def alert_high_error_rate(self, component: str, error_rate: float, threshold: float):
        """Alerta de alta taxa de erro"""
        await self.create_alert(
            alert_id=f"high_error_rate_{component}",
            title=f"Alta taxa de erro em {component}",
            message=f"Taxa de erro em {component}: {error_rate:.2f}% (limite: {threshold:.2f}%)",
            severity=AlertSeverity.HIGH if error_rate > threshold * 2 else AlertSeverity.MEDIUM,
            category=AlertCategory.PERFORMANCE,
            metadata={'component': component, 'error_rate': error_rate, 'threshold': threshold}
        )
    
    async def alert_slow_response(self, component: str, response_time: float, threshold: float):
        """Alerta de resposta lenta"""
        await self.create_alert(
            alert_id=f"slow_response_{component}",
            title=f"Resposta lenta em {component}",
            message=f"Tempo de resposta em {component}: {response_time:.2f}ms (limite: {threshold:.2f}ms)",
            severity=AlertSeverity.MEDIUM if response_time > threshold * 2 else AlertSeverity.LOW,
            category=AlertCategory.PERFORMANCE,
            metadata={'component': component, 'response_time': response_time, 'threshold': threshold}
        )
    
    async def alert_low_conversion_rate(self, current_rate: float, expected_rate: float):
        """Alerta de baixa taxa de conversão"""
        await self.create_alert(
            alert_id="low_conversion_rate",
            title="Taxa de conversão baixa",
            message=f"Taxa de conversão atual: {current_rate:.2f}% (esperado: {expected_rate:.2f}%)",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.BUSINESS,
            metadata={'current_rate': current_rate, 'expected_rate': expected_rate}
        )
    
    async def alert_security_threat(self, threat_type: str, source_ip: str, details: Dict[str, Any]):
        """Alerta de ameaça de segurança"""
        await self.create_alert(
            alert_id=f"security_threat_{threat_type}_{source_ip}",
            title=f"Ameaça de segurança detectada: {threat_type}",
            message=f"Ameaça {threat_type} detectada do IP {source_ip}",
            severity=AlertSeverity.HIGH,
            category=AlertCategory.SECURITY,
            metadata={'threat_type': threat_type, 'source_ip': source_ip, 'details': details}
        )


# Instância global do gerenciador de alertas
alert_manager = ProductionAlertManager()


# Funções de conveniência
async def alert_critical(title: str, message: str, metadata: Optional[Dict[str, Any]] = None):
    """Criar alerta crítico"""
    await alert_manager.create_alert(
        alert_id=f"critical_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        title=title,
        message=message,
        severity=AlertSeverity.CRITICAL,
        category=AlertCategory.SYSTEM,
        metadata=metadata
    )

async def alert_performance_issue(component: str, metric: str, value: float, threshold: float):
    """Criar alerta de performance"""
    await alert_manager.create_alert(
        alert_id=f"performance_{component}_{metric}",
        title=f"Problema de performance: {component}",
        message=f"{metric} em {component}: {value} (limite: {threshold})",
        severity=AlertSeverity.MEDIUM,
        category=AlertCategory.PERFORMANCE,
        metadata={'component': component, 'metric': metric, 'value': value, 'threshold': threshold}
    )
