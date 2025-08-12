"""
Sistema Completo de Monitoramento e SLA
=====================================

Sistema abrangente que implementa:
- Métricas de negócio detalhadas
- Monitoramento de SLA em tempo real
- Sistema de alertas configurável
- Dashboards de performance
- Tracking de disponibilidade
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics
from pathlib import Path
import aiofiles
import aiohttp

from app.utils.logger import get_logger, log_performance
from app.config.config_factory import ConfigFactory

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Níveis de severidade de alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SLAMetric(Enum):
    """Tipos de métricas de SLA"""
    RESPONSE_TIME = "response_time"
    UPTIME = "uptime"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    AVAILABILITY = "availability"


class BusinessMetric(Enum):
    """Métricas de negócio"""
    CONVERSATIONS_STARTED = "conversations_started"
    MESSAGES_PROCESSED = "messages_processed"
    BOOKINGS_CREATED = "bookings_created"
    CONVERSION_RATE = "conversion_rate"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    RESPONSE_QUALITY = "response_quality"
    LEAD_GENERATION = "lead_generation"
    REVENUE_IMPACT = "revenue_impact"


@dataclass
class SLAThreshold:
    """Configuração de threshold de SLA"""
    metric: SLAMetric
    warning_threshold: float
    critical_threshold: float
    unit: str
    description: str


@dataclass
class Alert:
    """Alerta do sistema"""
    id: str
    title: str
    description: str
    severity: AlertSeverity
    metric: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'metric': self.metric,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'metadata': self.metadata or {}
        }


@dataclass
class MetricData:
    """Dados de uma métrica"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels or {}
        }


class SLAMonitor:
    """Monitor de SLA em tempo real"""
    
    def __init__(self):
        self.config = ConfigFactory.get_singleton_config()
        self.thresholds = self._setup_sla_thresholds()
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.uptime_tracker = UptimeTracker()
        
    def _setup_sla_thresholds(self) -> Dict[SLAMetric, SLAThreshold]:
        """Configurar thresholds de SLA baseados na configuração"""
        return {
            SLAMetric.RESPONSE_TIME: SLAThreshold(
                metric=SLAMetric.RESPONSE_TIME,
                warning_threshold=self.config.sla_response_time_ms * 0.8,
                critical_threshold=self.config.sla_response_time_ms,
                unit="ms",
                description="Tempo de resposta da API"
            ),
            SLAMetric.ERROR_RATE: SLAThreshold(
                metric=SLAMetric.ERROR_RATE,
                warning_threshold=self.config.sla_error_rate_percentage * 0.7,
                critical_threshold=self.config.sla_error_rate_percentage,
                unit="%",
                description="Taxa de erro das requisições"
            ),
            SLAMetric.UPTIME: SLAThreshold(
                metric=SLAMetric.UPTIME,
                warning_threshold=self.config.sla_uptime_percentage - 0.1,
                critical_threshold=self.config.sla_uptime_percentage,
                unit="%",
                description="Disponibilidade do sistema"
            ),
            SLAMetric.THROUGHPUT: SLAThreshold(
                metric=SLAMetric.THROUGHPUT,
                warning_threshold=100.0,  # req/min
                critical_threshold=50.0,
                unit="req/min",
                description="Taxa de processamento"
            )
        }
    
    async def record_metric(self, metric: SLAMetric, value: float, labels: Dict[str, str] = None):
        """Registrar uma métrica de SLA"""
        timestamp = datetime.now(timezone.utc)
        metric_data = MetricData(
            name=metric.value,
            value=value,
            timestamp=timestamp,
            labels=labels
        )
        
        self.metrics_buffer[metric].append(metric_data)
        
        # Verificar threshold
        await self._check_sla_threshold(metric, value, timestamp)
        
        logger.debug(f"SLA metric recorded: {metric.value}={value}", {
            'metric': metric.value,
            'value': value,
            'labels': labels
        })
    
    async def _check_sla_threshold(self, metric: SLAMetric, value: float, timestamp: datetime):
        """Verificar se uma métrica violou o SLA"""
        threshold = self.thresholds.get(metric)
        if not threshold:
            return
        
        severity = None
        threshold_value = None
        
        # Lógica específica por métrica
        if metric == SLAMetric.RESPONSE_TIME:
            if value >= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif value >= threshold.warning_threshold:
                severity = AlertSeverity.HIGH
                threshold_value = threshold.warning_threshold
                
        elif metric == SLAMetric.ERROR_RATE:
            if value >= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif value >= threshold.warning_threshold:
                severity = AlertSeverity.HIGH
                threshold_value = threshold.warning_threshold
                
        elif metric == SLAMetric.UPTIME:
            if value <= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif value <= threshold.warning_threshold:
                severity = AlertSeverity.HIGH
                threshold_value = threshold.warning_threshold
        
        if severity:
            await self._create_sla_alert(metric, value, threshold_value, severity, timestamp)
    
    async def _create_sla_alert(self, metric: SLAMetric, current_value: float, 
                               threshold_value: float, severity: AlertSeverity, 
                               timestamp: datetime):
        """Criar alerta de violação de SLA"""
        alert_id = f"sla_{metric.value}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Evitar spam de alertas do mesmo tipo
        existing_key = f"sla_{metric.value}"
        if existing_key in self.active_alerts:
            return
        
        threshold_info = self.thresholds[metric]
        
        alert = Alert(
            id=alert_id,
            title=f"SLA Violation: {threshold_info.description}",
            description=f"{threshold_info.description} está em {current_value:.2f}{threshold_info.unit}, "
                       f"acima do threshold de {threshold_value:.2f}{threshold_info.unit}",
            severity=severity,
            metric=metric.value,
            current_value=current_value,
            threshold_value=threshold_value,
            timestamp=timestamp,
            metadata={
                'sla_type': metric.value,
                'unit': threshold_info.unit,
                'threshold_type': 'critical' if severity == AlertSeverity.CRITICAL else 'warning'
            }
        )
        
        self.active_alerts[existing_key] = alert
        self.alert_history.append(alert)
        
        logger.error(f"SLA Alert: {alert.title}", {
            'alert_id': alert.id,
            'severity': severity.value,
            'metric': metric.value,
            'current_value': current_value,
            'threshold_value': threshold_value
        })
    
    def get_sla_status(self, period_minutes: int = 60) -> Dict[str, Any]:
        """Obter status atual do SLA"""
        now = datetime.now(timezone.utc)
        since = now - timedelta(minutes=period_minutes)
        
        status = {}
        
        for metric, threshold in self.thresholds.items():
            recent_metrics = [
                m for m in self.metrics_buffer[metric]
                if m.timestamp >= since
            ]
            
            if recent_metrics:
                values = [m.value for m in recent_metrics]
                
                if metric == SLAMetric.RESPONSE_TIME:
                    current_value = statistics.mean(values)
                    is_healthy = current_value < threshold.warning_threshold
                elif metric == SLAMetric.ERROR_RATE:
                    current_value = statistics.mean(values)
                    is_healthy = current_value < threshold.warning_threshold
                elif metric == SLAMetric.UPTIME:
                    current_value = self.uptime_tracker.get_uptime_percentage(period_minutes)
                    is_healthy = current_value >= threshold.warning_threshold
                else:
                    current_value = statistics.mean(values)
                    is_healthy = current_value >= threshold.warning_threshold
                
                status[metric.value] = {
                    'current_value': round(current_value, 2),
                    'warning_threshold': threshold.warning_threshold,
                    'critical_threshold': threshold.critical_threshold,
                    'unit': threshold.unit,
                    'is_healthy': is_healthy,
                    'sample_count': len(values)
                }
            else:
                status[metric.value] = {
                    'current_value': None,
                    'warning_threshold': threshold.warning_threshold,
                    'critical_threshold': threshold.critical_threshold,
                    'unit': threshold.unit,
                    'is_healthy': None,
                    'sample_count': 0
                }
        
        return {
            'period_minutes': period_minutes,
            'metrics': status,
            'overall_health': all(
                s.get('is_healthy', True) for s in status.values()
            ),
            'active_alerts': len(self.active_alerts),
            'timestamp': now.isoformat()
        }


class UptimeTracker:
    """Rastreador de uptime do sistema"""
    
    def __init__(self):
        self.uptime_events = deque(maxlen=10000)
        self.downtime_start: Optional[datetime] = None
        
    def record_uptime(self):
        """Registrar que o sistema está funcionando"""
        now = datetime.now(timezone.utc)
        
        if self.downtime_start:
            # Sistema voltou
            downtime_duration = (now - self.downtime_start).total_seconds()
            self.uptime_events.append({
                'type': 'recovery',
                'timestamp': now,
                'downtime_duration': downtime_duration
            })
            self.downtime_start = None
        
        self.uptime_events.append({
            'type': 'heartbeat',
            'timestamp': now
        })
    
    def record_downtime(self):
        """Registrar que o sistema está com problemas"""
        now = datetime.now(timezone.utc)
        
        if not self.downtime_start:
            self.downtime_start = now
            self.uptime_events.append({
                'type': 'downtime',
                'timestamp': now
            })
    
    def get_uptime_percentage(self, period_minutes: int = 60) -> float:
        """Calcular porcentagem de uptime no período"""
        now = datetime.now(timezone.utc)
        since = now - timedelta(minutes=period_minutes)
        
        recent_events = [
            e for e in self.uptime_events
            if e['timestamp'] >= since
        ]
        
        if not recent_events:
            return 100.0
        
        total_seconds = period_minutes * 60
        downtime_seconds = 0
        
        current_downtime_start = None
        
        for event in recent_events:
            if event['type'] == 'downtime':
                current_downtime_start = event['timestamp']
            elif event['type'] == 'recovery' and current_downtime_start:
                downtime_seconds += (event['timestamp'] - current_downtime_start).total_seconds()
                current_downtime_start = None
        
        # Se ainda está em downtime
        if current_downtime_start:
            downtime_seconds += (now - current_downtime_start).total_seconds()
        
        uptime_percentage = ((total_seconds - downtime_seconds) / total_seconds) * 100
        return max(0.0, min(100.0, uptime_percentage))


class BusinessMetricsCollector:
    """Coletor de métricas de negócio"""
    
    def __init__(self):
        self.config = ConfigFactory.get_singleton_config()
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=5000))
        self.daily_aggregates = defaultdict(dict)
        
    async def record_business_metric(self, metric: BusinessMetric, value: float, 
                                   labels: Dict[str, str] = None):
        """Registrar métrica de negócio"""
        timestamp = datetime.now(timezone.utc)
        metric_data = MetricData(
            name=metric.value,
            value=value,
            timestamp=timestamp,
            labels=labels or {}
        )
        
        self.metrics_buffer[metric].append(metric_data)
        
        # Atualizar agregados diários
        date_key = timestamp.date().isoformat()
        if date_key not in self.daily_aggregates[metric]:
            self.daily_aggregates[metric][date_key] = {
                'total': 0,
                'count': 0,
                'min': float('inf'),
                'max': float('-inf')
            }
        
        agg = self.daily_aggregates[metric][date_key]
        agg['total'] += value
        agg['count'] += 1
        agg['min'] = min(agg['min'], value)
        agg['max'] = max(agg['max'], value)
        
        logger.debug(f"Business metric recorded: {metric.value}={value}", {
            'metric': metric.value,
            'value': value,
            'labels': labels
        })
    
    def get_business_summary(self, days: int = 7) -> Dict[str, Any]:
        """Obter resumo das métricas de negócio"""
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)
        
        summary = {}
        
        for metric in BusinessMetric:
            metric_summary = {
                'current_period': {},
                'trends': [],
                'totals': {}
            }
            
            # Calcular métricas do período
            total_value = 0
            total_count = 0
            daily_values = []
            
            for i in range(days):
                date = start_date + timedelta(days=i)
                date_key = date.isoformat()
                
                if date_key in self.daily_aggregates[metric]:
                    day_data = self.daily_aggregates[metric][date_key]
                    daily_avg = day_data['total'] / day_data['count'] if day_data['count'] > 0 else 0
                    daily_values.append(daily_avg)
                    total_value += day_data['total']
                    total_count += day_data['count']
                else:
                    daily_values.append(0)
            
            metric_summary['current_period'] = {
                'average': total_value / total_count if total_count > 0 else 0,
                'total': total_value,
                'sample_count': total_count
            }
            
            # Calcular tendência
            if len(daily_values) >= 2:
                recent_avg = statistics.mean(daily_values[-3:]) if len(daily_values) >= 3 else daily_values[-1]
                earlier_avg = statistics.mean(daily_values[:3]) if len(daily_values) >= 3 else daily_values[0]
                
                if earlier_avg > 0:
                    trend_percentage = ((recent_avg - earlier_avg) / earlier_avg) * 100
                else:
                    trend_percentage = 0
                
                metric_summary['trends'] = {
                    'direction': 'up' if trend_percentage > 5 else 'down' if trend_percentage < -5 else 'stable',
                    'percentage': round(trend_percentage, 2),
                    'daily_values': daily_values
                }
            
            summary[metric.value] = metric_summary
        
        return {
            'period_days': days,
            'metrics': summary,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


class MonitoringSystem:
    """Sistema principal de monitoramento"""
    
    def __init__(self):
        self.config = ConfigFactory.get_singleton_config()
        self.sla_monitor = SLAMonitor()
        self.business_metrics = BusinessMetricsCollector()
        self.alert_notifier = AlertNotifier()
        self.running = False
        
    async def start(self):
        """Iniciar sistema de monitoramento"""
        if not self.config.metrics_enabled:
            logger.info("Monitoramento desabilitado na configuração")
            return
        
        self.running = True
        logger.info("Sistema de monitoramento iniciado")
        
        # Iniciar tarefas de background
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._metrics_cleanup_loop())
        
    async def stop(self):
        """Parar sistema de monitoramento"""
        self.running = False
        logger.info("Sistema de monitoramento parado")
    
    async def _health_check_loop(self):
        """Loop de health check"""
        while self.running:
            try:
                # Simular health check
                start_time = time.time()
                # Aqui faria health check real dos serviços
                response_time = (time.time() - start_time) * 1000
                
                await self.sla_monitor.record_metric(SLAMetric.RESPONSE_TIME, response_time)
                self.sla_monitor.uptime_tracker.record_uptime()
                
                await asyncio.sleep(self.config.health_check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Erro no health check: {e}")
                self.sla_monitor.uptime_tracker.record_downtime()
                await asyncio.sleep(5)
    
    async def _metrics_cleanup_loop(self):
        """Loop de limpeza de métricas antigas"""
        while self.running:
            try:
                # Limpeza a cada hora
                await asyncio.sleep(3600)
                
                retention_days = self.config.metrics_retention_days
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
                
                # Limpar métricas antigas
                for metric_buffer in self.sla_monitor.metrics_buffer.values():
                    while metric_buffer and metric_buffer[0].timestamp < cutoff_date:
                        metric_buffer.popleft()
                
                logger.info(f"Limpeza de métricas antigas executada (>{retention_days} dias)")
                
            except Exception as e:
                logger.error(f"Erro na limpeza de métricas: {e}")
    
    @log_performance("record_api_call")
    async def record_api_call(self, endpoint: str, method: str, status_code: int, 
                            response_time_ms: float, user_id: str = None):
        """Registrar chamada da API para monitoramento"""
        
        # Métricas de SLA
        await self.sla_monitor.record_metric(SLAMetric.RESPONSE_TIME, response_time_ms, {
            'endpoint': endpoint,
            'method': method,
            'status_code': str(status_code)
        })
        
        # Taxa de erro
        is_error = status_code >= 400
        error_rate = 1.0 if is_error else 0.0
        await self.sla_monitor.record_metric(SLAMetric.ERROR_RATE, error_rate)
        
        # Métricas de negócio
        if endpoint.startswith('/webhook'):
            await self.business_metrics.record_business_metric(
                BusinessMetric.MESSAGES_PROCESSED, 1.0, {
                    'status_code': str(status_code),
                    'user_id': user_id or 'unknown'
                }
            )
    
    async def record_business_event(self, event_type: str, value: float = 1.0, 
                                  metadata: Dict[str, Any] = None):
        """Registrar evento de negócio"""
        
        # Mapear tipos de evento para métricas
        metric_mapping = {
            'conversation_started': BusinessMetric.CONVERSATIONS_STARTED,
            'booking_created': BusinessMetric.BOOKINGS_CREATED,
            'lead_generated': BusinessMetric.LEAD_GENERATION,
            'message_processed': BusinessMetric.MESSAGES_PROCESSED
        }
        
        if event_type in metric_mapping:
            metric = metric_mapping[event_type]
            labels = {k: str(v) for k, v in (metadata or {}).items()}
            await self.business_metrics.record_business_metric(metric, value, labels)
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Obter dados para dashboard de monitoramento"""
        return {
            'sla_status': self.sla_monitor.get_sla_status(),
            'business_metrics': self.business_metrics.get_business_summary(),
            'active_alerts': [alert.to_dict() for alert in self.sla_monitor.active_alerts.values()],
            'system_info': {
                'monitoring_enabled': self.config.metrics_enabled,
                'alerting_enabled': self.config.alerting_enabled,
                'uptime_percentage': self.sla_monitor.uptime_tracker.get_uptime_percentage(1440),  # 24h
                'config': {
                    'sla_response_time_ms': self.config.sla_response_time_ms,
                    'sla_uptime_percentage': self.config.sla_uptime_percentage,
                    'sla_error_rate_percentage': self.config.sla_error_rate_percentage
                }
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


class AlertNotifier:
    """Sistema de notificação de alertas"""
    
    def __init__(self):
        self.config = ConfigFactory.get_singleton_config()
    
    async def send_alert(self, alert: Alert):
        """Enviar alerta via canais configurados"""
        if not self.config.alerting_enabled:
            return
        
        try:
            # Email
            if self.config.alert_email:
                await self._send_email_alert(alert)
            
            # Slack
            if self.config.alert_slack_webhook:
                await self._send_slack_alert(alert)
                
        except Exception as e:
            logger.error(f"Erro ao enviar alerta: {e}")
    
    async def _send_email_alert(self, alert: Alert):
        """Enviar alerta por email"""
        # Implementação simplificada - em produção usar serviço real
        logger.info(f"Email alert sent: {alert.title}")
    
    async def _send_slack_alert(self, alert: Alert):
        """Enviar alerta para Slack"""
        if not self.config.alert_slack_webhook:
            return
        
        severity_colors = {
            AlertSeverity.LOW: "#36a64f",      # verde
            AlertSeverity.MEDIUM: "#ff9500",   # laranja
            AlertSeverity.HIGH: "#ff6b35",     # vermelho claro
            AlertSeverity.CRITICAL: "#e01e5a"  # vermelho escuro
        }
        
        payload = {
            "attachments": [{
                "color": severity_colors.get(alert.severity, "#cccccc"),
                "title": f"🚨 {alert.title}",
                "text": alert.description,
                "fields": [
                    {
                        "title": "Severity",
                        "value": alert.severity.value.upper(),
                        "short": True
                    },
                    {
                        "title": "Metric",
                        "value": alert.metric,
                        "short": True
                    },
                    {
                        "title": "Current Value",
                        "value": f"{alert.current_value:.2f}",
                        "short": True
                    },
                    {
                        "title": "Threshold",
                        "value": f"{alert.threshold_value:.2f}",
                        "short": True
                    }
                ],
                "timestamp": int(alert.timestamp.timestamp())
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.alert_slack_webhook, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent: {alert.title}")
                    else:
                        logger.error(f"Failed to send Slack alert: {response.status}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")


# Instância global do sistema de monitoramento
monitoring_system = MonitoringSystem()


# Funções convenientes para uso em outros módulos
async def record_api_call(endpoint: str, method: str, status_code: int, 
                         response_time_ms: float, user_id: str = None):
    """Registrar chamada da API"""
    await monitoring_system.record_api_call(endpoint, method, status_code, response_time_ms, user_id)


async def record_business_event(event_type: str, value: float = 1.0, metadata: Dict[str, Any] = None):
    """Registrar evento de negócio"""
    await monitoring_system.record_business_event(event_type, value, metadata)


def get_monitoring_dashboard() -> Dict[str, Any]:
    """Obter dashboard de monitoramento"""
    return monitoring_system.get_monitoring_dashboard()


async def init_monitoring():
    """Inicializar sistema de monitoramento"""
    await monitoring_system.start()


async def stop_monitoring():
    """Parar sistema de monitoramento"""
    await monitoring_system.stop()
