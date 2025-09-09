"""
🔄 Decorators para Cache Invalidation Automática
============================================== 

Decorators que automatizam a invalidação de cache após operações,
eliminando a necessidade de chamar manualmente as funções de invalidação.

Funcionalidades:
- Auto-invalidation baseado em eventos
- Extração automática de entity_id
- Suporte a context dinâmico
- Logging automático
- Tratamento de erros graceful

Autor: Claude AI
Status: Solução crítica para cache consistency
"""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional, Dict, Union
from app.services.cache_invalidation import CacheEvent, cache_invalidation_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


def invalidate_cache(
    event: CacheEvent, 
    entity_id_param: str = "id", 
    extract_from_result: bool = True,
    **static_kwargs
):
    """
    🎯 Decorator que invalida cache automaticamente após operações
    
    Args:
        event: Evento de cache a ser invalidado
        entity_id_param: Nome do parâmetro que contém o ID da entidade
        extract_from_result: Se deve extrair ID do resultado da função
        **static_kwargs: Valores estáticos para context
    
    Usage:
        @invalidate_cache(CacheEvent.APPOINTMENT_CREATED)
        async def create_appointment(appointment_data):
            # ... lógica ...
            return new_appointment
        
        @invalidate_cache(
            CacheEvent.APPOINTMENT_UPDATED, 
            entity_id_param="appointment_id"
        )
        async def update_appointment(appointment_id: int, data):
            # ... lógica ...
            return updated_appointment
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Executar função original
            result = await func(*args, **kwargs)
            
            try:
                # Extrair entity_id do resultado ou parâmetros
                entity_id = None
                context = dict(static_kwargs)  # Cópia dos valores estáticos
                
                # Tentativa 1: Extrair do resultado
                if extract_from_result and result:
                    if hasattr(result, 'id'):
                        entity_id = result.id
                    elif hasattr(result, 'appointment_id'):
                        entity_id = result.appointment_id
                    elif isinstance(result, dict) and 'id' in result:
                        entity_id = result['id']
                    elif isinstance(result, dict) and 'appointment_id' in result:
                        entity_id = result['appointment_id']
                
                # Tentativa 2: Extrair dos parâmetros
                if not entity_id and entity_id_param in kwargs:
                    entity_id = kwargs[entity_id_param]
                
                # Construir context com informações extraídas
                if entity_id:
                    if 'appointment' in event.value:
                        context['appointment_id'] = entity_id
                    elif 'conversation' in event.value:
                        context['conversation_id'] = entity_id
                    elif 'client' in event.value:
                        context['client_id'] = entity_id
                
                # Adicionar outros campos relevantes do resultado
                if result and hasattr(result, 'user_id'):
                    context['client_id'] = result.user_id
                if result and hasattr(result, 'business_id'):
                    context['business_id'] = result.business_id
                
                # Adicionar campos relevantes dos parâmetros
                for param_name in ['client_id', 'user_id', 'business_id']:
                    if param_name in kwargs:
                        context[param_name] = kwargs[param_name]
                
                # Invalidar cache
                await cache_invalidation_service.invalidate_for_event(
                    event=event,
                    context=context if context else None
                )
                
                logger.debug(f"✅ Cache invalidated automatically - Event: {event.value}, Context: {context}")
                
            except Exception as e:
                logger.error(f"❌ Erro na invalidação automática de cache: {e}")
                # Não falhar a operação principal por erro no cache
                pass
            
            return result
        return wrapper
    return decorator


def invalidate_multiple_caches(*events_and_configs):
    """
    🎯 Decorator para invalidar múltiplos caches
    
    Args:
        *events_and_configs: Lista de eventos ou tuplas (evento, config)
    
    Usage:
        @invalidate_multiple_caches(
            CacheEvent.APPOINTMENT_CREATED,
            (CacheEvent.CLIENT_UPDATED, {"extract_from_result": False})
        )
        async def create_appointment_with_client_update(data):
            # ... lógica ...
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Processar cada evento
            invalidation_tasks = []
            
            for event_config in events_and_configs:
                if isinstance(event_config, tuple):
                    event, config = event_config
                else:
                    event = event_config
                    config = {}
                
                # Criar task de invalidação
                task = _invalidate_for_event_with_config(
                    event, result, kwargs, config
                )
                invalidation_tasks.append(task)
            
            # Executar invalidações em paralelo
            if invalidation_tasks:
                await asyncio.gather(*invalidation_tasks, return_exceptions=True)
            
            return result
        return wrapper
    return decorator


async def _invalidate_for_event_with_config(
    event: CacheEvent,
    result: Any,
    func_kwargs: Dict[str, Any],
    config: Dict[str, Any]
):
    """Helper para invalidar cache com configuração específica"""
    try:
        extract_from_result = config.get('extract_from_result', True)
        entity_id_param = config.get('entity_id_param', 'id')
        static_kwargs = {k: v for k, v in config.items() 
                        if k not in ['extract_from_result', 'entity_id_param']}
        
        # Extrair entity_id
        entity_id = None
        context = dict(static_kwargs)
        
        if extract_from_result and result:
            if hasattr(result, 'id'):
                entity_id = result.id
            elif isinstance(result, dict) and 'id' in result:
                entity_id = result['id']
        
        if not entity_id and entity_id_param in func_kwargs:
            entity_id = func_kwargs[entity_id_param]
        
        # Construir context
        if entity_id:
            if 'appointment' in event.value:
                context['appointment_id'] = entity_id
            elif 'conversation' in event.value:
                context['conversation_id'] = entity_id
            elif 'client' in event.value:
                context['client_id'] = entity_id
        
        # Invalidar cache
        await cache_invalidation_service.invalidate_for_event(
            event=event,
            context=context if context else None
        )
        
    except Exception as e:
        logger.error(f"❌ Erro na invalidação múltipla de cache: {e}")


def cache_on_success(cache_key_template: str, ttl: int = 3600):
    """
    💾 Decorator que armazena resultado em cache apenas em caso de sucesso
    
    Args:
        cache_key_template: Template da chave de cache (pode usar {param_name})
        ttl: Time to live em segundos
    
    Usage:
        @cache_on_success("appointment:detail:{appointment_id}", ttl=300)
        async def get_appointment(appointment_id: int):
            # ... lógica ...
            return appointment
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from app.services.cache_optimized import cache_service
            
            # Construir chave de cache
            cache_key = cache_key_template.format(**kwargs)
            
            try:
                # Tentar buscar do cache primeiro
                cached = cache_service.get(cache_key)
                if cached:
                    logger.debug(f"💾 Cache hit: {cache_key}")
                    return cached
                
            except Exception as e:
                logger.debug(f"Cache lookup falhou: {e}")
            
            # Executar função e cachear resultado
            result = await func(*args, **kwargs)
            
            try:
                if result:  # Só cachear se há resultado válido
                    cache_service.set(cache_key, result, ttl=ttl)
                    logger.debug(f"💾 Cached result: {cache_key}")
                    
            except Exception as e:
                logger.debug(f"Cache store falhou: {e}")
            
            return result
        return wrapper
    return decorator


# ===== DECORATORS ESPECÍFICOS =====

def invalidate_appointment_cache_on_success(event: CacheEvent):
    """🎯 Decorator específico para operações de appointment"""
    return invalidate_cache(
        event, 
        entity_id_param="appointment_id",
        extract_from_result=True
    )


def invalidate_conversation_cache_on_success(event: CacheEvent):
    """🎯 Decorator específico para operações de conversation"""
    return invalidate_cache(
        event,
        entity_id_param="conversation_id", 
        extract_from_result=True
    )


def invalidate_client_cache_on_success(event: CacheEvent):
    """🎯 Decorator específico para operações de client"""
    return invalidate_cache(
        event,
        entity_id_param="client_id",
        extract_from_result=True
    )


# ===== LOGGING HELPERS =====

def log_cache_invalidation_activity():
    """📊 Log atividade recente de cache invalidation"""
    # Esta função pode ser expandida para mostrar métricas
    logger.info("📊 Cache invalidation decorators carregados")
    logger.info("🎯 Eventos suportados:")
    for event in CacheEvent:
        logger.info(f"  - {event.value}")
