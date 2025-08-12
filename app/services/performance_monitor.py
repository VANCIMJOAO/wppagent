"""
Sistema de Monitoramento de Performance Completo
===============================================

Monitora todas as métricas de performance do sistema:
- CPU, Memória, Disco
- Latência de APIs
- Throughput de mensagens
- Performance de banco de dados
- Disponibilidade de serviços
"""

import asyncio
import psutil
import time
import httpx
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import json

from app.services.production_logger import performance_logger, log_performance_metric
from app.utils.logger import get_logger
from app.services.automated_alerts import alert_manager, AlertSeverity, AlertCategory
logger = get_logger(__name__)
from app.services.business_metrics import metrics_collector
from app.database import AsyncSessionLocal
from sqlalchemy import text


@dataclass
class PerformanceMetric:
    """Métrica de performance"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    component: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'metadata': self.metadata
        }


class SystemPerformanceMonitor:
    """
    Monitor de performance do sistema
    """
    
    def __init__(self, storage_path: str = "logs/performance"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Métricas coletadas
        self.metrics_history: List[PerformanceMetric] = []
        
        # Thresholds de alerta
        self.thresholds = {
            'cpu_usage': {'warning': 80, 'critical': 95},
            'memory_usage': {'warning': 85, 'critical': 95},
            'disk_usage': {'warning': 85, 'critical': 95},
            'response_time': {'warning': 2000, 'critical': 5000},  # ms
            'error_rate': {'warning': 5, 'critical': 10},  # %
            'database_connections': {'warning': 80, 'critical': 95}  # %
        }
        
        # Cache de métricas para cálculos
        self.metrics_cache = {}
        
        # Status dos últimos checks
        self.last_check_status = {}
    
    async def collect_system_metrics(self) -> Dict[str, PerformanceMetric]:
        """Coletar métricas do sistema"""
        try:
            metrics = {}
            timestamp = datetime.now(timezone.utc)
            
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['cpu_usage'] = PerformanceMetric(
                name='cpu_usage',
                value=cpu_percent,
                unit='percent',
                timestamp=timestamp,
                component='system',
                metadata={'cores': psutil.cpu_count()}
            )
            
            # Memory Usage
            memory = psutil.virtual_memory()
            metrics['memory_usage'] = PerformanceMetric(
                name='memory_usage',
                value=memory.percent,
                unit='percent',
                timestamp=timestamp,
                component='system',
                metadata={
                    'total_gb': round(memory.total / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2)
                }
            )
            
            # Disk Usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics['disk_usage'] = PerformanceMetric(
                name='disk_usage',
                value=disk_percent,
                unit='percent',
                timestamp=timestamp,
                component='system',
                metadata={
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2)
                }
            )
            
            # Network I/O
            network = psutil.net_io_counters()
            metrics['network_bytes_sent'] = PerformanceMetric(
                name='network_bytes_sent',
                value=network.bytes_sent,
                unit='bytes',
                timestamp=timestamp,
                component='network',
                metadata={'packets_sent': network.packets_sent}
            )
            
            metrics['network_bytes_recv'] = PerformanceMetric(
                name='network_bytes_recv',
                value=network.bytes_recv,
                unit='bytes',
                timestamp=timestamp,
                component='network',
                metadata={'packets_recv': network.packets_recv}
            )
            
            # Process info
            process = psutil.Process()
            metrics['process_memory'] = PerformanceMetric(
                name='process_memory',
                value=process.memory_percent(),
                unit='percent',
                timestamp=timestamp,
                component='process',
                metadata={
                    'rss_mb': round(process.memory_info().rss / (1024**2), 2),
                    'vms_mb': round(process.memory_info().vms / (1024**2), 2)
                }
            )
            
            metrics['process_cpu'] = PerformanceMetric(
                name='process_cpu',
                value=process.cpu_percent(),
                unit='percent',
                timestamp=timestamp,
                component='process',
                metadata={'threads': process.num_threads()}
            )
            
            return metrics
            
        except Exception as e:
            performance_logger.error(f"Error collecting system metrics: {e}", exc_info=True)
            return {}
    
    async def check_database_performance(self) -> Dict[str, PerformanceMetric]:
        """Verificar performance do banco de dados"""
        try:
            metrics = {}
            timestamp = datetime.now(timezone.utc)
            
            async with AsyncSessionLocal() as db:
                # Test connection time
                start_time = time.time()
                await db.execute(text("SELECT 1"))
                connection_time = (time.time() - start_time) * 1000  # ms
                
                metrics['db_connection_time'] = PerformanceMetric(
                    name='db_connection_time',
                    value=connection_time,
                    unit='milliseconds',
                    timestamp=timestamp,
                    component='database',
                    metadata={}
                )
                
                # Test query performance
                start_time = time.time()
                result = await db.execute(text("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_users
                    FROM users
                """))
                query_time = (time.time() - start_time) * 1000  # ms
                
                row = result.fetchone()
                
                metrics['db_query_time'] = PerformanceMetric(
                    name='db_query_time',
                    value=query_time,
                    unit='milliseconds',
                    timestamp=timestamp,
                    component='database',
                    metadata={
                        'total_users': row[0] if row else 0,
                        'recent_users': row[1] if row else 0
                    }
                )
                
                # Check active connections
                result = await db.execute(text("""
                    SELECT COUNT(*) as active_connections
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """))
                active_connections = result.fetchone()[0] if result.fetchone() else 0
                
                metrics['db_active_connections'] = PerformanceMetric(
                    name='db_active_connections',
                    value=active_connections,
                    unit='count',
                    timestamp=timestamp,
                    component='database',
                    metadata={}
                )
            
            return metrics
            
        except Exception as e:
            performance_logger.error(f"Error checking database performance: {e}", exc_info=True)
            return {}
    
    async def check_api_performance(self) -> Dict[str, PerformanceMetric]:
        """Verificar performance das APIs"""
        try:
            metrics = {}
            timestamp = datetime.now(timezone.utc)
            
            # APIs para testar
            apis_to_test = [
                {'name': 'health_check', 'url': 'http://localhost:8000/health'},
                {'name': 'metrics', 'url': 'http://localhost:8000/metrics'}
            ]
            
            async with httpx.AsyncClient(timeout=10) as client:
                for api in apis_to_test:
                    try:
                        start_time = time.time()
                        response = await client.get(api['url'])
                        response_time = (time.time() - start_time) * 1000  # ms
                        
                        metrics[f"api_{api['name']}_response_time"] = PerformanceMetric(
                            name=f"api_{api['name']}_response_time",
                            value=response_time,
                            unit='milliseconds',
                            timestamp=timestamp,
                            component='api',
                            metadata={
                                'status_code': response.status_code,
                                'url': api['url']
                            }
                        )
                        
                        # Success rate
                        success = 1 if response.status_code == 200 else 0
                        metrics[f"api_{api['name']}_success"] = PerformanceMetric(
                            name=f"api_{api['name']}_success",
                            value=success,
                            unit='boolean',
                            timestamp=timestamp,
                            component='api',
                            metadata={'status_code': response.status_code}
                        )
                        
                    except Exception as e:
                        metrics[f"api_{api['name']}_success"] = PerformanceMetric(
                            name=f"api_{api['name']}_success",
                            value=0,
                            unit='boolean',
                            timestamp=timestamp,
                            component='api',
                            metadata={'error': str(e)}
                        )
            
            return metrics
            
        except Exception as e:
            performance_logger.error(f"Error checking API performance: {e}", exc_info=True)
            return {}
    
    async def check_external_services(self) -> Dict[str, PerformanceMetric]:
        """Verificar performance de serviços externos"""
        try:
            metrics = {}
            timestamp = datetime.now(timezone.utc)
            
            # Serviços externos para testar
            external_services = [
                {'name': 'openai', 'url': 'https://api.openai.com/v1/models', 'timeout': 10},
                {'name': 'whatsapp', 'url': 'https://graph.facebook.com/v17.0/me', 'timeout': 5}
            ]
            
            async with httpx.AsyncClient() as client:
                for service in external_services:
                    try:
                        start_time = time.time()
                        response = await client.get(
                            service['url'], 
                            timeout=service['timeout']
                        )
                        response_time = (time.time() - start_time) * 1000  # ms
                        
                        metrics[f"external_{service['name']}_response_time"] = PerformanceMetric(
                            name=f"external_{service['name']}_response_time",
                            value=response_time,
                            unit='milliseconds',
                            timestamp=timestamp,
                            component='external',
                            metadata={
                                'status_code': response.status_code,
                                'service': service['name']
                            }
                        )
                        
                        # Availability
                        available = 1 if response.status_code < 500 else 0
                        metrics[f"external_{service['name']}_availability"] = PerformanceMetric(
                            name=f"external_{service['name']}_availability",
                            value=available,
                            unit='boolean',
                            timestamp=timestamp,
                            component='external',
                            metadata={'status_code': response.status_code}
                        )
                        
                    except asyncio.TimeoutError:
                        metrics[f"external_{service['name']}_availability"] = PerformanceMetric(
                            name=f"external_{service['name']}_availability",
                            value=0,
                            unit='boolean',
                            timestamp=timestamp,
                            component='external',
                            metadata={'error': 'timeout'}
                        )
                    except Exception as e:
                        metrics[f"external_{service['name']}_availability"] = PerformanceMetric(
                            name=f"external_{service['name']}_availability",
                            value=0,
                            unit='boolean',
                            timestamp=timestamp,
                            component='external',
                            metadata={'error': str(e)}
                        )
            
            return metrics
            
        except Exception as e:
            performance_logger.error(f"Error checking external services: {e}", exc_info=True)
            return {}
    
    async def collect_all_metrics(self) -> Dict[str, PerformanceMetric]:
        """Coletar todas as métricas"""
        all_metrics = {}
        
        # Coletar métricas do sistema
        system_metrics = await self.collect_system_metrics()
        all_metrics.update(system_metrics)
        
        # Coletar métricas do banco
        db_metrics = await self.check_database_performance()
        all_metrics.update(db_metrics)
        
        # Coletar métricas das APIs
        api_metrics = await self.check_api_performance()
        all_metrics.update(api_metrics)
        
        # Coletar métricas de serviços externos
        external_metrics = await self.check_external_services()
        all_metrics.update(external_metrics)
        
        # Adicionar ao histórico
        self.metrics_history.extend(all_metrics.values())
        
        # Manter apenas últimas 1000 métricas
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Salvar métricas
        await self._save_metrics(all_metrics)
        
        return all_metrics
    
    async def _save_metrics(self, metrics: Dict[str, PerformanceMetric]):
        """Salvar métricas em arquivo"""
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            file_path = self.storage_path / f"performance_{date_str}.jsonl"
            
            with open(file_path, 'a', encoding='utf-8') as f:
                for metric in metrics.values():
                    f.write(json.dumps(metric.to_dict(), ensure_ascii=False) + '\n')
                    
        except Exception as e:
            performance_logger.error(f"Error saving metrics: {e}", exc_info=True)
    
    async def check_thresholds_and_alert(self, metrics: Dict[str, PerformanceMetric]):
        """Verificar thresholds e gerar alertas"""
        try:
            for metric_name, metric in metrics.items():
                # Buscar threshold para esta métrica
                threshold_key = metric.name
                if threshold_key in self.thresholds:
                    thresholds = self.thresholds[threshold_key]
                    
                    # Verificar se excedeu threshold crítico
                    if metric.value >= thresholds['critical']:
                        await alert_manager.create_alert(
                            alert_id=f"performance_critical_{metric.name}",
                            title=f"Performance crítica: {metric.name}",
                            message=f"{metric.name} atingiu nível crítico: {metric.value}{metric.unit} (limite: {thresholds['critical']}{metric.unit})",
                            severity=AlertSeverity.CRITICAL,
                            category=AlertCategory.PERFORMANCE,
                            metadata={
                                'metric': metric.to_dict(),
                                'threshold': thresholds['critical']
                            }
                        )
                    
                    # Verificar se excedeu threshold de warning
                    elif metric.value >= thresholds['warning']:
                        await alert_manager.create_alert(
                            alert_id=f"performance_warning_{metric.name}",
                            title=f"Performance degradada: {metric.name}",
                            message=f"{metric.name} atingiu nível de warning: {metric.value}{metric.unit} (limite: {thresholds['warning']}{metric.unit})",
                            severity=AlertSeverity.MEDIUM,
                            category=AlertCategory.PERFORMANCE,
                            metadata={
                                'metric': metric.to_dict(),
                                'threshold': thresholds['warning']
                            }
                        )
                    
                    # Resolver alerta se voltou ao normal
                    else:
                        await alert_manager.resolve_alert(f"performance_critical_{metric.name}")
                        await alert_manager.resolve_alert(f"performance_warning_{metric.name}")
                
                # Log da métrica para o sistema de métricas de negócio
                await metrics_collector.record_response_time(
                    response_time_ms=metric.value if 'time' in metric.name else 0,
                    component=metric.component
                )
                
                # Log para performance
                log_performance_metric(
                    operation=metric.name,
                    duration_ms=metric.value if 'time' in metric.name else 0,
                    additional_data=metric.metadata
                )
                
        except Exception as e:
            performance_logger.error(f"Error checking thresholds: {e}", exc_info=True)
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Obter resumo de performance"""
        try:
            if not self.metrics_history:
                return {}
            
            # Filtrar métricas das últimas 24 horas
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_metrics = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            # Agrupar por nome da métrica
            metrics_by_name = {}
            for metric in recent_metrics:
                if metric.name not in metrics_by_name:
                    metrics_by_name[metric.name] = []
                metrics_by_name[metric.name].append(metric.value)
            
            # Calcular estatísticas
            summary = {}
            for name, values in metrics_by_name.items():
                summary[name] = {
                    'current': values[-1] if values else 0,
                    'average': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'count': len(values)
                }
            
            return summary
            
        except Exception as e:
            performance_logger.error(f"Error generating performance summary: {e}", exc_info=True)
            return {}


class PerformanceMonitorDaemon:
    """
    Daemon para monitoramento contínuo de performance
    """
    
    def __init__(self, check_interval: int = 60):  # 1 minuto
        self.check_interval = check_interval
        self.monitor = SystemPerformanceMonitor()
        self.running = False
        self.task = None
    
    async def start(self):
        """Iniciar daemon de monitoramento"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitoring_loop())
        performance_logger.info("Performance monitoring daemon started")
    
    async def stop(self):
        """Parar daemon de monitoramento"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        performance_logger.info("Performance monitoring daemon stopped")
    
    async def _monitoring_loop(self):
        """Loop principal de monitoramento"""
        while self.running:
            try:
                # Coletar todas as métricas
                metrics = await self.monitor.collect_all_metrics()
                
                # Verificar thresholds e alertar se necessário
                await self.monitor.check_thresholds_and_alert(metrics)
                
                # Log do ciclo de monitoramento
                performance_logger.debug(
                    f"Performance monitoring cycle completed",
                    extra_data={
                        'metrics_collected': len(metrics),
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )
                
                # Aguardar próximo ciclo
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                performance_logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)


# Instâncias globais
performance_monitor = SystemPerformanceMonitor()
monitoring_daemon = PerformanceMonitorDaemon()


# Funções de conveniência
async def get_current_performance() -> Dict[str, Any]:
    """Obter performance atual do sistema"""
    metrics = await performance_monitor.collect_all_metrics()
    return {name: metric.to_dict() for name, metric in metrics.items()}

async def get_performance_summary() -> Dict[str, Any]:
    """Obter resumo de performance"""
    return await performance_monitor.get_performance_summary()

async def start_performance_monitoring():
    """Iniciar monitoramento de performance"""
    await monitoring_daemon.start()

async def stop_performance_monitoring():
    """Parar monitoramento de performance"""
    await monitoring_daemon.stop()
