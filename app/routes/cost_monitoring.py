"""
Rotas para monitoramento de custos da OpenAI
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
import logging
from datetime import datetime

from app.services.cost_tracker import cost_tracker
from app.utils.logger import get_logger
from app.middleware.rate_limit import RateLimiter
logger = get_logger(__name__)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/costs", tags=["costs"])

# Rate limiting para endpoints de custo
rate_limiter = RateLimiter(max_requests=20, window_minutes=1)

@router.get("/report")
async def get_cost_report():
    """Retorna relatório completo de custos"""
    try:
        report = cost_tracker.get_detailed_report()
        return {
            "success": True,
            "data": report,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erro ao gerar relatório de custos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session")
async def get_session_costs():
    """Retorna custos da sessão atual"""
    try:
        session_cost_usd = cost_tracker.get_session_cost()
        session_cost_brl = cost_tracker.get_cost_in_brl(session_cost_usd)
        
        return {
            "success": True,
            "data": {
                "cost_usd": round(session_cost_usd, 6),
                "cost_brl": round(session_cost_brl, 4),
                "usage": cost_tracker.session_usage
            }
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter custos da sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily")
async def get_daily_costs(date: Optional[str] = None):
    """Retorna custos diários"""
    try:
        if date and date != datetime.now().strftime("%Y-%m-%d"):
            # Validar formato da data
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
        
        daily_cost_usd = cost_tracker.get_daily_cost(date)
        daily_cost_brl = cost_tracker.get_cost_in_brl(daily_cost_usd)
        
        return {
            "success": True,
            "data": {
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "cost_usd": round(daily_cost_usd, 6),
                "cost_brl": round(daily_cost_brl, 4),
                "limit_usd": cost_tracker.daily_limit_usd,
                "limit_brl": cost_tracker.daily_limit_usd * cost_tracker.exchange_rate,
                "usage_percentage": round((daily_cost_usd / cost_tracker.daily_limit_usd * 100) if cost_tracker.daily_limit_usd > 0 else 0, 2)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter custos diários: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monthly")
async def get_monthly_costs(month: Optional[str] = None):
    """Retorna custos mensais"""
    try:
        if month and month != datetime.now().strftime("%Y-%m"):
            # Validar formato do mês
            try:
                datetime.strptime(month, "%Y-%m")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de mês inválido. Use YYYY-MM")
        
        monthly_cost_usd = cost_tracker.get_monthly_cost(month)
        monthly_cost_brl = cost_tracker.get_cost_in_brl(monthly_cost_usd)
        
        return {
            "success": True,
            "data": {
                "month": month or datetime.now().strftime("%Y-%m"),
                "cost_usd": round(monthly_cost_usd, 6),
                "cost_brl": round(monthly_cost_brl, 4),
                "limit_usd": cost_tracker.monthly_limit_usd,
                "limit_brl": cost_tracker.monthly_limit_usd * cost_tracker.exchange_rate,
                "usage_percentage": round((monthly_cost_usd / cost_tracker.monthly_limit_usd * 100) if cost_tracker.monthly_limit_usd > 0 else 0, 2)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter custos mensais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projection")
async def get_cost_projection(days: int = 30):
    """Retorna projeção de custos"""
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Dias deve estar entre 1 e 365")
        
        projection = cost_tracker.get_cost_projection(days)
        
        return {
            "success": True,
            "data": projection
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao obter projeção de custos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings")
async def update_cost_settings(
    daily_limit_usd: Optional[float] = None,
    monthly_limit_usd: Optional[float] = None,
    exchange_rate: Optional[float] = None,
    alert_threshold: Optional[float] = None
):
    """Atualiza configurações de limites de custo"""
    try:
        # Validações
        if daily_limit_usd is not None and daily_limit_usd <= 0:
            raise HTTPException(status_code=400, detail="Limite diário deve ser positivo")
        
        if monthly_limit_usd is not None and monthly_limit_usd <= 0:
            raise HTTPException(status_code=400, detail="Limite mensal deve ser positivo")
        
        if exchange_rate is not None and exchange_rate <= 0:
            raise HTTPException(status_code=400, detail="Taxa de câmbio deve ser positiva")
        
        if alert_threshold is not None and (alert_threshold <= 0 or alert_threshold > 1):
            raise HTTPException(status_code=400, detail="Threshold de alerta deve estar entre 0 e 1")
        
        cost_tracker.update_settings(
            daily_limit_usd=daily_limit_usd,
            monthly_limit_usd=monthly_limit_usd,
            exchange_rate=exchange_rate,
            alert_threshold=alert_threshold
        )
        
        return {
            "success": True,
            "message": "Configurações atualizadas com sucesso",
            "current_settings": {
                "daily_limit_usd": cost_tracker.daily_limit_usd,
                "monthly_limit_usd": cost_tracker.monthly_limit_usd,
                "exchange_rate": cost_tracker.exchange_rate,
                "alert_threshold": cost_tracker.alert_threshold
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar configurações: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-session")
async def reset_session_costs():
    """Reseta contadores da sessão atual"""
    try:
        cost_tracker.reset_session_usage()
        
        return {
            "success": True,
            "message": "Contadores de sessão resetados com sucesso"
        }
    except Exception as e:
        logger.error(f"❌ Erro ao resetar sessão: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_cost_summary():
    """Retorna resumo rápido de custos"""
    try:
        session_cost = cost_tracker.get_session_cost()
        daily_cost = cost_tracker.get_daily_cost()
        monthly_cost = cost_tracker.get_monthly_cost()
        
        return {
            "success": True,
            "data": {
                "session_usd": round(session_cost, 6),
                "session_brl": round(cost_tracker.get_cost_in_brl(session_cost), 4),
                "daily_usd": round(daily_cost, 6),
                "daily_brl": round(cost_tracker.get_cost_in_brl(daily_cost), 4),
                "daily_usage_pct": round((daily_cost / cost_tracker.daily_limit_usd * 100) if cost_tracker.daily_limit_usd > 0 else 0, 1),
                "monthly_usd": round(monthly_cost, 6),
                "monthly_brl": round(cost_tracker.get_cost_in_brl(monthly_cost), 4),
                "monthly_usage_pct": round((monthly_cost / cost_tracker.monthly_limit_usd * 100) if cost_tracker.monthly_limit_usd > 0 else 0, 1),
                "within_limits": {
                    "daily": daily_cost <= cost_tracker.daily_limit_usd,
                    "monthly": monthly_cost <= cost_tracker.monthly_limit_usd
                }
            }
        }
    except Exception as e:
        logger.error(f"❌ Erro ao obter resumo de custos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/timeline")
async def get_cost_timeline(days: int = 30):
    """Retorna histórico de custos por dia"""
    try:
        from datetime import datetime, timedelta
        import json
        
        timeline_data = []
        end_date = datetime.now().date()
        
        for i in range(days):
            date = end_date - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            # Obter custo do dia
            daily_cost = cost_tracker.get_daily_cost(date_str)
            
            timeline_data.append({
                "date": date_str,
                "cost": round(daily_cost, 6),
                "cost_brl": round(cost_tracker.get_cost_in_brl(daily_cost), 4)
            })
        
        # Ordenar por data (mais antigo primeiro)
        timeline_data.reverse()
        
        return {
            "success": True,
            "data": timeline_data,
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter timeline de custos: {e}")
        raise HTTPException(status_code=500, detail=str(e))
