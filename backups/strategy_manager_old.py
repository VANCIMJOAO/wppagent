"""
Gerenciador Principal de Estratégias LLM
Sistema limpo e extensível para gerenciar diferentes abordagens de processamento
"""
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from .strategy_base import (
    BaseStrategy, MessageContext, StrategyResponse, 
    StrategyType, StrategySelector
)
from .strategy_implementations import (
    SimpleLLMStrategy, AdvancedLLMStrategy, 
    CrewAIStrategy, HybridStrategy
)
from .lead_scoring import lead_scoring_service
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
        
        # Cache service
        self.cache = cache_service
        
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
            "enable_fallback": True,
            "max_retries": 2,
            "fallback_strategy": "advanced",  # Estratégia padrão em caso de erro
            "performance_monitoring": True,
            "cache_enabled": True,  # Cache de respostas habilitado
            "cache_ttl": 3600      # TTL padrão para cache de respostas
        }
        
        # Métricas globais
        self.global_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_processing_time": 0.0,
            "strategy_usage": {name: 0 for name in self.strategies.keys()}
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
        Processa mensagem usando a melhor estratégia disponível
        
        Args:
            user_id: ID do usuário
            conversation_id: ID da conversa
            message: Mensagem do cliente
            message_type: Tipo da mensagem
            additional_context: Contexto adicional opcional
            
        Returns:
            Resposta processada pela estratégia selecionada
        """
        start_time = datetime.now()
        
        try:
            # 1. Verificar cache primeiro (se habilitado)
            if self.config.get("cache_enabled", True):
                cached_response = await cache_service.get_cached_response(
                    message=message,
                    user_id=user_id,
                    context=additional_context
                )
                
                if cached_response:
                    processing_time = (datetime.now() - start_time).total_seconds()
                    logger.info(f"Cache HIT: Resposta para '{message[:30]}...' encontrada em cache")
                    
                    return StrategyResponse(
                        success=True,
                        response=cached_response,
                        strategy_used="cache",
                        processing_time=processing_time,
                        metadata={
                            "cache_hit": True,
                            "original_message": message[:50]
                        }
                    )
            
            # 2. Analisar contexto da mensagem
            context = await self._build_context(
                user_id, conversation_id, message, 
                message_type, additional_context
            )
            
            # 3. Selecionar estratégia mais adequada
            selected_strategy = self.selector.select_strategy(
                context, list(self.strategies.values())
            )
            
            if not selected_strategy:
                raise ValueError("Nenhuma estratégia disponível para processar a mensagem")
            
            logger.info(f"Estratégia selecionada: {selected_strategy.name} para mensagem: {message[:50]}...")
            
            # 4. Processar com a estratégia selecionada
            response = await self._execute_with_fallback(selected_strategy, context)
            
            # 5. Cachear resposta bem-sucedida (se habilitado)
            if (response.success and 
                self.config.get("cache_enabled", True) and
                response.strategy_used != "cache"):
                
                await cache_service.cache_response(
                    message=message,
                    user_id=user_id,
                    response=response.response,
                    context=additional_context,
                    custom_ttl=self.config.get("cache_ttl", 3600)
                )
            
            # 6. Atualizar métricas globais
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_global_metrics(selected_strategy.name, processing_time, response.success)
            
            # 7. Enriquecer resposta com informações adicionais
            response.metadata = {
                **(response.metadata or {}),
                "context_analysis": {
                    "lead_score": context.lead_score,
                    "confidence": context.confidence,
                    "complexity": context.complexity,
                    "customer_value": context.customer_value
                },
                "selection_reason": self._get_selection_reason(context, selected_strategy),
                "cache_hit": False
            }
            
            return response
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_global_metrics("error", processing_time, False)
            
            logger.error(f"Erro no StrategyManager: {e}")
            
            # Resposta de emergência
            return StrategyResponse(
                success=False,
                response="Desculpe, ocorreu um erro no sistema. Nossa equipe foi notificada.",
                strategy_used="emergency_fallback",
                processing_time=processing_time,
                metadata={"error": str(e), "emergency_mode": True}
            )
    
    async def _build_context(self, user_id: str, conversation_id: str,
                           message: str, message_type: str,
                           additional_context: Optional[Dict[str, Any]]) -> MessageContext:
        """Constrói contexto completo para análise"""
        
        try:
            # Tentar buscar lead score em cache primeiro
            cached_lead_score = await cache_service.get_cached_lead_score(user_id, message)
            
            if cached_lead_score:
                lead_score = float(cached_lead_score.get("total_score", 50.0))
                confidence = float(cached_lead_score.get("confidence", 0.5))
                customer_value = cached_lead_score.get("customer_value", "standard")
                logger.debug(f"Lead score obtido do cache para {user_id}")
            else:
                # Calcular lead score se não estiver em cache
                lead_score_result = lead_scoring_service.score_lead(
                    message=message,
                    phone=user_id,
                    customer_data=additional_context.get("customer_data") if additional_context else None,
                    context=additional_context or {}
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
                    lead_score = 50.0
                    confidence = 0.5
                    customer_value = "standard"
            
            # Analisar complexidade da mensagem
            complexity = self._assess_message_complexity(message)
            
            return MessageContext(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                message_type=message_type,
                lead_score=lead_score,
                confidence=confidence,
                complexity=complexity,
                customer_value=customer_value,
                metadata=additional_context or {}
            )
            
        except Exception as e:
            logger.warning(f"Erro ao construir contexto: {e}, usando valores padrão")
            
            return MessageContext(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                message_type=message_type,
                lead_score=50.0,
                confidence=0.5,
                complexity="medium",
                customer_value="standard",
                metadata=additional_context or {}
            )
    
    def _assess_message_complexity(self, message: str) -> str:
        """Avalia a complexidade da mensagem"""
        word_count = len(message.split())
        
        # Palavras que indicam complexidade
        complex_indicators = [
            "problema", "erro", "não funciona", "bug", "reclamação",
            "cancelar", "reagendar", "modificar", "alterar",
            "orçamento", "preço", "desconto", "negociar",
            "urgente", "imediato", "hoje", "agora"
        ]
        
        simple_indicators = [
            "oi", "olá", "ok", "sim", "não", "obrigado", "tchau"
        ]
        
        message_lower = message.lower()
        
        # Verificar indicadores
        has_complex = any(indicator in message_lower for indicator in complex_indicators)
        has_simple = any(indicator in message_lower for indicator in simple_indicators)
        
        if has_complex or word_count > 20:
            return "high"
        elif has_simple and word_count <= 3:
            return "low"
        else:
            return "medium"
    
    async def _execute_with_fallback(self, strategy: BaseStrategy, 
                                   context: MessageContext) -> StrategyResponse:
        """Executa estratégia com sistema de fallback"""
        
        for attempt in range(self.config["max_retries"] + 1):
            try:
                response = await strategy.execute(context)
                
                if response.success or not self.config["enable_fallback"]:
                    return response
                
                logger.warning(f"Estratégia {strategy.name} falhou (tentativa {attempt + 1})")
                
            except Exception as e:
                logger.error(f"Erro na estratégia {strategy.name} (tentativa {attempt + 1}): {e}")
        
        # Fallback para estratégia padrão
        if (self.config["enable_fallback"] and 
            strategy.name != self.config["fallback_strategy"]):
            
            fallback_strategy = self.strategies.get(self.config["fallback_strategy"])
            if fallback_strategy:
                logger.info(f"Usando fallback: {fallback_strategy.name}")
                return await fallback_strategy.execute(context)
        
        # Fallback final
        return StrategyResponse(
            success=False,
            response="Desculpe, estamos enfrentando dificuldades técnicas. Tente novamente em alguns minutos.",
            strategy_used=f"{strategy.name}_failed",
            processing_time=0.0,
            metadata={"fallback_exhausted": True}
        )
    
    def _get_selection_reason(self, context: MessageContext, 
                            strategy: BaseStrategy) -> str:
        """Explica por que uma estratégia foi selecionada"""
        
        if strategy.name == "crew":
            if context.lead_score >= 80:
                return "high_value_customer"
            elif context.complexity == "high":
                return "complex_query"
            else:
                return "quality_priority"
                
        elif strategy.name == "hybrid":
            return "balanced_approach"
            
        elif strategy.name == "advanced":
            if context.complexity == "low":
                return "simple_query"
            else:
                return "cost_optimization"
                
        else:  # simple
            return "fallback_strategy"
    
    def _update_global_metrics(self, strategy_name: str, 
                             processing_time: float, success: bool):
        """Atualiza métricas globais do sistema"""
        
        if not self.config["performance_monitoring"]:
            return
        
        self.global_metrics["total_requests"] += 1
        
        if success:
            self.global_metrics["successful_requests"] += 1
        else:
            self.global_metrics["failed_requests"] += 1
        
        # Atualizar tempo médio de processamento
        total_time = (self.global_metrics["avg_processing_time"] * 
                     (self.global_metrics["total_requests"] - 1) + processing_time)
        self.global_metrics["avg_processing_time"] = total_time / self.global_metrics["total_requests"]
        
        # Atualizar uso de estratégias
        if strategy_name in self.global_metrics["strategy_usage"]:
            self.global_metrics["strategy_usage"][strategy_name] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Retorna relatório completo de performance"""
        
        strategy_metrics = {}
        for name, strategy in self.strategies.items():
            strategy_metrics[name] = strategy.get_metrics()
        
        success_rate = (
            self.global_metrics["successful_requests"] / 
            max(self.global_metrics["total_requests"], 1)
        )
        
        return {
            "global_metrics": {
                **self.global_metrics,
                "success_rate": success_rate,
                "failure_rate": 1 - success_rate
            },
            "strategy_metrics": strategy_metrics,
            "configuration": self.config,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_strategy(self, name: str, strategy: BaseStrategy):
        """Adiciona nova estratégia ao sistema"""
        self.strategies[name] = strategy
        self.global_metrics["strategy_usage"][name] = 0
        logger.info(f"Estratégia '{name}' adicionada ao sistema")
    
    def remove_strategy(self, name: str):
        """Remove estratégia do sistema"""
        if name in self.strategies and name != self.config["fallback_strategy"]:
            del self.strategies[name]
            logger.info(f"Estratégia '{name}' removida do sistema")
        else:
            logger.warning(f"Não foi possível remover estratégia '{name}'")
    
    def update_config(self, **kwargs):
        """Atualiza configurações do sistema"""
        self.config.update(kwargs)
        logger.info(f"Configurações atualizadas: {kwargs}")
    
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
