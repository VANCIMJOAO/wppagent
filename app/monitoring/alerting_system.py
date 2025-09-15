#!/usr/bin/env python3
"""
TRILHA 2 FASE 3 - Alerting System
Sistema de alertas inteligente com notificações multi-canal
"""

import asyncio
import hashlib
import json
import smtplib
import ssl
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp


class AlertSeverity(Enum):
    """Severidade do alerta"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status do alerta"""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Canais de notificação"""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    CONSOLE = "console"


@dataclass
class AlertRule:
    """Regra de alerta"""

    name: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "ne", "gte", "lte"
    threshold: float
    duration: int  # segundos que a condição deve permanecer
    severity: AlertSeverity
    description: str
    tags: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def evaluate(self, value: float) -> bool:
        """Avalia se a regra foi violada"""
        if not self.enabled:
            return False

        conditions = {
            "gt": value > self.threshold,
            "gte": value >= self.threshold,
            "lt": value < self.threshold,
            "lte": value <= self.threshold,
            "eq": value == self.threshold,
            "ne": value != self.threshold,
        }
        return conditions.get(self.condition, False)


@dataclass
class Alert:
    """Alerta gerado"""

    id: str
    rule_name: str
    metric_name: str
    value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus
    message: str
    created_at: float
    updated_at: float
    acknowledged_at: Optional[float] = None
    resolved_at: Optional[float] = None
    acknowledged_by: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    suppressed_until: Optional[float] = None

    def is_active(self) -> bool:
        """Verifica se o alerta está ativo"""
        current_time = time.time()
        return self.status == AlertStatus.OPEN and (
            not self.suppressed_until or current_time > self.suppressed_until
        )

    def get_duration(self) -> int:
        """Obtém duração do alerta em segundos"""
        end_time = self.resolved_at or time.time()
        return int(end_time - self.created_at)

    def acknowledge(self, user: str):
        """Reconhece o alerta"""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = time.time()
        self.acknowledged_by = user
        self.updated_at = time.time()

    def resolve(self):
        """Resolve o alerta"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = time.time()
        self.updated_at = time.time()

    def suppress(self, duration_seconds: int):
        """Suprime o alerta por um período"""
        self.status = AlertStatus.SUPPRESSED
        self.suppressed_until = time.time() + duration_seconds
        self.updated_at = time.time()


@dataclass
class NotificationConfig:
    """Configuração de notificação"""

    channel: NotificationChannel
    target: str  # email, webhook URL, etc.
    enabled: bool = True
    min_severity: AlertSeverity = AlertSeverity.LOW
    rate_limit: int = 60  # segundos entre notificações
    template: Optional[str] = None


class AlertHistory:
    """Histórico de alertas"""

    def __init__(self, max_size: int = 10000):
        self.alerts: deque = deque(maxlen=max_size)
        self.metrics: Dict[str, Any] = defaultdict(int)

    def add_alert(self, alert: Alert):
        """Adiciona alerta ao histórico"""
        self.alerts.append(alert)
        self.metrics["total_alerts"] += 1
        self.metrics[f"severity_{alert.severity.value}"] += 1
        self.metrics[f"rule_{alert.rule_name}"] += 1

    def get_alerts_by_severity(
        self, severity: AlertSeverity, hours: int = 24
    ) -> List[Alert]:
        """Obtém alertas por severidade"""
        cutoff_time = time.time() - (hours * 3600)
        return [
            a
            for a in self.alerts
            if a.severity == severity and a.created_at >= cutoff_time
        ]

    def get_frequent_alerts(
        self, hours: int = 24, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obtém alertas mais frequentes"""
        cutoff_time = time.time() - (hours * 3600)
        recent_alerts = [a for a in self.alerts if a.created_at >= cutoff_time]

        rule_counts = defaultdict(int)
        for alert in recent_alerts:
            rule_counts[alert.rule_name] += 1

        return sorted(
            [{"rule": rule, "count": count} for rule, count in rule_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:limit]

    def get_mttr(self, hours: int = 24) -> float:
        """Obtém Mean Time To Resolution"""
        cutoff_time = time.time() - (hours * 3600)
        resolved_alerts = [
            a
            for a in self.alerts
            if a.status == AlertStatus.RESOLVED and a.created_at >= cutoff_time
        ]

        if not resolved_alerts:
            return 0.0

        durations = [a.get_duration() for a in resolved_alerts]
        return statistics.mean(durations)


class AnomalyDetector:
    """Detector de anomalias usando estatísticas simples"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metric_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )

    def add_value(self, metric_name: str, value: float):
        """Adiciona valor para análise"""
        self.metric_windows[metric_name].append(value)

    def detect_anomaly(
        self, metric_name: str, value: float, threshold_std: float = 2.0
    ) -> bool:
        """Detecta anomalia usando desvio padrão"""
        window = self.metric_windows[metric_name]

        if len(window) < 10:  # Precisa de dados suficientes
            return False

        values = list(window)
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0

        if std == 0:
            return False

        z_score = abs(value - mean) / std
        return z_score > threshold_std

    def get_prediction(self, metric_name: str) -> Dict[str, float]:
        """Obtém predição simples baseada em tendência"""
        window = self.metric_windows[metric_name]

        if len(window) < 5:
            return {"predicted": 0.0, "confidence": 0.0}

        values = list(window)
        # Regressão linear simples
        n = len(values)
        x = list(range(n))

        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)

        if n * sum_x2 - sum_x * sum_x == 0:
            return {"predicted": values[-1], "confidence": 0.5}

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n

        predicted = slope * n + intercept  # Próximo valor

        # Calcular R²
        y_mean = statistics.mean(values)
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        ss_res = sum((values[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))

        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        confidence = max(0, min(1, r_squared))

        return {"predicted": predicted, "confidence": confidence}


class NotificationService:
    """Serviço de notificações"""

    def __init__(self):
        self.configs: List[NotificationConfig] = []
        self.rate_limits: Dict[str, float] = {}
        self.templates = {
            "default": """
�� ALERT: {title}

📊 Metric: {metric_name}
📈 Value: {value:.2f}
🎯 Threshold: {threshold:.2f}
⚠️ Severity: {severity}
⏰ Time: {timestamp}

📝 Description: {description}

🏷️ Tags: {tags}
            """.strip(),
            "critical": """
🔴 CRITICAL ALERT: {title}

⚠️ IMMEDIATE ATTENTION REQUIRED ⚠️

📊 Metric: {metric_name}
📈 Current Value: {value:.2f}
🎯 Threshold: {threshold:.2f}
⏰ Triggered: {timestamp}

📝 {description}

Please investigate immediately!
            """.strip(),
        }

    def add_config(self, config: NotificationConfig):
        """Adiciona configuração de notificação"""
        self.configs.append(config)

    def should_notify(self, alert: Alert, config: NotificationConfig) -> bool:
        """Verifica se deve notificar"""
        # Verificar se está habilitado
        if not config.enabled:
            return False

        # Verificar severidade mínima
        severity_order = [s for s in AlertSeverity]
        if severity_order.index(alert.severity) < severity_order.index(
            config.min_severity
        ):
            return False

        # Verificar rate limit
        rate_key = f"{config.channel.value}:{config.target}:{alert.rule_name}"
        last_notification = self.rate_limits.get(rate_key, 0)

        if time.time() - last_notification < config.rate_limit:
            return False

        return True

    def format_message(self, alert: Alert, template_name: str = "default") -> str:
        """Formata mensagem do alerta"""
        template = self.templates.get(template_name, self.templates["default"])

        if alert.severity == AlertSeverity.CRITICAL:
            template = self.templates["critical"]

        return template.format(
            title=f"{alert.rule_name} - {alert.severity.value.upper()}",
            metric_name=alert.metric_name,
            value=alert.value,
            threshold=alert.threshold,
            severity=alert.severity.value.upper(),
            timestamp=datetime.fromtimestamp(alert.created_at).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            description=alert.message,
            tags=", ".join(f"{k}={v}" for k, v in alert.tags.items()) or "None",
        )

    async def send_notification(self, alert: Alert, config: NotificationConfig):
        """Envia notificação"""
        if not self.should_notify(alert, config):
            return False

        message = self.format_message(alert, config.template)
        success = False

        try:
            if config.channel == NotificationChannel.CONSOLE:
                success = await self._send_console(message)
            elif config.channel == NotificationChannel.EMAIL:
                success = await self._send_email(config.target, alert, message)
            elif config.channel == NotificationChannel.SLACK:
                success = await self._send_slack(config.target, message)
            elif config.channel == NotificationChannel.WEBHOOK:
                success = await self._send_webhook(config.target, alert, message)

            if success:
                # Atualizar rate limit
                rate_key = f"{config.channel.value}:{config.target}:{alert.rule_name}"
                self.rate_limits[rate_key] = time.time()

            return success

        except Exception as e:
            print(f"Error sending notification via {config.channel.value}: {e}")
            return False

    async def _send_console(self, message: str) -> bool:
        """Envia notificação para console"""
        print(f"\n{message}\n")
        return True

    async def _send_email(self, email: str, alert: Alert, message: str) -> bool:
        """Envia notificação por email (simulado)"""
        print(f"📧 EMAIL to {email}:")
        print(f"Subject: Alert: {alert.rule_name}")
        print(message)
        return True

    async def _send_slack(self, webhook_url: str, message: str) -> bool:
        """Envia notificação para Slack (simulado)"""
        print(f"💬 SLACK to {webhook_url}:")
        print(message)
        return True

    async def _send_webhook(self, url: str, alert: Alert, message: str) -> bool:
        """Envia notificação via webhook (simulado)"""
        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "metric_name": alert.metric_name,
            "value": alert.value,
            "threshold": alert.threshold,
            "severity": alert.severity.value,
            "message": message,
            "timestamp": alert.created_at,
            "tags": alert.tags,
        }

        print(f"🔗 WEBHOOK to {url}:")
        print(json.dumps(payload, indent=2))
        return True


class AlertManager:
    """Gerenciador principal de alertas"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.history = AlertHistory()
        self.notification_service = NotificationService()
        self.anomaly_detector = AnomalyDetector()
        self.rule_states: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.running = False
        self.task = None

        self._setup_default_rules()
        self._setup_default_notifications()

    def _setup_default_rules(self):
        """Configura regras padrão"""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                metric_name="system.cpu.usage_percent",
                condition="gte",
                threshold=80.0,
                duration=30,
                severity=AlertSeverity.HIGH,
                description="CPU usage is critically high",
            ),
            AlertRule(
                name="critical_cpu_usage",
                metric_name="system.cpu.usage_percent",
                condition="gte",
                threshold=95.0,
                duration=10,
                severity=AlertSeverity.CRITICAL,
                description="CPU usage is at critical levels",
            ),
            AlertRule(
                name="high_memory_usage",
                metric_name="system.memory.usage_percent",
                condition="gte",
                threshold=85.0,
                duration=60,
                severity=AlertSeverity.HIGH,
                description="Memory usage is high",
            ),
            AlertRule(
                name="disk_space_warning",
                metric_name="system.disk.usage_percent",
                condition="gte",
                threshold=85.0,
                duration=300,
                severity=AlertSeverity.MEDIUM,
                description="Disk space is running low",
            ),
            AlertRule(
                name="slow_response_time",
                metric_name="app.response_time.avg",
                condition="gte",
                threshold=2000.0,
                duration=30,
                severity=AlertSeverity.HIGH,
                description="Application response time is slow",
            ),
            AlertRule(
                name="ai_response_timeout",
                metric_name="app.ai.response_time",
                condition="gte",
                threshold=10000.0,
                duration=10,
                severity=AlertSeverity.CRITICAL,
                description="AI response is timing out",
            ),
            AlertRule(
                name="database_slow_query",
                metric_name="app.database.response_time",
                condition="gte",
                threshold=1000.0,
                duration=20,
                severity=AlertSeverity.MEDIUM,
                description="Database queries are slow",
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def _setup_default_notifications(self):
        """Configura notificações padrão"""
        # Console para todos os alertas
        self.notification_service.add_config(
            NotificationConfig(
                channel=NotificationChannel.CONSOLE,
                target="console",
                min_severity=AlertSeverity.LOW,
                rate_limit=30,
            )
        )

        # Email para alertas críticos (simulado)
        self.notification_service.add_config(
            NotificationConfig(
                channel=NotificationChannel.EMAIL,
                target="admin@whatsapp-agent.com",
                min_severity=AlertSeverity.HIGH,
                rate_limit=300,  # 5 minutos
            )
        )

        # Slack para alertas médios e acima (simulado)
        self.notification_service.add_config(
            NotificationConfig(
                channel=NotificationChannel.SLACK,
                target="https://hooks.slack.com/services/xxx",
                min_severity=AlertSeverity.MEDIUM,
                rate_limit=60,
            )
        )

    def add_rule(self, rule: AlertRule):
        """Adiciona regra de alerta"""
        self.rules[rule.name] = rule
        self.rule_states[rule.name] = {
            "violation_started": None,
            "last_value": None,
            "violation_count": 0,
        }

    def remove_rule(self, rule_name: str):
        """Remove regra de alerta"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            del self.rule_states[rule_name]

    def evaluate_metric(
        self, metric_name: str, value: float, timestamp: Optional[float] = None
    ):
        """Avalia métrica contra todas as regras"""
        current_time = timestamp or time.time()

        # Adicionar ao detector de anomalias
        self.anomaly_detector.add_value(metric_name, value)

        # Detectar anomalia
        if self.anomaly_detector.detect_anomaly(metric_name, value):
            self._create_anomaly_alert(metric_name, value, current_time)

        # Avaliar regras existentes
        for rule_name, rule in self.rules.items():
            if rule.metric_name == metric_name:
                self._evaluate_rule(rule, value, current_time)

    def _evaluate_rule(self, rule: AlertRule, value: float, timestamp: float):
        """Avalia uma regra específica"""
        rule_state = self.rule_states[rule.name]
        is_violation = rule.evaluate(value)

        rule_state["last_value"] = value

        if is_violation:
            if rule_state["violation_started"] is None:
                # Primeira violação
                rule_state["violation_started"] = timestamp
                rule_state["violation_count"] = 1
            else:
                # Violação contínua
                violation_duration = timestamp - rule_state["violation_started"]

                if violation_duration >= rule.duration:
                    # Duração mínima atingida, criar alerta
                    self._create_alert(rule, value, timestamp)

                    # Reset para evitar spam
                    rule_state["violation_started"] = timestamp

                rule_state["violation_count"] += 1
        else:
            # Não há violação
            if rule_state["violation_started"] is not None:
                # Resolver alertas ativos desta regra
                self._resolve_alerts_for_rule(rule.name)

                # Reset estado
                rule_state["violation_started"] = None
                rule_state["violation_count"] = 0

    def _create_alert(self, rule: AlertRule, value: float, timestamp: float):
        """Cria um novo alerta"""
        alert_id = hashlib.md5(
            f"{rule.name}:{rule.metric_name}:{timestamp}".encode()
        ).hexdigest()[:8]

        # Verificar se já existe alerta ativo para esta regra
        existing_alerts = [
            a
            for a in self.active_alerts.values()
            if a.rule_name == rule.name and a.is_active()
        ]

        if existing_alerts:
            # Atualizar alerta existente
            alert = existing_alerts[0]
            alert.value = value
            alert.updated_at = timestamp
        else:
            # Criar novo alerta
            alert = Alert(
                id=alert_id,
                rule_name=rule.name,
                metric_name=rule.metric_name,
                value=value,
                threshold=rule.threshold,
                severity=rule.severity,
                status=AlertStatus.OPEN,
                message=rule.description,
                created_at=timestamp,
                updated_at=timestamp,
                tags=rule.tags.copy(),
            )

            self.active_alerts[alert_id] = alert
            self.history.add_alert(alert)

            # Enviar notificações
            asyncio.create_task(self._send_alert_notifications(alert))

    def _create_anomaly_alert(self, metric_name: str, value: float, timestamp: float):
        """Cria alerta de anomalia"""
        prediction = self.anomaly_detector.get_prediction(metric_name)

        alert_id = hashlib.md5(
            f"anomaly:{metric_name}:{timestamp}".encode()
        ).hexdigest()[:8]

        alert = Alert(
            id=alert_id,
            rule_name="anomaly_detection",
            metric_name=metric_name,
            value=value,
            threshold=prediction["predicted"],
            severity=AlertSeverity.LOW,
            status=AlertStatus.OPEN,
            message=f"Anomaly detected in {metric_name}: {value:.2f} (expected ~{prediction['predicted']:.2f})",
            created_at=timestamp,
            updated_at=timestamp,
            tags={"type": "anomaly", "confidence": str(prediction["confidence"])},
        )

        self.active_alerts[alert_id] = alert
        self.history.add_alert(alert)

    def _resolve_alerts_for_rule(self, rule_name: str):
        """Resolve todos os alertas ativos de uma regra"""
        for alert in self.active_alerts.values():
            if alert.rule_name == rule_name and alert.is_active():
                alert.resolve()

    async def _send_alert_notifications(self, alert: Alert):
        """Envia notificações para um alerta"""
        for config in self.notification_service.configs:
            await self.notification_service.send_notification(alert, config)

    def get_active_alerts(self) -> List[Alert]:
        """Obtém alertas ativos"""
        return [a for a in self.active_alerts.values() if a.is_active()]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Obtém resumo dos alertas"""
        active_alerts = self.get_active_alerts()

        summary = {
            "total_active": len(active_alerts),
            "by_severity": defaultdict(int),
            "by_rule": defaultdict(int),
            "oldest_alert": None,
            "mttr": self.history.get_mttr(),
            "frequent_alerts": self.history.get_frequent_alerts(),
        }

        if active_alerts:
            oldest = min(active_alerts, key=lambda a: a.created_at)
            summary["oldest_alert"] = {
                "rule": oldest.rule_name,
                "age_seconds": int(time.time() - oldest.created_at),
            }

        for alert in active_alerts:
            summary["by_severity"][alert.severity.value] += 1
            summary["by_rule"][alert.rule_name] += 1

        return summary

    async def start(self):
        """Inicia o gerenciador de alertas"""
        if not self.running:
            self.running = True
            print("🚨 Alert Manager started")

    async def stop(self):
        """Para o gerenciador de alertas"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("🚨 Alert Manager stopped")


class AlertingDemo:
    """Demonstração do sistema de alertas"""

    def __init__(self):
        self.alert_manager = AlertManager()

    async def run_alerting_demo(self):
        """Executa demonstração do sistema de alertas"""
        print("🚨 TRILHA 2 FASE 3 - Alerting System Demo")
        print("📢 Sistema de Alertas Inteligente")
        print("=" * 60)

        # Iniciar alert manager
        await self.alert_manager.start()

        # Demonstrar diferentes cenários
        await self._demo_normal_metrics()
        await self._demo_threshold_violations()
        await self._demo_anomaly_detection()
        await self._demo_escalation()

        # Mostrar resumo final
        self._show_final_summary()

        # Parar alert manager
        await self.alert_manager.stop()

        print(f"\n🚨 Alerting System Demo Completed!")
        return True

    async def _demo_normal_metrics(self):
        """Demonstra métricas normais"""
        print(f"\n📊 Scenario 1: Normal Operations")
        print("=" * 40)

        # Métricas normais
        normal_metrics = [
            ("system.cpu.usage_percent", 45.0),
            ("system.memory.usage_percent", 60.0),
            ("app.response_time.avg", 150.0),
            ("app.database.response_time", 50.0),
        ]

        for metric, value in normal_metrics:
            self.alert_manager.evaluate_metric(metric, value)
            print(f"✅ {metric}: {value}")

        print(f"📈 All metrics within normal range")
        await asyncio.sleep(2)

    async def _demo_threshold_violations(self):
        """Demonstra violações de threshold"""
        print(f"\n⚠️ Scenario 2: Threshold Violations")
        print("=" * 40)

        # Simular violações que duram o tempo necessário
        violations = [
            ("system.cpu.usage_percent", 85.0, "high_cpu_usage", 35),  # Precisa de 30s
            (
                "system.memory.usage_percent",
                90.0,
                "high_memory_usage",
                65,
            ),  # Precisa de 60s
            (
                "app.response_time.avg",
                2500.0,
                "slow_response_time",
                35,
            ),  # Precisa de 30s
        ]

        for metric, value, rule_name, duration in violations:
            print(f"🔥 Simulating {rule_name}: {metric} = {value}")

            # Simular violação por tempo necessário
            start_time = time.time()
            while time.time() - start_time < duration:
                self.alert_manager.evaluate_metric(metric, value, time.time())
                await asyncio.sleep(1)

                # Mostrar alertas ativos
                active_alerts = self.alert_manager.get_active_alerts()
                new_alerts = [a for a in active_alerts if a.rule_name == rule_name]
                if new_alerts and len(new_alerts) == 1:  # Primeiro alerta criado
                    print(f"🚨 Alert triggered: {rule_name}")
                    break

        # Mostrar resumo de alertas
        summary = self.alert_manager.get_alert_summary()
        print(f"\n📊 Active Alerts: {summary['total_active']}")
        for severity, count in summary["by_severity"].items():
            print(f"   {severity}: {count}")

        await asyncio.sleep(2)

    async def _demo_anomaly_detection(self):
        """Demonstra detecção de anomalias"""
        print(f"\n🔍 Scenario 3: Anomaly Detection")
        print("=" * 40)

        # Criar padrão normal primeiro
        normal_values = [100, 105, 98, 102, 99, 103, 101, 97, 104, 100]
        for value in normal_values:
            self.alert_manager.evaluate_metric("app.custom_metric", value)

        print(f"📈 Established baseline: {normal_values}")

        # Introduzir anomalia
        anomalous_values = [250, 300, 280]  # Muito acima do normal
        for value in anomalous_values:
            self.alert_manager.evaluate_metric("app.custom_metric", value)
            print(f"🔍 Anomaly detected: {value} (expected ~100)")

        await asyncio.sleep(2)

    async def _demo_escalation(self):
        """Demonstra escalation de alertas"""
        print(f"\n📈 Scenario 4: Alert Escalation")
        print("=" * 40)

        # CPU crítico
        print(f"🔴 Triggering critical CPU alert...")
        start_time = time.time()
        while time.time() - start_time < 15:  # 15 segundos (precisa de 10)
            self.alert_manager.evaluate_metric("system.cpu.usage_percent", 98.0)
            await asyncio.sleep(1)

        # AI timeout crítico
        print(f"🔴 Triggering AI timeout alert...")
        start_time = time.time()
        while time.time() - start_time < 12:  # 12 segundos (precisa de 10)
            self.alert_manager.evaluate_metric("app.ai.response_time", 15000.0)
            await asyncio.sleep(1)

        await asyncio.sleep(2)

    def _show_final_summary(self):
        """Mostra resumo final"""
        print(f"\n📊 FINAL SUMMARY")
        print("=" * 40)

        summary = self.alert_manager.get_alert_summary()

        print(f"🚨 Total Active Alerts: {summary['total_active']}")
        print(f"📈 Mean Time To Resolution: {summary['mttr']:.1f} seconds")

        print(f"\n🏷️ Alerts by Severity:")
        for severity, count in summary["by_severity"].items():
            emoji = {
                "info": "ℹ️",
                "low": "🟡",
                "medium": "🟠",
                "high": "��",
                "critical": "🆘",
            }
            print(f"   {emoji.get(severity, '❓')} {severity}: {count}")

        print(f"\n📊 Frequent Alert Rules:")
        for item in summary["frequent_alerts"][:5]:
            print(f"   {item['rule']}: {item['count']} times")

        if summary["oldest_alert"]:
            oldest = summary["oldest_alert"]
            print(f"\n⏰ Oldest Alert: {oldest['rule']} ({oldest['age_seconds']}s ago)")

        print(f"\n📈 Total Alerts in History: {len(self.alert_manager.history.alerts)}")
        print(f"📋 Total Rules Configured: {len(self.alert_manager.rules)}")
        print(
            f"🔔 Notification Channels: {len(self.alert_manager.notification_service.configs)}"
        )


async def main():
    """Função principal"""
    demo = AlertingDemo()
    success = await demo.run_alerting_demo()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
