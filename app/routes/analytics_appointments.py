"""
Analytics Appointments Routes - Endpoints para análise de agendamentos
Implementação REAL com dados do PostgreSQL
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, case
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.database import Appointment, Service
from app.auth.middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics/appointments", tags=["analytics-appointments"])

@router.get("/by-status")
async def get_appointments_by_status(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Agendamentos agrupados por status (últimos N dias)
    
    Retorna: [
        {"status": "agendado", "count": 10},
        {"status": "confirmado", "count": 5},
        ...
    ]
    """
    try:
        logger.info(f"📊 Buscando agendamentos por status - {days} dias")
        
        start_date = datetime.now() - timedelta(days=days)
        
        result = await db.execute(
            select(
                Appointment.status,
                func.count(Appointment.id).label('count')
            )
            .where(Appointment.created_at >= start_date)
            .group_by(Appointment.status)
            .order_by(func.count(Appointment.id).desc())
        )
        
        # Mapear nomes de status para português
        status_map = {
            'agendado': 'Agendado',
            'confirmado': 'Confirmado',
            'realizado': 'Realizado',
            'cancelado': 'Cancelado',
            'pendente': 'Pendente'
        }
        
        data = [
            {
                'status': status_map.get(row.status, row.status.capitalize()),
                'count': row.count
            }
            for row in result
        ]
        
        logger.info(f"✅ {len(data)} status encontrados")
        
        return {
            "success": True,
            "data": data,
            "total": sum(item['count'] for item in data)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar agendamentos por status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar agendamentos por status: {str(e)}"
        )

@router.get("/by-service")
async def get_appointments_by_service(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Agendamentos agrupados por serviço (últimos N dias)
    
    Retorna: [
        {"service": "Consulta", "count": 15},
        {"service": "Atendimento", "count": 8},
        ...
    ]
    """
    try:
        logger.info(f"📊 Buscando agendamentos por serviço - {days} dias")
        
        start_date = datetime.now() - timedelta(days=days)
        
        result = await db.execute(
            select(
                Service.name.label('service'),
                func.count(Appointment.id).label('count')
            )
            .join(Service, Appointment.service_id == Service.id)
            .where(Appointment.created_at >= start_date)
            .group_by(Service.name)
            .order_by(func.count(Appointment.id).desc())
        )
        
        data = [
            {
                'service': row.service,
                'count': row.count
            }
            for row in result
        ]
        
        logger.info(f"✅ {len(data)} serviços encontrados")
        
        return {
            "success": True,
            "data": data,
            "total": sum(item['count'] for item in data)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar agendamentos por serviço: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar agendamentos por serviço: {str(e)}"
        )

@router.get("/by-timeslot")
async def get_appointments_by_timeslot(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Agendamentos agrupados por faixa horária (últimos N dias)
    
    Retorna: [
        {"time": "08:00-10:00", "count": 5},
        {"time": "10:00-12:00", "count": 12},
        ...
    ]
    """
    try:
        logger.info(f"📊 Buscando agendamentos por horário - {days} dias")
        
        start_date = datetime.now() - timedelta(days=days)
        
        result = await db.execute(
            select(
                case(
                    (extract('hour', Appointment.date_time).between(8, 9), '08:00-10:00'),
                    (extract('hour', Appointment.date_time).between(10, 11), '10:00-12:00'),
                    (extract('hour', Appointment.date_time).between(12, 13), '12:00-14:00'),
                    (extract('hour', Appointment.date_time).between(14, 15), '14:00-16:00'),
                    (extract('hour', Appointment.date_time).between(16, 17), '16:00-18:00'),
                    else_='18:00-20:00'
                ).label('time_slot'),
                func.count(Appointment.id).label('count')
            )
            .where(Appointment.created_at >= start_date)
            .group_by('time_slot')
            .order_by('time_slot')
        )
        
        data = [
            {
                'time': row.time_slot,
                'count': row.count
            }
            for row in result
        ]
        
        logger.info(f"✅ {len(data)} faixas horárias encontradas")
        
        return {
            "success": True,
            "data": data,
            "total": sum(item['count'] for item in data)
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar agendamentos por horário: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao carregar agendamentos por horário: {str(e)}"
        )

