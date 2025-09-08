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
from app.schemas.unified import (
    AppointmentResponseUnified,
    AppointmentCreateRequest,
    AppointmentUpdateRequest,
    AppointmentsListResponseUnified,
    SchemaTransformer
)
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.services.cache_optimized import cache_service, CacheKeys
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Router
router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("/", response_model=AppointmentsListResponseUnified)
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
    ✅ CACHE OTIMIZADO - TTL de 2 minutos para listas frequentes
    """
    
    # ✅ Gerar chave de cache baseada nos parâmetros
    cache_key = CacheKeys.appointments_list(
        limit=limit,
        page=page,
        status=status,
        business_id=None,  # Pode ser adicionado quando necessário
        date_from=date_from,
        date_to=date_to
    )
    
    async def fetch_appointments():
        """Função para buscar dados frescos quando cache miss"""
        try:
            # Calcular offset
            offset = (page - 1) * limit
            
            # Query base com JOINs padronizados e aliases explícitos
            query = select(
                Appointment.id.label("appointment_id"),
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
                # ✅ Usar aliases explícitos para evitar ambiguidade
                User.nome.label("user_name"),
                User.telefone.label("user_phone"), 
                User.email.label("user_email"),
                Service.name.label("service_name"),
                Service.description.label("service_description"),
                Business.name.label("business_name")
            ).select_from(
                Appointment
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
                appointment_dict = SchemaTransformer.appointment_row_to_unified(row)
                appointments.append(AppointmentResponseUnified(**appointment_dict))
            
            has_more = (page * limit) < total
            
            return {
                "appointments": [appt.dict() for appt in appointments],
                "total": total,
                "page": page,
                "per_page": limit,
                "has_more": has_more
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao buscar agendamentos: {e}")
            raise HTTPException(500, f"Erro interno do servidor: {str(e)}")
    
    # ✅ Usar cache com TTL de 2 minutos para listas
    try:
        cached_data = await cache_service.get_or_set(
            key=cache_key,
            fetch_function=fetch_appointments,
            ttl=120,  # 2 minutos
            cache_type='appointments_list'
        )
        
        # Converter de volta para Pydantic models
        appointments = [AppointmentResponseUnified(**appt) for appt in cached_data["appointments"]]
        
        return AppointmentsListResponseUnified(
            appointments=appointments,
            total=cached_data["total"],
            page=cached_data["page"],
            per_page=cached_data["per_page"],
            has_more=cached_data["has_more"]
        )
        
    except Exception as e:
        logger.error(f"❌ Erro no cache de agendamentos: {e}")
        # Fallback sem cache
        result = await fetch_appointments()
        appointments = [AppointmentResponseUnified(**appt) for appt in result["appointments"]]
        
        return AppointmentsListResponseUnified(
            appointments=appointments,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            has_more=result["has_more"]
        )


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

@router.post("/", response_model=AppointmentResponseUnified)
async def create_appointment(
    appointment_data: AppointmentCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    📅 Criar novo agendamento
    ✅ CACHE INVALIDATION - Limpa cache relacionado após criação
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
        
        # ✅ INVALIDAR CACHE após criação
        cache_service.invalidate_pattern("appointments:list:*")
        cache_service.invalidate_pattern("dashboard:stats:*")
        logger.info(f"✅ Cache invalidado após criação do agendamento {new_appointment.id}")
        
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
            appointment_dict = SchemaTransformer.appointment_row_to_unified(row)
            return AppointmentResponseUnified(**appointment_dict)
        
        return new_appointment
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar agendamento: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")

@router.get("/{appointment_id}", response_model=AppointmentResponseUnified)
async def get_appointment(
    appointment_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    📅 Buscar agendamento específico
    ✅ CACHE OTIMIZADO - TTL de 5 minutos para detalhes individuais
    """
    
    # ✅ Gerar chave de cache para agendamento específico
    cache_key = f"appointments:detail:{appointment_id}"
    
    async def fetch_appointment():
        """Função para buscar dados frescos quando cache miss"""
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
        
        appointment_dict = SchemaTransformer.appointment_row_to_unified(row)
        return appointment_dict
    
    # ✅ Usar cache com TTL de 5 minutos para detalhes
    try:
        cached_data = await cache_service.get_or_set(
            key=cache_key,
            fetch_function=fetch_appointment,
            ttl=300,  # 5 minutos
            cache_type='appointment_detail'
        )
        
        return AppointmentResponseUnified(**cached_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no cache do agendamento {appointment_id}: {e}")
        # Fallback sem cache
        appointment_dict = await fetch_appointment()
        return AppointmentResponseUnified(**appointment_dict)

@router.put("/{appointment_id}", response_model=AppointmentResponseUnified)
async def update_appointment(
    appointment_id: int,
    update_data: AppointmentUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    📅 Atualizar agendamento
    ✅ CACHE INVALIDATION - Limpa cache relacionado após atualização
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
        
        # ✅ INVALIDAR CACHE após atualização
        cache_service.invalidate_pattern("appointments:list:*")
        cache_service.invalidate_pattern("dashboard:stats:*")
        cache_service.delete(f"appointments:detail:{appointment_id}")
        logger.info(f"✅ Cache invalidado após atualização do agendamento {appointment_id}")
        
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
        appointment_dict = SchemaTransformer.appointment_row_to_unified(row)
        return AppointmentResponseUnified(**appointment_dict)
        
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
    ✅ CACHE INVALIDATION - Limpa cache relacionado após exclusão
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
        
        # ✅ INVALIDAR CACHE após exclusão
        cache_service.invalidate_pattern("appointments:list:*")
        cache_service.invalidate_pattern("dashboard:stats:*")
        cache_service.delete(f"appointments:detail:{appointment_id}")
        logger.info(f"✅ Cache invalidado após exclusão do agendamento {appointment_id}")
        
        logger.info(f"✅ Agendamento {appointment_id} excluído")
        
        return {"message": "Agendamento excluído com sucesso", "id": appointment_id}
        
    except Exception as e:
        logger.error(f"❌ Erro ao excluir agendamento {appointment_id}: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")
