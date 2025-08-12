"""
Endpoints para gerenciamento e monitoramento do sistema de estratégias
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.services.strategy_manager import strategy_manager
from app.utils.logger import get_logger
from app.services.strategy_compatibility import compatibility_service
logger = get_logger(__name__)
from app.services.cache_service import cache_service
from app.services.metrics_service import metrics_service
from app.services.state_manager import get_state_manager, ConversationStatus

# Inicializar state_manager
state_manager = get_state_manager()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/strategies", tags=["Strategy Management"])


@router.get("/performance")
async def get_performance_report():
    """Retorna relatório completo de performance das estratégias"""
    try:
        return strategy_manager.get_performance_report()
    except Exception as e:
        logger.error(f"Erro ao obter relatório de performance: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/usage-stats")
async def get_usage_stats():
    """Retorna estatísticas de uso dos sistemas antigo vs novo"""
    try:
        return compatibility_service.get_usage_stats()
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de uso: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/comparison")
async def get_performance_comparison():
    """Compara performance entre sistema antigo e novo"""
    try:
        return compatibility_service.get_performance_comparison()
    except Exception as e:
        logger.error(f"Erro ao obter comparação: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/enable-new-system")
async def enable_new_system():
    """Habilita o novo sistema de estratégias"""
    try:
        compatibility_service.enable_new_system()
        return {
            "success": True,
            "message": "Novo sistema de estratégias habilitado",
            "system_active": True
        }
    except Exception as e:
        logger.error(f"Erro ao habilitar novo sistema: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/disable-new-system")
async def disable_new_system():
    """Desabilita o novo sistema (usar apenas sistema legado)"""
    try:
        compatibility_service.disable_new_system()
        return {
            "success": True,
            "message": "Novo sistema desabilitado - usando sistema legado",
            "system_active": False
        }
    except Exception as e:
        logger.error(f"Erro ao desabilitar novo sistema: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/strategies")
async def list_strategies():
    """Lista todas as estratégias disponíveis com suas métricas"""
    try:
        strategies_info = []
        
        for name, strategy in strategy_manager.strategies.items():
            strategies_info.append({
                "name": name,
                "metrics": strategy.get_metrics(),
                "description": _get_strategy_description(name)
            })
        
        return {
            "strategies": strategies_info,
            "total_strategies": len(strategies_info),
            "active_system": "new" if compatibility_service.use_new_system else "legacy"
        }
        
    except Exception as e:
        logger.error(f"Erro ao listar estratégias: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.put("/config")
async def update_strategy_config(
    enable_fallback: Optional[bool] = None,
    max_retries: Optional[int] = None,
    fallback_strategy: Optional[str] = None,
    performance_monitoring: Optional[bool] = None
):
    """Atualiza configurações do sistema de estratégias"""
    try:
        config_updates = {}
        
        if enable_fallback is not None:
            config_updates["enable_fallback"] = enable_fallback
        
        if max_retries is not None:
            if max_retries < 0 or max_retries > 5:
                raise HTTPException(status_code=400, detail="max_retries deve estar entre 0 e 5")
            config_updates["max_retries"] = max_retries
        
        if fallback_strategy is not None:
            if fallback_strategy not in strategy_manager.strategies:
                raise HTTPException(status_code=400, detail="Estratégia de fallback inválida")
            config_updates["fallback_strategy"] = fallback_strategy
        
        if performance_monitoring is not None:
            config_updates["performance_monitoring"] = performance_monitoring
        
        if not config_updates:
            raise HTTPException(status_code=400, detail="Nenhuma configuração fornecida")
        
        strategy_manager.update_config(**config_updates)
        
        return {
            "success": True,
            "message": "Configurações atualizadas com sucesso",
            "updated_config": config_updates,
            "current_config": strategy_manager.config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar configurações: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/test-strategy/{strategy_name}")
async def test_strategy(
    strategy_name: str,
    message: str,
    user_id: str = "test_user",
    conversation_id: str = "test_conversation"
):
    """Testa uma estratégia específica com uma mensagem"""
    try:
        if strategy_name not in strategy_manager.strategies:
            raise HTTPException(status_code=404, detail="Estratégia não encontrada")
        
        # Processar com estratégia específica
        response = await strategy_manager.process(
            user_id=user_id,
            conversation_id=conversation_id,
            message=message,
            additional_context={"test_mode": True, "forced_strategy": strategy_name}
        )
        
        return {
            "test_result": {
                "strategy_used": response.strategy_used,
                "success": response.success,
                "response": response.response,
                "processing_time": response.processing_time,
                "confidence": response.confidence,
                "metadata": response.metadata
            },
            "strategy_name": strategy_name,
            "test_message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao testar estratégia {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


def _get_strategy_description(name: str) -> str:
    """Retorna descrição da estratégia"""
    descriptions = {
        "simple": "Estratégia LLM básica para respostas rápidas e simples",
        "advanced": "Estratégia LLM avançada com análise contextual completa",
        "crew": "Estratégia CrewAI para casos complexos e clientes VIP",
        "hybrid": "Estratégia híbrida que combina LLM e CrewAI de forma inteligente"
    }
    return descriptions.get(name, "Estratégia customizada")


@router.get("/health")
async def strategy_system_health():
    """Verifica saúde do sistema de estratégias"""
    try:
        health_status = {
            "system_active": compatibility_service.use_new_system,
            "strategies_count": len(strategy_manager.strategies),
            "global_metrics": strategy_manager.metrics,
            "config": strategy_manager.config,
            "status": "healthy"
        }
        
        # Verificar se há problemas
        success_rate = (
            strategy_manager.metrics["successful_requests"] /
            max(strategy_manager.metrics["total_requests"], 1)
        )
        
        if success_rate < 0.8:
            health_status["status"] = "degraded"
            health_status["warning"] = f"Taxa de sucesso baixa: {success_rate:.2%}"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do sistema: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "unknown"
        }


# CACHE MANAGEMENT ENDPOINTS

@router.get("/cache/stats")
async def get_cache_stats():
    """Retorna estatísticas detalhadas do cache"""
    try:
        return await cache_service.get_cache_stats()
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/cache/health")
async def get_cache_health():
    """Verifica saúde do sistema de cache"""
    try:
        return await cache_service.get_cache_health()
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/cache/clear")
async def clear_cache():
    """Limpa todo o cache do sistema"""
    try:
        await cache_service.clear_all_cache()
        return {
            "success": True,
            "message": "Cache limpo com sucesso",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/cache/clear/{cache_type}")
async def clear_cache_by_type(cache_type: str):
    """Limpa cache de um tipo específico"""
    try:
        # Validar tipo de cache
        valid_types = ["response", "intent", "lead_score", "user_context", "business_data"]
        if cache_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Tipo de cache inválido. Tipos válidos: {valid_types}")
        
        from app.services.cache_service import CacheType
        cache_enum = CacheType(cache_type)
        
        await cache_service.invalidate_cache_by_type(cache_enum)
        return {
            "success": True,
            "message": f"Cache do tipo '{cache_type}' limpo com sucesso",
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao limpar cache do tipo {cache_type}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/cache/clear/user/{user_id}")
async def clear_user_cache(user_id: str):
    """Limpa cache de um usuário específico"""
    try:
        await cache_service.invalidate_user_cache(user_id)
        return {
            "success": True,
            "message": f"Cache do usuário {user_id} limpo com sucesso",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao limpar cache do usuário {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/cache/enable")
async def enable_cache():
    """Habilita o sistema de cache"""
    try:
        cache_service.enabled = True
        if not cache_service.redis:
            await cache_service.initialize()
        
        return {
            "success": True,
            "message": "Cache habilitado com sucesso",
            "enabled": cache_service.enabled,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao habilitar cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/cache/disable")
async def disable_cache():
    """Desabilita o sistema de cache"""
    try:
        cache_service.enabled = False
        return {
            "success": True,
            "message": "Cache desabilitado com sucesso",
            "enabled": cache_service.enabled,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao desabilitar cache: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# === ENDPOINTS DE MÉTRICAS E OBSERVABILIDADE ===

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Retorna resumo completo de todas as métricas"""
    try:
        return {
            "success": True,
            "data": metrics_service.get_metrics_summary(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter resumo de métricas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Endpoint para Prometheus scraping"""
    try:
        metrics_data = metrics_service.export_prometheus_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Erro ao exportar métricas Prometheus: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/metrics/health")
async def get_metrics_health():
    """Health check do sistema de métricas"""
    try:
        return {
            "success": True,
            "data": metrics_service.health_check(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro no health check de métricas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/metrics/track/message")
async def track_custom_message(
    direction: str,
    message_type: str,
    status: str,
    strategy: str = "unknown",
    user_type: str = "standard"
):
    """Endpoint para tracking manual de mensagens"""
    try:
        metrics_service.track_message(direction, message_type, status, strategy, user_type)
        return {
            "success": True,
            "message": "Mensagem tracked com sucesso",
            "tracked_data": {
                "direction": direction,
                "message_type": message_type,
                "status": status,
                "strategy": strategy,
                "user_type": user_type
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao trackear mensagem: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/metrics/track/llm-cost")
async def track_llm_cost(
    cost: float,
    provider: str,
    model: str,
    strategy: str
):
    """Endpoint para tracking de custos LLM"""
    try:
        metrics_service.track_llm_cost(cost, provider, model, strategy)
        return {
            "success": True,
            "message": "Custo LLM tracked com sucesso",
            "tracked_data": {
                "cost": cost,
                "provider": provider,
                "model": model,
                "strategy": strategy
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao trackear custo LLM: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/metrics/conversations/active")
async def get_active_conversations():
    """Retorna número de conversas ativas"""
    try:
        # TODO: Implementar lógica real de contagem de conversas ativas
        # Por enquanto, retorna mock data
        active_count = 42  # Placeholder
        
        metrics_service.update_active_conversations(active_count)
        
        return {
            "success": True,
            "data": {
                "active_conversations": active_count,
                "last_updated": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter conversas ativas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/observability/dashboard")
async def get_observability_dashboard():
    """Retorna dados completos para dashboard de observabilidade"""
    try:
        strategy_stats = strategy_manager.get_stats()
        metrics_summary = metrics_service.get_metrics_summary()
        metrics_health = metrics_service.health_check()
        
        # Combinar cache stats se disponível
        try:
            cache_health = cache_service.health_check()
        except:
            cache_health = {"status": "unknown", "error": "Cache health check failed"}
        
        dashboard_data = {
            "system_status": "operational" if metrics_health["status"] == "healthy" else "degraded",
            "strategy_system": strategy_stats,
            "metrics_system": metrics_summary,
            "metrics_health": metrics_health,
            "cache_health": cache_health,
            "uptime": {
                "strategy_manager": strategy_stats.get("uptime_seconds", 0),
                "metrics_service": metrics_health.get("uptime_seconds", 0)
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


# =====================================
# ENDPOINTS DE GESTÃO DE ESTADO
# =====================================

@router.get("/state/health")
async def get_state_manager_health():
    """Verifica saúde do sistema de gestão de estado"""
    try:
        health = await state_manager.health_check()
        return {
            "success": True,
            "data": health,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao verificar saúde do state manager: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/state/stats")
async def get_state_manager_stats():
    """Retorna estatísticas do sistema de gestão de estado"""
    try:
        stats = state_manager.get_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter stats do state manager: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/state/active-conversations")
async def get_active_conversations():
    """Lista conversas ativas no sistema"""
    try:
        active_users = await state_manager.get_active_conversations()
        
        # Detalhes das conversas ativas
        conversations = []
        for user_id in active_users:
            try:
                state = await state_manager.get_state(user_id)
                conversations.append({
                    "user_id": user_id,
                    "phone": state.phone,
                    "status": state.status.value,
                    "started_at": state.started_at.isoformat(),
                    "last_activity": state.last_activity.isoformat(),
                    "total_messages": state.total_messages,
                    "has_booking": state.booking_context is not None,
                    "booking_step": state.booking_context.step if state.booking_context else None,
                    "duration_minutes": (datetime.now() - state.started_at).total_seconds() / 60
                })
            except Exception as e:
                logger.error(f"Erro ao obter detalhes da conversa {user_id}: {e}")
                conversations.append({
                    "user_id": user_id,
                    "error": "Erro ao obter detalhes"
                })
        
        return {
            "success": True,
            "data": {
                "total_active": len(active_users),
                "conversations": conversations
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter conversas ativas: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/state/conversation/{user_id}")
async def get_conversation_state(user_id: str):
    """Obtém estado completo de uma conversa específica"""
    try:
        state = await state_manager.get_state(user_id)
        
        conversation_data = {
            "user_id": state.user_id,
            "phone": state.phone,
            "status": state.status.value,
            "started_at": state.started_at.isoformat(),
            "last_activity": state.last_activity.isoformat(),
            "total_messages": state.total_messages,
            "session_id": state.session_id,
            "timeout_minutes": state.timeout_minutes,
            "is_expired": state.is_expired(),
            "context_summary": state.get_context_summary(),
            "strategy_history": state.strategy_history,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "message_id": msg.message_id,
                    "metadata": msg.metadata
                }
                for msg in state.messages[-20:]  # Últimas 20 mensagens
            ]
        }
        
        # Adiciona contexto de booking se existir
        if state.booking_context:
            conversation_data["booking_context"] = {
                "service_type": state.booking_context.service_type,
                "preferred_date": state.booking_context.preferred_date,
                "preferred_time": state.booking_context.preferred_time,
                "confirmed": state.booking_context.confirmed,
                "booking_id": state.booking_context.booking_id,
                "step": state.booking_context.step,
                "attempts": state.booking_context.attempts
            }
        
        return {
            "success": True,
            "data": conversation_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter estado da conversa {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.post("/state/conversation/{user_id}/status")
async def update_conversation_status(user_id: str, status: str):
    """Atualiza status de uma conversa"""
    try:
        # Valida status
        try:
            new_status = ConversationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status}")
        
        await state_manager.update_status(user_id, new_status)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "new_status": status,
                "updated_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar status da conversa {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.delete("/state/conversation/{user_id}")
async def delete_conversation_state(user_id: str):
    """Remove estado de uma conversa"""
    try:
        await state_manager.delete_state(user_id)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "deleted_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao deletar estado da conversa {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/state/conversation/{user_id}/history")
async def get_conversation_history(user_id: str, limit: int = 50):
    """Obtém histórico de mensagens de uma conversa"""
    try:
        messages = await state_manager.get_conversation_history(user_id, limit)
        
        history = [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "message_id": msg.message_id,
                "metadata": msg.metadata
            }
            for msg in messages
        ]
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "message_count": len(history),
                "messages": history
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter histórico da conversa {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/state/booking-contexts")
async def get_active_booking_contexts():
    """Lista contextos de booking ativos"""
    try:
        active_users = await state_manager.get_active_conversations()
        booking_contexts = []
        
        for user_id in active_users:
            try:
                state = await state_manager.get_state(user_id)
                if state.booking_context:
                    booking_contexts.append({
                        "user_id": user_id,
                        "phone": state.phone,
                        "service_type": state.booking_context.service_type,
                        "preferred_date": state.booking_context.preferred_date,
                        "preferred_time": state.booking_context.preferred_time,
                        "confirmed": state.booking_context.confirmed,
                        "booking_id": state.booking_context.booking_id,
                        "step": state.booking_context.step,
                        "attempts": state.booking_context.attempts,
                        "started_at": state.started_at.isoformat(),
                        "last_activity": state.last_activity.isoformat()
                    })
            except Exception as e:
                logger.error(f"Erro ao obter booking context de {user_id}: {e}")
        
        return {
            "success": True,
            "data": {
                "total_booking_contexts": len(booking_contexts),
                "contexts": booking_contexts
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter contextos de booking: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/state/dashboard")
async def get_state_dashboard():
    """Dashboard completo do sistema de gestão de estado"""
    try:
        # Stats básicos
        stats = state_manager.get_stats()
        health = await state_manager.health_check()
        active_users = await state_manager.get_active_conversations()
        
        # Estatísticas das conversas ativas
        conversation_stats = {
            "total_active": len(active_users),
            "by_status": {},
            "with_booking": 0,
            "average_duration": 0,
            "total_messages": 0
        }
        
        total_duration = 0
        for user_id in active_users:
            try:
                state = await state_manager.get_state(user_id)
                
                # Count by status
                status = state.status.value
                conversation_stats["by_status"][status] = conversation_stats["by_status"].get(status, 0) + 1
                
                # Count bookings
                if state.booking_context:
                    conversation_stats["with_booking"] += 1
                
                # Sum duration and messages
                duration = (datetime.now() - state.started_at).total_seconds() / 60
                total_duration += duration
                conversation_stats["total_messages"] += state.total_messages
                
            except Exception as e:
                logger.error(f"Erro ao processar stats de {user_id}: {e}")
        
        if len(active_users) > 0:
            conversation_stats["average_duration"] = total_duration / len(active_users)
        
        dashboard = {
            "system_health": health,
            "system_stats": stats,
            "conversation_stats": conversation_stats,
            "redis_status": health.get("redis_available", False),
            "memory_cache_size": health.get("memory_cache_size", 0),
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": dashboard,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard de estado: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
