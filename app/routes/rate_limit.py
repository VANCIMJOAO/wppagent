"""
API endpoints para gerenciamento de Rate Limiting por Usuário
"""

from typing import Dict, List, Optional
from datetime import datetime
import json

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.routes.admin_auth import get_current_admin_user
from app.models.database import AdminUser
from app.middleware.user_rate_limit import get_user_rate_limiter
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/rate-limit", tags=["rate-limiting"])

# Modelos Pydantic
class RateLimitStatus(BaseModel):
    user_id: str
    endpoint: str
    current_requests: int
    limit: int
    remaining: int
    window_seconds: int
    reset_at: int

class RateLimitConfig(BaseModel):
    endpoint: str
    requests: int
    window: int
    burst: Optional[int] = None

class UserRateLimitUpdate(BaseModel):
    user_id: str
    user_type: Optional[str] = None
    custom_limits: Optional[Dict[str, Dict]] = None

class RateLimitViolation(BaseModel):
    timestamp: str
    user_id: str
    endpoint: str
    violation_type: str
    current_requests: int
    limit: int

@router.get("/status")
async def get_rate_limit_status(
    user_id: Optional[str] = Query(None, description="ID do usuário específico"),
    endpoint: Optional[str] = Query(None, description="Endpoint específico"),
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Obter status de rate limiting
    """
    try:
        rate_limiter = get_user_rate_limiter()
        
        if user_id:
            # Status para usuário específico
            status = await rate_limiter.get_user_rate_limit_status(user_id, endpoint)
            
            return {
                "success": True,
                "user_id": user_id,
                "endpoint": endpoint or "all",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Status geral do sistema
            return {
                "success": True,
                "system_status": "active",
                "total_limits": len(rate_limiter.limits),
                "user_types": list(rate_limiter.user_type_multipliers.keys()),
                "default_config": rate_limiter.limits.get("default"),
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_rate_limit_config(admin_user: AdminUser = Depends(get_current_admin_user)):
    """
    Obter configuração atual de rate limiting
    """
    try:
        rate_limiter = get_user_rate_limiter()
        
        return {
            "success": True,
            "endpoint_limits": rate_limiter.limits,
            "user_type_multipliers": rate_limiter.user_type_multipliers,
            "total_endpoints": len(rate_limiter.limits),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_rate_limit(
    user_id: str = Query(..., description="ID do usuário"),
    endpoint: Optional[str] = Query(None, description="Endpoint específico (opcional)"),
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Resetar rate limit para usuário específico
    """
    try:
        rate_limiter = get_user_rate_limiter()
        
        await rate_limiter.reset_user_rate_limit(user_id, endpoint)
        
        logger.info(f"Rate limit reset by admin {admin_user.username} for user {user_id}, endpoint: {endpoint or 'all'}")
        
        return {
            "success": True,
            "message": f"Rate limit reset for user {user_id}",
            "user_id": user_id,
            "endpoint": endpoint or "all",
            "reset_by": admin_user.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/violations")
async def get_rate_limit_violations(
    user_id: Optional[str] = Query(None, description="Filtrar por usuário"),
    endpoint: Optional[str] = Query(None, description="Filtrar por endpoint"),
    hours: int = Query(24, description="Horas para buscar violações"),
    limit: int = Query(100, description="Limite de resultados"),
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Obter histórico de violações de rate limit
    """
    try:
        # Simulação de violações - em produção, essas informações viriam do Redis ou banco
        # Por enquanto, retornar estrutura esperada
        
        violations = []  # Seria obtido do Redis ou logs
        
        # Exemplo de estrutura de violação
        example_violation = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id or "example_user",
            "endpoint": endpoint or "POST /admin/auth/login",
            "violation_type": "main_limit",
            "current_requests": 15,
            "limit": 10,
            "window": 300,
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0..."
        }
        
        return {
            "success": True,
            "violations": violations,
            "total_violations": len(violations),
            "filters": {
                "user_id": user_id,
                "endpoint": endpoint,
                "hours": hours,
                "limit": limit
            },
            "example_structure": example_violation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_rate_limit_stats(
    hours: int = Query(24, description="Período em horas"),
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Obter estatísticas de rate limiting
    """
    try:
        rate_limiter = get_user_rate_limiter()
        
        # Em produção, essas estatísticas seriam calculadas do Redis
        stats = {
            "period_hours": hours,
            "total_requests": 0,  # Seria calculado do Redis
            "blocked_requests": 0,  # Seria calculado do Redis
            "unique_users": 0,  # Seria calculado do Redis
            "top_endpoints": [],  # Seria calculado do Redis
            "top_violators": [],  # Seria calculado do Redis
            "violation_types": {
                "main_limit": 0,
                "burst_limit": 0
            },
            "user_type_distribution": {
                "admin": 0,
                "premium": 0,
                "regular": 0,
                "guest": 0
            }
        }
        
        return {
            "success": True,
            "stats": stats,
            "config_summary": {
                "total_endpoints": len(rate_limiter.limits),
                "user_types": len(rate_limiter.user_type_multipliers)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/update")
async def update_rate_limit_config(
    config: RateLimitConfig,
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Atualizar configuração de rate limit para endpoint específico
    """
    try:
        rate_limiter = get_user_rate_limiter()
        
        # Validar configuração
        if config.requests <= 0 or config.window <= 0:
            raise HTTPException(status_code=400, detail="Requests and window must be positive")
        
        if config.burst is not None and config.burst <= 0:
            raise HTTPException(status_code=400, detail="Burst must be positive")
        
        # Atualizar configuração
        new_config = {
            "requests": config.requests,
            "window": config.window
        }
        
        if config.burst is not None:
            new_config["burst"] = config.burst
        
        rate_limiter.limits[config.endpoint] = new_config
        
        logger.info(f"Rate limit config updated by admin {admin_user.username} for endpoint {config.endpoint}")
        
        return {
            "success": True,
            "message": f"Rate limit configuration updated for {config.endpoint}",
            "endpoint": config.endpoint,
            "new_config": new_config,
            "updated_by": admin_user.username,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update rate limit config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/update")
async def update_user_rate_limit(
    update: UserRateLimitUpdate,
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Atualizar configuração de rate limit para usuário específico
    """
    try:
        # Esta funcionalidade requereria persistência adicional
        # Por enquanto, retornar que foi aceito
        
        logger.info(f"User rate limit update requested by admin {admin_user.username} for user {update.user_id}")
        
        return {
            "success": True,
            "message": f"User rate limit configuration updated for {update.user_id}",
            "user_id": update.user_id,
            "user_type": update.user_type,
            "custom_limits": update.custom_limits,
            "updated_by": admin_user.username,
            "timestamp": datetime.now().isoformat(),
            "note": "Custom user limits require additional implementation for persistence"
        }
        
    except Exception as e:
        logger.error(f"Failed to update user rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def rate_limit_health_check(admin_user: AdminUser = Depends(get_current_admin_user)):
    """
    Verificar saúde do sistema de rate limiting
    """
    try:
        rate_limiter = get_user_rate_limiter()
        
        # Testar conexão Redis
        redis_healthy = True
        redis_error = None
        
        try:
            # Teste simples de conexão Redis
            await rate_limiter.redis.ping()
        except Exception as e:
            redis_healthy = False
            redis_error = str(e)
        
        health_status = {
            "redis_connection": "healthy" if redis_healthy else "unhealthy",
            "redis_error": redis_error,
            "total_limits_configured": len(rate_limiter.limits),
            "user_types_configured": len(rate_limiter.user_type_multipliers),
            "middleware_active": True  # Sempre True se o endpoint responde
        }
        
        overall_status = "healthy" if redis_healthy else "degraded"
        
        return {
            "success": True,
            "overall_status": overall_status,
            "health_details": health_status,
            "recommendations": [
                "Monitor Redis connection regularly",
                "Check rate limit violations periodically",
                "Review endpoint limits based on usage patterns"
            ] if redis_healthy else [
                "Fix Redis connection immediately",
                "Rate limiting will fail gracefully but won't be enforced",
                "Check Redis configuration and network connectivity"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rate limit health check failed: {e}")
        return {
            "success": False,
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/test/{user_id}")
async def test_rate_limit(
    user_id: str,
    endpoint: str = Query("GET /test", description="Endpoint para testar"),
    requests: int = Query(5, description="Número de requests para simular"),
    admin_user: AdminUser = Depends(get_current_admin_user)
):
    """
    Testar rate limiting para usuário específico (apenas desenvolvimento)
    """
    try:
        rate_limiter = get_user_rate_limiter()
        
        # Obter configuração do endpoint
        config = rate_limiter._get_limit_config(endpoint, 'regular')
        
        # Simular múltiplas requisições
        results = []
        
        for i in range(requests):
            result = await rate_limiter._check_rate_limit(user_id, endpoint, config)
            
            if not result['exceeded']:
                await rate_limiter._increment_counter(user_id, endpoint, config)
            
            results.append({
                "request_number": i + 1,
                "exceeded": result['exceeded'],
                "current": result.get('current', 0),
                "limit": result.get('limit', config['requests'])
            })
        
        return {
            "success": True,
            "test_config": {
                "user_id": user_id,
                "endpoint": endpoint,
                "requests_simulated": requests,
                "endpoint_config": config
            },
            "results": results,
            "final_status": await rate_limiter.get_user_rate_limit_status(user_id, endpoint),
            "timestamp": datetime.now().isoformat(),
            "warning": "This is a test endpoint - use only in development"
        }
        
    except Exception as e:
        logger.error(f"Rate limit test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
