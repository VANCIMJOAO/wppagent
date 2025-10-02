"""
Analytics Endpoints - SPRINT 3
Endpoints otimizados para analytics calculados no backend
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.cache_service import cache_service
from ..config.logging_config import get_optimized_logger

logger = get_optimized_logger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/funnel")
async def get_conversion_funnel(
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    📊 Funil de Conversão
    
    Retorna o funil de conversão: Lead → Interessado → Negociação → Cliente
    com taxas de conversão entre estágios.
    """
    cache_key = f"analytics:funnel:{start_date}:{end_date}"
    
    # Verificar cache primeiro
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        logger.info("Analytics funnel served from cache", cache_key=cache_key)
        return cached_result
    
    try:
        # Construir filtros de data
        date_filters = []
        if start_date:
            date_filters.append(text("c.created_at >= :start_date"))
        if end_date:
            date_filters.append(text("c.created_at <= :end_date"))
        
        date_where = " AND ".join(date_filters) if date_filters else "1=1"
        
        # Query otimizada para funil de conversão
        funnel_query = text(f"""
            WITH conversation_stages AS (
                SELECT 
                    c.id,
                    c.status,
                    c.created_at,
                    CASE 
                        WHEN c.status = 'new' THEN 'Lead'
                        WHEN c.status = 'active' THEN 'Interessado'
                        WHEN c.status = 'negotiation' THEN 'Negociação'
                        WHEN c.status = 'closed' AND c.outcome = 'success' THEN 'Cliente'
                        WHEN c.status = 'closed' AND c.outcome != 'success' THEN 'Perdido'
                        ELSE 'Outros'
                    END as stage
                FROM conversations c
                WHERE {date_where}
            ),
            stage_counts AS (
                SELECT 
                    stage,
                    COUNT(*) as count,
                    MIN(created_at) as first_occurrence,
                    MAX(created_at) as last_occurrence
                FROM conversation_stages
                GROUP BY stage
            )
            SELECT 
                stage,
                count,
                first_occurrence,
                last_occurrence,
                ROUND(
                    (count::float / SUM(count) OVER()) * 100, 2
                ) as percentage_of_total
            FROM stage_counts
            ORDER BY 
                CASE stage
                    WHEN 'Lead' THEN 1
                    WHEN 'Interessado' THEN 2
                    WHEN 'Negociação' THEN 3
                    WHEN 'Cliente' THEN 4
                    WHEN 'Perdido' THEN 5
                    ELSE 6
                END
        """)
        
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        result = db.execute(funnel_query, params).fetchall()
        
        # Calcular taxas de conversão
        stages = [dict(row._mapping) for row in result]
        total_leads = next((s['count'] for s in stages if s['stage'] == 'Lead'), 0)
        
        conversion_rates = []
        for i, stage in enumerate(stages):
            if i == 0:  # Primeiro estágio
                conversion_rates.append(100.0)
            else:
                prev_count = stages[i-1]['count']
                current_count = stage['count']
                rate = (current_count / prev_count * 100) if prev_count > 0 else 0
                conversion_rates.append(round(rate, 2))
        
        # Adicionar taxas de conversão aos dados
        for i, stage in enumerate(stages):
            stage['conversion_rate'] = conversion_rates[i]
        
        response_data = {
            "funnel": stages,
            "summary": {
                "total_conversations": sum(s['count'] for s in stages),
                "total_leads": total_leads,
                "total_clients": next((s['count'] for s in stages if s['stage'] == 'Cliente'), 0),
                "overall_conversion_rate": round(
                    (next((s['count'] for s in stages if s['stage'] == 'Cliente'), 0) / total_leads * 100) 
                    if total_leads > 0 else 0, 2
                )
            },
            "generated_at": datetime.utcnow().isoformat(),
            "cache_ttl": 300  # 5 minutos
        }
        
        # Cache por 5 minutos
        await cache_service.set(cache_key, response_data, ttl=300)
        
        logger.info("Analytics funnel calculated", 
                   total_conversations=response_data['summary']['total_conversations'],
                   overall_conversion_rate=response_data['summary']['overall_conversion_rate'])
        
        return response_data
        
    except Exception as e:
        logger.error("Error calculating conversion funnel", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error calculating conversion funnel: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    ⚡ Métricas de Performance
    
    Retorna tempo médio de resposta, taxa de engajamento e satisfação do cliente.
    """
    cache_key = f"analytics:performance:{start_date}:{end_date}"
    
    # Verificar cache primeiro
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        logger.info("Analytics performance served from cache", cache_key=cache_key)
        return cached_result
    
    try:
        # Construir filtros de data
        date_filters = []
        if start_date:
            date_filters.append(text("c.created_at >= :start_date"))
        if end_date:
            date_filters.append(text("c.created_at <= :end_date"))
        
        date_where = " AND ".join(date_filters) if date_filters else "1=1"
        
        # Query para métricas de performance
        performance_query = text(f"""
            WITH conversation_metrics AS (
                SELECT 
                    c.id,
                    c.status,
                    c.created_at,
                    c.updated_at,
                    c.outcome,
                    COUNT(m.id) as message_count,
                    COUNT(CASE WHEN m.sender = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN m.sender = 'agent' THEN 1 END) as agent_messages,
                    EXTRACT(EPOCH FROM (c.updated_at - c.created_at)) as duration_seconds,
                    CASE 
                        WHEN c.outcome = 'success' THEN 5
                        WHEN c.outcome = 'partial' THEN 3
                        WHEN c.outcome = 'failed' THEN 1
                        ELSE NULL
                    END as satisfaction_score
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE {date_where}
                GROUP BY c.id, c.status, c.created_at, c.updated_at, c.outcome
            )
            SELECT 
                COUNT(*) as total_conversations,
                AVG(message_count) as avg_messages_per_conversation,
                AVG(duration_seconds) as avg_response_time_seconds,
                AVG(satisfaction_score) as avg_satisfaction_score,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_conversations,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_conversations,
                COUNT(CASE WHEN outcome = 'success' THEN 1 END) as successful_conversations,
                AVG(user_messages::float / NULLIF(message_count, 0)) as user_engagement_rate,
                AVG(agent_messages::float / NULLIF(message_count, 0)) as agent_engagement_rate
            FROM conversation_metrics
        """)
        
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        result = db.execute(performance_query, params).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="No performance data found")
        
        # Calcular métricas derivadas
        total_conversations = result.total_conversations or 0
        successful_conversations = result.successful_conversations or 0
        closed_conversations = result.closed_conversations or 0
        
        success_rate = (successful_conversations / closed_conversations * 100) if closed_conversations > 0 else 0
        engagement_rate = (result.user_engagement_rate or 0) * 100
        
        response_data = {
            "performance_metrics": {
                "total_conversations": total_conversations,
                "active_conversations": result.active_conversations or 0,
                "closed_conversations": closed_conversations,
                "successful_conversations": successful_conversations,
                "success_rate_percent": round(success_rate, 2),
                "avg_messages_per_conversation": round(result.avg_messages_per_conversation or 0, 2),
                "avg_response_time_seconds": round(result.avg_response_time_seconds or 0, 2),
                "avg_response_time_minutes": round((result.avg_response_time_seconds or 0) / 60, 2),
                "avg_satisfaction_score": round(result.avg_satisfaction_score or 0, 2),
                "user_engagement_rate_percent": round(engagement_rate, 2),
                "agent_engagement_rate_percent": round((result.agent_engagement_rate or 0) * 100, 2)
            },
            "generated_at": datetime.utcnow().isoformat(),
            "cache_ttl": 300  # 5 minutos
        }
        
        # Cache por 5 minutos
        await cache_service.set(cache_key, response_data, ttl=300)
        
        logger.info("Analytics performance calculated", 
                   total_conversations=total_conversations,
                   success_rate=success_rate,
                   avg_response_time=result.avg_response_time_seconds)
        
        return response_data
        
    except Exception as e:
        logger.error("Error calculating performance metrics", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error calculating performance metrics: {str(e)}")


@router.get("/timeseries")
async def get_timeseries_data(
    metric: str = Query("conversations", description="Métrica: conversations, messages, revenue, satisfaction"),
    granularity: str = Query("day", description="Granularidade: hour, day, week, month"),
    start_date: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    📈 Dados Temporais
    
    Retorna dados temporais por métrica com granularidade configurável.
    """
    cache_key = f"analytics:timeseries:{metric}:{granularity}:{start_date}:{end_date}"
    
    # Verificar cache primeiro
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        logger.info("Analytics timeseries served from cache", cache_key=cache_key)
        return cached_result
    
    try:
        # Validar parâmetros
        valid_metrics = ["conversations", "messages", "revenue", "satisfaction"]
        valid_granularities = ["hour", "day", "week", "month"]
        
        if metric not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Invalid metric. Must be one of: {valid_metrics}")
        
        if granularity not in valid_granularities:
            raise HTTPException(status_code=400, detail=f"Invalid granularity. Must be one of: {valid_granularities}")
        
        # Definir formato de data baseado na granularidade
        date_formats = {
            "hour": "%Y-%m-%d %H:00:00",
            "day": "%Y-%m-%d",
            "week": "%Y-%m-%d",
            "month": "%Y-%m-01"
        }
        
        date_format = date_formats[granularity]
        
        # Construir filtros de data
        date_filters = []
        if start_date:
            date_filters.append(text("c.created_at >= :start_date"))
        if end_date:
            date_filters.append(text("c.created_at <= :end_date"))
        
        date_where = " AND ".join(date_filters) if date_filters else "1=1"
        
        # Query baseada na métrica
        if metric == "conversations":
            timeseries_query = text(f"""
                SELECT 
                    TO_CHAR(c.created_at, '{date_format}') as period,
                    COUNT(*) as value,
                    COUNT(CASE WHEN c.status = 'closed' AND c.outcome = 'success' THEN 1 END) as successful,
                    COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active
                FROM conversations c
                WHERE {date_where}
                GROUP BY TO_CHAR(c.created_at, '{date_format}')
                ORDER BY period
            """)
        elif metric == "messages":
            timeseries_query = text(f"""
                SELECT 
                    TO_CHAR(m.created_at, '{date_format}') as period,
                    COUNT(*) as value,
                    COUNT(CASE WHEN m.sender = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN m.sender = 'agent' THEN 1 END) as agent_messages
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE {date_where}
                GROUP BY TO_CHAR(m.created_at, '{date_format}')
                ORDER BY period
            """)
        else:
            # Para revenue e satisfaction, usar conversas como base
            timeseries_query = text(f"""
                SELECT 
                    TO_CHAR(c.created_at, '{date_format}') as period,
                    COUNT(*) as value,
                    COUNT(CASE WHEN c.outcome = 'success' THEN 1 END) as successful_deals
                FROM conversations c
                WHERE {date_where}
                GROUP BY TO_CHAR(c.created_at, '{date_format}')
                ORDER BY period
            """)
        
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        result = db.execute(timeseries_query, params).fetchall()
        
        # Processar dados
        timeseries_data = []
        for row in result:
            data_point = {
                "period": row.period,
                "value": float(row.value) if row.value is not None else 0
            }
            
            # Adicionar métricas adicionais baseadas no tipo
            if metric == "conversations":
                data_point.update({
                    "successful": row.successful or 0,
                    "active": row.active or 0
                })
            elif metric == "messages":
                data_point.update({
                    "user_messages": row.user_messages or 0,
                    "agent_messages": row.agent_messages or 0
                })
            elif metric in ["revenue", "satisfaction"]:
                data_point.update({
                    "successful_deals": row.successful_deals or 0
                })
            
            timeseries_data.append(data_point)
        
        response_data = {
            "metric": metric,
            "granularity": granularity,
            "data": timeseries_data,
            "summary": {
                "total_points": len(timeseries_data),
                "total_value": sum(point["value"] for point in timeseries_data),
                "avg_value": sum(point["value"] for point in timeseries_data) / len(timeseries_data) if timeseries_data else 0
            },
            "generated_at": datetime.utcnow().isoformat(),
            "cache_ttl": 300  # 5 minutos
        }
        
        # Cache por 5 minutos
        await cache_service.set(cache_key, response_data, ttl=300)
        
        logger.info("Analytics timeseries calculated", 
                   metric=metric,
                   granularity=granularity,
                   data_points=len(timeseries_data))
        
        return response_data
        
    except Exception as e:
        logger.error("Error calculating timeseries data", error=str(e), error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"Error calculating timeseries data: {str(e)}")


@router.get("/health")
async def analytics_health():
    """
    🏥 Health Check dos Analytics
    
    Verifica se os endpoints de analytics estão funcionando.
    """
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "1.0.0",
        "endpoints": [
            "/api/analytics/funnel",
            "/api/analytics/performance", 
            "/api/analytics/timeseries"
        ],
        "cache_enabled": True,
        "timestamp": datetime.utcnow().isoformat()
    }