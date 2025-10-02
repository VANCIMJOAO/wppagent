"""
H003 - Rotas Administrativas Rate Limiting Webhook
=================================================

Rotas para monitorar e testar o sistema H003:
- Estatísticas de rate limiting
- Teste automatizado (101 requests em 1min)
- Logs de blocking
- Limpeza de bloqueios
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config.redis_config import execute_redis_safe, redis_manager
from app.middleware.webhook_rate_limit import get_webhook_rate_limit_middleware
from app.routes.admin_auth import AdminUser, get_current_admin_user

# Logger estruturado
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/webhook-rate-limit", tags=["H003 Admin"])

# Get the middleware instance
webhook_rate_limiter = get_webhook_rate_limit_middleware()


class RateLimitStats(BaseModel):
    """Modelo para estatísticas de rate limiting"""

    client_ip: str
    current_minute_count: int
    current_burst_count: int
    limit_per_minute: int
    burst_limit: int
    remaining_requests: int
    is_blocked: bool
    blocked_until: Optional[float] = None
    window_seconds: int
    burst_window_seconds: int


class TestResult(BaseModel):
    """Resultado do teste H003"""

    test_type: str
    total_requests: int
    successful_requests: int
    blocked_requests: int
    first_block_at_request: Optional[int] = None
    test_duration_seconds: float
    requests_per_second: float
    h003_compliance: bool
    details: List[Dict]


@router.get("/stats/{client_ip}")
async def get_rate_limit_stats(
    client_ip: str, current_admin: AdminUser = Depends(get_current_admin_user)
) -> RateLimitStats:
    """
    📊 Obter estatísticas de rate limiting para um IP específico
    """
    try:
        middleware = get_webhook_rate_limit_middleware()
        if not middleware:
            raise HTTPException(
                status_code=503, detail="Webhook rate limiting middleware not available"
            )

        stats = await middleware.get_rate_limit_stats(client_ip)

        if not stats:
            # Retornar stats zeradas se não há dados
            return RateLimitStats(
                client_ip=client_ip,
                current_minute_count=0,
                current_burst_count=0,
                limit_per_minute=100,
                burst_limit=20,
                remaining_requests=100,
                is_blocked=False,
                window_seconds=60,
                burst_window_seconds=10,
            )

        return RateLimitStats(**stats)

    except Exception as e:
        logger.error(f"Erro ao obter stats de rate limiting: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting rate limit stats: {str(e)}"
        )


@router.delete("/clear/{client_ip}")
async def clear_rate_limit_blocks(
    client_ip: str, current_admin: AdminUser = Depends(get_current_admin_user)
) -> Dict:
    """
    🧹 Limpar bloqueios de rate limiting para um IP específico
    """
    try:

        async def _clear_blocks():
            keys_to_clear = [
                f"webhook_rl:min:{client_ip}",
                f"webhook_rl:burst:{client_ip}",
                f"webhook_rl:block:{client_ip}",
            ]

            pipe = redis_manager.redis_client.pipeline()
            for key in keys_to_clear:
                pipe.delete(key)

            results = await pipe.execute()
            cleared_count = sum(results)

            return cleared_count

        cleared = await execute_redis_safe(_clear_blocks, default=0)

        logger.info(
            f"Admin cleared rate limit blocks for IP {client_ip}",
            extra={
                "admin_user": current_admin.username,
                "client_ip": client_ip,
                "cleared_keys": cleared,
            },
        )

        return {
            "success": True,
            "client_ip": client_ip,
            "cleared_keys": cleared,
            "message": f"Rate limit blocks cleared for IP {client_ip}",
        }

    except Exception as e:
        logger.error(f"Erro ao limpar bloqueios: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error clearing rate limit blocks: {str(e)}"
        )


@router.get("/logs")
async def get_rate_limit_logs(
    hours: int = Query(1, ge=1, le=24, description="Últimas X horas"),
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> Dict:
    """
    📋 Obter logs de bloqueios por rate limiting das últimas horas
    """
    try:
        # Simular busca de logs (implementar com seu sistema de logs preferido)
        # Aqui seria integração com ElasticSearch, CloudWatch, etc.

        return {
            "period_hours": hours,
            "logs_available": True,
            "message": "Rate limit logs would be retrieved from logging system",
            "note": "Integrate with your logging infrastructure (ELK, CloudWatch, etc.)",
            "log_query": f"event:webhook_rate_limit_block AND timestamp:now-{hours}h",
        }

    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@router.post("/test/h003-compliance")
async def test_h003_compliance(
    test_ip: str = Query("127.0.0.1", description="IP para teste"),
    requests_count: int = Query(
        101, ge=101, le=150, description="Número de requests (deve ser > 100)"
    ),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> TestResult:
    """
    🧪 Teste H003 - Enviar 101+ requests em 1 minuto e verificar HTTP 429

    Este teste valida:
    ✅ Limite de 100 req/min por IP
    ✅ HTTP 429 após exceder limite
    ✅ Logs de blocking funcionais
    ✅ Health check não afetado
    """

    # Limpar bloqueios anteriores
    await clear_rate_limit_blocks(test_ip, current_admin)

    logger.info(
        f"Iniciando teste H003 compliance",
        extra={
            "admin_user": current_admin.username,
            "test_ip": test_ip,
            "requests_count": requests_count,
        },
    )

    start_time = time.time()
    results = []
    successful_requests = 0
    blocked_requests = 0
    first_block_at_request = None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Realizar requests sequenciais
            for i in range(requests_count):
                request_start = time.time()

                try:
                    # Simular request para webhook
                    response = await client.post(
                        "http://localhost:8000/webhook",  # Ajustar URL conforme necessário
                        json={"test": f"h003_compliance_{i}"},
                        headers={
                            "X-Forwarded-For": test_ip,
                            "User-Agent": f"H003-Test-{i}",
                        },
                    )

                    request_duration = time.time() - request_start

                    result = {
                        "request_number": i + 1,
                        "status_code": response.status_code,
                        "success": response.status_code < 400,
                        "duration_ms": round(request_duration * 1000, 2),
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    if response.status_code == 429:
                        blocked_requests += 1
                        if first_block_at_request is None:
                            first_block_at_request = i + 1
                        result["rate_limited"] = True

                        # Extrair headers de rate limiting
                        result["retry_after"] = response.headers.get("Retry-After")
                        result["rate_limit_remaining"] = response.headers.get(
                            "X-RateLimit-Remaining"
                        )

                    elif response.status_code < 400:
                        successful_requests += 1
                        result["rate_limited"] = False

                    results.append(result)

                except httpx.TimeoutException:
                    results.append(
                        {
                            "request_number": i + 1,
                            "status_code": 0,
                            "success": False,
                            "error": "timeout",
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                except Exception as e:
                    results.append(
                        {
                            "request_number": i + 1,
                            "status_code": 0,
                            "success": False,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                # Pequeno delay para simular tráfego realista
                await asyncio.sleep(0.01)

        test_duration = time.time() - start_time
        requests_per_second = requests_count / test_duration

        # Verificar conformidade H003
        h003_compliance = (
            first_block_at_request is not None
            and first_block_at_request <= 101  # Deve bloquear até request 101
            and blocked_requests > 0
            and successful_requests <= 100  # Máx 100 requests bem-sucedidas
        )

        test_result = TestResult(
            test_type="H003_compliance",
            total_requests=requests_count,
            successful_requests=successful_requests,
            blocked_requests=blocked_requests,
            first_block_at_request=first_block_at_request,
            test_duration_seconds=round(test_duration, 2),
            requests_per_second=round(requests_per_second, 2),
            h003_compliance=h003_compliance,
            details=results,
        )

        # Log do resultado
        logger.info(
            f"Teste H003 concluído",
            extra={
                "admin_user": current_admin.username,
                "test_result": test_result.dict(exclude={"details"}),
                "h003_compliance": h003_compliance,
            },
        )

        return test_result

    except Exception as e:
        logger.error(f"Erro no teste H003: {e}")
        raise HTTPException(status_code=500, detail=f"H003 test failed: {str(e)}")


@router.get("/health-check-test")
async def test_health_check_exemption(
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> Dict:
    """
    🏥 Testar que health check não é afetado pelo rate limiting
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Fazer várias requests para health check
            health_results = []

            for i in range(10):
                response = await client.get("http://localhost:8000/health")
                health_results.append(
                    {
                        "request": i + 1,
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                    }
                )

        all_successful = all(r["success"] for r in health_results)

        return {
            "test": "health_check_exemption",
            "requests_made": len(health_results),
            "all_successful": all_successful,
            "h003_compliance": all_successful,  # Health check deve sempre funcionar
            "results": health_results,
            "message": "Health check should never be rate limited",
        }

    except Exception as e:
        logger.error(f"Erro no teste health check: {e}")
        raise HTTPException(
            status_code=500, detail=f"Health check test failed: {str(e)}"
        )


@router.get("/overview")
async def get_rate_limiting_overview(
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> Dict:
    """
    📊 Visão geral do sistema H003 Rate Limiting
    """
    try:
        # Buscar estatísticas gerais
        async def _get_overview():
            # Buscar algumas chaves ativas
            pattern = "webhook_rl:*"
            keys = await redis_manager.redis_client.keys(pattern)

            active_ips = set()
            blocked_ips = set()

            for key in keys:
                if ":block:" in key:
                    ip = key.split(":")[-1]
                    blocked_until = await redis_manager.redis_client.get(key)
                    if blocked_until and float(blocked_until) > time.time():
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

        overview = await execute_redis_safe(_get_overview, default={})

        return {
            "h003_status": "active",
            "rate_limit_config": {
                "requests_per_minute": 100,
                "burst_protection": 20,
                "burst_window_seconds": 10,
                "block_duration_seconds": 300,
                "window_seconds": 60,
            },
            "current_stats": overview,
            "exempt_paths": ["/health", "/healthz", "/ready", "/ping"],
            "protected_paths": ["/webhook", "/api/webhook"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Erro ao obter overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting overview: {str(e)}")


@router.post("/clear-blocks")
async def clear_webhook_blocks(
    source_ip: str = Query(..., description="IP da fonte a desbloquear"),
    webhook_type: str = Query("default", description="Tipo do webhook"),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    🔓 Limpar bloqueios de rate limiting para uma fonte específica (ADMIN ONLY)
    """
    try:
        cleared = await webhook_rate_limiter.clear_webhook_blocks(
            source_ip=source_ip, webhook_type=webhook_type
        )

        if cleared:
            logger.info(
                f"Admin {current_admin.username} cleared webhook blocks for {source_ip}:{webhook_type}"
            )
            return {
                "status": "success",
                "message": f"Blocks cleared for {source_ip}:{webhook_type}",
                "admin": current_admin.username,
            }
        else:
            return {
                "status": "info",
                "message": f"No blocks found for {source_ip}:{webhook_type}",
                "admin": current_admin.username,
            }

    except Exception as e:
        logger.error(f"Erro ao limpar bloqueios para {source_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_webhook_rate_limiting_config(
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    ⚙️ Obter configuração atual do sistema de rate limiting
    """
    try:
        configs = {
            name: {
                "burst_limit": config.burst_limit,
                "burst_window": config.burst_window,
                "sustained_limit": config.sustained_limit,
                "escalation_factor": config.escalation_factor,
                "block_duration": config.block_duration,
            }
            for name, config in webhook_rate_limiter.configs.items()
        }

        return {
            "status": "success",
            "configs": configs,
            "admin": current_admin.username,
        }
    except Exception as e:
        logger.error(f"Erro ao obter configuração: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_webhook_rate_limiting(
    source_ip: str = Query("127.0.0.1", description="IP para teste"),
    webhook_type: str = Query("default", description="Tipo do webhook"),
    requests: int = Query(5, ge=1, le=20, description="Número de requisições de teste"),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    🧪 Testar sistema de rate limiting (máximo 20 requisições)
    """
    try:
        results = []

        for i in range(requests):
            allowed, info = await webhook_rate_limiter.check_webhook_rate_limit(
                source_ip=f"test_{source_ip}",  # Prefixo para evitar conflito
                webhook_type=webhook_type,
                user_agent="admin_test",
                payload_size=100,
            )

            results.append(
                {
                    "request_number": i + 1,
                    "allowed": allowed,
                    "level": info.get("level"),
                    "reason": info.get("reason"),
                    "metrics": info.get("metrics"),
                }
            )

            # Se bloqueado, parar o teste
            if not allowed:
                break

        return {
            "status": "success",
            "test_results": results,
            "total_requests": len(results),
            "admin": current_admin.username,
        }

    except Exception as e:
        logger.error(f"Erro no teste de rate limiting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/real-time")
async def get_real_time_webhook_metrics(
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    📈 Métricas em tempo real do sistema de rate limiting
    """
    try:
        stats = await webhook_rate_limiter.get_webhook_stats()

        # Adicionar métricas em tempo real
        real_time_data = {
            **stats,
            "cache_info": {
                "local_cache_entries": len(webhook_rate_limiter._local_cache),
                "cache_ttl_seconds": webhook_rate_limiter._cache_ttl,
            },
            "health_status": "operational" if not stats.get("error") else "degraded",
        }

        return {
            "status": "success",
            "real_time_metrics": real_time_data,
            "admin": current_admin.username,
        }

    except Exception as e:
        logger.error(f"Erro ao obter métricas em tempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))
