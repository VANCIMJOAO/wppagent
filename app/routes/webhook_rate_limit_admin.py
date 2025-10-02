"""
Sistema de Rate Limiting para Webhooks - Interface Administrativa

Este arquivo foi criado para resolver o erro de deploy no Railway.
O arquivo original estava faltando e causava falha na inicialização.
"""

from fastapi import APIRouter

# Criar router vazio temporário
router = APIRouter()

@router.get("/webhook-rate-limit/admin/status")
async def webhook_rate_limit_admin_status():
    """Endpoint temporário para status do rate limiting de webhooks"""
    return {
        "status": "operational",
        "message": "Webhook rate limiting admin routes - temporary implementation",
        "features": "disabled"
    }

@router.get("/webhook-rate-limit/admin/stats")
async def webhook_rate_limit_admin_stats():
    """Endpoint temporário para estatísticas do rate limiting"""
    return {
        "total_requests": 0,
        "blocked_requests": 0,
        "rate_limit_hits": 0,
        "status": "disabled"
    }
