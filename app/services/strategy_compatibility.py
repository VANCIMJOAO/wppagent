from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Adaptador para migração suave do sistema híbrido antigo para o novo StrategyManager
Mantém compatibilidade enquanto introduz o novo sistema
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .strategy_manager import strategy_manager, StrategyResponse
from .hybrid_llm_crew import HybridLLMCrewService

logger = logging.getLogger(__name__)


class CompatibilityAdapter:
    """
    Adaptador que permite migração gradual do sistema antigo para o novo
    
    Funcionalidades:
    - Interface compatível com sistema antigo
    - Conversão entre formatos de resposta
    - Logging e métricas unificadas
    - Fallback para sistema antigo se necessário
    """
    
    def __init__(self):
        self.new_system = strategy_manager
        self.old_system = HybridLLMCrewService()
        self.use_new_system = True  # Flag para alternar sistemas
        
        # Contadores para monitoramento
        self.usage_stats = {
            "new_system": 0,
            "old_system": 0,
            "fallback_to_old": 0,
            "errors": 0
        }
    
    async def process_message(self, user_id: str, conversation_id: str,
                            message: str, message_type: str = "text",
                            **kwargs) -> Dict[str, Any]:
        """
        Interface compatível com sistema antigo
        
        Args:
            user_id: ID do usuário
            conversation_id: ID da conversa  
            message: Mensagem do cliente
            message_type: Tipo da mensagem
            **kwargs: Argumentos adicionais para compatibilidade
            
        Returns:
            Resposta no formato do sistema antigo
        """
        
        if self.use_new_system:
            try:
                # Usar novo sistema de estratégias
                self.usage_stats["new_system"] += 1
                
                new_response = await self.new_system.process(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message=message,
                    message_type=message_type,
                    additional_context=kwargs
                )
                
                # Converter para formato antigo
                return self._convert_new_to_old_format(new_response)
                
            except Exception as e:
                logger.error(f"Erro no novo sistema, usando fallback: {e}")
                self.usage_stats["fallback_to_old"] += 1
                
                # Fallback para sistema antigo
                return await self._use_old_system(
                    user_id, conversation_id, message, message_type, **kwargs
                )
        else:
            # Usar sistema antigo diretamente
            return await self._use_old_system(
                user_id, conversation_id, message, message_type, **kwargs
            )
    
    async def _use_old_system(self, user_id: str, conversation_id: str,
                            message: str, message_type: str, **kwargs) -> Dict[str, Any]:
        """Usa o sistema antigo com tratamento de erro"""
        
        try:
            self.usage_stats["old_system"] += 1
            
            return await self.old_system.process_message(
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                message_type=message_type
            )
            
        except Exception as e:
            logger.error(f"Erro no sistema antigo: {e}")
            self.usage_stats["errors"] += 1
            
            # Resposta de emergência
            return {
                "success": False,
                "response": "Desculpe, estamos enfrentando dificuldades técnicas. Tente novamente.",
                "processing_strategy": "error_fallback",
                "agent_used": "emergency",
                "response_time": 0.0,
                "interactive_buttons": [],
                "suggested_actions": [],
                "metadata": {"error": str(e), "system": "emergency"}
            }
    
    def _convert_new_to_old_format(self, new_response: StrategyResponse) -> Dict[str, Any]:
        """Converte resposta do novo sistema para formato do antigo"""
        
        return {
            "success": new_response.success,
            "response": new_response.response,
            "processing_strategy": new_response.strategy_used,
            "agent_used": new_response.metadata.get("agent_role", new_response.strategy_used),
            "response_time": new_response.processing_time,
            "intent": new_response.intent,
            "confidence": new_response.confidence,
            "interactive_buttons": new_response.interactive_buttons or [],
            "suggested_actions": new_response.suggested_actions or [],
            "metadata": {
                **(new_response.metadata or {}),
                "system_version": "new",
                "context_analysis": new_response.metadata.get("context_analysis", {}),
                "selection_reason": new_response.metadata.get("selection_reason", "unknown")
            }
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso dos sistemas"""
        
        total = sum(self.usage_stats.values())
        
        return {
            "usage_stats": self.usage_stats,
            "percentages": {
                key: (count / max(total, 1)) * 100 
                for key, count in self.usage_stats.items()
            },
            "new_system_enabled": self.use_new_system,
            "total_requests": total
        }
    
    def enable_new_system(self):
        """Habilita o novo sistema de estratégias"""
        self.use_new_system = True
        logger.info("Novo sistema de estratégias habilitado")
    
    def disable_new_system(self):
        """Desabilita o novo sistema (usa apenas o antigo)"""
        self.use_new_system = False
        logger.info("Novo sistema de estratégias desabilitado - usando sistema legado")
    
    def get_performance_comparison(self) -> Dict[str, Any]:
        """Compara performance entre sistemas antigo e novo"""
        
        new_system_metrics = self.new_system.get_performance_report()
        usage_stats = self.get_usage_stats()
        
        return {
            "new_system_performance": new_system_metrics,
            "usage_comparison": usage_stats,
            "migration_status": {
                "new_system_active": self.use_new_system,
                "migration_percentage": usage_stats["percentages"].get("new_system", 0),
                "fallback_rate": usage_stats["percentages"].get("fallback_to_old", 0),
                "error_rate": usage_stats["percentages"].get("errors", 0)
            },
            "timestamp": datetime.now().isoformat()
        }


# Instância global do adaptador
compatibility_service = CompatibilityAdapter()

# Manter compatibilidade com nome antigo
hybrid_service = compatibility_service
