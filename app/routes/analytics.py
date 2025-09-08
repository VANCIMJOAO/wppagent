from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

from ..database import get_db
from ..auth.middleware import require_admin

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/business-overview")
async def get_business_overview(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin)
):
    """Overview executivo do negócio"""
    
    # Definir período padrão (últimos 30 dias)
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = datetime.now().isoformat()
    
    # Query principal com métricas agregadas
    overview_query = await session.execute(text("""
        WITH period_data AS (
            SELECT 
                -- Clientes
                COUNT(DISTINCT u.id) as total_clients,
                COUNT(DISTINCT CASE 
                    WHEN u.created_at >= :start_date THEN u.id 
                END) as new_clients,
                
                -- Conversas
                COUNT(DISTINCT c.id) as total_conversations,
                COUNT(DISTINCT CASE 
                    WHEN c.status = 'active' THEN c.id 
                END) as active_conversations,
                
                -- Mensagens
                COUNT(DISTINCT m.id) as total_messages,
                COUNT(DISTINCT CASE 
                    WHEN m.direction = 'in' THEN m.id 
                END) as messages_received,
                COUNT(DISTINCT CASE 
                    WHEN m.direction = 'out' THEN m.id 
                END) as messages_sent,
                
                -- Agendamentos
                COUNT(DISTINCT a.id) as total_appointments,
                COUNT(DISTINCT CASE 
                    WHEN a.status = 'confirmado' THEN a.id 
                END) as confirmed_appointments,
                COUNT(DISTINCT CASE 
                    WHEN a.status = 'realizado' THEN a.id 
                END) as completed_appointments,
                
                -- Revenue (se disponível)
                COALESCE(SUM(CASE 
                    WHEN a.status = 'realizado' THEN a.price 
                END), 0) as total_revenue,
                
                -- Tempo médio resposta (segundos)
                AVG(CASE 
                    WHEN m.direction = 'out' THEN 
                        EXTRACT(EPOCH FROM m.created_at - 
                            LAG(m.created_at) OVER (
                                PARTITION BY m.user_id 
                                ORDER BY m.created_at
                            )
                        )
                END) as avg_response_time_seconds
                
            FROM users u
            LEFT JOIN conversations c ON u.id = c.user_id
            LEFT JOIN messages m ON u.id = m.user_id
            LEFT JOIN appointments a ON u.id = a.user_id
            WHERE 
                u.created_at >= :start_date 
                AND u.created_at <= :end_date
        ),
        previous_period AS (
            -- Mesmo período anterior para comparação
            SELECT 
                COUNT(DISTINCT u.id) as prev_total_clients,
                COUNT(DISTINCT c.id) as prev_total_conversations,
                COUNT(DISTINCT m.id) as prev_total_messages,
                COUNT(DISTINCT a.id) as prev_total_appointments,
                COALESCE(SUM(CASE 
                    WHEN a.status = 'realizado' THEN a.price 
                END), 0) as prev_total_revenue
            FROM users u
            LEFT JOIN conversations c ON u.id = c.user_id
            LEFT JOIN messages m ON u.id = m.user_id
            LEFT JOIN appointments a ON u.id = a.user_id
            WHERE 
                u.created_at >= :prev_start_date 
                AND u.created_at <= :prev_end_date
        )
        SELECT 
            p.*,
            pp.prev_total_clients,
            pp.prev_total_conversations,
            pp.prev_total_messages,
            pp.prev_total_appointments,
            pp.prev_total_revenue,
            
            -- Cálculo de growth rates
            CASE 
                WHEN pp.prev_total_clients > 0 THEN
                    ((p.total_clients - pp.prev_total_clients) * 100.0 / pp.prev_total_clients)
                ELSE 0 
            END as clients_growth_rate,
            
            CASE 
                WHEN pp.prev_total_revenue > 0 THEN
                    ((p.total_revenue - pp.prev_total_revenue) * 100.0 / pp.prev_total_revenue)
                ELSE 0 
            END as revenue_growth_rate
            
        FROM period_data p, previous_period pp
    """), {
        "start_date": start_date,
        "end_date": end_date,
        "prev_start_date": (datetime.fromisoformat(start_date) - timedelta(days=30)).isoformat(),
        "prev_end_date": (datetime.fromisoformat(end_date) - timedelta(days=30)).isoformat()
    })
    
    result = overview_query.fetchone()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "metrics": {
            "clients": {
                "total": result.total_clients or 0,
                "new": result.new_clients or 0,
                "growth_rate": round(result.clients_growth_rate or 0, 2)
            },
            "conversations": {
                "total": result.total_conversations or 0,
                "active": result.active_conversations or 0,
                "completion_rate": round(
                    (result.active_conversations / max(result.total_conversations, 1)) * 100, 2
                )
            },
            "messages": {
                "total": result.total_messages or 0,
                "received": result.messages_received or 0,
                "sent": result.messages_sent or 0,
                "response_rate": round(
                    (result.messages_sent / max(result.messages_received, 1)) * 100, 2
                ),
                "avg_response_time_seconds": round(result.avg_response_time_seconds or 0, 2)
            },
            "appointments": {
                "total": result.total_appointments or 0,
                "confirmed": result.confirmed_appointments or 0,
                "completed": result.completed_appointments or 0,
                "conversion_rate": round(
                    (result.confirmed_appointments / max(result.total_appointments, 1)) * 100, 2
                ),
                "completion_rate": round(
                    (result.completed_appointments / max(result.confirmed_appointments, 1)) * 100, 2
                )
            },
            "revenue": {
                "total": float(result.total_revenue or 0),
                "growth_rate": round(result.revenue_growth_rate or 0, 2),
                "avg_per_appointment": round(
                    float(result.total_revenue or 0) / max(result.completed_appointments, 1), 2
                )
            }
        }
    }

@router.get("/conversation-funnel")
async def get_conversation_funnel(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin)
):
    """Funil de conversão das conversas"""
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = datetime.now().isoformat()
    
    funnel_query = await session.execute(text("""
        WITH conversation_stages AS (
            SELECT 
                u.id as user_id,
                u.created_at,
                
                -- Stage 1: First Contact
                CASE WHEN EXISTS(
                    SELECT 1 FROM messages m 
                    WHERE m.user_id = u.id AND m.direction = 'in'
                ) THEN 1 ELSE 0 END as had_first_contact,
                
                -- Stage 2: Bot Response  
                CASE WHEN EXISTS(
                    SELECT 1 FROM messages m 
                    WHERE m.user_id = u.id AND m.direction = 'out'
                ) THEN 1 ELSE 0 END as received_response,
                
                -- Stage 3: Continued Conversation
                CASE WHEN (
                    SELECT COUNT(*) FROM messages m 
                    WHERE m.user_id = u.id
                ) >= 3 THEN 1 ELSE 0 END as had_conversation,
                
                -- Stage 4: Appointment Intent
                CASE WHEN EXISTS(
                    SELECT 1 FROM appointments a 
                    WHERE a.user_id = u.id
                ) THEN 1 ELSE 0 END as showed_appointment_intent,
                
                -- Stage 5: Confirmed Appointment
                CASE WHEN EXISTS(
                    SELECT 1 FROM appointments a 
                    WHERE a.user_id = u.id AND a.status IN ('confirmado', 'realizado')
                ) THEN 1 ELSE 0 END as confirmed_appointment,
                
                -- Stage 6: Completed Service
                CASE WHEN EXISTS(
                    SELECT 1 FROM appointments a 
                    WHERE a.user_id = u.id AND a.status = 'realizado'
                ) THEN 1 ELSE 0 END as completed_service
                
            FROM users u
            WHERE u.created_at >= :start_date AND u.created_at <= :end_date
        )
        SELECT 
            COUNT(*) as total_leads,
            SUM(had_first_contact) as first_contact,
            SUM(received_response) as received_response,
            SUM(had_conversation) as had_conversation,
            SUM(showed_appointment_intent) as appointment_intent,
            SUM(confirmed_appointment) as confirmed_appointment,
            SUM(completed_service) as completed_service,
            
            -- Conversion rates
            ROUND(SUM(received_response) * 100.0 / GREATEST(SUM(had_first_contact), 1), 2) as response_rate,
            ROUND(SUM(had_conversation) * 100.0 / GREATEST(SUM(received_response), 1), 2) as conversation_rate,
            ROUND(SUM(appointment_intent) * 100.0 / GREATEST(SUM(had_conversation), 1), 2) as intent_rate,
            ROUND(SUM(confirmed_appointment) * 100.0 / GREATEST(SUM(appointment_intent), 1), 2) as confirmation_rate,
            ROUND(SUM(completed_service) * 100.0 / GREATEST(SUM(confirmed_appointment), 1), 2) as completion_rate,
            
            -- Overall conversion
            ROUND(SUM(completed_service) * 100.0 / GREATEST(COUNT(*), 1), 2) as overall_conversion_rate
            
        FROM conversation_stages
    """), {
        "start_date": start_date,
        "end_date": end_date
    })
    
    result = funnel_query.fetchone()
    
    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "funnel_stages": [
            {
                "stage": "Total Leads",
                "count": result.total_leads or 0,
                "percentage": 100.0,
                "conversion_rate": None
            },
            {
                "stage": "First Contact",
                "count": result.first_contact or 0,
                "percentage": round((result.first_contact or 0) / max(result.total_leads, 1) * 100, 2),
                "conversion_rate": None
            },
            {
                "stage": "Received Response",
                "count": result.received_response or 0,
                "percentage": round((result.received_response or 0) / max(result.total_leads, 1) * 100, 2),
                "conversion_rate": result.response_rate or 0
            },
            {
                "stage": "Had Conversation",
                "count": result.had_conversation or 0,
                "percentage": round((result.had_conversation or 0) / max(result.total_leads, 1) * 100, 2),
                "conversion_rate": result.conversation_rate or 0
            },
            {
                "stage": "Appointment Intent",
                "count": result.appointment_intent or 0,
                "percentage": round((result.appointment_intent or 0) / max(result.total_leads, 1) * 100, 2),
                "conversion_rate": result.intent_rate or 0
            },
            {
                "stage": "Confirmed Appointment",
                "count": result.confirmed_appointment or 0,
                "percentage": round((result.confirmed_appointment or 0) / max(result.total_leads, 1) * 100, 2),
                "conversion_rate": result.confirmation_rate or 0
            },
            {
                "stage": "Completed Service",
                "count": result.completed_service or 0,
                "percentage": round((result.completed_service or 0) / max(result.total_leads, 1) * 100, 2),
                "conversion_rate": result.completion_rate or 0
            }
        ],
        "overall_conversion_rate": result.overall_conversion_rate or 0
    }

@router.get("/time-series")
async def get_time_series_data(
    metric: str = Query(..., description="Métrica: messages, conversations, appointments, revenue"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    granularity: str = Query("day", description="Granularidade: hour, day, week, month"),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin)
):
    """Dados de série temporal para gráficos"""
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = datetime.now().isoformat()
    
    # Definir format de agrupamento baseado na granularidade
    date_format_map = {
        "hour": "YYYY-MM-DD HH24:00:00",
        "day": "YYYY-MM-DD",
        "week": "YYYY-\"W\"WW",
        "month": "YYYY-MM"
    }
    
    date_format = date_format_map.get(granularity, "YYYY-MM-DD")
    
    # Query baseada na métrica solicitada
    if metric == "messages":
        query = text("""
            SELECT 
                TO_CHAR(m.created_at, :date_format) as period,
                COUNT(*) as total,
                COUNT(CASE WHEN m.direction = 'in' THEN 1 END) as received,
                COUNT(CASE WHEN m.direction = 'out' THEN 1 END) as sent
            FROM messages m
            WHERE m.created_at >= :start_date AND m.created_at <= :end_date
            GROUP BY TO_CHAR(m.created_at, :date_format)
            ORDER BY period
        """)
    elif metric == "conversations":
        query = text("""
            SELECT 
                TO_CHAR(c.created_at, :date_format) as period,
                COUNT(*) as total,
                COUNT(CASE WHEN c.status = 'active' THEN 1 END) as active,
                COUNT(CASE WHEN c.status = 'closed' THEN 1 END) as closed
            FROM conversations c
            WHERE c.created_at >= :start_date AND c.created_at <= :end_date
            GROUP BY TO_CHAR(c.created_at, :date_format)
            ORDER BY period
        """)
    elif metric == "appointments":
        query = text("""
            SELECT 
                TO_CHAR(a.created_at, :date_format) as period,
                COUNT(*) as total,
                COUNT(CASE WHEN a.status = 'confirmado' THEN 1 END) as confirmed,
                COUNT(CASE WHEN a.status = 'realizado' THEN 1 END) as completed,
                COUNT(CASE WHEN a.status = 'cancelado' THEN 1 END) as cancelled
            FROM appointments a
            WHERE a.created_at >= :start_date AND a.created_at <= :end_date
            GROUP BY TO_CHAR(a.created_at, :date_format)
            ORDER BY period
        """)
    elif metric == "revenue":
        query = text("""
            SELECT 
                TO_CHAR(a.created_at, :date_format) as period,
                COALESCE(SUM(CASE WHEN a.status = 'realizado' THEN a.price END), 0) as total,
                COUNT(CASE WHEN a.status = 'realizado' THEN 1 END) as completed_appointments,
                COALESCE(AVG(CASE WHEN a.status = 'realizado' THEN a.price END), 0) as avg_ticket
            FROM appointments a
            WHERE a.created_at >= :start_date AND a.created_at <= :end_date
            GROUP BY TO_CHAR(a.created_at, :date_format)
            ORDER BY period
        """)
    else:
        raise HTTPException(400, f"Métrica '{metric}' não suportada")
    
    result = await session.execute(query, {
        "date_format": date_format,
        "start_date": start_date,
        "end_date": end_date
    })
    
    data_points = []
    for row in result.fetchall():
        point = {"period": row.period, "total": row.total}
        
        # Adicionar campos específicos baseados na métrica
        for key, value in row._mapping.items():
            if key != "period":
                point[key] = value or 0
                
        data_points.append(point)
    
    return {
        "metric": metric,
        "granularity": granularity,
        "period": {"start_date": start_date, "end_date": end_date},
        "data_points": data_points
    }

@router.get("/performance-metrics")
async def get_performance_metrics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin)
):
    """Métricas de performance operacional"""
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
    if not end_date:
        end_date = datetime.now().isoformat()
    
    performance_query = await session.execute(text("""
        WITH response_times AS (
            SELECT 
                m.user_id,
                m.created_at,
                m.direction,
                LAG(m.created_at) OVER (
                    PARTITION BY m.user_id 
                    ORDER BY m.created_at
                ) as prev_message_time,
                LAG(m.direction) OVER (
                    PARTITION BY m.user_id 
                    ORDER BY m.created_at
                ) as prev_direction
            FROM messages m
            WHERE m.created_at >= :start_date AND m.created_at <= :end_date
        ),
        bot_response_times AS (
            SELECT 
                EXTRACT(EPOCH FROM (created_at - prev_message_time)) as response_time_seconds
            FROM response_times
            WHERE 
                direction = 'out' 
                AND prev_direction = 'in'
                AND prev_message_time IS NOT NULL
                AND EXTRACT(EPOCH FROM (created_at - prev_message_time)) < 3600 -- Max 1 hour
        ),
        conversation_metrics AS (
            SELECT 
                c.id,
                c.status,
                COUNT(m.id) as message_count,
                MAX(m.created_at) - MIN(m.created_at) as conversation_duration,
                COUNT(DISTINCT DATE(m.created_at)) as active_days
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.created_at >= :start_date AND c.created_at <= :end_date
            GROUP BY c.id, c.status
        )
        SELECT 
            -- Response time metrics
            COUNT(brt.response_time_seconds) as total_bot_responses,
            AVG(brt.response_time_seconds) as avg_response_time,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY brt.response_time_seconds) as median_response_time,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY brt.response_time_seconds) as p95_response_time,
            COUNT(CASE WHEN brt.response_time_seconds <= 5 THEN 1 END) as responses_under_5s,
            COUNT(CASE WHEN brt.response_time_seconds <= 10 THEN 1 END) as responses_under_10s,
            
            -- Conversation metrics
            COUNT(cm.id) as total_conversations,
            AVG(cm.message_count) as avg_messages_per_conversation,
            AVG(EXTRACT(EPOCH FROM cm.conversation_duration) / 3600) as avg_conversation_hours,
            COUNT(CASE WHEN cm.status = 'active' THEN 1 END) as active_conversations,
            COUNT(CASE WHEN cm.status = 'closed' THEN 1 END) as closed_conversations,
            
            -- Engagement metrics
            AVG(cm.active_days) as avg_engagement_days,
            COUNT(CASE WHEN cm.message_count >= 5 THEN 1 END) as engaged_conversations,
            COUNT(CASE WHEN cm.message_count >= 10 THEN 1 END) as highly_engaged_conversations
            
        FROM bot_response_times brt
        CROSS JOIN conversation_metrics cm
    """), {
        "start_date": start_date,
        "end_date": end_date
    })
    
    result = performance_query.fetchone()
    
    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "response_time": {
            "total_responses": result.total_bot_responses or 0,
            "avg_seconds": round(result.avg_response_time or 0, 2),
            "median_seconds": round(result.median_response_time or 0, 2),
            "p95_seconds": round(result.p95_response_time or 0, 2),
            "under_5s_rate": round(
                (result.responses_under_5s or 0) / max(result.total_bot_responses, 1) * 100, 2
            ),
            "under_10s_rate": round(
                (result.responses_under_10s or 0) / max(result.total_bot_responses, 1) * 100, 2
            )
        },
        "conversation_quality": {
            "total_conversations": result.total_conversations or 0,
            "avg_messages_per_conversation": round(result.avg_messages_per_conversation or 0, 2),
            "avg_duration_hours": round(result.avg_conversation_hours or 0, 2),
            "completion_rate": round(
                (result.closed_conversations or 0) / max(result.total_conversations, 1) * 100, 2
            ),
            "engagement_rate": round(
                (result.engaged_conversations or 0) / max(result.total_conversations, 1) * 100, 2
            ),
            "high_engagement_rate": round(
                (result.highly_engaged_conversations or 0) / max(result.total_conversations, 1) * 100, 2
            )
        }
    }

@router.get("/export")
async def export_analytics_data(
    report_type: str = Query(..., description="Tipo: overview, funnel, performance, time-series"),
    format: str = Query("json", description="Formato: json, csv, xlsx"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin)
):
    """Exportar dados de analytics em diferentes formatos"""
    
    # Buscar dados baseado no tipo de relatório
    if report_type == "overview":
        data = await get_business_overview(start_date, end_date, session, current_admin)
    elif report_type == "funnel":
        data = await get_conversation_funnel(start_date, end_date, session, current_admin)
    elif report_type == "performance":
        data = await get_performance_metrics(start_date, end_date, session, current_admin)
    else:
        raise HTTPException(400, f"Tipo de relatório '{report_type}' não suportado")
    
    if format == "json":
        return data
    elif format == "csv":
        # Converter para CSV usando pandas
        try:
            import pandas as pd
            import io
            
            # Flatten data structure for CSV
            flattened_data = flatten_dict(data)
            df = pd.DataFrame([flattened_data])
            
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            return Response(
                content=csv_buffer.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={report_type}_analytics.csv"}
            )
        except ImportError:
            return {"error": "Pandas não disponível para exportação CSV"}
    elif format == "xlsx":
        # Converter para Excel usando pandas
        try:
            import pandas as pd
            import io
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # Criar múltiplas sheets se necessário
                if report_type == "overview":
                    metrics_df = pd.DataFrame([flatten_dict(data['metrics'])])
                    metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
                elif report_type == "funnel":
                    funnel_df = pd.DataFrame(data['funnel_stages'])
                    funnel_df.to_excel(writer, sheet_name='Funnel', index=False)
            
            return Response(
                content=excel_buffer.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={report_type}_analytics.xlsx"}
            )
        except ImportError:
            return {"error": "Pandas/openpyxl não disponível para exportação Excel"}
    else:
        raise HTTPException(400, f"Formato '{format}' não suportado")

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Achatar dicionário aninhado para CSV/Excel"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
