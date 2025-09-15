"""
H003 - Middleware Rate Limiting Webhook
=====================================

Sistema de rate limiting específico para webhooks conforme H003:
- 100 req/min por IP
- Logs de blocking funcionais
- Health check não afetado
- Proteção contra DDoS
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import get_settings
from app.config.redis_config import execute_redis_safe_async, redis_manager

# Logger estruturado
logger = logging.getLogger(__name__)


@dataclass
class WebhookRateLimitConfig:
    """Configuração H003 Rate Limiting"""

    requests_per_minute: int = 100
    window_seconds: int = 60
    block_duration: int = 300  # 5 minutos de bloqueio
    burst_protection: int = 20  # Máx 20 req/10s (proteção burst)
    burst_window: int = 10


class WebhookRateLimitMiddleware(BaseHTTPMiddleware):
    """
    H003 - Middleware Rate Limiting Webhook

    Critérios implementados:
    ✅ Middleware rate limit ativo
    ✅ 100 req/min por IP
    ✅ Logs de blocking funcionais
    ✅ Health check não afetado
    ✅ Teste: 101 requests em 1min = HTTP 429
    """

    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()
        self.config = WebhookRateLimitConfig()

        # Paths que aplicam rate limiting
        self.webhook_paths = {"/webhook", "/webhook/", "/api/webhook", "/api/webhook/"}

        # Paths isentos (health check)
        self.exempt_paths = {"/health", "/health/", "/healthz", "/ready", "/ping"}

        logger.info(
            f"H003 WebhookRateLimitMiddleware initialized - {self.config.requests_per_minute} req/min per IP"
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """Processa rate limiting para webhooks"""

        # Debug logging
        path = request.url.path
        logger.info(f"H003 Debug: Processing request to path: {path}")

        # 1. Verificar se é endpoint isento (health check)
        if self._is_exempt_path(path):
            logger.info(f"H003 Debug: Path {path} is exempt, skipping rate limiting")
            return await call_next(request)

        # 2. Verificar se é webhook
        is_webhook = self._is_webhook_path(path)
        logger.info(f"H003 Debug: Path {path} is_webhook: {is_webhook}")

        if not is_webhook:
            logger.info(
                f"H003 Debug: Path {path} is not a webhook, skipping rate limiting"
            )
            return await call_next(request)

        # 3. Aplicar rate limiting
        client_ip = self._get_client_ip(request)
        logger.info(
            f"H003 Debug: Applying rate limiting to IP {client_ip} for path {path}"
        )

        try:
            # Verificar rate limit
            is_allowed, rate_info = await self._check_rate_limit(client_ip)
            logger.info(
                f"H003 Debug: Rate limit check result - allowed: {is_allowed}, info: {rate_info}"
            )

            if not is_allowed:
                # Log do blocking
                await self._log_rate_limit_block(client_ip, rate_info, request)

                # Retornar HTTP 429
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Too many requests. Please try again later.",
                        "retry_after": rate_info.get("retry_after", 60),
                        "limit": self.config.requests_per_minute,
                        "window": "1 minute",
                    },
                    headers={
                        "Retry-After": str(rate_info.get("retry_after", 60)),
                        "X-RateLimit-Limit": str(self.config.requests_per_minute),
                        "X-RateLimit-Window": "60",
                        "X-RateLimit-Remaining": str(
                            max(0, rate_info.get("remaining", 0))
                        ),
                    },
                )

            # Request permitida - registrar e prosseguir
            await self._record_request(client_ip)
            logger.info(f"H003 Debug: Request recorded for IP {client_ip}")

            # Adicionar headers informativos
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
            response.headers["X-RateLimit-Window"] = "60"
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, rate_info.get("remaining", 0))
            )

            logger.info(f"H003 Debug: Added rate limit headers to response")
            return response

        except Exception as e:
            logger.error(f"H003 Rate limiting error: {e}")
            # Em caso de erro, permitir request (fail-open)
            return await call_next(request)

    def _is_webhook_path(self, path: str) -> bool:
        """Verifica se é path de webhook"""
        path_normalized = path.rstrip("/")
        return any(
            path_normalized.startswith(webhook_path.rstrip("/"))
            for webhook_path in self.webhook_paths
        )

    def _is_exempt_path(self, path: str) -> bool:
        """Verifica se é path isento (health check)"""
        path_normalized = path.rstrip("/")
        return any(
            path_normalized == exempt_path.rstrip("/")
            for exempt_path in self.exempt_paths
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extrai IP do cliente considerando proxies"""
        # Verificar headers de proxy primeiro
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Pegar o primeiro IP (cliente original)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback para IP direto
        return request.client.host

    async def _check_rate_limit(self, client_ip: str) -> Tuple[bool, Dict]:
        """
        Verifica rate limit conforme H003

        Returns:
            Tuple[bool, Dict]: (is_allowed, rate_info)
        """
        current_time = time.time()

        async def _check_limits():
            # Chaves Redis
            minute_key = f"webhook_rl:min:{client_ip}"
            burst_key = f"webhook_rl:burst:{client_ip}"
            block_key = f"webhook_rl:block:{client_ip}"

            redis_client = redis_manager.async_client
            if not redis_client:
                return True, {"remaining": self.config.requests_per_minute}

            # Verificar se está bloqueado
            blocked_until = await redis_client.get(block_key)
            if blocked_until and float(blocked_until) > current_time:
                remaining_block = int(float(blocked_until) - current_time)
                return False, {
                    "reason": "blocked",
                    "retry_after": remaining_block,
                    "remaining": 0,
                }

            # Pipeline para operações atômicas
            pipe = redis_client.pipeline()

            # 1. Verificar/limpar janela de 1 minuto
            window_start = current_time - self.config.window_seconds
            pipe.zremrangebyscore(minute_key, 0, window_start)
            pipe.zcard(minute_key)

            # 2. Verificar/limpar janela de burst (10s)
            burst_start = current_time - self.config.burst_window
            pipe.zremrangebyscore(burst_key, 0, burst_start)
            pipe.zcard(burst_key)

            results = await pipe.execute()
            current_minute_count = results[1]
            current_burst_count = results[3]

            # Verificar limites
            minute_exceeded = current_minute_count >= self.config.requests_per_minute
            burst_exceeded = current_burst_count >= self.config.burst_protection

            if minute_exceeded or burst_exceeded:
                # Aplicar bloqueio
                block_until = current_time + self.config.block_duration
                await redis_client.setex(
                    block_key, self.config.block_duration, block_until
                )

                return False, {
                    "reason": "limit_exceeded",
                    "retry_after": self.config.block_duration,
                    "remaining": 0,
                    "minute_count": current_minute_count,
                    "burst_count": current_burst_count,
                }

            return True, {
                "remaining": self.config.requests_per_minute - current_minute_count,
                "minute_count": current_minute_count,
                "burst_count": current_burst_count,
            }

        return await execute_redis_safe_async(
            _check_limits,
            default=(True, {"remaining": self.config.requests_per_minute}),
        )

    async def _record_request(self, client_ip: str):
        """Registra request para contabilização"""
        current_time = time.time()

        async def _record():
            minute_key = f"webhook_rl:min:{client_ip}"
            burst_key = f"webhook_rl:burst:{client_ip}"

            redis_client = redis_manager.async_client
            if not redis_client:
                return

            pipe = redis_client.pipeline()

            # Adicionar timestamp atual
            pipe.zadd(minute_key, {str(current_time): current_time})
            pipe.zadd(burst_key, {str(current_time): current_time})

            # Definir expiração
            pipe.expire(minute_key, self.config.window_seconds + 30)  # +30s buffer
            pipe.expire(burst_key, self.config.burst_window + 10)  # +10s buffer

            await pipe.execute()

        await execute_redis_safe_async(_record)

    async def _log_rate_limit_block(
        self, client_ip: str, rate_info: Dict, request: Request
    ):
        """Log estruturado do bloqueio por rate limit"""

        # Log principal
        logger.warning(
            "H003 Webhook rate limit exceeded",
            extra={
                "event": "webhook_rate_limit_block",
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown"),
                "path": request.url.path,
                "method": request.method,
                "reason": rate_info.get("reason", "unknown"),
                "retry_after": rate_info.get("retry_after", 60),
                "minute_count": rate_info.get("minute_count", 0),
                "burst_count": rate_info.get("burst_count", 0),
                "limit_per_minute": self.config.requests_per_minute,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # Log de segurança adicional
        logger.error(
            f"SECURITY: Rate limit block - IP {client_ip} exceeded {self.config.requests_per_minute} req/min"
        )

    async def get_rate_limit_stats(self, client_ip: str) -> Dict:
        """Obter estatísticas atuais de rate limiting (para debug/admin)"""
        current_time = time.time()

        async def _get_stats():
            minute_key = f"webhook_rl:min:{client_ip}"
            burst_key = f"webhook_rl:burst:{client_ip}"
            block_key = f"webhook_rl:block:{client_ip}"

            redis_client = redis_manager.async_client
            if not redis_client:
                return {}

            pipe = redis_client.pipeline()

            # Limpar dados antigos e contar atuais
            window_start = current_time - self.config.window_seconds
            burst_start = current_time - self.config.burst_window

            pipe.zremrangebyscore(minute_key, 0, window_start)
            pipe.zcard(minute_key)
            pipe.zremrangebyscore(burst_key, 0, burst_start)
            pipe.zcard(burst_key)
            pipe.get(block_key)

            results = await pipe.execute()

            minute_count = results[1]
            burst_count = results[3]
            blocked_until = results[4]

            is_blocked = blocked_until and float(blocked_until) > current_time

            return {
                "client_ip": client_ip,
                "current_minute_count": minute_count,
                "current_burst_count": burst_count,
                "limit_per_minute": self.config.requests_per_minute,
                "burst_limit": self.config.burst_protection,
                "remaining_requests": max(
                    0, self.config.requests_per_minute - minute_count
                ),
                "is_blocked": is_blocked,
                "blocked_until": float(blocked_until) if blocked_until else None,
                "window_seconds": self.config.window_seconds,
                "burst_window_seconds": self.config.burst_window,
            }

        return await execute_redis_safe_async(_get_stats, default={})

    async def clear_rate_limit_data(self, client_ip: str) -> int:
        """Limpar dados de rate limiting para um IP específico"""

        async def _clear_data():
            keys_to_clear = [
                f"webhook_rl:min:{client_ip}",
                f"webhook_rl:burst:{client_ip}",
                f"webhook_rl:block:{client_ip}",
            ]

            redis_client = redis_manager.async_client
            if not redis_client:
                return 0

            pipe = redis_client.pipeline()
            for key in keys_to_clear:
                pipe.delete(key)

            results = await pipe.execute()
            return sum(results)

        return await execute_redis_safe_async(_clear_data, default=0)

    async def get_system_overview(self) -> Dict:
        """Obter visão geral do sistema de rate limiting"""

        async def _get_overview():
            # Buscar algumas chaves ativas
            pattern = "webhook_rl:*"

            redis_client = redis_manager.async_client
            if not redis_client:
                return {}

            keys = await redis_client.keys(pattern)

            active_ips = set()
            blocked_ips = set()
            current_time = time.time()

            for key in keys:
                if ":block:" in key:
                    ip = key.split(":")[-1]
                    blocked_until = await redis_client.get(key)
                    if blocked_until and float(blocked_until) > current_time:
                        blocked_ips.add(ip)
                elif ":min:" in key:
                    ip = key.split(":")[-1]
                    active_ips.add(ip)

            return {
                "total_active_ips": len(active_ips),
                "currently_blocked_ips": len(blocked_ips),
                "blocked_ips_list": list(blocked_ips),
                "redis_keys_count": len(keys),
            }

        return await execute_redis_safe_async(_get_overview, default={})


# Instância global para uso em rotas admin
webhook_rate_limit_middleware = None


def get_webhook_rate_limit_middleware() -> Optional[WebhookRateLimitMiddleware]:
    """Obter instância do middleware para uso em rotas admin"""
    global webhook_rate_limit_middleware
    if webhook_rate_limit_middleware is None:
        # Criar uma instância temporária para uso nas rotas admin
        webhook_rate_limit_middleware = WebhookRateLimitMiddleware(None)
    return webhook_rate_limit_middleware
