#!/usr/bin/env python3
"""
TRILHA 2 FASE 3 - Real-time Monitoring
Sistema de monitoramento em tempo real com dashboards dinâmicos
"""

import asyncio
import gc
import json
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil


class MetricType(Enum):
    """Tipos de métricas"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    TIMER = "timer"


class AlertLevel(Enum):
    """Níveis de alerta"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Ponto de métrica"""

    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """Definição de métrica"""

    name: str
    type: MetricType
    description: str
    unit: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    points: deque = field(default_factory=lambda: deque(maxlen=1000))

    def add_point(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Adiciona ponto de métrica"""
        point = MetricPoint(
            timestamp=time.time(), value=value, labels={**self.labels, **(labels or {})}
        )
        self.points.append(point)

    def get_current_value(self) -> float:
        """Obtém valor atual"""
        return self.points[-1].value if self.points else 0.0

    def get_average(self, duration_seconds: int = 60) -> float:
        """Obtém média dos últimos N segundos"""
        cutoff_time = time.time() - duration_seconds
        recent_points = [p.value for p in self.points if p.timestamp >= cutoff_time]
        return statistics.mean(recent_points) if recent_points else 0.0

    def get_percentile(self, percentile: float, duration_seconds: int = 60) -> float:
        """Obtém percentil dos últimos N segundos"""
        cutoff_time = time.time() - duration_seconds
        recent_points = [p.value for p in self.points if p.timestamp >= cutoff_time]
        if not recent_points:
            return 0.0
        sorted_points = sorted(recent_points)
        index = int(percentile / 100 * len(sorted_points))
        return sorted_points[min(index, len(sorted_points) - 1)]


class MetricsCollector:
    """Coletor de métricas do sistema"""

    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.collection_interval = 1.0  # segundos
        self.collecting = False
        self.collection_task = None

    def register_metric(self, metric: Metric) -> None:
        """Registra uma métrica"""
        self.metrics[metric.name] = metric

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ):
        """Incrementa contador"""
        if name in self.metrics:
            current = self.metrics[name].get_current_value()
            self.metrics[name].add_point(current + value, labels)

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Define valor de gauge"""
        if name in self.metrics:
            self.metrics[name].add_point(value, labels)

    def record_timer(
        self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None
    ):
        """Registra tempo de execução"""
        if name in self.metrics:
            self.metrics[name].add_point(duration_ms, labels)

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """Registra valor em histograma"""
        if name in self.metrics:
            self.metrics[name].add_point(value, labels)

    async def collect_system_metrics(self):
        """Coleta métricas do sistema"""
        while self.collecting:
            try:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=None)
                self.set_gauge("system.cpu.usage_percent", cpu_percent)

                # Memória
                memory = psutil.virtual_memory()
                self.set_gauge("system.memory.usage_percent", memory.percent)
                self.set_gauge(
                    "system.memory.available_mb", memory.available / 1024 / 1024
                )
                self.set_gauge("system.memory.used_mb", memory.used / 1024 / 1024)

                # Disco
                disk = psutil.disk_usage("/")
                self.set_gauge(
                    "system.disk.usage_percent", (disk.used / disk.total) * 100
                )
                self.set_gauge("system.disk.free_gb", disk.free / 1024 / 1024 / 1024)

                # Rede
                net_io = psutil.net_io_counters()
                self.set_gauge("system.network.bytes_sent", net_io.bytes_sent)
                self.set_gauge("system.network.bytes_recv", net_io.bytes_recv)

                # Processos Python
                process = psutil.Process()
                self.set_gauge(
                    "python.memory.rss_mb", process.memory_info().rss / 1024 / 1024
                )
                self.set_gauge("python.cpu.usage_percent", process.cpu_percent())
                self.set_gauge("python.threads.count", process.num_threads())

                # Garbage Collection
                gc_stats = gc.get_stats()
                for i, stat in enumerate(gc_stats):
                    self.set_gauge(
                        f"python.gc.generation_{i}_collections", stat["collections"]
                    )

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                print(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def start_collection(self):
        """Inicia coleta de métricas"""
        if not self.collecting:
            self.collecting = True
            self.collection_task = asyncio.create_task(self.collect_system_metrics())

    async def stop_collection(self):
        """Para coleta de métricas"""
        self.collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass


class RealTimeMonitor:
    """Monitor de tempo real com dashboard"""

    def __init__(self):
        self.collector = MetricsCollector()
        self.alerts: List[Dict[str, Any]] = []
        self.thresholds: Dict[str, Dict[str, float]] = {}
        self.dashboard_data: Dict[str, Any] = {}
        self.monitoring = False
        self.monitor_task = None
        self._setup_default_metrics()
        self._setup_default_thresholds()

    def _setup_default_metrics(self):
        """Configura métricas padrão"""

        # Métricas de sistema
        system_metrics = [
            Metric("system.cpu.usage_percent", MetricType.GAUGE, "CPU Usage", "%"),
            Metric(
                "system.memory.usage_percent", MetricType.GAUGE, "Memory Usage", "%"
            ),
            Metric(
                "system.memory.available_mb", MetricType.GAUGE, "Available Memory", "MB"
            ),
            Metric("system.memory.used_mb", MetricType.GAUGE, "Used Memory", "MB"),
            Metric("system.disk.usage_percent", MetricType.GAUGE, "Disk Usage", "%"),
            Metric("system.disk.free_gb", MetricType.GAUGE, "Free Disk Space", "GB"),
            Metric(
                "system.network.bytes_sent",
                MetricType.COUNTER,
                "Network Bytes Sent",
                "bytes",
            ),
            Metric(
                "system.network.bytes_recv",
                MetricType.COUNTER,
                "Network Bytes Received",
                "bytes",
            ),
        ]

        # Métricas Python
        python_metrics = [
            Metric("python.memory.rss_mb", MetricType.GAUGE, "Python Memory RSS", "MB"),
            Metric(
                "python.cpu.usage_percent", MetricType.GAUGE, "Python CPU Usage", "%"
            ),
            Metric("python.threads.count", MetricType.GAUGE, "Thread Count", "count"),
            Metric(
                "python.gc.generation_0_collections",
                MetricType.COUNTER,
                "GC Gen 0 Collections",
                "count",
            ),
            Metric(
                "python.gc.generation_1_collections",
                MetricType.COUNTER,
                "GC Gen 1 Collections",
                "count",
            ),
            Metric(
                "python.gc.generation_2_collections",
                MetricType.COUNTER,
                "GC Gen 2 Collections",
                "count",
            ),
        ]

        # Métricas de aplicação
        app_metrics = [
            Metric("app.requests.total", MetricType.COUNTER, "Total Requests", "count"),
            Metric(
                "app.requests.success",
                MetricType.COUNTER,
                "Successful Requests",
                "count",
            ),
            Metric("app.requests.error", MetricType.COUNTER, "Error Requests", "count"),
            Metric(
                "app.response_time.avg", MetricType.TIMER, "Average Response Time", "ms"
            ),
            Metric(
                "app.webhook.received", MetricType.COUNTER, "Webhooks Received", "count"
            ),
            Metric(
                "app.webhook.processed",
                MetricType.COUNTER,
                "Webhooks Processed",
                "count",
            ),
            Metric("app.messages.sent", MetricType.COUNTER, "Messages Sent", "count"),
            Metric(
                "app.messages.received",
                MetricType.COUNTER,
                "Messages Received",
                "count",
            ),
            Metric("app.ai.requests", MetricType.COUNTER, "AI Requests", "count"),
            Metric("app.ai.response_time", MetricType.TIMER, "AI Response Time", "ms"),
            Metric(
                "app.database.queries", MetricType.COUNTER, "Database Queries", "count"
            ),
            Metric(
                "app.database.response_time",
                MetricType.TIMER,
                "Database Response Time",
                "ms",
            ),
            Metric("app.cache.hits", MetricType.COUNTER, "Cache Hits", "count"),
            Metric("app.cache.misses", MetricType.COUNTER, "Cache Misses", "count"),
        ]

        # Registrar todas as métricas
        for metric in system_metrics + python_metrics + app_metrics:
            self.collector.register_metric(metric)

    def _setup_default_thresholds(self):
        """Configura thresholds padrão"""
        self.thresholds = {
            "system.cpu.usage_percent": {"warning": 70, "critical": 90},
            "system.memory.usage_percent": {"warning": 80, "critical": 95},
            "system.disk.usage_percent": {"warning": 85, "critical": 95},
            "python.memory.rss_mb": {"warning": 500, "critical": 1000},
            "app.response_time.avg": {"warning": 1000, "critical": 3000},
            "app.ai.response_time": {"warning": 5000, "critical": 10000},
            "app.database.response_time": {"warning": 500, "critical": 2000},
        }

    def check_thresholds(self):
        """Verifica thresholds e gera alertas"""
        current_time = time.time()

        for metric_name, thresholds in self.thresholds.items():
            if metric_name in self.collector.metrics:
                metric = self.collector.metrics[metric_name]
                current_value = metric.get_current_value()

                # Verificar threshold crítico
                if "critical" in thresholds and current_value >= thresholds["critical"]:
                    self.add_alert(
                        level=AlertLevel.CRITICAL,
                        metric=metric_name,
                        value=current_value,
                        threshold=thresholds["critical"],
                        message=f"{metric.description} is critically high: {current_value:.2f}{metric.unit}",
                    )

                # Verificar threshold de warning
                elif "warning" in thresholds and current_value >= thresholds["warning"]:
                    self.add_alert(
                        level=AlertLevel.WARNING,
                        metric=metric_name,
                        value=current_value,
                        threshold=thresholds["warning"],
                        message=f"{metric.description} is high: {current_value:.2f}{metric.unit}",
                    )

    def add_alert(
        self,
        level: AlertLevel,
        metric: str,
        value: float,
        threshold: float,
        message: str,
    ):
        """Adiciona alerta"""
        alert = {
            "timestamp": time.time(),
            "level": level.value,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "message": message,
            "acknowledged": False,
        }
        self.alerts.append(alert)

        # Manter apenas os últimos 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Obtém dados para dashboard"""
        current_time = time.time()

        # Dados principais
        dashboard = {
            "timestamp": current_time,
            "system": {},
            "application": {},
            "alerts": {
                "active": [
                    a
                    for a in self.alerts
                    if not a["acknowledged"] and current_time - a["timestamp"] < 300
                ],  # 5 min
                "recent": self.alerts[-10:] if self.alerts else [],
            },
            "health": "healthy",
        }

        # Métricas de sistema
        system_metrics = [
            "system.cpu.usage_percent",
            "system.memory.usage_percent",
            "system.disk.usage_percent",
            "python.memory.rss_mb",
            "python.cpu.usage_percent",
        ]

        for metric_name in system_metrics:
            if metric_name in self.collector.metrics:
                metric = self.collector.metrics[metric_name]
                dashboard["system"][metric_name] = {
                    "current": metric.get_current_value(),
                    "average_1m": metric.get_average(60),
                    "average_5m": metric.get_average(300),
                    "p95": metric.get_percentile(95, 300),
                    "unit": metric.unit,
                }

        # Métricas de aplicação
        app_metrics = [
            "app.requests.total",
            "app.response_time.avg",
            "app.webhook.processed",
            "app.messages.sent",
            "app.ai.requests",
            "app.database.queries",
        ]

        for metric_name in app_metrics:
            if metric_name in self.collector.metrics:
                metric = self.collector.metrics[metric_name]
                dashboard["application"][metric_name] = {
                    "current": metric.get_current_value(),
                    "average_1m": metric.get_average(60),
                    "average_5m": metric.get_average(300),
                    "unit": metric.unit,
                }

        # Determinar health geral
        active_critical_alerts = [
            a for a in dashboard["alerts"]["active"] if a["level"] == "critical"
        ]
        active_warning_alerts = [
            a for a in dashboard["alerts"]["active"] if a["level"] == "warning"
        ]

        if active_critical_alerts:
            dashboard["health"] = "critical"
        elif active_warning_alerts:
            dashboard["health"] = "warning"
        elif dashboard["alerts"]["active"]:
            dashboard["health"] = "degraded"

        return dashboard

    async def monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.monitoring:
            try:
                # Verificar thresholds
                self.check_thresholds()

                # Atualizar dashboard
                self.dashboard_data = self.get_dashboard_data()

                await asyncio.sleep(5)  # Verificar a cada 5 segundos

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def start_monitoring(self):
        """Inicia monitoramento"""
        if not self.monitoring:
            self.monitoring = True
            await self.collector.start_collection()
            self.monitor_task = asyncio.create_task(self.monitoring_loop())
            print("🎯 Real-time monitoring started")

    async def stop_monitoring(self):
        """Para monitoramento"""
        self.monitoring = False
        await self.collector.stop_collection()
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            print("🎯 Real-time monitoring stopped")

    def simulate_application_metrics(self):
        """Simula métricas de aplicação para demonstração"""
        import random

        # Simular requests
        self.collector.increment_counter("app.requests.total", random.randint(1, 5))
        self.collector.increment_counter("app.requests.success", random.randint(1, 4))

        # Simular response times
        self.collector.record_timer("app.response_time.avg", random.uniform(100, 800))

        # Simular webhooks
        if random.random() < 0.3:  # 30% chance
            self.collector.increment_counter("app.webhook.received")
            self.collector.increment_counter("app.webhook.processed")

        # Simular mensagens
        if random.random() < 0.4:  # 40% chance
            self.collector.increment_counter("app.messages.received")
            self.collector.increment_counter("app.messages.sent")

        # Simular IA
        if random.random() < 0.2:  # 20% chance
            self.collector.increment_counter("app.ai.requests")
            self.collector.record_timer(
                "app.ai.response_time", random.uniform(1000, 5000)
            )

        # Simular database
        self.collector.increment_counter("app.database.queries", random.randint(1, 3))
        self.collector.record_timer(
            "app.database.response_time", random.uniform(50, 300)
        )

        # Simular cache
        self.collector.increment_counter("app.cache.hits", random.randint(5, 15))
        self.collector.increment_counter("app.cache.misses", random.randint(0, 3))

    def print_dashboard(self):
        """Imprime dashboard no console"""
        data = self.dashboard_data

        print(
            f"\n🎯 REAL-TIME DASHBOARD - {datetime.fromtimestamp(data['timestamp']).strftime('%H:%M:%S')}"
        )
        print("=" * 70)

        # Health Status
        health_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "degraded": "🟡",
            "critical": "🔴",
        }
        print(
            f"🏥 System Health: {health_emoji.get(data['health'], '❓')} {data['health'].upper()}"
        )

        # System Metrics
        print(f"\n🖥️  SYSTEM METRICS:")
        if "system.cpu.usage_percent" in data["system"]:
            cpu = data["system"]["system.cpu.usage_percent"]
            print(
                f"   CPU Usage: {cpu['current']:.1f}% (avg: {cpu['average_1m']:.1f}%)"
            )

        if "system.memory.usage_percent" in data["system"]:
            mem = data["system"]["system.memory.usage_percent"]
            print(
                f"   Memory Usage: {mem['current']:.1f}% (avg: {mem['average_1m']:.1f}%)"
            )

        if "system.disk.usage_percent" in data["system"]:
            disk = data["system"]["system.disk.usage_percent"]
            print(f"   Disk Usage: {disk['current']:.1f}%")

        # Application Metrics
        print(f"\n🚀 APPLICATION METRICS:")
        if "app.requests.total" in data["application"]:
            req = data["application"]["app.requests.total"]
            print(f"   Total Requests: {req['current']:.0f}")

        if "app.response_time.avg" in data["application"]:
            resp = data["application"]["app.response_time.avg"]
            print(
                f"   Response Time: {resp['current']:.1f}ms (avg: {resp['average_1m']:.1f}ms)"
            )

        if "app.webhook.processed" in data["application"]:
            webhook = data["application"]["app.webhook.processed"]
            print(f"   Webhooks Processed: {webhook['current']:.0f}")

        if "app.messages.sent" in data["application"]:
            msg = data["application"]["app.messages.sent"]
            print(f"   Messages Sent: {msg['current']:.0f}")

        # Alerts
        active_alerts = data["alerts"]["active"]
        if active_alerts:
            print(f"\n🚨 ACTIVE ALERTS ({len(active_alerts)}):")
            for alert in active_alerts[-3:]:  # Mostrar apenas os 3 mais recentes
                level_emoji = {
                    "info": "ℹ️",
                    "warning": "⚠️",
                    "error": "❌",
                    "critical": "🔴",
                }
                print(f"   {level_emoji.get(alert['level'], '❓')} {alert['message']}")
        else:
            print(f"\n✅ No active alerts")


class MonitoringDemo:
    """Demonstração do sistema de monitoramento"""

    def __init__(self):
        self.monitor = RealTimeMonitor()

    async def run_monitoring_demo(self):
        """Executa demonstração do monitoramento"""
        print("🎯 TRILHA 2 FASE 3 - Real-time Monitoring Demo")
        print("📊 Sistema de Monitoramento em Tempo Real")
        print("=" * 60)

        # Iniciar monitoramento
        await self.monitor.start_monitoring()

        print("🚀 Monitoramento iniciado, coletando métricas...")

        # Executar por 30 segundos
        for i in range(6):  # 6 iterações de 5 segundos cada
            await asyncio.sleep(5)

            # Simular métricas de aplicação
            self.monitor.simulate_application_metrics()

            # Mostrar dashboard
            self.monitor.print_dashboard()

            # Simular carga para testar alertas
            if i == 3:  # Na 4ª iteração, simular carga alta
                print("\n🔥 Simulando carga alta do sistema...")
                self.monitor.collector.set_gauge(
                    "system.cpu.usage_percent", 85
                )  # Trigger warning
                self.monitor.collector.set_gauge(
                    "app.response_time.avg", 2500
                )  # Trigger warning

        # Parar monitoramento
        await self.monitor.stop_monitoring()

        # Relatório final
        print(f"\n📊 RELATÓRIO FINAL:")
        print(f"   Total de métricas: {len(self.monitor.collector.metrics)}")
        print(f"   Total de alertas: {len(self.monitor.alerts)}")
        print(
            f"   Status final: {self.monitor.dashboard_data.get('health', 'unknown')}"
        )

        print(f"\n🎯 Real-time Monitoring Demo Completed!")
        return True


async def main():
    """Função principal"""
    demo = MonitoringDemo()
    success = await demo.run_monitoring_demo()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
