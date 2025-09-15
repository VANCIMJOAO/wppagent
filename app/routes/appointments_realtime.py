"""
📋 Enhanced Appointments Routes with Real-time Updates
======================================================

Integração das rotas de appointments com o sistema de 
real-time updates via WebSocket.

Todas as operações CRUD agora disparam eventos WebSocket
para manter o dashboard sincronizado em tempo real.

Status: Resolução completa do problema 4.1 Real-time Updates Parciais
"""

import asyncio
import logging
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.appointment import Appointment
from app.websocket.event_broadcaster import (notify_appointment_created,
                                             notify_appointment_deleted,
                                             notify_appointment_updated,
                                             notify_system_message)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["appointments"])

# Schemas para validação
from pydantic import BaseModel, ConfigDict


class AppointmentCreate(BaseModel):
    nome: str
    telefone: str
    date_time: datetime  # Mantém compatibilidade com modelo do banco
    status: Optional[str] = "agendado"


class AppointmentUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    date_time: Optional[datetime] = None  # Mantém compatibilidade com modelo do banco
    status: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    nome: str
    telefone: str
    date_time: datetime
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    📅 Criar novo agendamento com broadcast em tempo real
    """
    try:
        # Criar appointment no banco
        new_appointment = Appointment(
            nome=appointment_data.nome,
            telefone=appointment_data.telefone,
            date_time=appointment_data.date_time,
            status=appointment_data.status,
        )

        db.add(new_appointment)
        await db.commit()
        await db.refresh(new_appointment)

        # Converter para dict para broadcasting
        appointment_dict = {
            "id": new_appointment.id,
            "nome": new_appointment.nome,
            "telefone": new_appointment.telefone,
            "date_time": new_appointment.date_time.isoformat(),
            "status": new_appointment.status,
            "created_at": new_appointment.created_at.isoformat(),
        }

        # 🚀 REAL-TIME UPDATE: Broadcast criação do agendamento
        background_tasks.add_task(notify_appointment_created, appointment_dict)

        # Log da operação
        logger.info(
            f"Appointment created: ID {new_appointment.id} for {new_appointment.nome}"
        )

        # Broadcast notificação do sistema
        background_tasks.add_task(
            notify_system_message,
            f"Novo agendamento criado para {new_appointment.nome} em {new_appointment.date_time.strftime('%d/%m/%Y às %H:%M')}",
            "success",
        )

        return new_appointment

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating appointment: {str(e)}",
        )


@router.get("/", response_model=List[AppointmentResponse])
async def list_appointments(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    date_filter: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    📋 Listar agendamentos com filtros
    """
    try:
        query = select(Appointment).offset(skip).limit(limit)

        # Aplicar filtros
        if status_filter:
            query = query.where(Appointment.status == status_filter)

        if date_filter:
            query = query.where(func.date(Appointment.date_time) == date_filter)

        # Ordenar por data/hora
        query = query.order_by(Appointment.date_time.desc())

        result = await db.execute(query)
        appointments = result.scalars().all()

        logger.info(f"Listed {len(appointments)} appointments")
        return appointments

    except Exception as e:
        logger.error(f"Error listing appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing appointments: {str(e)}",
        )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    """
    🔍 Obter agendamento específico por ID
    """
    try:
        query = select(Appointment).where(Appointment.id == appointment_id)
        result = await db.execute(query)
        appointment = result.scalar_one_or_none()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment {appointment_id} not found",
            )

        return appointment

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting appointment: {str(e)}",
        )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    ✏️ Atualizar agendamento com broadcast em tempo real
    """
    try:
        # Buscar appointment existente
        query = select(Appointment).where(Appointment.id == appointment_id)
        result = await db.execute(query)
        existing_appointment = result.scalar_one_or_none()

        if not existing_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment {appointment_id} not found",
            )

        # Dados antes da atualização (para comparação)
        old_data = {
            "id": existing_appointment.id,
            "nome": existing_appointment.nome,
            "telefone": existing_appointment.telefone,
            "date_time": existing_appointment.date_time.isoformat(),
            "status": existing_appointment.status,
        }

        # Atualizar campos fornecidos
        update_data = appointment_data.model_dump(exclude_unset=True)
        if update_data:
            await db.execute(
                update(Appointment)
                .where(Appointment.id == appointment_id)
                .values(**update_data)
            )
            await db.commit()

            # Buscar dados atualizados
            await db.refresh(existing_appointment)

        # Converter para dict para broadcasting
        updated_appointment_dict = {
            "id": existing_appointment.id,
            "nome": existing_appointment.nome,
            "telefone": existing_appointment.telefone,
            "date_time": existing_appointment.date_time.isoformat(),
            "status": existing_appointment.status,
            "created_at": existing_appointment.created_at.isoformat(),
            "previous_data": old_data,  # Para mostrar o que mudou
        }

        # 🚀 REAL-TIME UPDATE: Broadcast atualização do agendamento
        background_tasks.add_task(notify_appointment_updated, updated_appointment_dict)

        # Log da operação
        logger.info(f"Appointment updated: ID {appointment_id}")

        # Broadcast notificação do sistema
        background_tasks.add_task(
            notify_system_message,
            f"Agendamento atualizado: {existing_appointment.nome}",
            "info",
        )

        return existing_appointment

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating appointment: {str(e)}",
        )


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    🗑️ Deletar agendamento com broadcast em tempo real
    """
    try:
        # Buscar appointment antes de deletar (para broadcast)
        query = select(Appointment).where(Appointment.id == appointment_id)
        result = await db.execute(query)
        existing_appointment = result.scalar_one_or_none()

        if not existing_appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment {appointment_id} not found",
            )

        # Salvar dados para broadcast
        appointment_dict = {
            "id": existing_appointment.id,
            "nome": existing_appointment.nome,
            "telefone": existing_appointment.telefone,
            "date_time": existing_appointment.date_time.isoformat(),
            "status": existing_appointment.status,
        }

        # Deletar appointment
        await db.execute(delete(Appointment).where(Appointment.id == appointment_id))
        await db.commit()

        # 🚀 REAL-TIME UPDATE: Broadcast deleção do agendamento
        background_tasks.add_task(
            notify_appointment_deleted, appointment_id, appointment_dict
        )

        # Log da operação
        logger.info(f"Appointment deleted: ID {appointment_id}")

        # Broadcast notificação do sistema
        background_tasks.add_task(
            notify_system_message,
            f"Agendamento cancelado: {existing_appointment.nome}",
            "warning",
        )

        return {"message": f"Appointment {appointment_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting appointment: {str(e)}",
        )


@router.get("/stats/summary")
async def get_appointments_summary(db: AsyncSession = Depends(get_db)):
    """
    📊 Estatísticas resumidas dos agendamentos
    """
    try:
        # Total de agendamentos
        total_query = select(func.count(Appointment.id))
        total_result = await db.execute(total_query)
        total = total_result.scalar()

        # Agendamentos por status
        status_query = select(
            Appointment.status, func.count(Appointment.id).label("count")
        ).group_by(Appointment.status)
        status_result = await db.execute(status_query)
        status_counts = {row.status: row.count for row in status_result}

        # Agendamentos hoje
        today = datetime.now().date()
        today_query = select(func.count(Appointment.id)).where(
            func.date(Appointment.date_time) == today
        )
        today_result = await db.execute(today_query)
        today_count = today_result.scalar()

        summary = {
            "total_appointments": total,
            "appointments_today": today_count,
            "by_status": status_counts,
            "last_updated": datetime.utcnow().isoformat(),
        }

        logger.info("Generated appointments summary")
        return summary

    except Exception as e:
        logger.error(f"Error generating appointments summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}",
        )


@router.post("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    status: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    📋 Atualizar apenas status do agendamento
    """
    try:
        # Verificar se appointment existe
        query = select(Appointment).where(Appointment.id == appointment_id)
        result = await db.execute(query)
        appointment = result.scalar_one_or_none()

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Appointment {appointment_id} not found",
            )

        old_status = appointment.status

        # Atualizar status
        await db.execute(
            update(Appointment)
            .where(Appointment.id == appointment_id)
            .values(status=status)
        )
        await db.commit()
        await db.refresh(appointment)

        # Dados para broadcast
        appointment_dict = {
            "id": appointment.id,
            "nome": appointment.nome,
            "telefone": appointment.telefone,
            "date_time": appointment.date_time.isoformat(),
            "status": appointment.status,
            "previous_status": old_status,
        }

        # 🚀 REAL-TIME UPDATE: Broadcast mudança de status
        background_tasks.add_task(notify_appointment_updated, appointment_dict)

        # Notificação específica para mudança de status
        background_tasks.add_task(
            notify_system_message,
            f"Status alterado: {appointment.nome} - {old_status} → {status}",
            "info",
        )

        logger.info(
            f"Status updated for appointment {appointment_id}: {old_status} -> {status}"
        )

        return {
            "message": f"Status updated to {status}",
            "appointment_id": appointment_id,
            "old_status": old_status,
            "new_status": status,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating status for appointment {appointment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating status: {str(e)}",
        )
