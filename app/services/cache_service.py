"""
Sistema de Cache para WhatsApp Agent
Otimização de respostas com Redis e cache em memória como fallback
"""
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Any, Dict, List, Union

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger = logging.getLogger(__name__)

# Tentar importar Redis
try:
    import redis
    REDIS_AVAILABLE = True
    logger.info("Redis biblioteca disponível")
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis não disponível, usando cache em memória")


class CacheType(Enum):
    """Tipos de cache disponíveis"""
    RESPONSE = "response"
    INTENT = "intent"
    LEAD_SCORE = "lead_score"
    USER_CONTEXT = "user_context"
    BUSINESS_DATA = "business_data"


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


class CacheService:
    """
    Serviço de cache inteligente com múltiplas estratégias
    
    Funcionalidades:
    - Cache de respostas frequentes
    - Cache de análises de intenção
    - Cache de lead scoring
    - Cache de contexto do usuário
    - TTL configurável por tipo
    - Invalidação inteligente
    - Métricas de performance
    """
    
    def __init__(self):
        # Configuração Redis
        redis_config = {
            "host": getattr(settings, "redis_host", "localhost"),
            "port": getattr(settings, "redis_port", 6379),
            "db": getattr(settings, "redis_db", 0),
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
            "retry_on_timeout": True
        }
        
        # Adicionar senha se configurada
        if hasattr(settings, "redis_password") and settings.redis_password:
            redis_config["password"] = settings.redis_password
        
class CacheService:
    """
    Serviço de cache inteligente com suporte a Redis e fallback para memória
    
    Funcionalidades:
    - Cache de respostas frequentes
    - Cache de análises de intenção
    - Cache de lead scoring
    - Cache de contexto do usuário
    - TTL configurável por tipo
    - Invalidação inteligente
    - Métricas de performance
    - Fallback para cache em memória
    """
    
    def __init__(self):
        # Verificar disponibilidade do Redis
        self.redis_available = REDIS_AVAILABLE
        self.redis = None
        self.enabled = getattr(settings, "cache_enabled", True)
        
        # Cache em memória como fallback
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.memory_cache_timestamps: Dict[str, datetime] = {}
        
        # Configuração Redis
        if self.redis_available:
            self.redis_config = {
                "host": getattr(settings, "redis_host", "localhost"),
                "port": getattr(settings, "redis_port", 6379),
                "db": getattr(settings, "redis_db", 0),
                "decode_responses": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5
            }
            
            # Adicionar senha se configurada
            if hasattr(settings, "redis_password") and settings.redis_password:
                self.redis_config["password"] = settings.redis_password
        
        # TTL por tipo de cache (em segundos)
        self.ttl_config = {
            CacheType.RESPONSE: 3600,      # 1 hora - respostas podem ser reutilizadas
            CacheType.INTENT: 1800,        # 30 min - intenções são mais estáveis
            CacheType.LEAD_SCORE: 7200,    # 2 horas - lead score muda lentamente
            CacheType.USER_CONTEXT: 900,   # 15 min - contexto muda com frequência
            CacheType.BUSINESS_DATA: 14400 # 4 horas - dados do negócio são estáveis
        }
        
        # Prefixos para organização
        self.prefixes = {
            CacheType.RESPONSE: "whatsapp:response",
            CacheType.INTENT: "whatsapp:intent", 
            CacheType.LEAD_SCORE: "whatsapp:lead_score",
            CacheType.USER_CONTEXT: "whatsapp:context",
            CacheType.BUSINESS_DATA: "whatsapp:business"
        }
        
        # Métricas de cache
        self.metrics = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "total_requests": 0
        }
        
        logger.info(f"CacheService inicializado - Redis: {self.redis_available}, Enabled: {self.enabled}")
    
    async def initialize(self):
        """Inicializa conexão com Redis se disponível"""
        if not self.enabled:
            logger.info("Cache desabilitado por configuração")
            return
        
        if self.redis_available:
            try:
                self.redis = redis.Redis(**self.redis_config)
                # Teste de conectividade síncrono
                self.redis.ping()
                logger.info("✅ Conexão com Redis estabelecida")
            except Exception as e:
                logger.warning(f"Redis não disponível, usando cache em memória: {e}")
                self.redis = None
        else:
            logger.info("Redis não instalado, usando cache em memória")
    
    async def close(self):
        """Fecha conexão com Redis se existir"""
        if self.redis:
            try:
                self.redis.close()
                logger.info("Conexão com Redis fechada")
            except:
                pass
    
    # MÉTODOS DE CACHE UNIFICADOS
    async def _get_from_cache(self, key: str) -> Optional[str]:
        """Busca valor do cache (Redis ou memória)"""
        try:
            if self.redis:
                # Usar Redis
                return self.redis.get(key)
            else:
                # Usar cache em memória
                if key in self.memory_cache:
                    # Verificar se não expirou
                    timestamp = self.memory_cache_timestamps.get(key)
                    if timestamp and (datetime.now() - timestamp).total_seconds() < 3600:  # TTL padrão
                        return json.dumps(self.memory_cache[key])
                    else:
                        # Expirou, remover
                        self.memory_cache.pop(key, None)
                        self.memory_cache_timestamps.pop(key, None)
                return None
        except Exception as e:
            logger.error(f"Erro ao buscar cache: {e}")
            return None
    
    async def _set_to_cache(self, key: str, value: str, ttl: int = 3600):
        """Armazena valor no cache (Redis ou memória)"""
        try:
            if self.redis:
                # Usar Redis com TTL
                self.redis.setex(key, ttl, value)
            else:
                # Usar cache em memória
                self.memory_cache[key] = json.loads(value)
                self.memory_cache_timestamps[key] = datetime.now()
                
                # Limpar cache expirado periodicamente
                self._cleanup_memory_cache()
                
        except Exception as e:
            logger.error(f"Erro ao armazenar cache: {e}")
    
    def _cleanup_memory_cache(self):
        """Limpa entradas expiradas do cache em memória"""
        try:
            now = datetime.now()
            expired_keys = []
            
            for key, timestamp in self.memory_cache_timestamps.items():
                if (now - timestamp).total_seconds() > 3600:  # TTL padrão
                    expired_keys.append(key)
            
            for key in expired_keys:
                self.memory_cache.pop(key, None)
                self.memory_cache_timestamps.pop(key, None)
                
            if expired_keys:
                logger.debug(f"Limpeza do cache em memória: {len(expired_keys)} chaves expiradas removidas")
                
        except Exception as e:
            logger.error(f"Erro na limpeza do cache em memória: {e}")
    
    # CACHE DE RESPOSTAS
    async def get_cached_response(self, message: str, user_id: str, 
                                context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Busca resposta em cache baseada na mensagem e contexto"""
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_response_key(message, user_id, context)
            cached_data = await self._get_from_cache(cache_key)
            
            self._update_metrics("total_requests")
            
            if cached_data:
                entry = self._deserialize_cache_entry(cached_data)
                self._update_metrics("hits")
                logger.debug(f"Cache HIT para resposta: {message[:30]}...")
                return entry.data
            else:
                self._update_metrics("misses")
                logger.debug(f"Cache MISS para resposta: {message[:30]}...")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar resposta em cache: {e}")
            self._update_metrics("errors")
            return None
    
    async def cache_response(self, message: str, user_id: str, response: str,
                           context: Optional[Dict[str, Any]] = None,
                           custom_ttl: Optional[int] = None):
        """Armazena resposta em cache"""
        if not self.enabled or not response:
            return
        
        try:
            cache_key = self._generate_response_key(message, user_id, context)
            ttl = custom_ttl or self.ttl_config[CacheType.RESPONSE]
            
            entry = CacheEntry(
                data=response,
                timestamp=datetime.now().isoformat(),
                ttl=ttl,
                cache_type=CacheType.RESPONSE.value,
                metadata={
                    "user_id": user_id,
                    "message_hash": self._hash_message(message),
                    "context_keys": list(context.keys()) if context else []
                }
            )
            
            serialized = self._serialize_cache_entry(entry)
            await self._set_to_cache(cache_key, serialized, ttl)
            
            self._update_metrics("sets")
            logger.debug(f"Resposta cacheada para: {message[:30]}... (TTL: {ttl}s)")
            
        except Exception as e:
            logger.error(f"Erro ao cachear resposta: {e}")
            self._update_metrics("errors")
    
    # CACHE DE LEAD SCORE
    async def get_cached_lead_score(self, user_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Busca lead score em cache"""
        if not self.enabled:
            return None
        
        try:
            cache_key = self._generate_lead_score_key(user_id, message)
            cached_data = await self._get_from_cache(cache_key)
            
            if cached_data:
                entry = self._deserialize_cache_entry(cached_data)
                return entry.data
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar lead score em cache: {e}")
            return None
    
    async def cache_lead_score(self, user_id: str, message: str, 
                              lead_score_data: Dict[str, Any],
                              custom_ttl: Optional[int] = None):
        """Armazena lead score em cache"""
        if not self.enabled:
            return
        
        try:
            cache_key = self._generate_lead_score_key(user_id, message)
            ttl = custom_ttl or self.ttl_config[CacheType.LEAD_SCORE]
            
            entry = CacheEntry(
                data=lead_score_data,
                timestamp=datetime.now().isoformat(),
                ttl=ttl,
                cache_type=CacheType.LEAD_SCORE.value,
                metadata={"user_id": user_id, "message_hash": self._hash_message(message)}
            )
            
            serialized = self._serialize_cache_entry(entry)
            await self._set_to_cache(cache_key, serialized, ttl)
            
        except Exception as e:
            logger.error(f"Erro ao cachear lead score: {e}")
    
    # INVALIDAÇÃO DE CACHE
    async def invalidate_user_cache(self, user_id: str):
        """Invalida todos os caches relacionados a um usuário"""
        if not self.enabled:
            return
        
        try:
            if self.redis:
                # Redis: usar padrões para encontrar chaves
                patterns = [
                    f"{self.prefixes[CacheType.RESPONSE]}:*:{user_id}:*",
                    f"{self.prefixes[CacheType.USER_CONTEXT]}:{user_id}",
                    f"{self.prefixes[CacheType.LEAD_SCORE]}:{user_id}:*"
                ]
                
                for pattern in patterns:
                    try:
                        keys = self.redis.keys(pattern)
                        if keys:
                            self.redis.delete(*keys)
                            logger.debug(f"Invalidado cache do usuário {user_id}: {len(keys)} chaves")
                    except:
                        pass
            else:
                # Cache em memória: filtrar por chaves
                keys_to_remove = []
                for key in list(self.memory_cache.keys()):
                    if user_id in key:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    self.memory_cache.pop(key, None)
                    self.memory_cache_timestamps.pop(key, None)
                
                if keys_to_remove:
                    logger.debug(f"Invalidado cache em memória do usuário {user_id}: {len(keys_to_remove)} chaves")
        
        except Exception as e:
            logger.error(f"Erro ao invalidar cache do usuário {user_id}: {e}")
    
    async def invalidate_cache_by_type(self, cache_type: CacheType):
        """Invalida todos os caches de um tipo específico"""
        if not self.enabled:
            return
        
        try:
            prefix = self.prefixes[cache_type]
            
            if self.redis:
                pattern = f"{prefix}:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"Invalidado cache do tipo {cache_type.value}: {len(keys)} chaves")
            else:
                # Cache em memória
                keys_to_remove = [k for k in self.memory_cache.keys() if k.startswith(prefix)]
                for key in keys_to_remove:
                    self.memory_cache.pop(key, None)
                    self.memory_cache_timestamps.pop(key, None)
                
                if keys_to_remove:
                    logger.info(f"Invalidado cache em memória do tipo {cache_type.value}: {len(keys_to_remove)} chaves")
        
        except Exception as e:
            logger.error(f"Erro ao invalidar cache do tipo {cache_type.value}: {e}")
    
    async def clear_all_cache(self):
        """Limpa todo o cache do WhatsApp Agent"""
        if not self.enabled:
            return
        
        try:
            if self.redis:
                pattern = "whatsapp:*"
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"Cache Redis totalmente limpo: {len(keys)} chaves removidas")
            else:
                # Cache em memória
                count = len(self.memory_cache)
                self.memory_cache.clear()
                self.memory_cache_timestamps.clear()
                logger.info(f"Cache em memória totalmente limpo: {count} chaves removidas")
        
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
    
    # MÉTODOS AUXILIARES
    def _generate_response_key(self, message: str, user_id: str, 
                              context: Optional[Dict[str, Any]] = None) -> str:
        """Gera chave de cache para resposta"""
        message_hash = self._hash_message(message)
        context_hash = self._hash_context(context) if context else "no_context"
        return f"{self.prefixes[CacheType.RESPONSE]}:{message_hash}:{user_id}:{context_hash}"
    
    def _generate_lead_score_key(self, user_id: str, message: str) -> str:
        """Gera chave de cache para lead score"""
        message_hash = self._hash_message(message)
        return f"{self.prefixes[CacheType.LEAD_SCORE]}:{user_id}:{message_hash}"
    
    def _hash_message(self, message: str) -> str:
        """Gera hash MD5 da mensagem normalizada"""
        normalized = message.lower().strip()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()[:12]
    
    def _hash_context(self, context: Dict[str, Any]) -> str:
        """Gera hash do contexto"""
        context_str = json.dumps(context, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(context_str.encode('utf-8')).hexdigest()[:8]
    
    def _serialize_cache_entry(self, entry: CacheEntry) -> str:
        """Serializa entrada de cache para JSON"""
        return json.dumps(asdict(entry), ensure_ascii=False)
    
    def _deserialize_cache_entry(self, data: str) -> CacheEntry:
        """Deserializa entrada de cache do JSON"""
        entry_dict = json.loads(data)
        return CacheEntry(**entry_dict)
    
    def _update_metrics(self, metric_name: str):
        """Atualiza métricas do cache"""
        if metric_name in self.metrics:
            self.metrics[metric_name] += 1
    
    # MÉTODOS DE MONITORAMENTO
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas do cache"""
        if not self.enabled:
            return {"enabled": False, "message": "Cache desabilitado"}
        
        try:
            # Estatísticas básicas
            total_requests = self.metrics["total_requests"]
            hit_rate = (self.metrics["hits"] / max(total_requests, 1)) * 100
            
            # Informações do sistema de cache
            cache_info = {
                "cache_type": "Redis" if self.redis else "Memory",
                "redis_available": self.redis_available,
                "redis_connected": bool(self.redis)
            }
            
            # Contagem de chaves
            if self.redis:
                # Redis keys
                key_counts = {}
                total_keys = 0
                for cache_type, prefix in self.prefixes.items():
                    try:
                        keys = self.redis.keys(f"{prefix}:*")
                        count = len(keys)
                        key_counts[cache_type.value] = count
                        total_keys += count
                    except:
                        key_counts[cache_type.value] = 0
            else:
                # Memory cache keys
                total_keys = len(self.memory_cache)
                key_counts = {"memory_total": total_keys}
            
            return {
                "enabled": self.enabled,
                "metrics": self.metrics,
                "hit_rate_percentage": round(hit_rate, 2),
                "key_counts": key_counts,
                "total_keys": total_keys,
                "cache_info": cache_info,
                "ttl_config": {k.value: v for k, v in self.ttl_config.items()},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {e}")
            return {"error": str(e), "enabled": self.enabled}
    
    async def get_cache_health(self) -> Dict[str, Any]:
        """Verifica saúde do sistema de cache"""
        if not self.enabled:
            return {"status": "disabled", "healthy": False}
        
        try:
            if self.redis:
                # Teste de conectividade Redis
                self.redis.ping()
                
                # Teste de escrita/leitura
                test_key = "whatsapp:health:test"
                self.redis.setex(test_key, 10, "test_value")
                test_value = self.redis.get(test_key)
                self.redis.delete(test_key)
                
                healthy = test_value == "test_value"
            else:
                # Cache em memória sempre funcional
                healthy = True
            
            return {
                "status": "healthy" if healthy else "unhealthy",
                "healthy": healthy,
                "cache_type": "Redis" if self.redis else "Memory",
                "redis_connected": bool(self.redis),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro na verificação de saúde do cache: {e}")
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Instância global do serviço de cache
cache_service = CacheService()
