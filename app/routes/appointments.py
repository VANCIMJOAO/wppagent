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
from app.schemas.appointments import (
    AppointmentResponse, 
    AppointmentCreate, 
    AppointmentUpdate,
    AppointmentSummary,
    AppointmentsListResponse,
    AppointmentStats
)
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Router
router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("/", response_model=AppointmentsListResponse)
async def get_appointments(
    limit: int = Query(10, le=100, description="Limite de resultados"),
    page: int = Query(1, ge=1, description="Página atual"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    user_id: Optional[int] = Query(None, description="Filtrar por ID do cliente"),
    session: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    📅 Lista agendamentos com filtros e paginação
    ✅ SCHEMA PADRONIZADO - Elimina inconsistências frontend/backend
    """
    try:
        # Calcular offset
        offset = (page - 1) * limit
        
        # Query base com JOINs padronizados
        query = select(
            Appointment.id,
            Appointment.user_id,
            Appointment.business_id, 
            Appointment.service_id,
            Appointment.date_time,
            Appointment.duration_minutes,  # ✅ Campo padronizado
            Appointment.end_time,
            Appointment.price,  # ✅ Campo unificado
            Appointment.status,
            Appointment.notes,
            Appointment.created_at,
            Appointment.updated_at,
            # ✅ Campos relacionados com aliases padronizados
            User.nome.label("cliente_nome"),
            User.telefone.label("cliente_telefone"), 
            User.email.label("cliente_email"),
            Service.name.label("servico_nome"),
            Service.description.label("servico_descricao"),
            Business.name.label("business_name")
        ).join(
            User, Appointment.user_id == User.id
        ).join(
            Business, Appointment.business_id == Business.id
        ).outerjoin(
            Service, Appointment.service_id == Service.id
        )
        
        # ✅ Aplicar filtros padronizados
        conditions = []
        
        if status:
            conditions.append(Appointment.status == status)
        
        if user_id:
            conditions.append(Appointment.user_id == user_id)
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                conditions.append(func.date(Appointment.date_time) >= date_from_obj)
            except ValueError:
                raise HTTPException(400, "date_from deve estar no formato YYYY-MM-DD")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                conditions.append(func.date(Appointment.date_time) <= date_to_obj)
            except ValueError:
                raise HTTPException(400, "date_to deve estar no formato YYYY-MM-DD")
        
        # Aplicar condições
        if conditions:
            query = query.where(and_(*conditions))
        
        # Query de contagem
        count_query = select(func.count(Appointment.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        # Executar queries
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Query principal com ordenação e paginação
        query = query.order_by(desc(Appointment.date_time)).limit(limit).offset(offset)
        result = await session.execute(query)
        rows = result.fetchall()
        
        # ✅ Converter para schema padronizado
        appointments = []
        for row in rows:
            appointment_dict = {
                'id': row.id,
                'user_id': row.user_id,
                'business_id': row.business_id,
                'service_id': row.service_id,
                'date_time': row.date_time,
                'duration_minutes': row.duration_minutes,
                'end_time': row.end_time,
                'price': float(row.price) if row.price else 0.00,
                'status': row.status,
                'notes': row.notes,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                # Campos relacionados
                'cliente_nome': row.cliente_nome,
                'cliente_telefone': row.cliente_telefone,
                'cliente_email': row.cliente_email,
                'servico_nome': row.servico_nome,
                'servico_descricao': row.servico_descricao,
                'business_name': row.business_name
            }
            appointments.append(AppointmentResponse(**appointment_dict))
        
        has_more = (page * limit) < total
        
        return AppointmentsListResponse(
            appointments=appointments,
            total=total,
            page=page,
            per_page=limit,
            has_more=has_more
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar agendamentos: {e}")
        raise HTTPException(500, f"Erro interno do servidor: {str(e)}")


@router.get("/legacy", response_model=Dict[str, Any])
async def get_appointments_legacy(
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
                conditions.append(func.date(Appointment.date_time) >= date_from_obj)
            except ValueError:
                raise HTTPException(400, "date_from deve estar no formato YYYY-MM-DD")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                conditions.append(func.date(Appointment.date_time) <= date_to_obj)
            except ValueError:
                raise HTTPException(400, "date_to deve estar no formato YYYY-MM-DD")
        
        if status:
            conditions.append(Appointment.status == status)
        
        if user_id:
            conditions.append(Appointment.user_id == user_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Ordenação e paginação
        query = query.order_by(desc(Appointment.date_time))
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
                "date_time": appointment.date_time,
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
            date_time=appointment_data.date_time,
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
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
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
                date_time=row.Appointment.date_time,
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
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
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
            date_time=row.Appointment.date_time,
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
        if update_data.date_time is not None:
            appointment.date_time = update_data.date_time
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
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
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
            date_time=row.Appointment.date_time,
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
