"""
Gerenciador Principal de Estratégias LLM - Versão Limpa
Sistema limpo e extensível para gerenciar diferentes abordagens de processamento
"""
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from .strategy_base import (
    BaseStrategy, MessageContext, StrategyResponse, StrategySelector
)
from .strategy_implementations import (
    SimpleLLMStrategy, AdvancedLLMStrategy, CrewAIStrategy, HybridStrategy
)
from .lead_scoring import LeadScoringService
from .cache_service import cache_service

logger = logging.getLogger(__name__)


class StrategyManager:
    """
    Gerenciador centralizado de estratégias LLM
    
    Características:
    - Seleção inteligente de estratégia
    - Métricas de performance
    - Sistema de fallback robusto
    - Extensibilidade para novas estratégias
    """
    
    def __init__(self):
        # Inicializar estratégias disponíveis
        self.strategies: Dict[str, BaseStrategy] = {
            'simple': SimpleLLMStrategy(),
            'advanced': AdvancedLLMStrategy(),
            'crew': CrewAIStrategy(),
            'hybrid': HybridStrategy()
        }
        
        # Seletor de estratégias
        self.selector = StrategySelector()
        
        # Registrar estratégias no seletor
        for name, strategy in self.strategies.items():
            self.selector.register_strategy(name, strategy)
        
        # Cache service
        self.cache = cache_service
        
        # Lead scoring service
        self.lead_scoring = LeadScoringService()
        
        # Métricas e estatísticas
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "strategy_usage": {}
        }
        self.start_time = time.time()
        
        # Configurações
        self.config = {
            "cache_enabled": True,
            "fallback_strategy": "hybrid",
            "max_response_time": 30.0,
            "enable_metrics": True
        }
        
        logger.info(f"StrategyManager inicializado com {len(self.strategies)} estratégias")
    
    async def process(self, message: str, user_id: str, phone: str) -> StrategyResponse:
        """
        Processa mensagem usando a melhor estratégia disponível
        """
        start_time = time.time()
        
        try:
            # Incrementa contador de requisições
            self.metrics["total_requests"] += 1
            
            # Constrói contexto da mensagem
            context = await self._build_context(message, user_id, phone)
            
            # Seleciona estratégia apropriada
            selected = self.selector.select_strategy(context)
            
            if not selected:
                # Fallback se nenhuma estratégia disponível
                self.metrics["failed_requests"] += 1
                return StrategyResponse(
                    response="Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes.",
                    confidence=0.0,
                    strategy_used="fallback",
                    processing_time=time.time() - start_time
                )
            
            strategy_name, strategy = selected
            
            # Executa estratégia selecionada
            result = await strategy.execute(context)
            
            # Registra métricas de sucesso
            self.metrics["successful_requests"] += 1
            response_time = time.time() - start_time
            self.metrics["response_times"].append(response_time)
            
            # Atualiza uso de estratégias
            if strategy_name not in self.metrics["strategy_usage"]:
                self.metrics["strategy_usage"][strategy_name] = 0
            self.metrics["strategy_usage"][strategy_name] += 1
            
            return result
            
        except Exception as e:
            # Registra erro
            self.metrics["failed_requests"] += 1
            logger.error(f"Erro no processamento: {e}")
            
            return StrategyResponse(
                response="Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes.",
                confidence=0.0,
                strategy_used="error_fallback",
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )
    
    async def _build_context(self, message: str, user_id: str, phone: str) -> MessageContext:
        """
        Constrói contexto completo da mensagem
        """
        try:
            # Calcular lead score (com cache)
            cached_lead_score = await cache_service.get_cached_lead_score(user_id, message)
            
            if cached_lead_score:
                lead_score = cached_lead_score.get("total_score", 0.5)
                confidence = cached_lead_score.get("confidence", 0.5)
                customer_value = cached_lead_score.get("customer_value", "standard")
                logger.info(f"Lead score em cache para {user_id}: {lead_score}")
            else:
                # Calcular novo lead score
                try:
                    lead_score_result = await self.lead_scoring.calculate_score(
                        message=message,
                        user_id=user_id,
                        phone_number=phone,
                        conversation_history=[]  # TODO: implementar histórico
                    )
                    
                    # Extrair valores do lead score com validação
                    if hasattr(lead_score_result, 'total_score'):
                        lead_score = float(lead_score_result.total_score)
                        confidence = float(getattr(lead_score_result, 'confidence', 0.5))
                        customer_value = "vip" if lead_score >= 80 else "standard"
                        
                        # Cachear resultado do lead score
                        await cache_service.cache_lead_score(
                            user_id=user_id,
                            message=message,
                            lead_score_data={
                                "total_score": lead_score,
                                "confidence": confidence,
                                "customer_value": customer_value,
                                "category": getattr(lead_score_result, 'category', 'unknown').value if hasattr(getattr(lead_score_result, 'category', None), 'value') else str(getattr(lead_score_result, 'category', 'unknown')),
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                    else:
                        # Valores padrão se lead scoring falhar
                        lead_score = 0.5
                        confidence = 0.5
                        customer_value = "standard"
                        logger.warning(f"Lead scoring retornou formato inválido para {user_id}")
                        
                except Exception as e:
                    logger.error(f"Erro no lead scoring para {user_id}: {e}")
                    lead_score = 0.5
                    confidence = 0.5
                    customer_value = "standard"
            
            # Criar contexto da mensagem
            context = MessageContext(
                message=message,
                user_id=user_id,
                phone=phone,
                timestamp=datetime.now(),
                conversation_history=[],  # TODO: implementar histórico
                user_context={
                    "lead_score": lead_score,
                    "confidence": confidence,
                    "customer_value": customer_value
                }
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Erro ao construir contexto: {e}")
            # Contexto padrão em caso de erro
            return MessageContext(
                message=message,
                user_id=user_id,
                phone=phone,
                timestamp=datetime.now(),
                conversation_history=[],
                user_context={"lead_score": 0.5, "confidence": 0.5, "customer_value": "standard"}
            )
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do sistema"""
        total_requests = self.metrics.get("total_requests", 0)
        successful_requests = self.metrics.get("successful_requests", 0)
        failed_requests = self.metrics.get("failed_requests", 0)
        
        # Calcula métricas
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        average_response_time = (
            sum(self.metrics.get("response_times", [])) / 
            len(self.metrics.get("response_times", [])) 
            if self.metrics.get("response_times") else 0
        )
        
        # Estatísticas do cache
        cache_stats = {}
        if hasattr(self, 'cache') and self.cache:
            cache_stats = self.cache.get_stats()
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate,
            "average_response_time": average_response_time,
            "strategy_usage": self.metrics.get("strategy_usage", {}),
            "cache_stats": cache_stats,
            "uptime_seconds": time.time() - self.start_time,
            "strategies_available": list(self.strategies.keys()),
            "configuration": self.config
        }
    
    def reset_stats(self):
        """Reseta todas as estatísticas"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "strategy_usage": {}
        }
        self.start_time = time.time()
        logger.info("Estatísticas resetadas")


# Instância global do gerenciador
strategy_manager = StrategyManager()
