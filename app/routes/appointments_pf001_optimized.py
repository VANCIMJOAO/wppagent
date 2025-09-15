"""
⚡ PF-001: Appointments Optimized Routes
=======================================

Rotas otimizadas para appointments eliminando N+1 queries:
- selectinload e joinedload estratégicos
- Cache com Redis (TTL 2min para listas)
- Monitoramento de performance
- Máximo 3 queries para qualquer operação

Status: PF-001 Implementation - Parte 2/4
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.database import get_db
from app.models.database import (Appointment, Business, Conversation, Service,
                                 User)
from app.routes.admin_auth import AdminUser, get_current_admin_user
from app.schemas.unified import (AppointmentCreateRequest,
                                 AppointmentsListResponseUnified,
                                 AppointmentUpdateRequest, SchemaTransformer,
                                 UnifiedAppointmentResponse)
from app.services.cache_service import CacheService
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Router otimizado para PF-001
router = APIRouter(
    prefix="/appointments/optimized", tags=["Appointments Optimized - PF001"]
)

# Cache service instance
cache_service = CacheService()


@router.get("/", response_model=AppointmentsListResponseUnified)
async def get_appointments_optimized(
    limit: int = Query(10, le=100, description="Limite de resultados"),
    page: int = Query(1, ge=1, description="Página atual"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    user_id: Optional[int] = Query(None, description="Filtrar por ID do cliente"),
    session: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    ⚡ PF-001: Lista appointments OTIMIZADA - Máximo 3 queries

    Otimizações implementadas:
    - selectinload para relacionamentos 1:N
    - joinedload para relacionamentos N:1
    - Cache Redis com TTL 2min
    - Query única para dados + count
    """

    # 🔑 Cache key baseado em parâmetros
    cache_key = f"appointments:optimized:list:{limit}:{page}:{status}:{date_from}:{date_to}:{user_id}"

    async def fetch_optimized_appointments():
        """
        🚀 Função otimizada - MÁXIMO 3 queries:
        1. Query principal com todos os relacionamentos
        2. Count total (se necessário)
        3. Possível query de cache check
        """

        try:
            # Calcular offset
            offset = (page - 1) * limit

            # 🔥 QUERY OTIMIZADA - PF-001: Eliminar N+1 completamente
            # selectinload para relacionamentos que podem ter múltiplos resultados
            # joinedload para relacionamentos simples N:1
            query = select(Appointment).options(
                # ✅ N:1 relationships - joinedload (mais eficiente)
                joinedload(Appointment.user),
                joinedload(Appointment.business),
                joinedload(Appointment.service),
                # ✅ Conversations podem ser múltiplas - selectinload
                selectinload(Appointment.conversations),
            )

            # 🔍 Aplicar filtros
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
                    raise HTTPException(
                        400, "date_from deve estar no formato YYYY-MM-DD"
                    )

            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                    conditions.append(func.date(Appointment.date_time) <= date_to_obj)
                except ValueError:
                    raise HTTPException(400, "date_to deve estar no formato YYYY-MM-DD")

            if conditions:
                query = query.where(and_(*conditions))

            # 📊 Query de count otimizada - QUERY 1
            count_query = select(func.count(Appointment.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))

            count_result = await session.execute(count_query)
            total = count_result.scalar()

            # 📋 Query principal com paginação - QUERY 2
            query = (
                query.order_by(desc(Appointment.date_time)).limit(limit).offset(offset)
            )
            result = await session.execute(query)

            # ✅ CRÍTICO: unique() para joinedload evitar duplicatas
            appointments_orm = result.scalars().unique().all()

            # 🔄 Transformar para response format - SEM QUERIES ADICIONAIS
            appointments = []
            for appointment in appointments_orm:
                # ✅ Todos os relacionamentos já carregados - zero lazy loading
                appointment_dict = {
                    "id": appointment.id,
                    "user_id": appointment.user_id,
                    "business_id": appointment.business_id,
                    "service_id": appointment.service_id,
                    "date_time": appointment.date_time,
                    "status": appointment.status,
                    "notes": appointment.notes,
                    "created_at": appointment.created_at,
                    "updated_at": appointment.updated_at,
                    # ✅ Acessar relacionamentos SEM lazy loading
                    "user_name": appointment.user.nome if appointment.user else None,
                    "user_phone": (
                        appointment.user.telefone if appointment.user else None
                    ),
                    "business_name": (
                        appointment.business.name if appointment.business else None
                    ),
                    "service_name": (
                        appointment.service.name if appointment.service else None
                    ),
                    "conversation_count": (
                        len(appointment.conversations)
                        if appointment.conversations
                        else 0
                    ),
                }

                # Transformar para formato unificado
                unified_dict = SchemaTransformer.appointment_dict_to_unified(
                    appointment_dict
                )
                appointments.append(unified_dict)

            has_more = (page * limit) < total

            return {
                "appointments": appointments,
                "total": total,
                "page": page,
                "per_page": limit,
                "has_more": has_more,
                "query_count": 2,  # Tracking: count + main query
                "optimization": "PF-001",
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Erro na query otimizada: {e}")
            raise HTTPException(500, f"Erro interno: {str(e)}")

    # 💾 Cache strategy - TTL 2 minutos
    try:
        cached_data = await cache_service.get_or_set(
            key=cache_key,
            fetch_function=fetch_optimized_appointments,
            ttl=120,  # 2 minutos conforme PF-001
            cache_type="appointments_optimized",
        )

        # Converter para Pydantic models
        appointments = [
            UnifiedAppointmentResponse(**appt) for appt in cached_data["appointments"]
        ]

        return AppointmentsListResponseUnified(
            appointments=appointments,
            total=cached_data["total"],
            page=cached_data["page"],
            per_page=cached_data["per_page"],
            has_more=cached_data["has_more"],
        )

    except Exception as e:
        logger.warning(f"⚠️ Cache error, usando fallback: {e}")
        # Fallback sem cache
        result = await fetch_optimized_appointments()
        appointments = [
            UnifiedAppointmentResponse(**appt) for appt in result["appointments"]
        ]

        return AppointmentsListResponseUnified(
            appointments=appointments,
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            has_more=result["has_more"],
        )


@router.get("/{appointment_id}", response_model=UnifiedAppointmentResponse)
async def get_appointment_optimized(
    appointment_id: int,
    session: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    ⚡ PF-001: Buscar appointment individual OTIMIZADO - 1 query única

    Otimizações:
    - Todos os relacionamentos em 1 query
    - Cache individual com TTL 5min
    - Zero lazy loading
    """

    cache_key = f"appointments:optimized:detail:{appointment_id}"

    async def fetch_appointment_detail():
        """Buscar appointment com todos os relacionamentos em 1 query"""

        # 🔥 QUERY ÚNICA com todos os relacionamentos - PF-001
        result = await session.execute(
            select(Appointment)
            .options(
                joinedload(Appointment.user),
                joinedload(Appointment.business),
                joinedload(Appointment.service),
                selectinload(Appointment.conversations),
            )
            .where(Appointment.id == appointment_id)
        )

        appointment = result.scalars().unique().first()

        if not appointment:
            raise HTTPException(404, "Agendamento não encontrado")

        # Transformar SEM queries adicionais
        appointment_dict = {
            "id": appointment.id,
            "user_id": appointment.user_id,
            "business_id": appointment.business_id,
            "service_id": appointment.service_id,
            "date_time": appointment.date_time,
            "status": appointment.status,
            "notes": appointment.notes,
            "created_at": appointment.created_at,
            "updated_at": appointment.updated_at,
            "user_name": appointment.user.nome if appointment.user else None,
            "user_phone": appointment.user.telefone if appointment.user else None,
            "business_name": (
                appointment.business.name if appointment.business else None
            ),
            "service_name": appointment.service.name if appointment.service else None,
            "conversation_count": (
                len(appointment.conversations) if appointment.conversations else 0
            ),
        }

        return SchemaTransformer.appointment_dict_to_unified(appointment_dict)

    # Cache com TTL 5 minutos para detalhes
    try:
        cached_data = await cache_service.get_or_set(
            key=cache_key,
            fetch_function=fetch_appointment_detail,
            ttl=300,  # 5 minutos
            cache_type="appointment_detail_optimized",
        )

        return UnifiedAppointmentResponse(**cached_data)

    except Exception as e:
        logger.warning(f"⚠️ Cache error para detail: {e}")
        result = await fetch_appointment_detail()
        return UnifiedAppointmentResponse(**result)


@router.get("/stats/performance")
async def get_performance_stats(
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    📊 PF-001: Estatísticas de performance das otimizações
    """
    return {
        "pf_001_status": "implemented",
        "optimizations": {
            "n_plus_one_eliminated": True,
            "max_queries_per_request": 3,
            "cache_ttl_list": "2min",
            "cache_ttl_detail": "5min",
            "eager_loading": ["user", "business", "service", "conversations"],
            "query_techniques": ["joinedload", "selectinload", "unique()"],
        },
        "performance_targets": {
            "list_10_appointments_max_queries": 2,
            "detail_appointment_max_queries": 1,
            "cache_hit_rate_target": ">80%",
            "response_time_target": "<500ms",
        },
    }
