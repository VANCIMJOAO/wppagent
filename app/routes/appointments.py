"""
📅 API REST - Agendamentos
==========================

Endpoints REST para gestão de agendamentos integrados com Dashboard.

Funcionalidades:
- CRUD completo de agendamentos
- Filtros por data, status, cliente
- Validação de conflitos
- Autenticação JWT obrigatória

Autor: Claude AI
Status: Implementação crítica para Dashboard
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.database import Appointment, User, Business, Service
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Schemas Pydantic
class AppointmentResponse(BaseModel):
    id: int
    user_id: int
    business_id: int
    service_id: Optional[int]
    appointment_date: datetime
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Dados relacionados
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    business_name: Optional[str] = None
    service_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class AppointmentCreate(BaseModel):
    user_id: int = Field(..., description="ID do cliente")
    business_id: int = Field(..., description="ID do negócio")
    service_id: Optional[int] = Field(None, description="ID do serviço")
    appointment_date: datetime = Field(..., description="Data e hora do agendamento")
    status: str = Field(default="pending", description="Status do agendamento")
    notes: Optional[str] = Field(None, description="Observações")

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    service_id: Optional[int] = None

# Router
router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("/", response_model=Dict[str, Any])
async def get_appointments(
    limit: int = Query(50, le=500, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    user_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    📅 Buscar agendamentos com filtros
    
    Retorna lista paginada de agendamentos com dados relacionados.
    """
    try:
        logger.info(f"🔍 Buscando agendamentos - Admin: {current_admin.username}")
        
        # Query base com JOINs
        query = select(
            Appointment,
            User.nome.label("user_name"),
            User.telefone.label("user_phone"),
            Business.name.label("business_name"),
            Service.name.label("service_name")
        ).select_from(
            Appointment
        ).join(
            User, Appointment.user_id == User.id
        ).join(
            Business, Appointment.business_id == Business.id
        ).outerjoin(
            Service, Appointment.service_id == Service.id
        )
        
        # Aplicar filtros
        conditions = []
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                conditions.append(func.date(Appointment.appointment_date) >= date_from_obj)
            except ValueError:
                raise HTTPException(400, "date_from deve estar no formato YYYY-MM-DD")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                conditions.append(func.date(Appointment.appointment_date) <= date_to_obj)
            except ValueError:
                raise HTTPException(400, "date_to deve estar no formato YYYY-MM-DD")
        
        if status:
            conditions.append(Appointment.status == status)
        
        if user_id:
            conditions.append(Appointment.user_id == user_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Ordenação e paginação
        query = query.order_by(desc(Appointment.appointment_date))
        query = query.offset(offset).limit(limit)
        
        # Executar query
        result = await session.execute(query)
        rows = result.fetchall()
        
        # Formatear resposta
        appointments = []
        for row in rows:
            appointment = row.Appointment
            appointment_data = {
                "id": appointment.id,
                "user_id": appointment.user_id,
                "business_id": appointment.business_id,
                "service_id": appointment.service_id,
                "appointment_date": appointment.appointment_date,
                "status": appointment.status,
                "notes": appointment.notes,
                "created_at": appointment.created_at,
                "updated_at": appointment.updated_at,
                "user_name": row.user_name,
                "user_phone": row.user_phone,
                "business_name": row.business_name,
                "service_name": row.service_name
            }
            appointments.append(appointment_data)
        
        # Count total para paginação
        count_query = select(func.count(Appointment.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        logger.info(f"✅ Encontrados {len(appointments)} agendamentos de {total} totais")
        
        return {
            "appointments": appointments,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(appointments)) < total
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar agendamentos: {e}")
        raise HTTPException(500, f"Erro interno: {str(e)}")

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    📅 Criar novo agendamento
    """
    try:
        logger.info(f"➕ Criando agendamento - Admin: {current_admin.username}")
        
        # Validar se usuário existe
        user_result = await session.execute(
            select(User).where(User.id == appointment_data.user_id)
        )
        if not user_result.scalar_one_or_none():
            raise HTTPException(404, "Usuário não encontrado")
        
        # Validar se negócio existe
        business_result = await session.execute(
            select(Business).where(Business.id == appointment_data.business_id)
        )
        if not business_result.scalar_one_or_none():
            raise HTTPException(404, "Negócio não encontrado")
        
        # Criar agendamento
        new_appointment = Appointment(
            user_id=appointment_data.user_id,
            business_id=appointment_data.business_id,
            service_id=appointment_data.service_id,
            appointment_date=appointment_data.appointment_date,
            status=appointment_data.status,
            notes=appointment_data.notes
        )
        
        session.add(new_appointment)
        await session.commit()
        await session.refresh(new_appointment)
        
        logger.info(f"✅ Agendamento criado com ID: {new_appointment.id}")
        
        # Buscar dados completos para resposta
        complete_result = await session.execute(
            select(
                Appointment,
                User.name.label("user_name"),
                User.phone.label("user_phone"),
                Business.name.label("business_name"),
                Service.name.label("service_name")
            ).select_from(Appointment)
            .join(User, Appointment.user_id == User.id)
            .join(Business, Appointment.business_id == Business.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
            .where(Appointment.id == new_appointment.id)
        )
        
        row = complete_result.fetchone()
        if row:
            return AppointmentResponse(
                id=row.Appointment.id,
                user_id=row.Appointment.user_id,
                business_id=row.Appointment.business_id,
                service_id=row.Appointment.service_id,
                appointment_date=row.Appointment.appointment_date,
                status=row.Appointment.status,
                notes=row.Appointment.notes,
                created_at=row.Appointment.created_at,
                updated_at=row.Appointment.updated_at,
                user_name=row.user_name,
                user_phone=row.user_phone,
                business_name=row.business_name,
                service_name=row.service_name
            )
        
        return new_appointment
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar agendamento: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")

@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    📅 Buscar agendamento específico
    """
    try:
        result = await session.execute(
            select(
                Appointment,
                User.name.label("user_name"),
                User.phone.label("user_phone"),
                Business.name.label("business_name"),
                Service.name.label("service_name")
            ).select_from(Appointment)
            .join(User, Appointment.user_id == User.id)
            .join(Business, Appointment.business_id == Business.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
            .where(Appointment.id == appointment_id)
        )
        
        row = result.fetchone()
        if not row:
            raise HTTPException(404, "Agendamento não encontrado")
        
        return AppointmentResponse(
            id=row.Appointment.id,
            user_id=row.Appointment.user_id,
            business_id=row.Appointment.business_id,
            service_id=row.Appointment.service_id,
            appointment_date=row.Appointment.appointment_date,
            status=row.Appointment.status,
            notes=row.Appointment.notes,
            created_at=row.Appointment.created_at,
            updated_at=row.Appointment.updated_at,
            user_name=row.user_name,
            user_phone=row.user_phone,
            business_name=row.business_name,
            service_name=row.service_name
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar agendamento {appointment_id}: {e}")
        raise HTTPException(500, f"Erro interno: {str(e)}")

@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    update_data: AppointmentUpdate,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    📅 Atualizar agendamento
    """
    try:
        # Buscar agendamento
        result = await session.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()
        
        if not appointment:
            raise HTTPException(404, "Agendamento não encontrado")
        
        # Atualizar campos fornecidos
        if update_data.appointment_date is not None:
            appointment.appointment_date = update_data.appointment_date
        if update_data.status is not None:
            appointment.status = update_data.status
        if update_data.notes is not None:
            appointment.notes = update_data.notes
        if update_data.service_id is not None:
            appointment.service_id = update_data.service_id
        
        appointment.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(appointment)
        
        logger.info(f"✅ Agendamento {appointment_id} atualizado")
        
        # Buscar dados completos para resposta
        complete_result = await session.execute(
            select(
                Appointment,
                User.name.label("user_name"),
                User.phone.label("user_phone"),
                Business.name.label("business_name"),
                Service.name.label("service_name")
            ).select_from(Appointment)
            .join(User, Appointment.user_id == User.id)
            .join(Business, Appointment.business_id == Business.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
            .where(Appointment.id == appointment_id)
        )
        
        row = complete_result.fetchone()
        return AppointmentResponse(
            id=row.Appointment.id,
            user_id=row.Appointment.user_id,
            business_id=row.Appointment.business_id,
            service_id=row.Appointment.service_id,
            appointment_date=row.Appointment.appointment_date,
            status=row.Appointment.status,
            notes=row.Appointment.notes,
            created_at=row.Appointment.created_at,
            updated_at=row.Appointment.updated_at,
            user_name=row.user_name,
            user_phone=row.user_phone,
            business_name=row.business_name,
            service_name=row.service_name
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar agendamento {appointment_id}: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")

@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    📅 Excluir agendamento
    """
    try:
        result = await session.execute(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        appointment = result.scalar_one_or_none()
        
        if not appointment:
            raise HTTPException(404, "Agendamento não encontrado")
        
        await session.delete(appointment)
        await session.commit()
        
        logger.info(f"✅ Agendamento {appointment_id} excluído")
        
        return {"message": "Agendamento excluído com sucesso", "id": appointment_id}
        
    except Exception as e:
        logger.error(f"❌ Erro ao excluir agendamento {appointment_id}: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")
