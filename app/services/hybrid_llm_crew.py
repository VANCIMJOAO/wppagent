"""
Serviço Híbrido LLM + CrewAI Multi-Agentes
Combina o melhor dos dois mundos para máxima eficiência
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .llm_advanced import advanced_llm_service, LLMResponse, ConversationState
from .crew_agents import whatsapp_crew, AgentRole
from .lead_scoring import lead_scoring_service, LeadCategory
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger = logging.getLogger(__name__)


class HybridLLMCrewService:
    """
    Serviço híbrido que combina:
    - LLM Advanced: Para processamento rápido e contextual
    - CrewAI: Para tarefas especializadas e complexas
    """
    
    def __init__(self):
        self.llm_service = advanced_llm_service
        self.crew_service = whatsapp_crew
        
        # Configurações de decisão
        self.crew_activation_rules = {
            "high_value_customer": 80,  # Lead score > 80 vai para crew
            "complex_query": ["problema", "reclamação", "cancelar", "reagendar"],
            "sales_opportunity": ["preço", "promoção", "desconto", "combo"],
            "scheduling_request": ["agendar", "marcar", "horário", "disponibilidade"],
            "always_crew": settings.debug  # Em desenvolvimento, sempre usa crew
        }
        
        # Métricas comparativas
        self.performance_metrics = {
            "llm_only": {"requests": 0, "success_rate": 0.0, "avg_time": 0.0},
            "crew_only": {"requests": 0, "success_rate": 0.0, "avg_time": 0.0},
            "hybrid": {"requests": 0, "success_rate": 0.0, "avg_time": 0.0}
        }
    
    async def process_message(
        self, 
        user_id: str, 
        conversation_id: str,
        message: str, 
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Processa mensagem usando lógica híbrida inteligente
        
        Args:
            user_id: ID do usuário
            conversation_id: ID da conversa
            message: Mensagem do cliente
            message_type: Tipo da mensagem
            
        Returns:
            Resposta otimizada do sistema híbrido
        """
        start_time = datetime.now()
        
        try:
            # 1. ANÁLISE RÁPIDA INICIAL (LLM)
            initial_analysis = await self._quick_llm_analysis(
                user_id, conversation_id, message, message_type
            )
            
            # 2. DECISÃO: LLM vs CREW vs HÍBRIDO
            processing_strategy = self._decide_strategy(
                message, user_id, initial_analysis
            )
            
            logger.info(f"Estratégia selecionada: {processing_strategy} para: {message[:50]}...")
            
            # 3. PROCESSAMENTO BASEADO NA ESTRATÉGIA
            if processing_strategy == "llm_only":
                result = await self._process_with_llm_only(
                    user_id, conversation_id, message, message_type
                )
                
            elif processing_strategy == "crew_only":
                result = await self._process_with_crew_only(
                    user_id, message, initial_analysis
                )
                
            else:  # hybrid
                result = await self._process_hybrid(
                    user_id, conversation_id, message, message_type, initial_analysis
                )
            
            # 4. ATUALIZAR MÉTRICAS
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            self._update_performance_metrics(
                processing_strategy, 
                result.get("success", True), 
                response_time
            )
            
            # 5. ENRIQUECER RESPOSTA COM METADATA
            result["processing_strategy"] = processing_strategy
            result["response_time"] = response_time
            result["timestamp"] = end_time.isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no processamento híbrido: {e}")
            
            # Fallback para LLM básico
            try:
                fallback_result = await self.llm_service.process_message(
                    user_id, conversation_id, message, message_type
                )
                
                return {
                    "success": True,
                    "response": fallback_result.text,
                    "confidence": fallback_result.confidence,
                    "processing_strategy": "fallback_llm",
                    "metadata": {"fallback_reason": str(e)}
                }
                
            except Exception as fallback_error:
                logger.error(f"Erro no fallback: {fallback_error}")
                
                return {
                    "success": False,
                    "response": "Desculpe, estamos com problemas técnicos. Nossa equipe foi notificada e resolveremos em breve!",
                    "processing_strategy": "error_fallback",
                    "error": str(e)
                }
    
    async def _quick_llm_analysis(
        self, 
        user_id: str, 
        conversation_id: str, 
        message: str, 
        message_type: str
    ) -> Dict[str, Any]:
        """Análise rápida inicial usando LLM para tomar decisões"""
        
        try:
            # Usar o sistema LLM avançado para análise inicial
            llm_response = await self.llm_service.process_message(
                user_id, conversation_id, message, message_type
            )
            
            return {
                "llm_response": llm_response,
                "intent": llm_response.intent,
                "confidence": llm_response.confidence,
                "conversation_state": llm_response.metadata.get("state"),
                "context_available": bool(llm_response.metadata.get("context")),
                "message_complexity": self._assess_message_complexity(message),
                "customer_value": self._assess_customer_value(user_id)
            }
            
        except Exception as e:
            logger.warning(f"Erro na análise LLM inicial: {e}")
            
            return {
                "llm_response": None,
                "intent": None,
                "confidence": 0.0,
                "conversation_state": "unknown",
                "context_available": False,
                "message_complexity": "medium",
                "customer_value": "standard"
            }
    
    def _safe_get_lead_score(self, lead_score: Any) -> float:
        """Extrai score de forma segura"""
        try:
            if hasattr(lead_score, 'total_score'):
                return float(lead_score.total_score)
            elif isinstance(lead_score, (int, float)):
                return float(lead_score)
            else:
                logger.warning(f"Lead score inválido: {lead_score}")
                return 50.0  # Default médio
        except (ValueError, TypeError) as e:
            logger.warning(f"Erro na conversão do lead score: {e}")
            return 50.0  # Default médio
    
    def _decide_strategy(self, message: str, user_id: str, context: Dict[str, Any]) -> str:
        """Decide qual estratégia usar baseada na mensagem e contexto"""
        
        try:
            # 1. Calcular Lead Score primeiro - com validação simplificada
            lead_score = lead_scoring_service.score_lead(
                message=message,
                phone=user_id,
                customer_data=context.get("customer_data", {}),
                context=context
            )
            
            logger.info(f"Lead Score recebido: {lead_score}, type: {type(lead_score)}")
            
            # Validação simplificada - apenas verifica se existe
            if not lead_score:
                logger.warning("Lead score não retornou resultado válido, usando estratégia LLM only")
                return "llm_only"
                
            # Extrair valores com função segura
            total_score = self._safe_get_lead_score(lead_score)
            confidence = getattr(lead_score, 'confidence', 0.5)
            category = getattr(lead_score, 'category', LeadCategory.COLD)
            priority_level = getattr(lead_score, 'priority_level', 2)
            
            # Garantir tipos corretos para outros campos
            try:
                confidence = float(confidence) if confidence is not None else 0.5
                priority_level = int(priority_level) if priority_level is not None else 2
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro na conversão de tipos auxiliares do lead score: {e}, usando valores padrão")
                confidence = 0.5
                priority_level = 2
            
            logger.info(f"Lead Score processado: score={total_score}, confidence={confidence}, category={category}, priority={priority_level}")
            
            # 2. Regras baseadas no Lead Score
            if category in [LeadCategory.OPPORTUNITY, LeadCategory.QUALIFIED]:
                # Leads de alta qualidade sempre usam CrewAI
                logger.info(f"Estratégia crew_only por categoria: {category}")
                return "crew_only"
            
            if priority_level >= 4:
                # Alta prioridade usa CrewAI
                logger.info(f"Estratégia crew_only por prioridade: {priority_level}")
                return "crew_only"
            
            # 3. Análise da mensagem
            message_lower = message.lower()
            word_count = len(message.split())
            
            # 4. Regras existentes com ajustes do Lead Score
            # Clientes VIP (baseado no score)
            if total_score >= 80:
                logger.info(f"Estratégia crew_only por score VIP: {total_score}")
                return "crew_only"
            
            # Mensagens muito simples e score baixo
            if word_count <= 3 and total_score < 40:
                logger.info(f"Estratégia llm_only por simplicidade: words={word_count}, score={total_score}")
                return "llm_only"
            
            # Queries complexas ou oportunidades
            complex_keywords = [
                "problema", "reclamação", "cancelar", "reagendar", "urgente",
                "preço", "promoção", "desconto", "orçamento", "agendar"
            ]
            
            if any(keyword in message_lower for keyword in complex_keywords):
                # Se tem palavras complexas e score médio/alto, usa CrewAI
                if total_score >= 50:
                    logger.info(f"Estratégia crew_only por complexidade e score: {total_score}")
                    return "crew_only"
                else:
                    logger.info(f"Estratégia hybrid por complexidade e score baixo: {total_score}")
                    return "hybrid"
            
            # Baseado na confiança do lead score
            if confidence < 0.6:
                logger.info(f"Estratégia hybrid por baixa confiança: {confidence}")
                return "hybrid"  # Baixa confiança = usar híbrido
            
            # Default baseado no score
            if total_score >= 60:
                return "crew_only"
            elif total_score >= 30:
                return "hybrid"
            else:
                return "llm_only"
                
        except Exception as e:
            logger.error(f"Erro ao decidir estratégia: {e}")
            # Fallback seguro
            if len(message.split()) > 10:
                return "hybrid"
            else:
                return "llm_only"
    
    async def _process_with_llm_only(
        self, 
        user_id: str, 
        conversation_id: str, 
        message: str, 
        message_type: str
    ) -> Dict[str, Any]:
        """Processamento usando apenas LLM avançado"""
        
        llm_response = await self.llm_service.process_message(
            user_id, conversation_id, message, message_type
        )
        
        return {
            "success": True,
            "response": llm_response.text,
            "intent": llm_response.intent,
            "confidence": llm_response.confidence,
            "interactive_buttons": llm_response.interactive_buttons,
            "suggested_actions": llm_response.suggested_actions or [],
            "metadata": llm_response.metadata,
            "agent_used": "llm_advanced"
        }
    
    async def _process_with_crew_only(
        self, 
        user_id: str, 
        message: str, 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Processamento usando apenas CrewAI"""
        
        # Preparar contexto para o crew
        conversation_context = {
            "user_id": user_id,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
        crew_result = self.crew_service.process_message(
            message, user_id, conversation_context
        )
        
        # Gerar suggested_actions baseado no resultado do crew
        suggested_actions = []
        if crew_result.get("action"):
            action = crew_result["action"]
            if action.get("type") == "create_appointment":
                suggested_actions.append({
                    "type": "create_appointment",
                    "data": action.get("data", {}),
                    "priority": "high"
                })
        
        return {
            "success": crew_result.get("success", True),
            "response": crew_result.get("response", ""),
            "agent_used": crew_result.get("agent_used", "unknown"),
            "action": crew_result.get("action"),
            "suggested_actions": suggested_actions,
            "metadata": {
                "crew_result": crew_result,
                "response_time": crew_result.get("response_time", 0)
            }
        }
    
    async def _process_hybrid(
        self, 
        user_id: str, 
        conversation_id: str, 
        message: str, 
        message_type: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processamento híbrido que combina LLM + CrewAI
        LLM para velocidade, Crew para especialização
        """
        
        try:
            # Executar ambos em paralelo para comparar
            llm_task = self._process_with_llm_only(
                user_id, conversation_id, message, message_type
            )
            
            crew_task = self._process_with_crew_only(
                user_id, message, analysis
            )
            
            # Aguardar ambos com timeout
            llm_result, crew_result = await asyncio.gather(
                llm_task, crew_task, return_exceptions=True
            )
            
            # Decidir qual resposta usar
            final_result = self._choose_best_response(llm_result, crew_result, analysis)
            
            final_result["hybrid_comparison"] = {
                "llm_available": not isinstance(llm_result, Exception),
                "crew_available": not isinstance(crew_result, Exception),
                "chosen_source": final_result.get("chosen_source", "unknown")
            }
            
            return final_result
            
        except Exception as e:
            logger.error(f"Erro no processamento híbrido: {e}")
            
            # Fallback para LLM
            return await self._process_with_llm_only(
                user_id, conversation_id, message, message_type
            )
    
    def _choose_best_response(
        self, 
        llm_result: Dict[str, Any], 
        crew_result: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Escolhe a melhor resposta entre LLM e Crew baseado em critérios"""
        
        # Se um deu erro, usa o outro
        if isinstance(llm_result, Exception):
            crew_result["chosen_source"] = "crew_fallback"
            return crew_result
            
        if isinstance(crew_result, Exception):
            llm_result["chosen_source"] = "llm_fallback"
            return llm_result
        
        # Critérios de qualidade
        llm_score = self._calculate_response_quality(llm_result, "llm")
        crew_score = self._calculate_response_quality(crew_result, "crew")
        
        if crew_score > llm_score:
            crew_result["chosen_source"] = "crew_better_quality"
            crew_result["quality_scores"] = {"llm": llm_score, "crew": crew_score}
            return crew_result
        else:
            llm_result["chosen_source"] = "llm_better_quality"
            llm_result["quality_scores"] = {"llm": llm_score, "crew": crew_score}
            return llm_result
    
    def _calculate_response_quality(self, result: Dict[str, Any], source: str) -> float:
        """Calcula score de qualidade da resposta"""
        score = 0.0
        
        # Critério 1: Sucesso da operação
        if result.get("success", False):
            score += 30
        
        # Critério 2: Confiança (para LLM)
        if source == "llm":
            confidence = result.get("confidence", 0)
            score += confidence * 25
        
        # Critério 3: Tempo de resposta (mais rápido = melhor)
        response_time = result.get("metadata", {}).get("response_time", 5.0)
        if response_time < 2.0:
            score += 20
        elif response_time < 5.0:
            score += 10
        
        # Critério 4: Presença de ações específicas (mais importante)
        if result.get("suggested_actions") and len(result.get("suggested_actions", [])) > 0:
            score += 25  # Priorizar respostas com suggested_actions
        elif result.get("action") or result.get("interactive_buttons"):
            score += 15
        
        # Critério 5: Tamanho da resposta (nem muito curta, nem muito longa)
        response_length = len(result.get("response", ""))
        if 50 <= response_length <= 300:
            score += 10
        
        return min(score, 100.0)
    
    def _assess_message_complexity(self, message: str) -> str:
        """Avalia complexidade da mensagem"""
        
        words = message.split()
        
        # Indicadores de complexidade
        complex_indicators = [
            "problema", "não funcionou", "cancelar", "reagendar", 
            "reclamação", "insatisfeito", "dificuldade", "confuso"
        ]
        
        questions = message.count("?")
        complex_words = sum(1 for word in words if word.lower() in complex_indicators)
        
        if len(words) > 20 or questions > 2 or complex_words > 1:
            return "high"
        elif len(words) > 10 or questions > 0 or complex_words > 0:
            return "medium"
        else:
            return "low"
    
    def _assess_customer_value(self, user_id: str) -> str:
        """Avalia valor do cliente (integração futura com CRM)"""
        # Por enquanto, lógica simples baseada no ID
        # Futura integração com banco de dados real
        
        if user_id.endswith(("vip", "premium")):
            return "vip"
        elif len(user_id) > 15:  # IDs longos = clientes antigos
            return "returning"
        else:
            return "standard"
    
    def _update_performance_metrics(
        self, 
        strategy: str, 
        success: bool, 
        response_time: float
    ):
        """Atualiza métricas de performance comparativas"""
        
        if strategy not in self.performance_metrics:
            return
        
        metrics = self.performance_metrics[strategy]
        metrics["requests"] += 1
        
        # Atualizar success rate
        total_requests = metrics["requests"]
        current_successes = metrics["success_rate"] * (total_requests - 1)
        new_successes = current_successes + (1 if success else 0)
        metrics["success_rate"] = new_successes / total_requests
        
        # Atualizar tempo médio
        current_avg = metrics["avg_time"]
        metrics["avg_time"] = ((current_avg * (total_requests - 1)) + response_time) / total_requests
    
    def get_hybrid_analytics(self) -> Dict[str, Any]:
        """Retorna analytics completos do sistema híbrido"""
        
        crew_analytics = self.crew_service.get_performance_metrics()
        llm_analytics = self.llm_service.get_analytics_report()
        
        return {
            "system_type": "hybrid_llm_crew",
            "performance_comparison": self.performance_metrics,
            "crew_analytics": crew_analytics,
            "llm_analytics": llm_analytics,
            "activation_rules": self.crew_activation_rules,
            "recommendations": self._generate_optimization_recommendations()
        }
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Gera recomendações de otimização baseado nas métricas"""
        
        recommendations = []
        
        # Analisar performance relativa
        llm_success = self.performance_metrics["llm_only"]["success_rate"]
        crew_success = self.performance_metrics["crew_only"]["success_rate"]
        
        if crew_success > llm_success + 0.1:
            recommendations.append(
                "Considere usar mais o CrewAI - está superando o LLM em qualidade"
            )
        
        if llm_success > crew_success + 0.1:
            recommendations.append(
                "LLM está performando muito bem - considere expandir seu uso"
            )
        
        # Analisar tempos de resposta
        llm_time = self.performance_metrics["llm_only"]["avg_time"]
        crew_time = self.performance_metrics["crew_only"]["avg_time"]
        
        if crew_time > llm_time * 2:
            recommendations.append(
                "CrewAI está lento - considere otimização ou uso mais seletivo"
            )
        
        # Recomendações gerais
        total_requests = sum(
            metrics["requests"] for metrics in self.performance_metrics.values()
        )
        
        if total_requests < 100:
            recommendations.append(
                "Colete mais dados para análises mais precisas"
            )
        
        return recommendations


# Instância global do serviço híbrido
hybrid_service = HybridLLMCrewService()
