"""
🚀 Cache Otimizado para Queries Frequentes
==========================================

Sistema de cache Redis otimizado especificamente para queries de API
frequentes, com foco em performance e simplicidade.

Autor: Desenvolvedor
Data: 2025-09-08
"""

import json
import os
import redis
from typing import Any, Optional, Dict, List, Callable
from datetime import timedelta
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OptimizedCacheService:
    """
    🎯 Serviço de Cache Otimizado
    
    Focado em queries frequentes de API com Redis como backend principal.
    Implementa padrão cache-aside com fallback graceful.
    """
    
    def __init__(self):
        """Inicializa conexão Redis com configuração otimizada"""
        self.redis_client = None
        
        try:
            # Configuração Railway Redis
            redis_url = os.getenv('REDIS_URL', 'redis://default:SvSHiMNuuQEtmIUgGIEGqPpXsdZeInDG@yamanote.proxy.rlwy.net:14106')
            
            if redis_url:
                # Conexão Redis Railway
                self.redis_client = redis.Redis.from_url(
                    redis_url,
                    # ✅ Configurações otimizadas para Railway
                    decode_responses=True,
                    socket_connect_timeout=10,  # Aumentado para Railway
                    socket_timeout=10,          # Aumentado para Railway
                    retry_on_timeout=True,
                    health_check_interval=30,
                    max_connections=20          # Pool de conexões
                )
                
                # Teste de conectividade
                self.redis_client.ping()
                logger.info("✅ Redis cache service initialized successfully (Railway)")
            else:
                logger.warning("⚠️ No Redis URL configured, cache disabled")
                
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.info("🔄 Running without cache - performance may be degraded")
            self.redis_client = None
        
        # ✅ Configurações de TTL por tipo de dado
        self.ttl_configs = {
            'appointments_list': 120,      # 2 minutos para listas
            'appointment_detail': 300,     # 5 minutos para detalhes
            'conversations_list': 60,      # 1 minuto para conversas
            'dashboard_stats': 180,        # 3 minutos para stats
            'business_config': 600,        # 10 minutos para configurações
            'user_profile': 900,           # 15 minutos para perfis
            'default': 300                 # 5 minutos padrão
        }
    
    async def get_or_set(
        self, 
        key: str, 
        fetch_function: Callable, 
        ttl: Optional[int] = None,
        cache_type: str = 'default'
    ) -> Any:
        """
        🎯 Padrão Cache-Aside Otimizado
        
        Busca no cache primeiro, se não encontrar executa a função
        e armazena o resultado com TTL configurado.
        
        Args:
            key: Chave única do cache
            fetch_function: Função async para buscar dados
            ttl: Time to live em segundos (opcional)
            cache_type: Tipo do cache para TTL automático
        
        Returns:
            Dados do cache ou resultado da função
        """
        if not self.redis_client:
            # Modo sem cache - executa função diretamente
            logger.warning(f"Cache disabled, executing function for key: {key}")
            return await fetch_function()
        
        try:
            # ✅ Tentar buscar do cache
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                logger.debug(f"🎯 Cache HIT: {key}")
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Cache data corruption for {key}: {e}")
                    # Remove cache corrompido
                    self.redis_client.delete(key)
            
            # ✅ Cache miss - buscar dados frescos
            logger.debug(f"💨 Cache MISS: {key}")
            start_time = time.time()
            
            data = await fetch_function()
            
            fetch_time = time.time() - start_time
            logger.debug(f"📊 Function executed in {fetch_time:.3f}s for key: {key}")
            
            # ✅ Salvar no cache com TTL apropriado
            cache_ttl = ttl or self.ttl_configs.get(cache_type, self.ttl_configs['default'])
            
            # Serializar com handling de tipos especiais
            serialized_data = json.dumps(data, default=self._json_serializer, ensure_ascii=False)
            
            self.redis_client.setex(key, cache_ttl, serialized_data)
            logger.debug(f"💾 Cached data for {key} with TTL {cache_ttl}s")
            
            return data
            
        except redis.RedisError as e:
            logger.error(f"❌ Redis error for key {key}: {e}")
            # Fallback graceful - executar função sem cache
            return await fetch_function()
        
        except Exception as e:
            logger.error(f"❌ Unexpected cache error for key {key}: {e}")
            # Fallback graceful
            return await fetch_function()
    
    def get(self, key: str) -> Optional[Any]:
        """
        🔍 Buscar apenas do cache (sem fallback)
        
        Args:
            key: Chave do cache
            
        Returns:
            Dados do cache ou None se não encontrado
        """
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"❌ Cache get error for {key}: {e}")
            return None
    
    def set(
        self, 
        key: str, 
        data: Any, 
        ttl: Optional[int] = None,
        cache_type: str = 'default'
    ) -> bool:
        """
        💾 Armazenar dados no cache
        
        Args:
            key: Chave do cache
            data: Dados para armazenar
            ttl: Time to live em segundos
            cache_type: Tipo do cache para TTL automático
            
        Returns:
            True se sucesso, False se erro
        """
        if not self.redis_client:
            return False
        
        try:
            cache_ttl = ttl or self.ttl_configs.get(cache_type, self.ttl_configs['default'])
            serialized_data = json.dumps(data, default=self._json_serializer, ensure_ascii=False)
            
            result = self.redis_client.setex(key, cache_ttl, serialized_data)
            if result:
                logger.debug(f"💾 Data cached for {key} with TTL {cache_ttl}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Cache set error for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        🗑️ Remover item do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            True se removido ou não existia, False se erro
        """
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"🗑️ Cache key deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"❌ Cache delete error for {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        🧹 Invalidar cache por padrão (wildcard)
        
        Args:
            pattern: Padrão de chaves (ex: "appointments:*", "user:123:*")
            
        Returns:
            Número de chaves removidas
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"🧹 Invalidated {deleted_count} cache keys matching: {pattern}")
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"❌ Cache pattern invalidation error for {pattern}: {e}")
            return 0
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """
        👤 Invalidar todo cache relacionado a um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Número de chaves removidas
        """
        patterns = [
            f"appointments:user:{user_id}:*",
            f"conversations:user:{user_id}:*",
            f"user:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.invalidate_pattern(pattern)
        
        logger.info(f"👤 Invalidated {total_deleted} cache entries for user {user_id}")
        return total_deleted
    
    def invalidate_business_cache(self, business_id: int) -> int:
        """
        🏢 Invalidar todo cache relacionado a um negócio
        
        Args:
            business_id: ID do negócio
            
        Returns:
            Número de chaves removidas
        """
        patterns = [
            f"appointments:business:{business_id}:*",
            f"conversations:business:{business_id}:*",
            f"dashboard:business:{business_id}:*",
            f"business:{business_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            total_deleted += self.invalidate_pattern(pattern)
        
        logger.info(f"🏢 Invalidated {total_deleted} cache entries for business {business_id}")
        return total_deleted
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        📊 Informações sobre o cache (debug/monitoring)
        
        Returns:
            Dicionário com estatísticas do cache
        """
        if not self.redis_client:
            return {"status": "disabled", "error": "Redis not available"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "active",
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), 
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"❌ Error getting cache info: {e}")
            return {"status": "error", "error": str(e)}
    
    def health_check(self) -> bool:
        """
        ❤️ Verificação de saúde do cache
        
        Returns:
            True se cache está funcionando, False caso contrário
        """
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"❌ Cache health check failed: {e}")
            return False
    
    def _json_serializer(self, obj):
        """
        🔄 Serializer customizado para tipos especiais
        
        Handles datetime, Decimal, e outros tipos não-JSON nativos
        """
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Objects with __dict__
            return obj.__dict__
        elif hasattr(obj, 'to_dict'):  # Objects with to_dict method
            return obj.to_dict()
        else:
            return str(obj)
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """
        📈 Calcular taxa de acerto do cache
        
        Args:
            hits: Número de hits
            misses: Número de misses
            
        Returns:
            Taxa de acerto em porcentagem
        """
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100


# ✅ Instância global singleton
cache_service = OptimizedCacheService()


# ✅ Decorador para cache automático
def cached(
    key_template: str,
    ttl: Optional[int] = None,
    cache_type: str = 'default'
):
    """
    🎯 Decorador para cache automático de funções
    
    Args:
        key_template: Template da chave (ex: "user:{user_id}:profile")
        ttl: Time to live em segundos
        cache_type: Tipo do cache
    
    Usage:
        @cached("appointments:list:{limit}:{page}")
        async def get_appointments(limit, page):
            return fetch_appointments()
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Gerar chave do cache baseada nos argumentos
            format_args = {}
            format_args.update(kwargs)
            for i, arg in enumerate(args):
                format_args[f'arg_{i}'] = arg
            cache_key = key_template.format(**format_args)
            
            async def fetch_data():
                return await func(*args, **kwargs)
            
            return await cache_service.get_or_set(
                cache_key, 
                fetch_data, 
                ttl=ttl, 
                cache_type=cache_type
            )
        
        return wrapper
    return decorator


# ✅ Context manager para invalidação automática
class CacheInvalidationContext:
    """
    🧹 Context manager para invalidação automática de cache
    
    Usage:
        async with CacheInvalidationContext(["appointments:*"]):
            # Operações que invalidam cache
            await create_appointment()
    """
    
    def __init__(self, patterns: List[str]):
        self.patterns = patterns
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:  # Apenas se não houve erro
            for pattern in self.patterns:
                cache_service.invalidate_pattern(pattern)


# ✅ Utilitários para chaves de cache
class CacheKeys:
    """
    🗝️ Gerador padronizado de chaves de cache
    
    Centraliza a criação de chaves para evitar inconsistências
    """
    
    @staticmethod
    def appointments_list(
        limit: int, 
        page: int, 
        status: Optional[str] = None,
        business_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> str:
        """Chave para lista de agendamentos"""
        return f"appointments:list:{business_id or 'all'}:{limit}:{page}:{status or 'all'}:{date_from or 'none'}:{date_to or 'none'}"
    
    @staticmethod
    def appointment_detail(appointment_id: int) -> str:
        """Chave para detalhes de agendamento"""
        return f"appointment:detail:{appointment_id}"
    
    @staticmethod
    def conversations_list(
        limit: int, 
        page: int, 
        business_id: Optional[int] = None
    ) -> str:
        """Chave para lista de conversas"""
        return f"conversations:list:{business_id or 'all'}:{limit}:{page}"
    
    @staticmethod
    def dashboard_stats(
        business_id: int, 
        period: str = 'daily'
    ) -> str:
        """Chave para estatísticas do dashboard"""
        return f"dashboard:stats:{business_id}:{period}"
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        """Chave para perfil de usuário"""
        return f"user:profile:{user_id}"
    
    @staticmethod
    def business_config(business_id: int) -> str:
        """Chave para configurações do negócio"""
        return f"business:config:{business_id}"


import time
