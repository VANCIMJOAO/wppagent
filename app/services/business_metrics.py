"""
Sistema de Métricas de Negócio Centralizadas
===========================================

Centraliza todas as métricas de negócio importantes:
- Conversões e vendas
- Engagement de usuários
- Performance de atendimento
- Análise de leads
- ROI e custos
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
from pathlib import Path
from collections import defaultdict, deque
import statistics

from app.services.production_logger import business_logger, log_business_event
from app.utils.logger import get_logger

logger = get_logger(__name__)

class MetricType(Enum):
    """Tipos de métricas de negócio"""
    CONVERSATION = "conversation"
    LEAD = "lead"
    BOOKING = "booking"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    COST = "cost"
    SATISFACTION = "satisfaction"


class MetricPeriod(Enum):
    """Períodos para agregação de métricas"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


@dataclass
class BusinessMetric:
    """Estrutura de uma métrica de negócio"""
    metric_type: MetricType
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any]
    tags: List[str]
    period: MetricPeriod = MetricPeriod.DAY
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        return {
            'metric_type': self.metric_type.value,
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'tags': self.tags,
            'period': self.period.value
        }


class BusinessMetricsCollector:
    """
    Coletor centralizado de métricas de negócio
    """
    
    def __init__(self, storage_path: str = "logs/business_metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Cache de métricas em memória para agregações rápidas
        self.metrics_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Contadores em tempo real
        self.real_time_counters: Dict[str, float] = defaultdict(float)
        
        # Métricas agregadas por período
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Inicializar métricas base
        self._initialize_base_metrics()
    
    def _initialize_base_metrics(self):
        """Inicializar métricas base do sistema"""
        base_metrics = [
            'total_conversations',
            'active_conversations', 
            'completed_conversations',
            'conversion_rate',
            'average_response_time',
            'user_satisfaction',
            'lead_score_average',
            'booking_conversion_rate',
            'revenue_total',
            'cost_per_conversation',
            'messages_per_conversation',
            'handoff_rate'
        ]
        
        for metric in base_metrics:
            self.real_time_counters[metric] = 0.0
    
    async def record_metric(self, metric: BusinessMetric):
        """
        Registrar uma nova métrica
        """
        try:
            # Adicionar ao cache
            cache_key = f"{metric.metric_type.value}_{metric.name}"
            self.metrics_cache[cache_key].append(metric)
            
            # Atualizar contador em tempo real
            self.real_time_counters[metric.name] = metric.value
            
            # Log do evento
            log_business_event(f"metric_recorded_{metric.metric_type.value}", {
                'metric_name': metric.name,
                'value': metric.value,
                'unit': metric.unit,
                'tags': metric.tags
            })
            
            # Salvar no arquivo
            await self._save_metric_to_file(metric)
            
            # Atualizar agregações
            await self._update_aggregations(metric)
            
        except Exception as e:
            business_logger.error(f"Error recording metric: {e}", exc_info=True)
    
    async def _save_metric_to_file(self, metric: BusinessMetric):
        """Salvar métrica em arquivo JSON"""
        try:
            date_str = metric.timestamp.strftime("%Y%m%d")
            file_path = self.storage_path / f"metrics_{date_str}.jsonl"
            
            async with aiofiles.open(file_path, mode='a', encoding='utf-8') as f:
                await f.write(json.dumps(metric.to_dict(), ensure_ascii=False) + '\n')
                
        except Exception as e:
            business_logger.error(f"Error saving metric to file: {e}", exc_info=True)
    
    async def _update_aggregations(self, metric: BusinessMetric):
        """Atualizar agregações de métricas"""
        try:
            # Chaves para agregação
            hour_key = metric.timestamp.strftime("%Y%m%d_%H")
            day_key = metric.timestamp.strftime("%Y%m%d")
            week_key = metric.timestamp.strftime("%Y%W")
            month_key = metric.timestamp.strftime("%Y%m")
            
            periods = {
                MetricPeriod.HOUR: hour_key,
                MetricPeriod.DAY: day_key,
                MetricPeriod.WEEK: week_key,
                MetricPeriod.MONTH: month_key
            }
            
            for period, key in periods.items():
                agg_key = f"{metric.metric_type.value}_{metric.name}_{period.value}_{key}"
                
                if agg_key not in self.aggregated_metrics:
                    self.aggregated_metrics[agg_key] = {
                        'count': 0,
                        'sum': 0.0,
                        'min': float('inf'),
                        'max': float('-inf'),
                        'values': []
                    }
                
                agg = self.aggregated_metrics[agg_key]
                agg['count'] += 1
                agg['sum'] += metric.value
                agg['min'] = min(agg['min'], metric.value)
                agg['max'] = max(agg['max'], metric.value)
                agg['values'].append(metric.value)
                
                # Manter apenas últimos 100 valores para cálculos estatísticos
                if len(agg['values']) > 100:
                    agg['values'] = agg['values'][-100:]
                    
        except Exception as e:
            business_logger.error(f"Error updating aggregations: {e}", exc_info=True)
    
    # === MÉTRICAS DE CONVERSAÇÃO ===
    
    async def record_conversation_started(self, user_id: str, channel: str = "whatsapp"):
        """Registrar início de conversa"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.CONVERSATION,
            name="conversation_started",
            value=1.0,
            unit="count",
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": user_id, "channel": channel},
            tags=["conversation", "start", channel]
        ))
        
        self.real_time_counters['total_conversations'] += 1
        self.real_time_counters['active_conversations'] += 1
    
    async def record_conversation_completed(self, user_id: str, duration_minutes: float, 
                                          satisfaction_score: Optional[float] = None):
        """Registrar conversa concluída"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.CONVERSATION,
            name="conversation_completed",
            value=1.0,
            unit="count",
            timestamp=datetime.now(timezone.utc),
            metadata={
                "user_id": user_id, 
                "duration_minutes": duration_minutes,
                "satisfaction_score": satisfaction_score
            },
            tags=["conversation", "completed"]
        ))
        
        # Registrar duração
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.PERFORMANCE,
            name="conversation_duration",
            value=duration_minutes,
            unit="minutes",
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": user_id},
            tags=["performance", "duration"]
        ))
        
        self.real_time_counters['completed_conversations'] += 1
        self.real_time_counters['active_conversations'] = max(0, self.real_time_counters['active_conversations'] - 1)
        
        if satisfaction_score:
            await self.record_satisfaction_score(satisfaction_score)
    
    async def record_conversation_handoff(self, user_id: str, reason: str):
        """Registrar transferência para humano"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.CONVERSATION,
            name="conversation_handoff",
            value=1.0,
            unit="count",
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": user_id, "reason": reason},
            tags=["conversation", "handoff", reason]
        ))
    
    # === MÉTRICAS DE LEAD ===
    
    async def record_lead_generated(self, user_id: str, lead_score: float, source: str):
        """Registrar lead gerado"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.LEAD,
            name="lead_generated",
            value=1.0,
            unit="count",
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": user_id, "lead_score": lead_score, "source": source},
            tags=["lead", "generated", source]
        ))
        
        # Registrar score do lead
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.LEAD,
            name="lead_score",
            value=lead_score,
            unit="score",
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": user_id, "source": source},
            tags=["lead", "score"]
        ))
    
    async def record_lead_qualified(self, user_id: str, qualification_criteria: List[str]):
        """Registrar lead qualificado"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.LEAD,
            name="lead_qualified",
            value=1.0,
            unit="count",
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": user_id, "criteria": qualification_criteria},
            tags=["lead", "qualified"] + qualification_criteria
        ))
    
    # === MÉTRICAS DE AGENDAMENTO ===
    
    async def record_booking_requested(self, user_id: str, service_type: str):
        """Registrar solicitação de agendamento"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.BOOKING,
            name="booking_requested",
            value=1.0,
            unit="count",
            timestamp=datetime.now(timezone.utc),
            metadata={"user_id": user_id, "service_type": service_type},
            tags=["booking", "requested", service_type]
        ))
    
    async def record_booking_completed(self, user_id: str, service_type: str, 
                                     revenue: float, booking_id: str):
        """Registrar agendamento concluído"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.BOOKING,
            name="booking_completed",
            value=1.0,
            unit="count",
            timestamp=datetime.now(timezone.utc),
            metadata={
                "user_id": user_id, 
                "service_type": service_type,
                "revenue": revenue,
                "booking_id": booking_id
            },
            tags=["booking", "completed", service_type]
        ))
        
        # Registrar receita
        await self.record_revenue(revenue, "booking", service_type)
    
    # === MÉTRICAS DE RECEITA ===
    
    async def record_revenue(self, amount: float, source: str, category: str = "general"):
        """Registrar receita"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.REVENUE,
            name="revenue_generated",
            value=amount,
            unit="BRL",
            timestamp=datetime.now(timezone.utc),
            metadata={"source": source, "category": category},
            tags=["revenue", source, category]
        ))
        
        self.real_time_counters['revenue_total'] += amount
    
    # === MÉTRICAS DE PERFORMANCE ===
    
    async def record_response_time(self, response_time_ms: float, component: str):
        """Registrar tempo de resposta"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.PERFORMANCE,
            name="response_time",
            value=response_time_ms,
            unit="milliseconds",
            timestamp=datetime.now(timezone.utc),
            metadata={"component": component},
            tags=["performance", "response_time", component]
        ))
    
    async def record_api_call_cost(self, cost: float, api_name: str, tokens_used: int = 0):
        """Registrar custo de chamada API"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.COST,
            name="api_cost",
            value=cost,
            unit="USD",
            timestamp=datetime.now(timezone.utc),
            metadata={"api_name": api_name, "tokens_used": tokens_used},
            tags=["cost", "api", api_name]
        ))
    
    async def record_satisfaction_score(self, score: float):
        """Registrar score de satisfação"""
        await self.record_metric(BusinessMetric(
            metric_type=MetricType.SATISFACTION,
            name="satisfaction_score",
            value=score,
            unit="score",
            timestamp=datetime.now(timezone.utc),
            metadata={},
            tags=["satisfaction", "user_feedback"]
        ))
    
    # === RELATÓRIOS E ANÁLISES ===
    
    async def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Obter dados para dashboard em tempo real"""
        try:
            # Calcular métricas derivadas
            total_conv = self.real_time_counters.get('total_conversations', 0)
            completed_conv = self.real_time_counters.get('completed_conversations', 0)
            conversion_rate = (completed_conv / total_conv * 100) if total_conv > 0 else 0
            
            # Buscar últimas métricas do cache
            recent_response_times = []
            recent_satisfaction = []
            recent_lead_scores = []
            
            for cache_key, metrics in self.metrics_cache.items():
                if 'response_time' in cache_key:
                    recent_response_times.extend([m.value for m in list(metrics)[-10:]])
                elif 'satisfaction_score' in cache_key:
                    recent_satisfaction.extend([m.value for m in list(metrics)[-10:]])
                elif 'lead_score' in cache_key:
                    recent_lead_scores.extend([m.value for m in list(metrics)[-10:]])
            
            dashboard = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'conversations': {
                    'total': self.real_time_counters.get('total_conversations', 0),
                    'active': self.real_time_counters.get('active_conversations', 0),
                    'completed': self.real_time_counters.get('completed_conversations', 0),
                    'conversion_rate': round(conversion_rate, 2)
                },
                'performance': {
                    'avg_response_time': round(statistics.mean(recent_response_times), 2) if recent_response_times else 0,
                    'satisfaction_avg': round(statistics.mean(recent_satisfaction), 2) if recent_satisfaction else 0
                },
                'business': {
                    'total_revenue': self.real_time_counters.get('revenue_total', 0),
                    'avg_lead_score': round(statistics.mean(recent_lead_scores), 2) if recent_lead_scores else 0
                },
                'system': {
                    'metrics_collected': sum(len(cache) for cache in self.metrics_cache.values()),
                    'cache_size': len(self.metrics_cache)
                }
            }
            
            return dashboard
            
        except Exception as e:
            business_logger.error(f"Error generating dashboard: {e}", exc_info=True)
            return {}
    
    async def get_period_report(self, period: MetricPeriod, 
                              start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Gerar relatório por período"""
        try:
            report = {
                'period': period.value,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': {}
            }
            
            # Buscar métricas agregadas para o período
            for agg_key, agg_data in self.aggregated_metrics.items():
                if period.value in agg_key:
                    metric_name = agg_key.split('_')[2]  # Extrair nome da métrica
                    
                    if agg_data['count'] > 0:
                        report['metrics'][metric_name] = {
                            'count': agg_data['count'],
                            'total': agg_data['sum'],
                            'average': agg_data['sum'] / agg_data['count'],
                            'min': agg_data['min'],
                            'max': agg_data['max'],
                            'median': statistics.median(agg_data['values']) if agg_data['values'] else 0
                        }
            
            return report
            
        except Exception as e:
            business_logger.error(f"Error generating period report: {e}", exc_info=True)
            return {}
    
    async def export_metrics(self, start_date: datetime, end_date: datetime) -> str:
        """Exportar métricas para arquivo CSV"""
        try:
            export_data = []
            
            # Buscar todos os arquivos de métricas no período
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_str = current_date.strftime("%Y%m%d")
                file_path = self.storage_path / f"metrics_{date_str}.jsonl"
                
                if file_path.exists():
                    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                        async for line in f:
                            if line.strip():
                                metric_data = json.loads(line.strip())
                                metric_time = datetime.fromisoformat(metric_data['timestamp'])
                                
                                if start_date <= metric_time <= end_date:
                                    export_data.append(metric_data)
                
                current_date += timedelta(days=1)
            
            # Salvar arquivo de export
            export_file = self.storage_path / f"export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
            
            async with aiofiles.open(export_file, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(export_data, ensure_ascii=False, indent=2))
            
            return str(export_file)
            
        except Exception as e:
            business_logger.error(f"Error exporting metrics: {e}", exc_info=True)
            return ""


# Instância global do coletor de métricas
metrics_collector = BusinessMetricsCollector()


# Funções de conveniência para uso direto
async def track_conversation_start(user_id: str, channel: str = "whatsapp"):
    """Função de conveniência para tracking de início de conversa"""
    await metrics_collector.record_conversation_started(user_id, channel)

async def track_conversation_end(user_id: str, duration_minutes: float, satisfaction: Optional[float] = None):
    """Função de conveniência para tracking de fim de conversa"""
    await metrics_collector.record_conversation_completed(user_id, duration_minutes, satisfaction)

async def track_lead_conversion(user_id: str, lead_score: float, source: str = "whatsapp"):
    """Função de conveniência para tracking de conversão de lead"""
    await metrics_collector.record_lead_generated(user_id, lead_score, source)

async def track_booking_success(user_id: str, service_type: str, revenue: float, booking_id: str):
    """Função de conveniência para tracking de agendamento bem-sucedido"""
    await metrics_collector.record_booking_completed(user_id, service_type, revenue, booking_id)

async def track_api_cost(cost: float, api_name: str, tokens: int = 0):
    """Função de conveniência para tracking de custos de API"""
    await metrics_collector.record_api_call_cost(cost, api_name, tokens)
