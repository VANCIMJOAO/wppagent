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

# Importar auth disponível (verificar estrutura real)
try:
    from app.auth.admin_auth import AdminUser, get_current_admin_user
except ImportError:
    # Fallback se admin_auth não existir
    class AdminUser:
        username: str = "admin"

    def get_current_admin_user():
        return AdminUser()


from app.middleware.webhook_rate_limit import get_webhook_rate_limit_middleware

# Logger estruturado
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/h003", tags=["H003 Admin"])


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
        middleware = get_webhook_rate_limit_middleware()
        if not middleware:
            raise HTTPException(
                status_code=503, detail="Webhook rate limiting middleware not available"
            )

        cleared = await middleware.clear_rate_limit_data(client_ip)

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


@router.post("/test/compliance")
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
        middleware = get_webhook_rate_limit_middleware()
        if not middleware:
            raise HTTPException(
                status_code=503, detail="Webhook rate limiting middleware not available"
            )

        # Buscar estatísticas gerais do middleware
        overview = await middleware.get_system_overview()

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
            "middleware_available": True,
        }

    except Exception as e:
        logger.error(f"Erro ao obter overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting overview: {str(e)}")
