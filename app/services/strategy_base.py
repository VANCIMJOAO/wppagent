from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema de Gerenciamento de Estratégias LLM
Implementação limpa baseada no padrão Strategy
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Tipos de estratégias disponíveis"""
    SIMPLE = "simple"
    ADVANCED = "advanced"
    CREW = "crew"
    HYBRID = "hybrid"


@dataclass
class MessageContext:
    """Contexto da mensagem para processamento"""
    user_id: str
    conversation_id: str
    message: str
    message_type: str = "text"
    lead_score: float = 0.0
    confidence: float = 0.0
    complexity: str = "medium"
    customer_value: str = "standard"
    conversation_state: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StrategyResponse:
    """Resposta padronizada das estratégias"""
    success: bool
    response: str
    strategy_used: str
    processing_time: float
    intent: Optional[str] = None
    confidence: float = 0.0
    interactive_buttons: Optional[List[Dict[str, str]]] = None
    suggested_actions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.suggested_actions is None:
            self.suggested_actions = []


class BaseStrategy(ABC):
    """Interface base para todas as estratégias"""
    
    def __init__(self, name: str):
        self.name = name
        self.performance_metrics = {
            "requests": 0,
            "success_rate": 0.0,
            "avg_time": 0.0,
            "total_time": 0.0,
            "successes": 0
        }
    
    @abstractmethod
    async def execute(self, context: MessageContext) -> StrategyResponse:
        """Executa a estratégia com o contexto fornecido"""
        pass
    
    @abstractmethod
    def can_handle(self, context: MessageContext) -> bool:
        """Verifica se a estratégia pode processar o contexto"""
        pass
    
    @abstractmethod
    def get_priority(self, context: MessageContext) -> int:
        """Retorna a prioridade da estratégia (0-100)"""
        pass
    
    def update_metrics(self, processing_time: float, success: bool):
        """Atualiza métricas de performance"""
        self.performance_metrics["requests"] += 1
        self.performance_metrics["total_time"] += processing_time
        
        if success:
            self.performance_metrics["successes"] += 1
        
        self.performance_metrics["success_rate"] = (
            self.performance_metrics["successes"] / 
            self.performance_metrics["requests"]
        )
        
        self.performance_metrics["avg_time"] = (
            self.performance_metrics["total_time"] / 
            self.performance_metrics["requests"]
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas da estratégia"""
        return {
            "name": self.name,
            **self.performance_metrics
        }


class StrategySelector:
    """Seletor inteligente de estratégias"""
    
    def __init__(self):
        self.rules = [
            # Regras de negócio para seleção de estratégia
            self._check_high_value_customer,
            self._check_complex_query,
            self._check_simple_query,
            self._check_sales_opportunity,
            self._check_scheduling_request,
            self._check_default_strategy
        ]
    
    def select_strategy(self, context: MessageContext, 
                       available_strategies: List[BaseStrategy]) -> BaseStrategy:
        """Seleciona a melhor estratégia baseada no contexto"""
        
        # Aplicar regras de negócio
        for rule in self.rules:
            strategy_type = rule(context)
            if strategy_type:
                # Encontrar estratégia correspondente
                for strategy in available_strategies:
                    if (strategy.name.lower() == strategy_type.value and 
                        strategy.can_handle(context)):
                        return strategy
        
        # Fallback: selecionar por prioridade
        valid_strategies = [s for s in available_strategies if s.can_handle(context)]
        if valid_strategies:
            return max(valid_strategies, key=lambda s: s.get_priority(context))
        
        # Fallback final: primeira estratégia disponível
        return available_strategies[0] if available_strategies else None
    
    def _check_high_value_customer(self, context: MessageContext) -> Optional[StrategyType]:
        """Clientes de alto valor usam CrewAI"""
        if context.lead_score >= 80 or context.customer_value == "vip":
            return StrategyType.CREW
        return None
    
    def _check_complex_query(self, context: MessageContext) -> Optional[StrategyType]:
        """Queries complexas usam estratégia híbrida ou crew"""
        complex_keywords = [
            "problema", "reclamação", "cancelar", "reagendar", "urgente",
            "suporte", "help", "ajuda", "não funciona", "bug"
        ]
        
        if any(keyword in context.message.lower() for keyword in complex_keywords):
            if context.lead_score >= 50:
                return StrategyType.CREW
            else:
                return StrategyType.HYBRID
        return None
    
    def _check_simple_query(self, context: MessageContext) -> Optional[StrategyType]:
        """Queries muito simples usam LLM avançado"""
        word_count = len(context.message.split())
        
        if (word_count <= 3 and 
            context.lead_score < 40 and
            context.complexity == "low"):
            return StrategyType.ADVANCED
        return None
    
    def _check_sales_opportunity(self, context: MessageContext) -> Optional[StrategyType]:
        """Oportunidades de venda usam CrewAI"""
        sales_keywords = [
            "preço", "promoção", "desconto", "orçamento", "comprar",
            "contratar", "valor", "quanto custa", "combo"
        ]
        
        if any(keyword in context.message.lower() for keyword in sales_keywords):
            return StrategyType.CREW
        return None
    
    def _check_scheduling_request(self, context: MessageContext) -> Optional[StrategyType]:
        """Pedidos de agendamento usam estratégia específica"""
        scheduling_keywords = [
            "agendar", "marcar", "horário", "disponibilidade",
            "consulta", "atendimento", "reunião"
        ]
        
        if any(keyword in context.message.lower() for keyword in scheduling_keywords):
            if context.lead_score >= 60:
                return StrategyType.CREW
            else:
                return StrategyType.HYBRID
        return None
    
    def _check_default_strategy(self, context: MessageContext) -> Optional[StrategyType]:
        """Estratégia padrão baseada no lead score"""
        if context.lead_score >= 70:
            return StrategyType.CREW
        elif context.lead_score >= 40:
            return StrategyType.HYBRID
        else:
            return StrategyType.ADVANCED
