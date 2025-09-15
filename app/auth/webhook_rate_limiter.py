"""
🚀 Advanced Webhook Rate Limiter with Burst Protection
====================================================

Sistema avançado de rate limiting específico para webhooks com:
- Proteção contra burst de requisições
- Rate limiting escalonado
- Detecção de padrões de spam
- Blacklist automática
- Métricas em tempo real
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import redis

from app.config import get_settings
from app.config.redis_config import execute_redis_safe, redis_manager

logger = logging.getLogger(__name__)


class WebhookRateLimitLevel(Enum):
    """Níveis de rate limiting para webhooks"""

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKED = "blocked"


@dataclass
class WebhookRateConfig:
    """Configuração de rate limiting para webhook"""

    burst_limit: int  # Máximo de requisições em burst
    burst_window: int  # Janela do burst em segundos
    sustained_limit: int  # Limite sustentado por minuto
    escalation_factor: float  # Fator de escalação quando suspeito
    block_duration: int  # Duração do bloqueio em segundos


@dataclass
class WebhookMetrics:
    """Métricas de webhook em tempo real"""

    requests_last_minute: int
    requests_last_hour: int
    burst_violations: int
    sustained_violations: int
    current_level: WebhookRateLimitLevel
    blocked_until: Optional[datetime]
    last_request: datetime


class WebhookRateLimiter:
    """
    Sistema avançado de rate limiting para webhooks

    Features:
    - Burst protection (50 req/10s)
    - Sustained limit (100 req/min)
    - Escalation system
    - Automatic blacklisting
    - Real-time metrics
    """

    def __init__(self):
        self.settings = get_settings()

        # Configurações por fonte/tipo
        self.configs = {
            "whatsapp_business": WebhookRateConfig(
                burst_limit=50,
                burst_window=10,
                sustained_limit=100,
                escalation_factor=0.5,
                block_duration=300,  # 5 minutos
            ),
            "meta_webhook": WebhookRateConfig(
                burst_limit=30,
                burst_window=10,
                sustained_limit=60,
                escalation_factor=0.3,
                block_duration=600,  # 10 minutos
            ),
            "default": WebhookRateConfig(
                burst_limit=20,
                burst_window=10,
                sustained_limit=40,
                escalation_factor=0.2,
                block_duration=900,  # 15 minutos
            ),
        }

        # Cache local para performance
        self._local_cache: Dict[str, dict] = {}
        self._cache_ttl = 60  # 1 minuto

    async def check_webhook_rate_limit(
        self,
        source_ip: str,
        webhook_type: str = "default",
        user_agent: str = "",
        payload_size: int = 0,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifica se webhook pode prosseguir baseado em rate limiting avançado

        Returns:
            Tuple[bool, Dict]: (allowed, metrics_and_info)
        """
        try:
            config = self.configs.get(webhook_type, self.configs["default"])
            key = f"webhook_rl:{webhook_type}:{source_ip}"

            # Verificar cache local primeiro
            if self._check_local_cache(key):
                cached_result = self._local_cache[key]
                if cached_result.get("blocked_until", 0) > time.time():
                    return False, {
                        "level": "BLOCKED",
                        "reason": "cached_block",
                        "retry_after": int(
                            cached_result["blocked_until"] - time.time()
                        ),
                    }

            # Verificar no Redis
            current_time = time.time()

            # 1. Verificar burst limit
            burst_allowed, burst_info = await self._check_burst_limit(
                key, config, current_time
            )

            if not burst_allowed:
                await self._escalate_blocking(key, config, "burst_violation")
                return False, {
                    "level": "BLOCKED",
                    "reason": "burst_limit_exceeded",
                    "burst_info": burst_info,
                    "retry_after": config.burst_window,
                }

            # 2. Verificar sustained limit
            sustained_allowed, sustained_info = await self._check_sustained_limit(
                key, config, current_time
            )

            if not sustained_allowed:
                await self._escalate_blocking(key, config, "sustained_violation")
                return False, {
                    "level": "BLOCKED",
                    "reason": "sustained_limit_exceeded",
                    "sustained_info": sustained_info,
                    "retry_after": 60,
                }

            # 3. Verificar padrões suspeitos
            suspicious_level = await self._analyze_suspicious_patterns(
                key, payload_size, user_agent, current_time
            )

            # 4. Registrar requisição válida
            await self._record_valid_request(key, config, current_time)

            # 5. Obter métricas atuais
            metrics = await self._get_current_metrics(key, config)

            # 6. Atualizar cache local
            self._update_local_cache(key, metrics)

            return True, {
                "level": suspicious_level.value,
                "metrics": asdict(metrics),
                "config_applied": webhook_type,
            }

        except Exception as e:
            logger.error(f"Erro no webhook rate limiter: {e}")
            # Em caso de erro, permitir mas logar
            return True, {"level": "ERROR", "reason": f"rate_limiter_error: {str(e)}"}

    async def _check_burst_limit(
        self, key: str, config: WebhookRateConfig, current_time: float
    ) -> Tuple[bool, Dict]:
        """Verifica limite de burst"""
        burst_key = f"{key}:burst"

        async def _burst_check():
            # Limpar requisições antigas
            cutoff = current_time - config.burst_window

            # Remover timestamps antigos e contar atuais
            pipe = redis_manager.redis_client.pipeline()
            pipe.zremrangebyscore(burst_key, 0, cutoff)
            pipe.zcard(burst_key)
            pipe.zadd(burst_key, {str(current_time): current_time})
            pipe.expire(burst_key, config.burst_window * 2)

            results = await pipe.execute()
            current_count = results[1]

            return current_count < config.burst_limit, {
                "current_burst_count": current_count,
                "burst_limit": config.burst_limit,
                "window_seconds": config.burst_window,
            }

        return await execute_redis_safe(
            _burst_check, default=(True, {"status": "redis_unavailable"})
        )

    async def _check_sustained_limit(
        self, key: str, config: WebhookRateConfig, current_time: float
    ) -> Tuple[bool, Dict]:
        """Verifica limite sustentado"""
        sustained_key = f"{key}:sustained"

        async def _sustained_check():
            # Janela de 1 minuto
            cutoff = current_time - 60

            pipe = redis_manager.redis_client.pipeline()
            pipe.zremrangebyscore(sustained_key, 0, cutoff)
            pipe.zcard(sustained_key)
            pipe.zadd(sustained_key, {str(current_time): current_time})
            pipe.expire(sustained_key, 120)

            results = await pipe.execute()
            current_count = results[1]

            return current_count < config.sustained_limit, {
                "current_sustained_count": current_count,
                "sustained_limit": config.sustained_limit,
                "window_seconds": 60,
            }

        return await execute_redis_safe(
            _sustained_check, default=(True, {"status": "redis_unavailable"})
        )

    async def _analyze_suspicious_patterns(
        self, key: str, payload_size: int, user_agent: str, current_time: float
    ) -> WebhookRateLimitLevel:
        """Analisa padrões suspeitos"""

        suspicious_indicators = 0

        # 1. Payload muito pequeno ou muito grande
        if payload_size < 10 or payload_size > 100000:
            suspicious_indicators += 1

        # 2. User-Agent suspeito ou ausente
        suspicious_agents = ["bot", "crawler", "scanner", "", "curl", "wget"]
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            suspicious_indicators += 1

        # 3. Frequência muito alta de requisições idênticas
        pattern_key = f"{key}:pattern"
        pattern_hash = hashlib.md5(f"{payload_size}:{user_agent}".encode()).hexdigest()

        async def _check_pattern():
            pipe = redis_manager.redis_client.pipeline()
            pipe.hincrby(pattern_key, pattern_hash, 1)
            pipe.hget(pattern_key, pattern_hash)
            pipe.expire(pattern_key, 300)  # 5 minutos
            results = await pipe.execute()
            return int(results[1] or 0)

        pattern_count = await execute_redis_safe(_check_pattern, default=0)

        if pattern_count > 20:  # Mais de 20 requisições idênticas
            suspicious_indicators += 2

        # Determinar nível baseado nos indicadores
        if suspicious_indicators >= 3:
            return WebhookRateLimitLevel.CRITICAL
        elif suspicious_indicators >= 2:
            return WebhookRateLimitLevel.WARNING
        else:
            return WebhookRateLimitLevel.NORMAL

    async def _escalate_blocking(
        self, key: str, config: WebhookRateConfig, violation_type: str
    ):
        """Escala bloqueio baseado no tipo de violação"""
        block_key = f"{key}:blocked"
        violation_key = f"{key}:violations"

        async def _escalate():
            # Contar violações anteriores
            pipe = redis_manager.redis_client.pipeline()
            pipe.incr(violation_key)
            pipe.expire(violation_key, 3600)  # Reset a cada hora
            results = await pipe.execute()

            violation_count = results[0]

            # Calcular duração do bloqueio com escalação
            base_duration = config.block_duration
            escalated_duration = int(
                base_duration * (1 + violation_count * config.escalation_factor)
            )
            max_duration = base_duration * 5  # Máximo 5x a duração base

            block_duration = min(escalated_duration, max_duration)
            block_until = time.time() + block_duration

            # Definir bloqueio
            pipe = redis_manager.redis_client.pipeline()
            pipe.set(block_key, block_until, ex=block_duration)
            pipe.hset(
                f"{key}:info",
                mapping={
                    "last_violation": violation_type,
                    "violation_count": violation_count,
                    "blocked_until": block_until,
                    "block_duration": block_duration,
                },
            )
            await pipe.execute()

            logger.warning(
                f"Webhook blocked: {key}, violation: {violation_type}, "
                f"count: {violation_count}, duration: {block_duration}s"
            )

        await execute_redis_safe(_escalate)

    async def _record_valid_request(
        self, key: str, config: WebhookRateConfig, current_time: float
    ):
        """Registra requisição válida para métricas"""
        metrics_key = f"{key}:metrics"

        async def _record():
            pipe = redis_manager.redis_client.pipeline()
            pipe.hset(
                metrics_key,
                mapping={
                    "last_request": current_time,
                    "total_requests": await redis_manager.redis_client.hincrby(
                        metrics_key, "total_requests", 1
                    ),
                },
            )
            pipe.expire(metrics_key, 3600)
            await pipe.execute()

        await execute_redis_safe(_record)

    async def _get_current_metrics(
        self, key: str, config: WebhookRateConfig
    ) -> WebhookMetrics:
        """Obtém métricas atuais"""
        current_time = time.time()

        async def _get_metrics():
            # Contar requisições na última hora e minuto
            burst_key = f"{key}:burst"
            sustained_key = f"{key}:sustained"
            violations_key = f"{key}:violations"
            blocked_key = f"{key}:blocked"

            pipe = redis_manager.redis_client.pipeline()
            pipe.zcount(sustained_key, current_time - 60, current_time)  # Último minuto
            pipe.zcount(burst_key, current_time - 3600, current_time)  # Última hora
            pipe.get(violations_key)
            pipe.get(blocked_key)

            results = await pipe.execute()

            blocked_until = None
            if results[3]:
                blocked_timestamp = float(results[3])
                if blocked_timestamp > current_time:
                    blocked_until = datetime.fromtimestamp(
                        blocked_timestamp, tz=timezone.utc
                    )

            return WebhookMetrics(
                requests_last_minute=results[0],
                requests_last_hour=results[1],
                burst_violations=int(results[2] or 0),
                sustained_violations=0,  # Calculado separadamente se necessário
                current_level=(
                    WebhookRateLimitLevel.BLOCKED
                    if blocked_until
                    else WebhookRateLimitLevel.NORMAL
                ),
                blocked_until=blocked_until,
                last_request=datetime.fromtimestamp(current_time, tz=timezone.utc),
            )

        return await execute_redis_safe(
            _get_metrics,
            default=WebhookMetrics(
                requests_last_minute=0,
                requests_last_hour=0,
                burst_violations=0,
                sustained_violations=0,
                current_level=WebhookRateLimitLevel.NORMAL,
                blocked_until=None,
                last_request=datetime.now(tz=timezone.utc),
            ),
        )

    def _check_local_cache(self, key: str) -> bool:
        """Verifica cache local"""
        if key in self._local_cache:
            cache_entry = self._local_cache[key]
            if cache_entry["expires"] > time.time():
                return True
            else:
                del self._local_cache[key]
        return False

    def _update_local_cache(self, key: str, metrics: WebhookMetrics):
        """Atualiza cache local"""
        self._local_cache[key] = {
            "metrics": asdict(metrics),
            "blocked_until": (
                metrics.blocked_until.timestamp() if metrics.blocked_until else 0
            ),
            "expires": time.time() + self._cache_ttl,
        }

    async def get_webhook_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas gerais dos webhooks"""
        try:

            async def _get_stats():
                # Buscar todas as chaves de webhook
                pattern = "webhook_rl:*"
                keys = await redis_manager.redis_client.keys(pattern)

                stats = {
                    "total_sources": len(
                        set(k.split(":")[2] for k in keys if k.count(":") >= 2)
                    ),
                    "active_limits": len(keys),
                    "configs": {
                        name: asdict(config) for name, config in self.configs.items()
                    },
                    "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                }

                return stats

            return await execute_redis_safe(
                _get_stats,
                default={
                    "total_sources": 0,
                    "active_limits": 0,
                    "configs": {
                        name: asdict(config) for name, config in self.configs.items()
                    },
                    "error": "redis_unavailable",
                },
            )
        except Exception as e:
            logger.error(f"Erro ao obter stats do webhook: {e}")
            return {"error": str(e)}

    async def clear_webhook_blocks(
        self, source_ip: str, webhook_type: str = "default"
    ) -> bool:
        """Limpa bloqueios para um webhook específico (admin only)"""
        try:
            key = f"webhook_rl:{webhook_type}:{source_ip}"

            async def _clear_blocks():
                keys_to_delete = [
                    f"{key}:blocked",
                    f"{key}:violations",
                    f"{key}:burst",
                    f"{key}:sustained",
                    f"{key}:pattern",
                    f"{key}:metrics",
                    f"{key}:info",
                ]

                pipe = redis_manager.redis_client.pipeline()
                for k in keys_to_delete:
                    pipe.delete(k)
                results = await pipe.execute()

                # Limpar cache local também
                if key in self._local_cache:
                    del self._local_cache[key]

                return sum(results) > 0

            cleared = await execute_redis_safe(_clear_blocks, default=False)

            if cleared:
                logger.info(f"Cleared webhook blocks for {source_ip}:{webhook_type}")

            return cleared

        except Exception as e:
            logger.error(f"Erro ao limpar bloqueios: {e}")
            return False


# Instância global do rate limiter para webhooks
webhook_rate_limiter = WebhookRateLimiter()


# Decorator para aplicar rate limiting em webhooks
def webhook_rate_limit(webhook_type: str = "default"):
    """
    Decorator para aplicar rate limiting avançado em endpoints de webhook

    Usage:
        @webhook_rate_limit(webhook_type="whatsapp_business")
        async def webhook_endpoint(request: Request):
            ...
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extrair request do contexto
            request = None
            for arg in args:
                if hasattr(arg, "client"):  # FastAPI Request
                    request = arg
                    break

            if not request:
                # Se não conseguir extrair request, prosseguir sem rate limiting
                return await func(*args, **kwargs)

            # Obter informações da requisição
            source_ip = request.client.host
            user_agent = request.headers.get("user-agent", "")
            content_length = int(request.headers.get("content-length", "0"))

            # Verificar rate limiting
            allowed, info = await webhook_rate_limiter.check_webhook_rate_limit(
                source_ip=source_ip,
                webhook_type=webhook_type,
                user_agent=user_agent,
                payload_size=content_length,
            )

            if not allowed:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "info": info,
                        "retry_after": info.get("retry_after", 60),
                    },
                    headers={
                        "Retry-After": str(info.get("retry_after", 60)),
                        "X-RateLimit-Level": info.get("level", "BLOCKED"),
                    },
                )

            # Adicionar informações de rate limiting ao request
            request.state.webhook_rate_info = info

            return await func(*args, **kwargs)

        return wrapper

    return decorator
