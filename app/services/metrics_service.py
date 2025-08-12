from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema de Métricas e Observabilidade com Prometheus
Monitoramento completo do WhatsApp Agent para produção
"""
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import logging

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, Info, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Fallback implementations
    class MockMetric:
        def inc(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self

logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Estrutura para dados de métricas"""
    timestamp: datetime
    metric_name: str
    value: float
    labels: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None


class MetricsService:
    """
    Serviço completo de métricas e observabilidade
    
    Features:
    - Métricas Prometheus nativas
    - Fallback para métricas em memória
    - Tracking de performance em tempo real
    - Análise de custos de LLM
    - Monitoramento de conversas ativas
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry
        self.start_time = time.time()
        self.in_memory_metrics = {}
        
        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()
            logger.info("Prometheus metrics inicializadas com sucesso")
        else:
            self._init_fallback_metrics()
            logger.warning("Prometheus não disponível, usando métricas em memória")
    
    def _init_prometheus_metrics(self):
        """Inicializa métricas Prometheus"""
        # Métricas de mensagens
        self.message_counter = Counter(
            'whatsapp_bot_messages_total',
            'Total de mensagens processadas pelo bot',
            ['direction', 'type', 'status', 'strategy', 'user_type'],
            registry=self.registry
        )
        
        # Métricas de tempo de resposta
        self.response_time = Histogram(
            'whatsapp_bot_response_duration_seconds',
            'Tempo de resposta do bot em segundos',
            ['strategy', 'complexity', 'cache_hit'],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0, float('inf')),
            registry=self.registry
        )
        
        # Conversas ativas
        self.active_conversations = Gauge(
            'whatsapp_bot_active_conversations',
            'Número de conversas ativas',
            ['status'],
            registry=self.registry
        )
        
        # Custos de LLM
        self.llm_cost_tracker = Counter(
            'whatsapp_bot_llm_cost_dollars',
            'Custo total de APIs LLM em dólares',
            ['provider', 'model', 'strategy'],
            registry=self.registry
        )
        
        # Métricas de cache
        self.cache_operations = Counter(
            'whatsapp_bot_cache_operations_total',
            'Operações de cache realizadas',
            ['operation', 'cache_type', 'result'],
            registry=self.registry
        )
        
        # Taxa de erro
        self.error_rate = Counter(
            'whatsapp_bot_errors_total',
            'Total de erros do sistema',
            ['error_type', 'component', 'severity'],
            registry=self.registry
        )
        
        # Lead scoring métricas
        self.lead_scores = Histogram(
            'whatsapp_bot_lead_scores',
            'Distribuição de lead scores',
            ['category', 'customer_type'],
            buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            registry=self.registry
        )
        
        # Estratégias de processamento
        self.strategy_selection = Counter(
            'whatsapp_bot_strategy_selections_total',
            'Seleções de estratégia de processamento',
            ['strategy', 'reason', 'success'],
            registry=self.registry
        )
        
        # Performance do sistema
        self.system_performance = Summary(
            'whatsapp_bot_system_performance_seconds',
            'Performance geral do sistema',
            ['component'],
            registry=self.registry
        )
        
        # Informações do sistema
        self.system_info = Info(
            'whatsapp_bot_system_info',
            'Informações do sistema',
            registry=self.registry
        )
        
        # Configura informações do sistema
        self.system_info.info({
            'version': '2.0.0',
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'features': 'strategy_management,cache_system,prometheus_metrics',
            'environment': 'production'
        })
    
    def _init_fallback_metrics(self):
        """Inicializa métricas fallback em memória"""
        self.message_counter = MockMetric()
        self.response_time = MockMetric()
        self.active_conversations = MockMetric()
        self.llm_cost_tracker = MockMetric()
        self.cache_operations = MockMetric()
        self.error_rate = MockMetric()
        self.lead_scores = MockMetric()
        self.strategy_selection = MockMetric()
        self.system_performance = MockMetric()
        self.system_info = MockMetric()
        
        # Métricas em memória para relatórios
        self.in_memory_metrics = {
            'messages': {'total': 0, 'by_type': {}, 'by_status': {}},
            'response_times': [],
            'active_conversations': 0,
            'llm_costs': 0.0,
            'cache_operations': {'hits': 0, 'misses': 0, 'sets': 0},
            'errors': {'total': 0, 'by_type': {}},
            'lead_scores': [],
            'strategies': {}
        }
    
    # === TRACKING DE MENSAGENS ===
    
    def track_message(self, direction: str, message_type: str, status: str, 
                     strategy: str = "unknown", user_type: str = "standard"):
        """Trackeia processamento de mensagens"""
        try:
            self.message_counter.labels(
                direction=direction,
                type=message_type,
                status=status,
                strategy=strategy,
                user_type=user_type
            ).inc()
            
            # Fallback para métricas em memória
            if not PROMETHEUS_AVAILABLE:
                self.in_memory_metrics['messages']['total'] += 1
                self.in_memory_metrics['messages']['by_status'][status] = \
                    self.in_memory_metrics['messages']['by_status'].get(status, 0) + 1
                    
            logger.debug(f"Mensagem tracked: {direction}/{message_type}/{status}")
            
        except Exception as e:
            logger.error(f"Erro ao trackear mensagem: {e}")
    
    @contextmanager
    def track_response_time(self, strategy: str, complexity: str = "normal", 
                           cache_hit: bool = False):
        """Context manager para tracking de tempo de resposta"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            try:
                self.response_time.labels(
                    strategy=strategy,
                    complexity=complexity,
                    cache_hit="hit" if cache_hit else "miss"
                ).observe(duration)
                
                if not PROMETHEUS_AVAILABLE:
                    self.in_memory_metrics['response_times'].append(duration)
                    
            except Exception as e:
                logger.error(f"Erro ao trackear tempo de resposta: {e}")
    
    # === CONVERSAS ATIVAS ===
    
    def update_active_conversations(self, count: int, status: str = "active"):
        """Atualiza contador de conversas ativas"""
        try:
            self.active_conversations.labels(status=status).set(count)
            
            if not PROMETHEUS_AVAILABLE:
                self.in_memory_metrics['active_conversations'] = count
                
        except Exception as e:
            logger.error(f"Erro ao atualizar conversas ativas: {e}")
    
    def increment_active_conversations(self, status: str = "active"):
        """Incrementa conversas ativas"""
        try:
            self.active_conversations.labels(status=status).inc()
            
            if not PROMETHEUS_AVAILABLE:
                self.in_memory_metrics['active_conversations'] += 1
                
        except Exception as e:
            logger.error(f"Erro ao incrementar conversas ativas: {e}")
    
    def decrement_active_conversations(self, status: str = "active"):
        """Decrementa conversas ativas"""
        try:
            self.active_conversations.labels(status=status).dec()
            
            if not PROMETHEUS_AVAILABLE:
                self.in_memory_metrics['active_conversations'] = max(0, 
                    self.in_memory_metrics['active_conversations'] - 1)
                
        except Exception as e:
            logger.error(f"Erro ao decrementar conversas ativas: {e}")
    
    # === CUSTOS DE LLM ===
    
    def track_llm_cost(self, cost: float, provider: str, model: str, strategy: str):
        """Trackeia custos de API LLM"""
        try:
            self.llm_cost_tracker.labels(
                provider=provider,
                model=model,
                strategy=strategy
            ).inc(cost)
            
            if not PROMETHEUS_AVAILABLE:
                self.in_memory_metrics['llm_costs'] += cost
                
            logger.debug(f"Custo LLM tracked: ${cost:.4f} ({provider}/{model})")
            
        except Exception as e:
            logger.error(f"Erro ao trackear custo LLM: {e}")
    
    # === CACHE OPERATIONS ===
    
    def track_cache_operation(self, operation: str, cache_type: str, result: str):
        """Trackeia operações de cache"""
        try:
            self.cache_operations.labels(
                operation=operation,
                cache_type=cache_type,
                result=result
            ).inc()
            
            if not PROMETHEUS_AVAILABLE:
                self.in_memory_metrics['cache_operations'][result] += 1
                
        except Exception as e:
            logger.error(f"Erro ao trackear operação de cache: {e}")
    
    # === ERROS ===
    
    def track_error(self, error_type: str, component: str, severity: str = "error"):
        """Trackeia erros do sistema"""
        try:
            self.error_rate.labels(
                error_type=error_type,
                component=component,
                severity=severity
            ).inc()
            
            if not PROMETHEUS_AVAILABLE:
                self.in_memory_metrics['errors']['total'] += 1
                self.in_memory_metrics['errors']['by_type'][error_type] = \
                    self.in_memory_metrics['errors']['by_type'].get(error_type, 0) + 1
                    
            logger.warning(f"Erro tracked: {error_type} em {component} ({severity})")
            
        except Exception as e:
            logger.error(f"Erro ao trackear erro: {e}")
    
    # === LEAD SCORING ===
    
    def track_lead_score(self, score: float, category: str, customer_type: str):
        """Trackeia lead scores"""
        try:
            self.lead_scores.labels(
                category=category,
                customer_type=customer_type
            ).observe(score)
            
            if not PROMETHEUS_AVAILABLE:
                self.in_memory_metrics['lead_scores'].append({
                    'score': score,
                    'category': category,
                    'customer_type': customer_type
                })
                
        except Exception as e:
            logger.error(f"Erro ao trackear lead score: {e}")
    
    # === ESTRATÉGIAS ===
    
    def track_strategy_selection(self, strategy: str, reason: str, success: bool):
        """Trackeia seleção de estratégias"""
        try:
            self.strategy_selection.labels(
                strategy=strategy,
                reason=reason,
                success="true" if success else "false"
            ).inc()
            
            if not PROMETHEUS_AVAILABLE:
                if strategy not in self.in_memory_metrics['strategies']:
                    self.in_memory_metrics['strategies'][strategy] = 0
                self.in_memory_metrics['strategies'][strategy] += 1
                
        except Exception as e:
            logger.error(f"Erro ao trackear seleção de estratégia: {e}")
    
    # === PERFORMANCE ===
    
    @contextmanager
    def track_component_performance(self, component: str):
        """Context manager para tracking de performance de componentes"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            try:
                self.system_performance.labels(component=component).observe(duration)
            except Exception as e:
                logger.error(f"Erro ao trackear performance de {component}: {e}")
    
    # === RELATÓRIOS ===
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo de todas as métricas"""
        uptime = time.time() - self.start_time
        
        summary = {
            "system": {
                "uptime_seconds": uptime,
                "uptime_hours": uptime / 3600,
                "prometheus_available": PROMETHEUS_AVAILABLE,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        if PROMETHEUS_AVAILABLE:
            summary["metrics_backend"] = "prometheus"
            summary["registry_available"] = self.registry is not None
        else:
            summary["metrics_backend"] = "in_memory"
            summary["metrics_data"] = self.in_memory_metrics
            
            # Cálculos para métricas in-memory
            if self.in_memory_metrics['response_times']:
                avg_response_time = sum(self.in_memory_metrics['response_times']) / len(self.in_memory_metrics['response_times'])
                summary["calculated_metrics"] = {
                    "average_response_time": avg_response_time,
                    "total_responses": len(self.in_memory_metrics['response_times']),
                    "total_llm_cost": self.in_memory_metrics['llm_costs']
                }
        
        return summary
    
    def export_prometheus_metrics(self) -> str:
        """Exporta métricas no formato Prometheus"""
        if PROMETHEUS_AVAILABLE and self.registry:
            return generate_latest(self.registry).decode('utf-8')
        else:
            return "# Prometheus não disponível\n"
    
    def health_check(self) -> Dict[str, Any]:
        """Health check do sistema de métricas"""
        return {
            "status": "healthy" if PROMETHEUS_AVAILABLE else "degraded",
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "uptime_seconds": time.time() - self.start_time,
            "metrics_count": len(self.in_memory_metrics) if not PROMETHEUS_AVAILABLE else "prometheus_managed",
            "last_check": datetime.now().isoformat()
        }


# Instância global do serviço de métricas
metrics_service = MetricsService()
