"""
🔧 SISTEMA UNIFICADO DE CONTROLE DE RESPOSTA
============================================

Substitui os múltiplos controles sobrepostos por um sistema único e eficiente
baseado em Redis com fallback inteligente.

CARACTERÍSTICAS:
- ✅ Controle único via Redis com TTL automático
- ✅ Fallback para cache em memória se Redis não disponível
- ✅ Hash determinístico para detectar mensagens duplicadas
- ✅ Janela temporal configurável (padrão: 30 segundos)
- ✅ Métricas detalhadas e logging
- ✅ Performance otimizada

RESOLVE:
- ❌ Sobreposição de controles redundantes
- ❌ Cache persistente em arquivos temporários
- ❌ Verificações desnecessárias no banco
- ❌ Rate limiting middleware duplicado
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import redis.asyncio as redis

from app.config.redis_config import redis_manager

logger = logging.getLogger(__name__)


@dataclass
class ResponseControlStats:
    """Estatísticas do controle de resposta"""

    messages_processed: int = 0
    messages_blocked: int = 0
    messages_allowed: int = 0
    duplicates_prevented: int = 0
    redis_operations: int = 0
    fallback_operations: int = 0
    errors: int = 0
    last_reset: float = field(default_factory=time.time)

    def reset_if_needed(self):
        """Reset estatísticas a cada hora"""
        if time.time() - self.last_reset > 3600:  # 1 hora
            self.messages_processed = 0
            self.messages_blocked = 0
            self.messages_allowed = 0
            self.duplicates_prevented = 0
            self.redis_operations = 0
            self.fallback_operations = 0
            self.errors = 0
            self.last_reset = time.time()
            logger.info("📊 Estatísticas resetadas")


class UnifiedResponseControl:
    """
    Sistema unificado de controle de resposta única

    Funcionalidades consolidadas:
    - ✅ Controle de mensagens duplicadas (hash-based)
    - ✅ Rate limiting por usuário (janela deslizante)
    - ✅ Flood protection (burst detection)
    - ✅ Redis com fallback para memória
    """

    def __init__(self, window_seconds: int = 30, rate_limit_per_minute: int = 50):
        self.window_seconds = window_seconds
        self.rate_limit_per_minute = rate_limit_per_minute  # Rate limiting por usuário
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, float] = {}
        self.stats = ResponseControlStats()
        self._lock = asyncio.Lock()
        self._redis_initialized = False
        # Redis será inicializado no primeiro uso (lazy initialization)

    async def _ensure_redis_initialized(self):
        """Inicializa conexão Redis de forma assíncrona (lazy)"""
        if self._redis_initialized:
            return
            
        try:
            redis_config = redis_manager._config
            
            if redis_config and redis_config.available and redis_config.url:
                # Criar cliente Redis assíncrono
                # Adicionar /0 para garantir database 0
                redis_url = redis_config.url
                if not redis_url.endswith(('/0', '/1', '/2', '/3', '/4', '/5', '/6', '/7', '/8', '/9')):
                    redis_url = f"{redis_url}/0"
                
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                )
                # Testar conexão
                await self.redis_client.ping()
                logger.info(f"✅ Redis UnifiedResponseControl conectado")
                
            else:
                logger.warning("⚠️ Redis não disponível - usando cache em memória")
                self.redis_client = None
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Redis: {e}")
            self.redis_client = None
        finally:
            self._redis_initialized = True

    def generate_message_hash(self, content: str) -> str:
        """
        Gera hash determinístico do conteúdo da mensagem

        Args:
            content: Conteúdo da mensagem

        Returns:
            Hash MD5 truncado (12 caracteres) do conteúdo normalizado
        """
        # Normalizar conteúdo
        content_clean = content.strip().lower()
        # Limitar tamanho para evitar hash de mensagens muito grandes
        content_clean = content_clean[:200]
        # Gerar hash
        return hashlib.md5(content_clean.encode("utf-8")).hexdigest()[:12]

    def _get_cache_key(self, user_id: str, message_hash: str) -> str:
        """Gera chave única para cache"""
        return f"msg_processed:{user_id}:{message_hash}"

    async def can_process_message(self, user_id: str, content: str) -> Tuple[bool, str]:
        """
        Verifica se a mensagem pode ser processada (sistema unificado)

        Args:
            user_id: ID único do usuário (telefone)
            content: Conteúdo da mensagem

        Returns:
            Tuple[bool, str]: (pode_processar, motivo)
        """
        async with self._lock:
            # Garantir que Redis está inicializado (dentro do lock para thread-safety)
            await self._ensure_redis_initialized()
            
            self.stats.messages_processed += 1
            self.stats.reset_if_needed()

            try:
                # 1. Verificar rate limiting por usuário primeiro
                rate_check = await self._check_user_rate_limit(user_id)
                if not rate_check[0]:
                    return await self._block_message(
                        user_id, f"Rate limit: {rate_check[1]}"
                    )

                # 2. Verificar mensagem duplicada
                message_hash = self.generate_message_hash(content)
                cache_key = self._get_cache_key(user_id, message_hash)

                logger.debug(f"🔍 Verificando: {user_id} - hash:{message_hash}")

                # Tentar usar Redis primeiro
                redis_result = await self._can_process_redis(cache_key)
                
                if redis_result:
                    # Redis retornou True = chave foi criada (primeira vez)
                    # IMPORTANTE: Também salvar na memória como backup redundante
                    self.memory_cache[cache_key] = time.time()
                    
                    self.stats.messages_allowed += 1
                    logger.info(f"✅ PERMITIDO: {user_id} - Redis (primeira vez)")
                    return True, "Redis - primeira vez"

                # Se Redis falhou ou key já existe, verificar memória
                memory_result = await self._can_process_memory(cache_key)
                
                if memory_result:
                    # Memória retornou True = chave foi criada (primeira vez)
                    self.stats.messages_allowed += 1
                    logger.info(f"✅ PERMITIDO: {user_id} - Memory fallback")
                    return True, "Memory - primeira vez"

                # Mensagem já processada (duplicata detectada)
                return await self._block_message(
                    user_id, "Mensagem duplicada detectada"
                )

            except Exception as e:
                self.stats.errors += 1
                logger.error(f"❌ Erro no controle de resposta: {e}")
                # Em caso de erro, permitir processamento para evitar bloqueio completo
                return True, f"Erro no controle - permitindo: {str(e)}"

    async def _can_process_redis(self, cache_key: str) -> bool:
        """Verifica via Redis se pode processar mensagem"""
        if not self.redis_client:
            return False

        try:
            self.stats.redis_operations += 1

            # Usar SET com NX (só define se não existir) e EX (TTL)
            result = await self.redis_client.set(
                cache_key,
                "1",
                ex=self.window_seconds,  # TTL automático
                nx=True,  # Só define se a chave não existir
            )

            # Se result é True, a chave foi criada (mensagem pode ser processada)
            # Se result é None ou False, a chave já existia (mensagem duplicada)
            return result is True

        except Exception as e:
            logger.warning(f"⚠️ Erro Redis: {e} - usando fallback")
            return False

    async def _can_process_memory(self, cache_key: str) -> bool:
        """Verifica via cache em memória se pode processar mensagem"""
        try:
            self.stats.fallback_operations += 1
            current_time = time.time()

            # Limpar entradas expiradas
            expired_keys = [
                key
                for key, timestamp in self.memory_cache.items()
                if current_time - timestamp > self.window_seconds
            ]

            for key in expired_keys:
                del self.memory_cache[key]

            # Verificar se chave já existe
            if cache_key in self.memory_cache:
                return False  # Já processada

            # Marcar como processada
            self.memory_cache[cache_key] = current_time
            return True

        except Exception as e:
            logger.error(f"❌ Erro cache memória: {e}")
            return True  # Em caso de erro, permitir processamento

    async def _allow_message(
        self, user_id: str, cache_key: str, reason: str
    ) -> Tuple[bool, str]:
        """Permite processamento da mensagem"""
        self.stats.messages_allowed += 1
        logger.info(f"✅ PERMITIDO: {user_id} - {reason}")
        return True, reason

    async def _block_message(self, user_id: str, reason: str) -> Tuple[bool, str]:
        """Bloqueia processamento da mensagem"""
        self.stats.messages_blocked += 1
        self.stats.duplicates_prevented += 1
        logger.warning(f"🚫 BLOQUEADO: {user_id} - {reason}")
        return False, reason

    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas"""
        self.stats.reset_if_needed()

        # Calcular percentuais
        total = self.stats.messages_processed
        blocked_pct = (self.stats.messages_blocked / total * 100) if total > 0 else 0
        allowed_pct = (self.stats.messages_allowed / total * 100) if total > 0 else 0

        return {
            "messages_processed": self.stats.messages_processed,
            "messages_blocked": self.stats.messages_blocked,
            "messages_allowed": self.stats.messages_allowed,
            "duplicates_prevented": self.stats.duplicates_prevented,
            "redis_operations": self.stats.redis_operations,
            "fallback_operations": self.stats.fallback_operations,
            "errors": self.stats.errors,
            "blocked_percentage": round(blocked_pct, 2),
            "allowed_percentage": round(allowed_pct, 2),
            "redis_available": self.redis_client is not None,
            "window_seconds": self.window_seconds,
            "memory_cache_size": len(self.memory_cache),
            "last_reset": datetime.fromtimestamp(self.stats.last_reset).isoformat(),
        }

    async def clear_cache(self) -> Dict[str, Any]:
        """Limpa todos os caches (para testes/debug)"""
        try:
            # Garantir que Redis está inicializado
            await self._ensure_redis_initialized()
            
            cleared_redis = 0
            cleared_memory = len(self.memory_cache)

            # Limpar Redis
            if self.redis_client:
                # Buscar chaves do padrão
                keys = await self.redis_client.keys("msg_processed:*")
                if keys:
                    cleared_redis = await self.redis_client.delete(*keys)

            # Limpar cache em memória
            self.memory_cache.clear()

            return {
                "cleared_redis_keys": cleared_redis,
                "cleared_memory_keys": cleared_memory,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache: {e}")
            return {"error": str(e), "status": "error"}

    async def cleanup_expired(self):
        """
        Remove registros expirados do cache (chamado periodicamente)

        Para Redis: chaves com TTL são removidas automaticamente
        Para cache em memória: remove entradas mais antigas que window_seconds
        """
        try:
            current_time = time.time()
            expired_keys = []

            # Limpar apenas cache em memória (Redis tem TTL automático)
            async with self._lock:
                for key, timestamp in list(self.memory_cache.items()):
                    if current_time - timestamp > self.window_seconds:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.memory_cache[key]

            if expired_keys:
                logger.info(
                    f"🧹 Cleanup: {len(expired_keys)} chaves expiradas removidas da memória"
                )

            return {"expired_keys_removed": len(expired_keys)}

        except Exception as e:
            logger.error(f"❌ Erro no cleanup: {e}")
            return {"error": str(e)}

    async def _check_user_rate_limit(self, user_id: str) -> Tuple[bool, str]:
        """
        Verifica rate limiting por usuário usando janela deslizante

        Args:
            user_id: ID único do usuário

        Returns:
            Tuple[bool, str]: (pode_processar, motivo)
        """
        try:
            rate_key = f"rate_limit:user:{user_id}"
            current_time = int(time.time())
            window_start = current_time - 60  # Janela de 1 minuto

            # Usar Redis se disponível
            if self.redis_client:
                try:
                    # Usar sorted set para janela deslizante
                    pipe = self.redis_client.pipeline()

                    # Remover entradas antigas
                    pipe.zremrangebyscore(rate_key, 0, window_start)

                    # Contar requisições no último minuto
                    pipe.zcard(rate_key)

                    # Adicionar nova entrada
                    pipe.zadd(rate_key, {str(current_time): current_time})

                    # TTL da chave
                    pipe.expire(rate_key, 120)  # 2 minutos

                    results = await pipe.execute()
                    current_count = results[1]

                    if current_count >= self.rate_limit_per_minute:
                        return (
                            False,
                            f"Rate limit excedido: {current_count}/{self.rate_limit_per_minute} req/min",
                        )

                    return (
                        True,
                        f"Rate limit OK: {current_count}/{self.rate_limit_per_minute}",
                    )

                except Exception as e:
                    logger.warning(f"⚠️ Erro Redis rate limit: {e}")
                    # Fallback para memória
                    pass

            # Fallback: usar cache em memória com janela simples
            user_requests = getattr(self, "_user_requests", {})
            if not hasattr(self, "_user_requests"):
                self._user_requests = user_requests

            # Limpar requisições antigas
            user_requests[user_id] = [
                req_time
                for req_time in user_requests.get(user_id, [])
                if current_time - req_time < 60
            ]

            # Verificar limite
            current_count = len(user_requests.get(user_id, []))
            if current_count >= self.rate_limit_per_minute:
                return (
                    False,
                    f"Rate limit excedido (memory): {current_count}/{self.rate_limit_per_minute} req/min",
                )

            # Adicionar nova requisição
            if user_id not in user_requests:
                user_requests[user_id] = []
            user_requests[user_id].append(current_time)

            return (
                True,
                f"Rate limit OK (memory): {current_count + 1}/{self.rate_limit_per_minute}",
            )

        except Exception as e:
            logger.error(f"❌ Erro no rate limiting: {e}")
            # Em caso de erro, permitir processamento
            return True, f"Rate limit error - permitindo: {str(e)}"


# Variável para instância singleton
_unified_response_control_instance = None


def get_unified_response_control() -> UnifiedResponseControl:
    """
    🔧 Singleton pattern para garantir apenas uma instância do response control

    Returns:
        UnifiedResponseControl: Instância única do controle de resposta
    """
    global _unified_response_control_instance
    if _unified_response_control_instance is None:
        # Criando instância singleton do UnifiedResponseControl
        _unified_response_control_instance = UnifiedResponseControl()
    return _unified_response_control_instance


# Para compatibilidade com código existente
unified_response_control = None
