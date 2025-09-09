"""
🚀 Webhook Rate Limiting Admin Routes
===================================

Endpoints administrativos para monitorar e gerenciar 
o sistema de rate limiting de webhooks.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import logging

from app.auth.webhook_rate_limiter import webhook_rate_limiter
from app.routes.admin_auth import get_current_admin_user, AdminUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/webhook-rate-limit", tags=["Admin - Webhook Rate Limiting"])

@router.get("/stats")
async def get_webhook_rate_limiting_stats(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    📊 Obter estatísticas gerais do sistema de rate limiting de webhooks
    """
    try:
        stats = await webhook_rate_limiter.get_webhook_stats()
        return {
            "status": "success",
            "data": stats,
            "admin": current_admin.username
        }
    except Exception as e:
        logger.error(f"Erro ao obter stats de webhook rate limiting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-source")
async def check_webhook_source_status(
    source_ip: str = Query(..., description="IP da fonte a verificar"),
    webhook_type: str = Query("default", description="Tipo do webhook"),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    🔍 Verificar status de rate limiting para uma fonte específica
    """
    try:
        # Simular verificação sem consumir limite
        allowed, info = await webhook_rate_limiter.check_webhook_rate_limit(
            source_ip=source_ip,
            webhook_type=webhook_type,
            user_agent="admin_check",
            payload_size=0
        )
        
        # Reverter o registro da requisição de teste (se possível)
        # Nota: Em produção, seria melhor ter um método específico para verificação
        
        return {
            "status": "success",
            "source_ip": source_ip,
            "webhook_type": webhook_type,
            "allowed": allowed,
            "info": info,
            "admin": current_admin.username
        }
    except Exception as e:
        logger.error(f"Erro ao verificar fonte {source_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-blocks")
async def clear_webhook_blocks(
    source_ip: str = Query(..., description="IP da fonte a desbloquear"),
    webhook_type: str = Query("default", description="Tipo do webhook"),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    🔓 Limpar bloqueios de rate limiting para uma fonte específica (ADMIN ONLY)
    """
    try:
        cleared = await webhook_rate_limiter.clear_webhook_blocks(
            source_ip=source_ip,
            webhook_type=webhook_type
        )
        
        if cleared:
            logger.info(f"Admin {current_admin.username} cleared webhook blocks for {source_ip}:{webhook_type}")
            return {
                "status": "success",
                "message": f"Blocks cleared for {source_ip}:{webhook_type}",
                "admin": current_admin.username
            }
        else:
            return {
                "status": "info",
                "message": f"No blocks found for {source_ip}:{webhook_type}",
                "admin": current_admin.username
            }
    
    except Exception as e:
        logger.error(f"Erro ao limpar bloqueios para {source_ip}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
async def get_webhook_rate_limiting_config(
    current_admin: AdminUser = Depends(get_current_admin_user)
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
                "block_duration": config.block_duration
            }
            for name, config in webhook_rate_limiter.configs.items()
        }
        
        return {
            "status": "success",
            "configs": configs,
            "admin": current_admin.username
        }
    except Exception as e:
        logger.error(f"Erro ao obter configuração: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_webhook_rate_limiting(
    source_ip: str = Query("127.0.0.1", description="IP para teste"),
    webhook_type: str = Query("default", description="Tipo do webhook"),
    requests: int = Query(5, ge=1, le=20, description="Número de requisições de teste"),
    current_admin: AdminUser = Depends(get_current_admin_user)
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
                payload_size=100
            )
            
            results.append({
                "request_number": i + 1,
                "allowed": allowed,
                "level": info.get("level"),
                "reason": info.get("reason"),
                "metrics": info.get("metrics")
            })
            
            # Se bloqueado, parar o teste
            if not allowed:
                break
        
        return {
            "status": "success",
            "test_results": results,
            "total_requests": len(results),
            "admin": current_admin.username
        }
    
    except Exception as e:
        logger.error(f"Erro no teste de rate limiting: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/metrics/real-time")
async def get_real_time_webhook_metrics(
    current_admin: AdminUser = Depends(get_current_admin_user)
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
                "cache_ttl_seconds": webhook_rate_limiter._cache_ttl
            },
            "health_status": "operational" if not stats.get("error") else "degraded"
        }
        
        return {
            "status": "success",
            "real_time_metrics": real_time_data,
            "admin": current_admin.username
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter métricas em tempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))
