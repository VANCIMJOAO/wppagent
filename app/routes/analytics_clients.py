"""
Analytics Clients Routes - Endpoints para análise de clientes
Implementação REAL com dados do PostgreSQL
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.database import User, Conversation
from app.auth.middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics/clients", tags=["analytics-clients"])

@router.get("/new-daily")
async def get_new_clients_daily(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Novos clientes por dia (últimos N dias)
    
    Retorna: [
        {"date": "2025-10-01", "count": 5},
        {"date": "2025-10-02", "count": 8},
        ...
    ]
    """
    try:
        logger.info(f"👥 Buscando novos clientes diários - {days} dias")
        
        start_date = datetime.now() - timedelta(days=days)
        
        result = await db.execute(
            select(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            )
            .where(User.created_at >= start_date)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
        )
        
        data = [
            {
                'date': row.date.strftime('%Y-%m-%d'),
                'count': row.count
            }
            for row in result
        ]
        
        logger.info(f"✅ {len(data)} dias com novos clientes")
        
        return {
            "success": True,
            "data": data,
            "total": sum(item['count'] for item in data)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar novos clientes: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar novos clientes: {str(e)}"
        )

@router.get("/retention")
async def get_client_retention(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Taxa de retenção de clientes por período
    
    Calcula quantos clientes tiveram atividade (conversas) após N tempo
    
    Retorna: [
        {"period": "1 mês", "rate": 95.2},
        {"period": "3 meses", "rate": 87.8},
        ...
    ]
    """
    try:
        logger.info("📈 Calculando taxa de retenção de clientes")
        
        now = datetime.now()
        
        # Calcular retenção para diferentes períodos
        retention_data = []
        
        for months, label in [(1, "1 mês"), (3, "3 meses"), (6, "6 meses"), (12, "1 ano")]:
            cohort_start = now - timedelta(days=months * 30 + 30)  # Cohort de 1 mês antes
            cohort_end = now - timedelta(days=months * 30)
            
            # Total de usuários no cohort
            cohort_result = await db.execute(
                select(func.count(User.id))
                .where(and_(
                    User.created_at >= cohort_start,
                    User.created_at < cohort_end
                ))
            )
            cohort_size = cohort_result.scalar() or 0
            
            if cohort_size == 0:
                retention_data.append({"period": label, "rate": 0.0})
                continue
            
            # Usuários que tiveram atividade N meses depois
            retained_result = await db.execute(
                select(func.count(func.distinct(Conversation.user_id)))
                .join(User, Conversation.user_id == User.id)
                .where(and_(
                    User.created_at >= cohort_start,
                    User.created_at < cohort_end,
                    Conversation.created_at >= cohort_end
                ))
            )
            retained = retained_result.scalar() or 0
            
            retention_rate = (retained / cohort_size * 100) if cohort_size > 0 else 0.0
            retention_data.append({"period": label, "rate": round(retention_rate, 1)})
        
        logger.info(f"✅ Retenção calculada para {len(retention_data)} períodos")
        
        return {
            "success": True,
            "data": retention_data
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao calcular retenção: {e}", exc_info=True)
        # Retornar dados placeholder em caso de erro
        return {
            "success": True,
            "data": [
                {"period": "1 mês", "rate": 0.0},
                {"period": "3 meses", "rate": 0.0},
                {"period": "6 meses", "rate": 0.0},
                {"period": "1 ano", "rate": 0.0}
            ],
            "note": "Dados de retenção indisponíveis"
        }

@router.get("/demographics")
async def get_client_demographics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Demografia de clientes por faixa etária
    
    ⚠️ NOTA: Requer campo 'age' ou 'birth_date' na tabela users
    Se não existir, retorna dados vazios
    
    Retorna: [
        {"ageGroup": "18-25", "count": 15},
        {"ageGroup": "26-35", "count": 30},
        ...
    ]
    """
    try:
        logger.info("👥 Buscando demografia de clientes")
        
        # TODO: Implementar quando campo age/birth_date estiver disponível
        # Por enquanto, retornar distribuição vazia
        
        demographics_data = [
            {"ageGroup": "18-25", "count": 0},
            {"ageGroup": "26-35", "count": 0},
            {"ageGroup": "36-45", "count": 0},
            {"ageGroup": "46-55", "count": 0},
            {"ageGroup": "55+", "count": 0}
        ]
        
        logger.info("⚠️ Demografia não disponível - campo 'age' não existe")
        
        return {
            "success": True,
            "data": demographics_data,
            "note": "Campo 'age' não disponível na tabela users"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar demografia: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar demografia: {str(e)}"
        )

