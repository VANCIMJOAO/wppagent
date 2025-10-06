"""
Analytics Revenue Routes - Endpoints para dados de receita
Implementação REAL com dados do PostgreSQL
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, text
from typing import Literal
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.database import Appointment
from app.auth.middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics-revenue"])

@router.get("/revenue")
async def get_revenue_data(
    period: Literal['daily', 'monthly', 'yearly'] = Query(...),
    days: int = Query(default=7, ge=1, le=365),
    months: int = Query(default=6, ge=1, le=24),
    years: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Retorna dados de receita por período
    
    Parâmetros:
    - period: 'daily', 'monthly', ou 'yearly'
    - days: número de dias (para daily)
    - months: número de meses (para monthly)
    - years: número de anos (para yearly)
    """
    try:
        logger.info(f"💰 Buscando receita - período: {period}")
        
        if period == 'daily':
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Receita Diária (últimos N dias)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            start_date = datetime.now() - timedelta(days=days)
            
            # Query SQL direta para evitar problemas de GROUP BY
            sql_query = text("""
                SELECT 
                    DATE_TRUNC('day', created_at)::date as date,
                    COALESCE(SUM(price), 0) as value
                FROM appointments 
                WHERE created_at >= :start_date
                GROUP BY DATE_TRUNC('day', created_at)
                ORDER BY DATE_TRUNC('day', created_at)
            """)
            
            result = await db.execute(sql_query, {"start_date": start_date})
            
            data = [
                {
                    'date': row.date.strftime('%Y-%m-%d'),
                    'value': float(row.value)
                }
                for row in result
            ]
            
        elif period == 'monthly':
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Receita Mensal (últimos N meses)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            start_date = datetime.now() - timedelta(days=months * 30)
            
            # Query SQL direta para evitar problemas de GROUP BY
            sql_query = text("""
                SELECT 
                    DATE_TRUNC('month', created_at) as month,
                    COALESCE(SUM(price), 0) as value
                FROM appointments 
                WHERE created_at >= :start_date
                GROUP BY DATE_TRUNC('month', created_at)
                ORDER BY DATE_TRUNC('month', created_at)
            """)
            
            result = await db.execute(sql_query, {"start_date": start_date})
            
            month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                           'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            
            data = [
                {
                    'month': month_names[row.month.month - 1],
                    'value': float(row.value)
                }
                for row in result
            ]
            
        else:  # yearly
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # Receita Anual (últimos N anos)
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            result = await db.execute(
                select(
                    extract('year', Appointment.created_at).label('year'),
                    func.coalesce(func.sum(Appointment.price), 0).label('value')
                )
                .group_by(extract('year', Appointment.created_at))
                .order_by(extract('year', Appointment.created_at).desc())
                .limit(years)
            )
            
            data = [
                {
                    'year': str(int(row.year)),
                    'value': float(row.value)
                }
                for row in result
            ]
        
        logger.info(f"✅ Receita {period} carregada: {len(data)} pontos")
        
        return {
            "success": True,
            "data": data,
            "period": period,
            "total": sum(item['value'] for item in data)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar receita {period}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar dados de receita: {str(e)}"
        )

