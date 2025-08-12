"""
🚀 Sistema de Cache Otimizado para WhatsApp Agent
Cache inteligente com Redis e fallback para memória, operações críticas otimizadas
"""
import json
import hashlib
import asyncio
import time
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Any, Dict, List, Union, Callable
import redis

from app.config import settings
from app.utils.logger import get_logger
from app.config.redis_config import redis_manager

logger = get_logger(__name__)
logger = logging.getLogger(__name__)


class CacheType(Enum):
    """Tipos de cache disponíveis"""
    RESPONSE = "response"
    INTENT = "intent"
    LEAD_SCORE = "lead_score"
    USER_CONTEXT = "user_context"
    BUSINESS_DATA = "business_data"
    QUERY_RESULT = "query_result"
    API_RESPONSE = "api_response"


@dataclass
class CacheEntry:
    """Entrada de cache estruturada"""
    data: Any
    timestamp: str
    ttl: int
    cache_type: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class OptimizedCacheService:
    """
    🚀 Serviço de Cache Otimizado
    
    Funcionalidades:
    - Cache Redis com connection pooling
    - Fallback para cache em memória
    - Cache inteligente de queries
    - Cache de respostas frequentes
    - Cache de análises de intenção
    - Cache de contexto do usuário
    - TTL configurável por tipo
    - Invalidação inteligente
    - Métricas de performance
    - Compressão automática
    """
    
    def __init__(self):
        self.redis_available = redis_manager.is_available
        self.redis = redis_manager.client
        self.redis_pool = None
        self.enabled = getattr(settings, "cache_enabled", True)
        
        # Cache em memória como fallback
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.memory_cache_timestamps: Dict[str, datetime] = {}
        
        # Configuração Redis otimizada
        if self.redis_available:
            logger.info(f"🚀 OptimizedCacheService inicializado - Redis: {self.redis_available}")
        else:
            logger.info("🚀 OptimizedCacheService inicializado - Redis: False (usando cache em memória)")
        
        # Configurar TTL padrão por tipo
        self.default_ttl = {
            CacheType.RESPONSE: 3600,        # 1 hora - respostas reutilizáveis
            CacheType.INTENT: 1800,          # 30 min - intenções estáveis
            CacheType.LEAD_SCORE: 7200,      # 2 horas - lead score lento para mudar
            CacheType.USER_CONTEXT: 900,     # 15 min - contexto dinâmico
            CacheType.BUSINESS_DATA: 14400,  # 4 horas - dados negócio estáveis
            CacheType.QUERY_RESULT: 600,     # 10 min - queries podem mudar
            CacheType.API_RESPONSE: 300      # 5 min - API responses
        }
        
        # Configuração de compressão
        self.compression_threshold = 1024  # 1KB
        
        # Inicializar conectividade
        self._setup_connections()
        
        # Prefixos organizacionais
        self.prefixes = {
            CacheType.RESPONSE: "wa:resp",
            CacheType.INTENT: "wa:intent", 
            CacheType.LEAD_SCORE: "wa:lead",
            CacheType.USER_CONTEXT: "wa:ctx",
            CacheType.BUSINESS_DATA: "wa:biz",
            CacheType.QUERY_RESULT: "wa:query",
            CacheType.API_RESPONSE: "wa:api"
        }
        
        # Métricas detalhadas
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "total_requests": 0,
            "memory_usage": 0,
            "redis_operations": 0,
            "compression_savings": 0
        }
        
        # Cache de operações críticas
        self.critical_operations = {
            "user_lookups": {},
            "conversation_history": {},
            "intent_analysis": {},
            "response_generation": {}
        }
        
        logger.info(f"🚀 OptimizedCacheService inicializado - Redis: {self.redis_available}")
    
    def _setup_connections(self):
        """Configura conexões com Redis usando redis_manager"""
        # Não fazer nada especial aqui - redis_manager já cuida da conexão
        # Esta versão usa redis_manager que já fez toda a detecção
        pass
    
    async def initialize(self):
        """Inicializa conexão otimizada com Redis"""
        if not self.enabled:
            logger.info("Cache desabilitado")
            return False
            
        if self.redis_available and self.redis:
            try:
                # Testar se Redis está funcionando
                await asyncio.get_event_loop().run_in_executor(None, self.redis.ping)
                logger.info("✅ Conexão Redis estabelecida via redis_manager")
                return True
            except Exception as e:
                logger.debug(f"Redis ping falhou: {e}")
                return False
        else:
            # Redis não disponível - usar cache em memória sem warning
            logger.debug("Cache funcionando em modo memória (Redis não disponível)")
            return False
    
    def _compress_data(self, data: str) -> bytes:
        """Comprime dados para economizar memória"""
        try:
            import gzip
            compressed = gzip.compress(data.encode('utf-8'))
            savings = len(data.encode('utf-8')) - len(compressed)
            self.metrics["compression_savings"] += savings
            return compressed
        except:
            return data.encode('utf-8')
    
    def _decompress_data(self, data: bytes) -> str:
        """Descomprime dados"""
        try:
            import gzip
            return gzip.decompress(data).decode('utf-8')
        except:
            return data.decode('utf-8')
    
    async def set(self, key: str, data: Any, cache_type: CacheType, ttl: int = None) -> bool:
        """
        Armazena dados no cache com compressão automática
        """
        if not self.enabled:
            return False
            
        try:
            # TTL padrão baseado no tipo
            if ttl is None:
                ttl = self.ttl_config[cache_type]
            
            # Criar entrada estruturada
            cache_entry = CacheEntry(
                data=data,
                timestamp=datetime.now().isoformat(),
                ttl=ttl,
                cache_type=cache_type.value,
                metadata={
                    "size": len(str(data)) if data else 0,
                    "created_at": datetime.now().isoformat(),
                    "compressed": True
                }
            )
            
            # Chave com prefixo
            cache_key = f"{self.prefixes[cache_type]}:{key}"
            
            # Serializar e comprimir dados
            serialized_data = json.dumps(asdict(cache_entry), default=str)
            
            # Tentar Redis primeiro
            if self.redis:
                compressed_data = self._compress_data(serialized_data)
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis.setex, cache_key, ttl, compressed_data
                )
                self.metrics["redis_operations"] += 1
            else:
                # Fallback para memória
                self.memory_cache[cache_key] = cache_entry
                self.memory_cache_timestamps[cache_key] = datetime.now() + timedelta(seconds=ttl)
                self.metrics["memory_usage"] += len(serialized_data)
            
            self.metrics["sets"] += 1
            logger.debug(f"📝 Cache SET: {cache_key} (TTL: {ttl}s, Type: {cache_type.value})")
            return True
            
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"❌ Erro ao definir cache {key}: {e}")
            return False
    
    async def get(self, key: str, cache_type: CacheType) -> Optional[Any]:
        """
        Recupera dados do cache com descompressão automática
        """
        if not self.enabled:
            return None
            
        try:
            self.metrics["total_requests"] += 1
            cache_key = f"{self.prefixes[cache_type]}:{key}"
            
            # Tentar Redis primeiro
            if self.redis:
                cached_data = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis.get, cache_key
                )
                
                if cached_data:
                    # Descomprimir se necessário
                    if isinstance(cached_data, bytes):
                        decompressed_data = self._decompress_data(cached_data)
                    else:
                        decompressed_data = cached_data
                    
                    entry_dict = json.loads(decompressed_data)
                    entry = CacheEntry(**entry_dict)
                    
                    self.metrics["hits"] += 1
                    self.metrics["redis_operations"] += 1
                    logger.debug(f"✅ Redis Cache HIT: {cache_key}")
                    return entry.data
            else:
                # Verificar cache em memória
                if cache_key in self.memory_cache:
                    # Verificar se não expirou
                    if datetime.now() < self.memory_cache_timestamps[cache_key]:
                        entry = self.memory_cache[cache_key]
                        self.metrics["hits"] += 1
                        logger.debug(f"✅ Memory Cache HIT: {cache_key}")
                        return entry.data
                    else:
                        # Remover entrada expirada
                        self._remove_from_memory_cache(cache_key)
            
            self.metrics["misses"] += 1
            logger.debug(f"❌ Cache MISS: {cache_key}")
            return None
            
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"❌ Erro ao buscar cache {key}: {e}")
            return None
    
    def _remove_from_memory_cache(self, cache_key: str):
        """Remove entrada do cache em memória"""
        if cache_key in self.memory_cache:
            entry_size = len(str(self.memory_cache[cache_key]))
            del self.memory_cache[cache_key]
            self.metrics["memory_usage"] -= entry_size
        if cache_key in self.memory_cache_timestamps:
            del self.memory_cache_timestamps[cache_key]
    
    async def delete(self, key: str, cache_type: CacheType = None) -> bool:
        """
        Remove dados do cache com suporte a padrões
        """
        if not self.enabled:
            return False
            
        try:
            if cache_type:
                cache_key = f"{self.prefixes[cache_type]}:{key}"
            else:
                cache_key = key
            
            # Tentar Redis primeiro
            if self.redis:
                # Se key contém wildcard, usar scan
                if '*' in cache_key:
                    keys = await asyncio.get_event_loop().run_in_executor(
                        None, self.redis.keys, cache_key
                    )
                    if keys:
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.redis.delete, *keys
                        )
                        self.metrics["deletes"] += len(keys)
                        self.metrics["redis_operations"] += len(keys)
                        logger.debug(f"🗑️ Redis Cache DELETE: {len(keys)} chaves removidas")
                        return True
                else:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, self.redis.delete, cache_key
                    )
                    if result:
                        self.metrics["deletes"] += 1
                        self.metrics["redis_operations"] += 1
                    logger.debug(f"🗑️ Redis Cache DELETE: {cache_key}")
                    return bool(result)
            else:
                # Cache em memória
                if '*' in cache_key:
                    # Buscar por padrão
                    pattern = cache_key.replace('*', '')
                    keys_to_remove = [k for k in self.memory_cache.keys() if pattern in k]
                    for k in keys_to_remove:
                        self._remove_from_memory_cache(k)
                    self.metrics["deletes"] += len(keys_to_remove)
                    logger.debug(f"🗑️ Memory Cache DELETE: {len(keys_to_remove)} chaves removidas")
                    return len(keys_to_remove) > 0
                else:
                    if cache_key in self.memory_cache:
                        self._remove_from_memory_cache(cache_key)
                        self.metrics["deletes"] += 1
                        logger.debug(f"🗑️ Memory Cache DELETE: {cache_key}")
                        return True
            
            return False
            
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"❌ Erro ao deletar cache {key}: {e}")
            return False
    
    async def get_or_set(self, 
                        key: str, 
                        cache_type: CacheType, 
                        data_function: Callable,
                        ttl: int = None,
                        **kwargs) -> Any:
        """
        Busca no cache ou executa função se não existir (Cache-aside pattern)
        """
        # Tentar buscar no cache primeiro
        cached_data = await self.get(key, cache_type)
        if cached_data is not None:
            return cached_data
        
        # Executar função para obter dados
        try:
            if asyncio.iscoroutinefunction(data_function):
                fresh_data = await data_function(**kwargs)
            else:
                fresh_data = data_function(**kwargs)
            
            # Armazenar no cache se dados válidos
            if fresh_data is not None:
                await self.set(key, fresh_data, cache_type, ttl)
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar função para cache {key}: {e}")
            return None
    
    async def cache_user_context(self, wa_id: str, context: Dict[str, Any], ttl: int = 900):
        """Cache otimizado do contexto do usuário"""
        return await self.set(f"user_context_{wa_id}", context, CacheType.USER_CONTEXT, ttl)
    
    async def get_user_context(self, wa_id: str) -> Optional[Dict[str, Any]]:
        """Recupera contexto do usuário"""
        return await self.get(f"user_context_{wa_id}", CacheType.USER_CONTEXT)
    
    async def cache_intent_analysis(self, message: str, intent_data: Dict[str, Any], ttl: int = 1800):
        """Cache de análise de intenção com hash da mensagem"""
        message_hash = hashlib.md5(message.lower().strip().encode()).hexdigest()
        return await self.set(f"intent_{message_hash}", intent_data, CacheType.INTENT, ttl)
    
    async def get_intent_analysis(self, message: str) -> Optional[Dict[str, Any]]:
        """Recupera análise de intenção"""
        message_hash = hashlib.md5(message.lower().strip().encode()).hexdigest()
        return await self.get(f"intent_{message_hash}", CacheType.INTENT)
    
    async def cache_response(self, context_key: str, response: str, ttl: int = 3600):
        """Cache de resposta gerada"""
        return await self.set(f"response_{context_key}", response, CacheType.RESPONSE, ttl)
    
    async def get_cached_response(self, context_key: str) -> Optional[str]:
        """Recupera resposta em cache"""
        return await self.get(f"response_{context_key}", CacheType.RESPONSE)
    
    async def cache_query_result(self, query_hash: str, result: Any, ttl: int = 600):
        """Cache de resultado de query de banco"""
        return await self.set(f"query_{query_hash}", result, CacheType.QUERY_RESULT, ttl)
    
    async def get_query_result(self, query_hash: str) -> Optional[Any]:
        """Recupera resultado de query"""
        return await self.get(f"query_{query_hash}", CacheType.QUERY_RESULT)
    
    async def cache_api_response(self, api_key: str, response: Any, ttl: int = 300):
        """Cache de resposta de API externa"""
        return await self.set(f"api_{api_key}", response, CacheType.API_RESPONSE, ttl)
    
    async def get_api_response(self, api_key: str) -> Optional[Any]:
        """Recupera resposta de API externa"""
        return await self.get(f"api_{api_key}", CacheType.API_RESPONSE)
    
    async def invalidate_user_cache(self, wa_id: str):
        """Invalida todo cache relacionado ao usuário"""
        patterns = [
            f"{self.prefixes[CacheType.USER_CONTEXT]}:user_context_{wa_id}*",
            f"{self.prefixes[CacheType.RESPONSE]}:*{wa_id}*",
            f"{self.prefixes[CacheType.LEAD_SCORE]}:*{wa_id}*"
        ]
        
        for pattern in patterns:
            await self.delete(pattern)
    
    async def clear_by_type(self, cache_type: CacheType) -> bool:
        """Remove todos os dados de um tipo específico"""
        pattern = f"{self.prefixes[cache_type]}:*"
        return await self.delete(pattern)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas detalhadas do cache
        """
        stats = {
            "enabled": self.enabled,
            "redis_available": self.redis_available,
            "redis_connected": bool(self.redis),
            "metrics": self.metrics.copy(),
            "memory_cache_size": len(self.memory_cache),
            "memory_usage_bytes": self.metrics["memory_usage"],
            "ttl_config": {k.value: v for k, v in self.ttl_config.items()}
        }
        
        # Calcular hit rate
        total_requests = self.metrics["total_requests"]
        if total_requests > 0:
            stats["hit_rate"] = round(self.metrics["hits"] / total_requests * 100, 2)
            stats["miss_rate"] = round(self.metrics["misses"] / total_requests * 100, 2)
        else:
            stats["hit_rate"] = 0
            stats["miss_rate"] = 0
        
        # Informações do Redis se disponível
        if self.redis:
            try:
                redis_info = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis.info
                )
                stats["redis_info"] = {
                    "used_memory": redis_info.get("used_memory_human", "N/A"),
                    "used_memory_peak": redis_info.get("used_memory_peak_human", "N/A"),
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "total_commands_processed": redis_info.get("total_commands_processed", 0),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0),
                    "evicted_keys": redis_info.get("evicted_keys", 0)
                }
                
                # Hit rate do Redis
                redis_hits = redis_info.get("keyspace_hits", 0)
                redis_misses = redis_info.get("keyspace_misses", 0)
                redis_total = redis_hits + redis_misses
                if redis_total > 0:
                    stats["redis_hit_rate"] = round(redis_hits / redis_total * 100, 2)
                else:
                    stats["redis_hit_rate"] = 0
                    
            except Exception as e:
                logger.warning(f"Erro ao obter informações do Redis: {e}")
                stats["redis_info"] = {"error": str(e)}
        
        # Estatísticas de compressão
        if self.metrics["compression_savings"] > 0:
            stats["compression_savings_bytes"] = self.metrics["compression_savings"]
            stats["compression_savings_mb"] = round(self.metrics["compression_savings"] / 1024 / 1024, 2)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica saúde do sistema de cache
        """
        health = {
            "status": "healthy",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if self.redis:
                # Testar Redis com operação real
                start_time = time.time()
                test_key = "health_check_test"
                
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis.set, test_key, "test", 10
                )
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis.get, test_key
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis.delete, test_key
                )
                
                response_time = time.time() - start_time
                
                health["details"]["redis"] = {
                    "status": "healthy" if result == "test" else "unhealthy",
                    "response_time_ms": round(response_time * 1000, 2),
                    "test_passed": result == "test"
                }
            else:
                # Testar cache em memória
                test_entry = CacheEntry(
                    data="test",
                    timestamp=datetime.now().isoformat(),
                    ttl=10,
                    cache_type="test"
                )
                test_key = "memory_health_test"
                self.memory_cache[test_key] = test_entry
                
                test_result = test_key in self.memory_cache
                if test_key in self.memory_cache:
                    del self.memory_cache[test_key]
                
                health["details"]["memory_cache"] = {
                    "status": "healthy" if test_result else "unhealthy",
                    "entries": len(self.memory_cache),
                    "test_passed": test_result
                }
            
            # Verificar métricas para problemas
            if self.metrics["errors"] > self.metrics["sets"] * 0.1:  # Mais de 10% de erro
                health["status"] = "degraded"
                health["details"]["error_rate"] = "high"
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["details"]["error"] = str(e)
            logger.error(f"❌ Health check falhou: {e}")
        
        return health
    
    async def cleanup_expired_memory_cache(self):
        """Limpa entradas expiradas do cache em memória"""
        now = datetime.now()
        expired_keys = [
            key for key, expiry in self.memory_cache_timestamps.items()
            if now >= expiry
        ]
        
        for key in expired_keys:
            self._remove_from_memory_cache(key)
        
        if expired_keys:
            logger.debug(f"🧹 Limpeza cache memória: {len(expired_keys)} entradas expiradas removidas")
        
        return len(expired_keys)
    
    async def close(self):
        """Fecha conexões do cache"""
        try:
            if self.redis_pool:
                self.redis_pool.disconnect()
                logger.info("🔌 Pool de conexões Redis fechado")
        except Exception as e:
            logger.warning(f"Erro ao fechar conexões Redis: {e}")

# Instância global otimizada
optimized_cache = OptimizedCacheService()
