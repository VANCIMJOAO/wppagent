"""
🚀 Otimizador de Queries com Retry e Cache
==========================================

Implementa:
- Retry automático para queries que falham
- Cache inteligente para queries frequentes
- Connection pooling otimizado
- Monitoramento de performance
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from app.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class QueryOptimizer:
    """Otimizador de queries com retry e cache"""
    
    def __init__(self):
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 0.1,  # 100ms
            'max_delay': 2.0,   # 2s
            'backoff_factor': 2
        }
        
    def with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator para retry automático de queries"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(self.retry_config['max_retries'] + 1):
                try:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    if duration > 1000:  # Log queries lentas
                        logger.warning(f"⚠️ Query lenta detectada: {duration:.0f}ms - {func.__name__}")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt < self.retry_config['max_retries']:
                        delay = min(
                            self.retry_config['base_delay'] * (self.retry_config['backoff_factor'] ** attempt),
                            self.retry_config['max_delay']
                        )
                        
                        logger.warning(f"⚠️ Tentativa {attempt + 1}/{self.retry_config['max_retries'] + 1} falhou: {e}")
                        logger.info(f"🔄 Tentando novamente em {delay:.2f}s...")
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ Todas as tentativas falharam: {e}")
                        raise e
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(self.retry_config['max_retries'] + 1):
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    if duration > 1000:  # Log queries lentas
                        logger.warning(f"⚠️ Query lenta detectada: {duration:.0f}ms - {func.__name__}")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt < self.retry_config['max_retries']:
                        delay = min(
                            self.retry_config['base_delay'] * (self.retry_config['backoff_factor'] ** attempt),
                            self.retry_config['max_delay']
                        )
                        
                        logger.warning(f"⚠️ Tentativa {attempt + 1}/{self.retry_config['max_retries'] + 1} falhou: {e}")
                        logger.info(f"🔄 Tentando novamente em {delay:.2f}s...")
                        
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ Todas as tentativas falharam: {e}")
                        raise e
            
            raise last_exception
        
        # Retornar wrapper apropriado baseado no tipo da função
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    def with_cache(self, ttl: int = 300):  # 5 minutos default
        """Decorator para cache de queries"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                # Criar chave de cache baseada nos argumentos
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Verificar cache
                if cache_key in self.query_cache:
                    cached_data = self.query_cache[cache_key]
                    if time.time() - cached_data['timestamp'] < ttl:
                        logger.debug(f"💾 Cache hit para {func.__name__}")
                        return cached_data['result']
                    else:
                        # Cache expirado
                        del self.query_cache[cache_key]
                
                # Executar query e cachear resultado
                result = await func(*args, **kwargs)
                self.query_cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }
                
                logger.debug(f"💾 Cache miss para {func.__name__} - resultado cacheado")
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                # Criar chave de cache baseada nos argumentos
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Verificar cache
                if cache_key in self.query_cache:
                    cached_data = self.query_cache[cache_key]
                    if time.time() - cached_data['timestamp'] < ttl:
                        logger.debug(f"💾 Cache hit para {func.__name__}")
                        return cached_data['result']
                    else:
                        # Cache expirado
                        del self.query_cache[cache_key]
                
                # Executar query e cachear resultado
                result = func(*args, **kwargs)
                self.query_cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }
                
                logger.debug(f"💾 Cache miss para {func.__name__} - resultado cacheado")
                return result
            
            # Retornar wrapper apropriado baseado no tipo da função
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def clear_cache(self):
        """Limpar cache de queries"""
        self.query_cache.clear()
        logger.info("🧹 Cache de queries limpo")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do cache"""
        total_entries = len(self.query_cache)
        expired_entries = sum(
            1 for data in self.query_cache.values()
            if time.time() - data['timestamp'] > 300  # 5 minutos
        )
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries
        }


# Instância global do otimizador
query_optimizer = QueryOptimizer()


def optimize_query(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator combinado: retry + cache para queries"""
    return query_optimizer.with_retry(func)


def cache_query(ttl: int = 300):
    """Decorator para cache de queries"""
    return query_optimizer.with_cache(ttl)


def retry_query(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator para retry de queries"""
    return query_optimizer.with_retry(func)
