from app.utils.logger import get_logger

logger = get_logger(__name__)
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
from .metrics_service import metrics_service
from .state_manager import (
    state_manager, ConversationMessage, MessageRole, ConversationStatus
)

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
        
        # Metrics service
        self.metrics_service = metrics_service
        
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
        Com gestão de estado avançada
        """
        start_time = time.time()
        
        try:
            # Incrementa contador de requisições e métricas
            self.metrics["total_requests"] += 1
            self.metrics_service.track_message(
                direction="inbound", 
                message_type="text", 
                status="processing"
            )
            
            # === GESTÃO DE ESTADO ===
            # Obtém estado da conversa
            conversation_state = await state_manager.get_state(user_id)
            
            # Se primeira mensagem, configura telefone
            if not conversation_state.phone and phone:
                conversation_state.phone = phone
                conversation_state.status = ConversationStatus.ACTIVE
            
            # Adiciona mensagem do usuário ao histórico
            await state_manager.add_message(
                user_id,
                ConversationMessage(
                    role=MessageRole.USER,
                    content=message,
                    timestamp=datetime.now(),
                    metadata={"phone": phone}
                )
            )
            
            # Constrói contexto da mensagem com histórico
            with self.metrics_service.track_component_performance("context_building"):
                context = await self._build_context_with_state(message, user_id, phone, conversation_state)
            
            # Seleciona estratégia apropriada
            with self.metrics_service.track_component_performance("strategy_selection"):
                selected = self.selector.select_strategy(context, list(self.strategies.values()))
            
            if not selected:
                # Fallback se nenhuma estratégia disponível
                self.metrics["failed_requests"] += 1
                self.metrics_service.track_message(
                    direction="outbound",
                    message_type="text", 
                    status="error"
                )
                self.metrics_service.track_error(
                    error_type="no_strategy_available",
                    component="strategy_manager"
                )
                
                return StrategyResponse(
                    success=False,
                    response="Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes.",
                    strategy_used="fallback",
                    processing_time=time.time() - start_time
                )
            
            strategy = selected
            strategy_name = strategy.name
            
            # Track seleção de estratégia
            self.metrics_service.track_strategy_selection(
                strategy=strategy_name,
                reason="context_based_selection",
                success=True
            )
            
            # Executa estratégia selecionada com tracking de tempo
            with self.metrics_service.track_response_time(
                strategy=strategy_name,
                complexity="normal",  # TODO: detectar complexidade
                cache_hit=False  # TODO: detectar cache hit
            ):
                result = await strategy.execute(context)
            
            # Registra métricas de sucesso
            self.metrics["successful_requests"] += 1
            response_time = time.time() - start_time
            self.metrics["response_times"].append(response_time)
            
            # Track métricas detalhadas
            self.metrics_service.track_message(
                direction="outbound",
                message_type="text",
                status="success" if result.success else "error",
                strategy=strategy_name,
                user_type=context.user_context.get("customer_value", "standard")
            )
            
            # Atualiza uso de estratégias
            if strategy_name not in self.metrics["strategy_usage"]:
                self.metrics["strategy_usage"][strategy_name] = 0
            self.metrics["strategy_usage"][strategy_name] += 1
            
            # === SALVAR RESPOSTA NO ESTADO ===
            # Adiciona resposta do assistant ao histórico
            if result.success and result.response:
                await state_manager.add_message(
                    user_id,
                    ConversationMessage(
                        role=MessageRole.ASSISTANT,
                        content=result.response,
                        timestamp=datetime.now(),
                        metadata={
                            "strategy_used": strategy_name,
                            "processing_time": response_time,
                            "confidence": result.confidence if hasattr(result, 'confidence') else 0.8
                        }
                    )
                )
                
                # Atualiza estratégias usadas no estado
                conversation_state = await state_manager.get_state(user_id)
                conversation_state.strategy_history.append(strategy_name)
                
                # Se é uma resposta de agendamento, atualiza contexto de booking
                message_lower = message.lower()
                response_lower = result.response.lower()
                if any(word in message_lower for word in ["agendar", "marcar", "horário"]) or \
                   any(word in response_lower for word in ["agendar", "agendamento", "horário"]):
                    if not conversation_state.booking_context:
                        await state_manager.start_booking_flow(user_id)
                    
                    # Análise da resposta para determinar próximo step
                    if "confirmar" in response_lower:
                        await state_manager.update_booking_context(user_id, step="confirmation")
                    elif "serviço" in response_lower:
                        await state_manager.update_booking_context(user_id, step="service_selection")
                    elif "horário" in response_lower or "data" in response_lower:
                        await state_manager.update_booking_context(user_id, step="datetime")
                
                # Salva estado atualizado
                await state_manager.save_state(user_id, conversation_state)
            
            return result
            
        except Exception as e:
            # Registra erro
            self.metrics["failed_requests"] += 1
            self.metrics_service.track_error(
                error_type="processing_exception",
                component="strategy_manager",
                severity="error"
            )
            self.metrics_service.track_message(
                direction="outbound",
                message_type="text",
                status="error"
            )
            
            logger.error(f"Erro no processamento: {e}")
            
            return StrategyResponse(
                success=False,
                response="Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes.",
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
                    lead_score_result = await self.lead_scoring.calculate_lead_score(
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
                        
                        # Track lead score metrics
                        self.metrics_service.track_lead_score(
                            score=lead_score,
                            category=str(getattr(lead_score_result, 'category', 'unknown')),
                            customer_type=customer_value
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
                user_id=user_id,
                conversation_id=phone,  # Usando phone como conversation_id temporariamente
                message=message,
                message_type="text",
                lead_score=lead_score,
                confidence=confidence,
                customer_value=customer_value
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Erro ao construir contexto: {e}")
            # Contexto padrão em caso de erro
            return MessageContext(
                user_id=user_id,
                conversation_id=phone,
                message=message,
                message_type="text",
                lead_score=0.5,
                confidence=0.5,
                customer_value="standard"
            )
    
    async def _build_context_with_state(self, message: str, user_id: str, phone: str, conversation_state) -> MessageContext:
        """
        Constrói contexto da mensagem com estado da conversa
        """
        try:
            # Pega histórico de mensagens recentes
            recent_messages = conversation_state.get_recent_messages(10)
            
            # Análise de contexto baseada no histórico
            conversation_context = {
                "message_count": len(conversation_state.messages),
                "conversation_duration": (datetime.now() - conversation_state.started_at).total_seconds() / 60,
                "status": conversation_state.status.value,
                "has_booking": conversation_state.booking_context is not None,
                "booking_step": conversation_state.booking_context.step if conversation_state.booking_context else None
            }
            
            # Verifica cache para lead score existente
            cached_lead_score = None
            if self.config.get("cache_enabled", True):
                cached_lead_score = await cache_service.get_cached_lead_score(user_id, message)
            
            if cached_lead_score:
                lead_score = cached_lead_score.get("total_score", 0.5)
                confidence = cached_lead_score.get("confidence", 0.5)  
                customer_value = cached_lead_score.get("customer_value", "standard")
            else:
                # Calcular novo lead score com histórico
                try:
                    # Converte mensagens para formato histórico
                    history = [
                        {
                            "role": msg.role.value,
                            "content": msg.content,
                            "timestamp": msg.timestamp.isoformat()
                        }
                        for msg in recent_messages
                    ]
                    
                    lead_score_result = await self.lead_scoring.calculate_lead_score(
                        message=message,
                        user_id=user_id,
                        phone_number=phone,
                        conversation_history=history
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
                        
                        # Track lead score metrics
                        self.metrics_service.track_lead_score(
                            score=lead_score,
                            category=str(getattr(lead_score_result, 'category', 'unknown')),
                            customer_type=customer_value
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
            
            # Criar contexto da mensagem com estado da conversa
            context = MessageContext(
                user_id=user_id,
                conversation_id=conversation_state.session_id or phone,
                message=message,
                message_type="text",
                lead_score=lead_score,
                confidence=confidence,
                customer_value=customer_value,
                conversation_context=conversation_context,
                message_history=recent_messages
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Erro ao construir contexto com estado: {e}")
            # Fallback para método original
            return await self._build_context(message, user_id, phone)
    
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
            try:
                cache_stats = self.cache.get_stats()
            except AttributeError:
                # Fallback se cache não tem get_stats
                cache_stats = {"error": "Cache stats não disponível"}
        
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
