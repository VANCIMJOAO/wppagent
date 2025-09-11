"""
📊 WEBHOOK PERFORMANCE MONITOR
==============================

Sistema de monitoramento e alertas para performance do webhook.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque
import asyncio

from app.services.structured_apm import get_structured_logger, LogCategory

# Configurar logger
logger = get_structured_logger("webhook.performance")


@dataclass
class WebhookMetrics:
    """Métricas de performance do webhook"""
    total_batches: int = 0
    total_messages: int = 0
    total_processing_time: float = 0.0
    avg_batch_size: float = 0.0
    avg_processing_time: float = 0.0
    messages_per_second: float = 0.0
    success_rate: float = 100.0
    last_reset: float = field(default_factory=time.time)
    
    # Histórico recente (últimas 100 requisições)
    recent_batches: deque = field(default_factory=lambda: deque(maxlen=100))


class PerformanceMonitor:
    """Monitor de performance para webhook"""
    
    def __init__(self):
        self.metrics = WebhookMetrics()
        self._lock = asyncio.Lock()
        self.alert_thresholds = {
            "avg_processing_time": 5.0,  # 5 segundos
            "messages_per_second": 1.0,  # Mínimo 1 msg/s
            "success_rate": 80.0,        # Mínimo 80%
            "batch_timeout_rate": 10.0   # Máximo 10% timeouts
        }
    
    async def record_batch(
        self,
        batch_size: int,
        processing_time: float,
        processed: int,
        blocked: int,
        had_timeout: bool = False
    ):
        """Registra métricas de um batch processado"""
        async with self._lock:
            self.metrics.total_batches += 1
            self.metrics.total_messages += batch_size
            self.metrics.total_processing_time += processing_time
            
            # Calcular médias
            self.metrics.avg_batch_size = self.metrics.total_messages / self.metrics.total_batches
            self.metrics.avg_processing_time = self.metrics.total_processing_time / self.metrics.total_batches
            self.metrics.messages_per_second = batch_size / processing_time if processing_time > 0 else 0
            self.metrics.success_rate = (processed / batch_size) * 100 if batch_size > 0 else 0
            
            # Adicionar ao histórico recente
            self.metrics.recent_batches.append({
                "timestamp": time.time(),
                "batch_size": batch_size,
                "processing_time": processing_time,
                "processed": processed,
                "blocked": blocked,
                "had_timeout": had_timeout,
                "success_rate": self.metrics.success_rate,
                "messages_per_second": self.metrics.messages_per_second
            })
            
            # Verificar alertas
            await self._check_performance_alerts(
                processing_time, self.metrics.messages_per_second, 
                self.metrics.success_rate, had_timeout
            )
    
    async def _check_performance_alerts(
        self, 
        processing_time: float, 
        messages_per_second: float,
        success_rate: float,
        had_timeout: bool
    ):
        """Verifica se há alertas de performance a serem enviados"""
        alerts = []
        
        if processing_time > self.alert_thresholds["avg_processing_time"]:
            alerts.append(f"⚠️ Processing time alto: {processing_time:.2f}s")
        
        if messages_per_second < self.alert_thresholds["messages_per_second"]:
            alerts.append(f"⚠️ Throughput baixo: {messages_per_second:.2f} msg/s")
        
        if success_rate < self.alert_thresholds["success_rate"]:
            alerts.append(f"⚠️ Success rate baixo: {success_rate:.1f}%")
        
        if had_timeout:
            alerts.append("⚠️ Timeout detectado no batch")
        
        # Log alertas se houver
        if alerts:
            logger.warning(
                "🚨 Performance alerts detected",
                metadata={
                    "alerts": alerts,
                    "current_metrics": {
                        "processing_time": processing_time,
                        "messages_per_second": messages_per_second,
                        "success_rate": success_rate,
                        "had_timeout": had_timeout
                    },
                    "thresholds": self.alert_thresholds
                },
                category=LogCategory.PERFORMANCE
            )
    
    async def get_performance_stats(self) -> Dict:
        """Retorna estatísticas atuais de performance"""
        async with self._lock:
            # Calcular estatísticas dos últimos batches
            recent_list = list(self.metrics.recent_batches)
            
            recent_stats = {}
            if recent_list:
                recent_processing_times = [b["processing_time"] for b in recent_list]
                recent_success_rates = [b["success_rate"] for b in recent_list]
                recent_mps = [b["messages_per_second"] for b in recent_list]
                
                recent_stats = {
                    "recent_avg_processing_time": sum(recent_processing_times) / len(recent_processing_times),
                    "recent_avg_success_rate": sum(recent_success_rates) / len(recent_success_rates),
                    "recent_avg_messages_per_second": sum(recent_mps) / len(recent_mps),
                    "recent_batches_count": len(recent_list)
                }
            
            return {
                "overall_metrics": {
                    "total_batches": self.metrics.total_batches,
                    "total_messages": self.metrics.total_messages,
                    "avg_batch_size": round(self.metrics.avg_batch_size, 2),
                    "avg_processing_time": round(self.metrics.avg_processing_time, 3),
                    "messages_per_second": round(self.metrics.messages_per_second, 2),
                    "success_rate": round(self.metrics.success_rate, 2)
                },
                "recent_performance": recent_stats,
                "alert_thresholds": self.alert_thresholds,
                "uptime_seconds": round(time.time() - self.metrics.last_reset, 0)
            }
    
    async def reset_metrics(self):
        """Reset das métricas"""
        async with self._lock:
            self.metrics = WebhookMetrics()
            logger.info("📊 Performance metrics reset", category=LogCategory.PERFORMANCE)


# Instância global do monitor
performance_monitor = PerformanceMonitor()
