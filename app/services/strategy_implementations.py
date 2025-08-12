from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Implementações concretas das estratégias LLM
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .strategy_base import BaseStrategy, MessageContext, StrategyResponse, StrategyType
from .llm_advanced import advanced_llm_service, LLMResponse
from .crew_agents import whatsapp_crew, AgentRole
from .lead_scoring import lead_scoring_service

logger = logging.getLogger(__name__)


class SimpleLLMStrategy(BaseStrategy):
    """Estratégia simples usando LLM básico"""
    
    def __init__(self):
        super().__init__("simple")
        # Para futuro: implementar LLM mais simples/rápido
        self.llm_service = advanced_llm_service  # Temporário
    
    async def execute(self, context: MessageContext) -> StrategyResponse:
        start_time = datetime.now()
        
        try:
            # Processamento simplificado
            response = await self._simple_process(context)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(processing_time, True)
            
            return StrategyResponse(
                success=True,
                response=response["text"],
                strategy_used=self.name,
                processing_time=processing_time,
                intent=response.get("intent"),
                confidence=response.get("confidence", 0.7),
                metadata={"processing_method": "simple_llm"}
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(processing_time, False)
            
            logger.error(f"Erro na estratégia simples: {e}")
            return StrategyResponse(
                success=False,
                response="Desculpe, ocorreu um erro. Tente novamente.",
                strategy_used=self.name,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    def can_handle(self, context: MessageContext) -> bool:
        """Estratégia simples pode processar qualquer mensagem"""
        return True
    
    def get_priority(self, context: MessageContext) -> int:
        """Prioridade baixa - usado como fallback"""
        return 10
    
    async def _simple_process(self, context: MessageContext) -> Dict[str, Any]:
        """Processamento simplificado da mensagem"""
        # Implementação temporária usando LLM avançado
        # TODO: Implementar LLM mais leve
        llm_response = await self.llm_service.process_message(
            context.user_id,
            context.conversation_id,
            context.message,
            context.message_type
        )
        
        return {
            "text": llm_response.text,
            "intent": llm_response.intent,
            "confidence": llm_response.confidence
        }


class AdvancedLLMStrategy(BaseStrategy):
    """Estratégia avançada usando LLM completo"""
    
    def __init__(self):
        super().__init__("advanced")
        self.llm_service = advanced_llm_service
    
    async def execute(self, context: MessageContext) -> StrategyResponse:
        start_time = datetime.now()
        
        try:
            llm_response = await self.llm_service.process_message(
                context.user_id,
                context.conversation_id,
                context.message,
                context.message_type
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(processing_time, True)
            
            return StrategyResponse(
                success=True,
                response=llm_response.text,
                strategy_used=self.name,
                processing_time=processing_time,
                intent=llm_response.intent,
                confidence=llm_response.confidence,
                interactive_buttons=llm_response.interactive_buttons,
                suggested_actions=llm_response.suggested_actions or [],
                metadata={
                    **llm_response.metadata,
                    "processing_method": "advanced_llm"
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(processing_time, False)
            
            logger.error(f"Erro na estratégia avançada: {e}")
            return StrategyResponse(
                success=False,
                response="Desculpe, ocorreu um erro no processamento. Tente novamente.",
                strategy_used=self.name,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    def can_handle(self, context: MessageContext) -> bool:
        """Estratégia avançada pode processar qualquer mensagem"""
        return True
    
    def get_priority(self, context: MessageContext) -> int:
        """Prioridade média"""
        if context.lead_score < 50:
            return 60
        return 40


class CrewAIStrategy(BaseStrategy):
    """Estratégia usando CrewAI para casos complexos"""
    
    def __init__(self):
        super().__init__("crew")
        self.crew_service = whatsapp_crew
    
    async def execute(self, context: MessageContext) -> StrategyResponse:
        start_time = datetime.now()
        
        try:
            # Determinar agente apropriado
            agent_role = self._select_agent(context)
            
            # Processar com CrewAI
            crew_response = await self.crew_service.process_complex_request(
                user_message=context.message,
                agent_role=agent_role,
                user_id=context.user_id,
                context_data=context.metadata or {}
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(processing_time, True)
            
            return StrategyResponse(
                success=True,
                response=crew_response.get("response", ""),
                strategy_used=self.name,
                processing_time=processing_time,
                intent=crew_response.get("intent"),
                confidence=crew_response.get("confidence", 0.9),
                interactive_buttons=crew_response.get("interactive_buttons"),
                suggested_actions=crew_response.get("suggested_actions", []),
                metadata={
                    **crew_response.get("metadata", {}),
                    "agent_role": agent_role.value,
                    "processing_method": "crew_ai"
                }
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(processing_time, False)
            
            logger.error(f"Erro na estratégia CrewAI: {e}")
            return StrategyResponse(
                success=False,
                response="Estou processando sua solicitação. Um momento, por favor...",
                strategy_used=self.name,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    def can_handle(self, context: MessageContext) -> bool:
        """CrewAI pode processar qualquer mensagem, mas tem custo maior"""
        return True
    
    def get_priority(self, context: MessageContext) -> int:
        """Alta prioridade para clientes VIP e casos complexos"""
        priority = 30
        
        if context.lead_score >= 80:
            priority += 50
        elif context.lead_score >= 60:
            priority += 30
            
        if context.complexity == "high":
            priority += 20
            
        if context.customer_value == "vip":
            priority += 40
            
        return min(priority, 100)
    
    def _select_agent(self, context: MessageContext) -> AgentRole:
        """Seleciona o agente mais apropriado baseado no contexto"""
        message_lower = context.message.lower()
        
        # Mapeamento de palavras-chave para agentes
        if any(word in message_lower for word in ["agendar", "marcar", "horário"]):
            return AgentRole.SCHEDULING_SPECIALIST
        elif any(word in message_lower for word in ["preço", "valor", "comprar", "contratar"]):
            return AgentRole.SALES_SPECIALIST
        elif any(word in message_lower for word in ["problema", "reclamação", "cancelar"]):
            return AgentRole.SUPPORT_SPECIALIST
        elif any(word in message_lower for word in ["informação", "sobre", "como"]):
            return AgentRole.INFORMATION_SPECIALIST
        else:
            return AgentRole.CUSTOMER_SERVICE


class HybridStrategy(BaseStrategy):
    """Estratégia híbrida que combina LLM e CrewAI"""
    
    def __init__(self):
        super().__init__("hybrid")
        self.llm_strategy = AdvancedLLMStrategy()
        self.crew_strategy = CrewAIStrategy()
    
    async def execute(self, context: MessageContext) -> StrategyResponse:
        start_time = datetime.now()
        
        try:
            # Análise inicial rápida com LLM
            llm_response = await self.llm_strategy.execute(context)
            
            # Decisão: refinar com CrewAI?
            needs_crew_refinement = self._needs_crew_refinement(
                context, llm_response
            )
            
            if needs_crew_refinement:
                # Enriquecer contexto com resultado do LLM
                enhanced_context = MessageContext(
                    **context.__dict__,
                    metadata={
                        **(context.metadata or {}),
                        "llm_analysis": {
                            "intent": llm_response.intent,
                            "confidence": llm_response.confidence,
                            "initial_response": llm_response.response
                        }
                    }
                )
                
                # Processar com CrewAI
                crew_response = await self.crew_strategy.execute(enhanced_context)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                self.update_metrics(processing_time, crew_response.success)
                
                # Combinar resultados
                return StrategyResponse(
                    success=crew_response.success,
                    response=crew_response.response,
                    strategy_used=f"{self.name}_with_crew",
                    processing_time=processing_time,
                    intent=crew_response.intent or llm_response.intent,
                    confidence=max(crew_response.confidence, llm_response.confidence),
                    interactive_buttons=crew_response.interactive_buttons or llm_response.interactive_buttons,
                    suggested_actions=(crew_response.suggested_actions or []) + (llm_response.suggested_actions or []),
                    metadata={
                        "processing_method": "hybrid_llm_crew",
                        "llm_used": True,
                        "crew_used": True,
                        "crew_refinement_reason": "confidence_below_threshold"
                    }
                )
            else:
                # Usar apenas resultado do LLM
                processing_time = (datetime.now() - start_time).total_seconds()
                self.update_metrics(processing_time, llm_response.success)
                
                llm_response.strategy_used = f"{self.name}_llm_only"
                llm_response.processing_time = processing_time
                llm_response.metadata["processing_method"] = "hybrid_llm_only"
                
                return llm_response
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(processing_time, False)
            
            logger.error(f"Erro na estratégia híbrida: {e}")
            return StrategyResponse(
                success=False,
                response="Desculpe, ocorreu um erro no processamento. Tente novamente.",
                strategy_used=self.name,
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    def can_handle(self, context: MessageContext) -> bool:
        """Estratégia híbrida pode processar qualquer mensagem"""
        return True
    
    def get_priority(self, context: MessageContext) -> int:
        """Prioridade média-alta, especialmente para casos intermediários"""
        if 40 <= context.lead_score < 80:
            return 70
        return 50
    
    def _needs_crew_refinement(self, context: MessageContext, 
                             llm_response: StrategyResponse) -> bool:
        """Decide se precisa refinar com CrewAI"""
        
        # Se LLM não teve sucesso, tentar CrewAI
        if not llm_response.success:
            return True
            
        # Se confiança muito baixa, refinar
        if llm_response.confidence < 0.6:
            return True
            
        # Se cliente tem alto valor, refinar
        if context.lead_score >= 70:
            return True
            
        # Se mensagem tem palavras complexas
        complex_keywords = [
            "problema", "reclamação", "urgente", "cancelar",
            "preço", "desconto", "orçamento"
        ]
        
        if any(keyword in context.message.lower() for keyword in complex_keywords):
            return True
            
        return False
