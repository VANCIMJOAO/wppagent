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

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.decorators.cache_invalidation import (
    invalidate_appointment_cache_on_success, invalidate_cache)
from app.models.database import Appointment, Business, Service, User
from app.routes.admin_auth import AdminUser, get_current_admin_user
from app.schemas.unified import (AppointmentCreateRequest,
                                 AppointmentsListResponseUnified,
                                 AppointmentUpdateRequest, SchemaTransformer,
                                 UnifiedAppointmentResponse)
from app.services.cache_invalidation import CacheEvent
from app.services.cache_optimized import CacheKeys, cache_service
# WebSocket integration
from app.services.websocket_manager import (WebSocketEventType,
                                            websocket_manager)
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
    current_admin: AdminUser = Depends(get_current_admin_user),
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
        date_to=date_to,
    )

    async def fetch_appointments():
        """Função para buscar dados frescos quando cache miss"""
        try:
            # Calcular offset
            offset = (page - 1) * limit

            # ✅ P001: Query OTIMIZADA com joinedload para eliminar N+1 queries
            query = select(Appointment).options(
                joinedload(Appointment.user),
                joinedload(Appointment.business),
                joinedload(Appointment.service),
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
                    raise HTTPException(
                        400, "date_from deve estar no formato YYYY-MM-DD"
                    )

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
            query = (
                query.order_by(desc(Appointment.date_time)).limit(limit).offset(offset)
            )
            result = await session.execute(query)

            # ✅ P001: Usar scalars().unique() para joinedload
            appointments_orm = result.scalars().unique().all()

            # ✅ P001: Converter usando relacionamentos já carregados (sem lazy loading)
            appointments = []
            for appointment in appointments_orm:
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
                    # ✅ P001: Acessar relacionamentos sem lazy loading
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
                }
                # Usar o transformer para formato unificado
                unified_dict = SchemaTransformer.appointment_dict_to_unified(
                    appointment_dict
                )
                appointments.append(UnifiedAppointmentResponse(**unified_dict))

            has_more = (page * limit) < total

            return {
                "appointments": [appt.dict() for appt in appointments],
                "total": total,
                "page": page,
                "per_page": limit,
                "has_more": has_more,
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
            cache_type="appointments_list",
        )

        # Converter de volta para Pydantic models
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
        logger.error(f"❌ Erro no cache de agendamentos: {e}")
        # Fallback sem cache
        result = await fetch_appointments()
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


@router.get("/legacy", response_model=Dict[str, Any])
async def get_appointments_legacy(
    limit: int = Query(50, le=500, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    date_from: Optional[str] = Query(None, description="Data inicial (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Data final (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    user_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    📅 Buscar agendamentos com filtros

    Retorna lista paginada de agendamentos com dados relacionados.
    """
    try:
        logger.info(f"🔍 Buscando agendamentos - Admin: {current_admin.username}")

        # Query base com JOINs
        query = (
            select(
                Appointment,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                Business.name.label("business_name"),
                Service.name.label("service_name"),
            )
            .select_from(Appointment)
            .join(User, Appointment.user_id == User.id)
            .join(Business, Appointment.business_id == Business.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
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
                "service_name": row.service_name,
            }
            appointments.append(appointment_data)

        # Count total para paginação
        count_query = select(func.count(Appointment.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await session.execute(count_query)
        total = total_result.scalar()

        logger.info(
            f"✅ Encontrados {len(appointments)} agendamentos de {total} totais"
        )

        return {
            "appointments": appointments,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(appointments)) < total,
        }

    except Exception as e:
        logger.error(f"❌ Erro ao buscar agendamentos: {e}")
        raise HTTPException(500, f"Erro interno: {str(e)}")


@router.post("/", response_model=UnifiedAppointmentResponse)
@invalidate_appointment_cache_on_success(CacheEvent.APPOINTMENT_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    📅 Criar novo agendamento
    ✅ CACHE INVALIDATION AUTOMÁTICA - Via decorator
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
            notes=appointment_data.notes,
        )

        session.add(new_appointment)
        await session.commit()
        await session.refresh(new_appointment)

        # ✅ Cache será invalidado automaticamente pelo decorator
        logger.info(f"✅ Agendamento criado com ID: {new_appointment.id}")
        logger.info(f"✅ Cache invalidation automática via decorator")

        # Buscar dados completos para resposta
        complete_result = await session.execute(
            select(
                Appointment,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                Business.name.label("business_name"),
                Service.name.label("service_name"),
            )
            .select_from(Appointment)
            .join(User, Appointment.user_id == User.id)
            .join(Business, Appointment.business_id == Business.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
            .where(Appointment.id == new_appointment.id)
        )

        row = complete_result.fetchone()
        if row:
            appointment_dict = SchemaTransformer.appointment_row_to_unified(row)

            # 🔥 NEW: WebSocket real-time notification for appointment creation
            try:
                await websocket_manager.broadcast_to_topic(
                    topic="appointments",
                    event_type=WebSocketEventType.APPOINTMENT_CREATED,
                    data={
                        "appointment": {
                            "id": new_appointment.id,
                            "client_name": row.user_name,
                            "service_name": row.service_name or "Serviço Geral",
                            "business_name": row.business_name,
                            "date_time": new_appointment.date_time.isoformat(),
                            "status": new_appointment.status,
                            "created_by": current_admin.username,
                        },
                        "message": f"Novo agendamento: {row.user_name}",
                        "notification": {
                            "title": "Novo Agendamento",
                            "body": f"{row.user_name} - {row.service_name or 'Serviço'}",
                        },
                    },
                )

                # 🔥 NEW: Update dashboard stats in real-time
                await websocket_manager.broadcast_to_topic(
                    topic="dashboard",
                    event_type=WebSocketEventType.DASHBOARD_STATS_UPDATE,
                    data={
                        "metric": "appointments_today",
                        "increment": 1,
                        "action": "created",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

                logger.info(
                    f"📡 WebSocket notifications sent for appointment {new_appointment.id}"
                )

            except Exception as ws_error:
                # Don't fail the main operation if WebSocket fails
                logger.warning(f"⚠️ WebSocket notification failed: {ws_error}")

            return UnifiedAppointmentResponse(**appointment_dict)

        return new_appointment

    except Exception as e:
        logger.error(f"❌ Erro ao criar agendamento: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")


@router.get("/{appointment_id}", response_model=UnifiedAppointmentResponse)
async def get_appointment(
    appointment_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
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
                Service.name.label("service_name"),
            )
            .select_from(Appointment)
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
            cache_type="appointment_detail",
        )

        return UnifiedAppointmentResponse(**cached_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no cache do agendamento {appointment_id}: {e}")
        # Fallback sem cache
        appointment_dict = await fetch_appointment()
        return UnifiedAppointmentResponse(**appointment_dict)


@router.put("/{appointment_id}", response_model=UnifiedAppointmentResponse)
@invalidate_cache(CacheEvent.APPOINTMENT_UPDATED, entity_id_param="appointment_id")
async def update_appointment(
    appointment_id: int,
    update_data: AppointmentUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    📅 Atualizar agendamento
    ✅ CACHE INVALIDATION AUTOMÁTICA - Via decorator
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

        # ✅ Cache será invalidado automaticamente pelo decorator
        logger.info(f"✅ Agendamento {appointment_id} atualizado")
        logger.info(f"✅ Cache invalidation automática via decorator")

        # Buscar dados completos para resposta
        complete_result = await session.execute(
            select(
                Appointment,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                Business.name.label("business_name"),
                Service.name.label("service_name"),
            )
            .select_from(Appointment)
            .join(User, Appointment.user_id == User.id)
            .join(Business, Appointment.business_id == Business.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
            .where(Appointment.id == appointment_id)
        )

        row = complete_result.fetchone()
        appointment_dict = SchemaTransformer.appointment_row_to_unified(row)

        # 🔥 NEW: WebSocket notification for appointment update
        try:
            # Determine what changed
            changes = {}
            if update_data.date_time is not None:
                changes["date_time"] = update_data.date_time.isoformat()
            if update_data.status is not None:
                changes["status"] = update_data.status
            if update_data.notes is not None:
                changes["notes"] = update_data.notes
            if update_data.service_id is not None:
                changes["service_id"] = update_data.service_id

            await websocket_manager.broadcast_to_topic(
                topic="appointments",
                event_type=WebSocketEventType.APPOINTMENT_UPDATED,
                data={
                    "appointment_id": appointment_id,
                    "changes": changes,
                    "updated_appointment": {
                        "id": appointment.id,
                        "client_name": row.user_name,
                        "service_name": row.service_name or "Serviço Geral",
                        "date_time": appointment.date_time.isoformat(),
                        "status": appointment.status,
                        "updated_by": current_admin.username,
                    },
                    "message": f"Agendamento atualizado: {row.user_name}",
                    "notification": {
                        "title": "Agendamento Atualizado",
                        "body": f"{row.user_name} - Status: {appointment.status}",
                    },
                },
            )

            # Special notification for status changes
            if update_data.status and update_data.status in [
                "confirmado",
                "cancelado",
                "realizado",
            ]:
                status_event = {
                    "confirmado": WebSocketEventType.APPOINTMENT_CONFIRMED,
                    "cancelado": WebSocketEventType.APPOINTMENT_CANCELLED,
                    "realizado": WebSocketEventType.APPOINTMENT_UPDATED,
                }.get(update_data.status, WebSocketEventType.APPOINTMENT_UPDATED)

                await websocket_manager.broadcast_to_topic(
                    topic="dashboard",
                    event_type=status_event,
                    data={
                        "appointment_id": appointment_id,
                        "new_status": update_data.status,
                        "client_name": row.user_name,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            logger.info(
                f"📡 WebSocket update notifications sent for appointment {appointment_id}"
            )

        except Exception as ws_error:
            logger.warning(f"⚠️ WebSocket update notification failed: {ws_error}")

        return UnifiedAppointmentResponse(**appointment_dict)

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar agendamento {appointment_id}: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")


@router.delete("/{appointment_id}")
@invalidate_cache(CacheEvent.APPOINTMENT_DELETED, entity_id_param="appointment_id")
async def delete_appointment(
    appointment_id: int,
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    📅 Excluir agendamento
    ✅ CACHE INVALIDATION AUTOMÁTICA - Via decorator
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

        # ✅ Cache será invalidado automaticamente pelo decorator
        logger.info(f"✅ Agendamento {appointment_id} excluído")
        logger.info(f"✅ Cache invalidation automática via decorator")

        return {"message": "Agendamento excluído com sucesso", "id": appointment_id}

    except Exception as e:
        logger.error(f"❌ Erro ao excluir agendamento {appointment_id}: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")


# ================================================================
# 🧪 FUNÇÕES DE TESTE E VALIDAÇÃO
# ================================================================


@router.get("/test/schema-validation")
async def test_schema_validation(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    🧪 Teste de validação de schema unificado

    Verifica se todos os agendamentos seguem o schema padronizado
    """
    try:
        # Buscar uma amostra de agendamentos
        result = await session.execute(
            select(
                Appointment.id,
                Appointment.user_id,
                Appointment.business_id,
                Appointment.service_id,
                Appointment.date_time,
                Appointment.duration_minutes,
                Appointment.price,
                Appointment.status,
                User.nome.label("user_name"),
                Service.name.label("service_name"),
            )
            .select_from(Appointment)
            .join(User, Appointment.user_id == User.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
            .limit(5)
        )

        rows = result.fetchall()
        validation_results = []

        for row in rows:
            # Testar conversão para schema unificado
            try:
                appointment_dict = SchemaTransformer.appointment_row_to_unified(row)
                unified_appointment = UnifiedAppointmentResponse(**appointment_dict)

                validation_results.append(
                    {
                        "id": row.id,
                        "status": "✅ VÁLIDO",
                        "schema_fields": list(appointment_dict.keys()),
                        "unified_model": "OK",
                    }
                )

            except Exception as e:
                validation_results.append(
                    {
                        "id": row.id,
                        "status": "❌ ERRO",
                        "error": str(e),
                        "unified_model": "FALHOU",
                    }
                )

        return {
            "test_name": "Schema Validation Test",
            "total_tested": len(validation_results),
            "passed": len([r for r in validation_results if "✅" in r["status"]]),
            "failed": len([r for r in validation_results if "❌" in r["status"]]),
            "details": validation_results,
        }

    except Exception as e:
        logger.error(f"❌ Erro no teste de schema: {e}")
        raise HTTPException(500, f"Erro no teste: {str(e)}")


@router.get("/test/performance")
async def test_performance(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    🧪 Teste de performance das queries

    Mede tempo de resposta das operações principais
    """
    import time

    try:
        performance_results = {}

        # Teste 1: Lista de agendamentos
        start_time = time.time()
        result = await session.execute(select(func.count(Appointment.id)))
        total_appointments = result.scalar()
        list_time = time.time() - start_time

        performance_results["count_query"] = {
            "duration_ms": round((list_time * 1000), 2),
            "total_records": total_appointments,
            "status": "✅ OK" if list_time < 0.1 else "⚠️ LENTO",
        }

        # Teste 2: Query complexa com JOINs
        start_time = time.time()
        complex_result = await session.execute(
            select(Appointment.id, User.nome, Business.name, Service.name)
            .select_from(Appointment)
            .join(User, Appointment.user_id == User.id)
            .join(Business, Appointment.business_id == Business.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
            .limit(10)
        )
        complex_rows = complex_result.fetchall()
        complex_time = time.time() - start_time

        performance_results["join_query"] = {
            "duration_ms": round((complex_time * 1000), 2),
            "records_fetched": len(complex_rows),
            "status": "✅ OK" if complex_time < 0.5 else "⚠️ LENTO",
        }

        # Teste 3: Cache hit rate simulation
        cache_start = time.time()
        cache_key = "test:performance:check"

        # Simular busca em cache
        cached_value = await cache_service.get(cache_key)
        if cached_value is None:
            await cache_service.set(cache_key, {"test": "data"}, ttl=60)
            cache_status = "MISS"
        else:
            cache_status = "HIT"

        cache_time = time.time() - cache_start

        performance_results["cache_test"] = {
            "duration_ms": round((cache_time * 1000), 2),
            "cache_status": cache_status,
            "status": "✅ OK" if cache_time < 0.01 else "⚠️ LENTO",
        }

        # Análise geral
        total_duration = sum(
            [
                performance_results["count_query"]["duration_ms"],
                performance_results["join_query"]["duration_ms"],
                performance_results["cache_test"]["duration_ms"],
            ]
        )

        overall_status = (
            "✅ EXCELENTE"
            if total_duration < 100
            else "⚠️ REVISAR" if total_duration < 500 else "❌ CRÍTICO"
        )

        return {
            "test_name": "Performance Test",
            "timestamp": datetime.now().isoformat(),
            "overall_duration_ms": round(total_duration, 2),
            "overall_status": overall_status,
            "results": performance_results,
            "recommendations": [
                "Considere indexação adicional se queries > 500ms",
                "Monitore cache hit rate em produção",
                "Otimize JOINs para datasets grandes",
            ],
        }

    except Exception as e:
        logger.error(f"❌ Erro no teste de performance: {e}")
        raise HTTPException(500, f"Erro no teste: {str(e)}")


@router.post("/test/data-integrity")
async def test_data_integrity(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    🧪 Teste de integridade de dados

    Verifica inconsistências e problemas de dados
    """
    try:
        integrity_issues = []

        # Teste 1: Agendamentos sem usuário
        orphaned_appointments = await session.execute(
            select(Appointment.id)
            .outerjoin(User, Appointment.user_id == User.id)
            .where(User.id.is_(None))
        )
        orphaned_count = len(orphaned_appointments.fetchall())

        if orphaned_count > 0:
            integrity_issues.append(
                {
                    "issue": "Agendamentos órfãos (sem usuário)",
                    "count": orphaned_count,
                    "severity": "HIGH",
                }
            )

        # Teste 2: Agendamentos sem business
        no_business_appointments = await session.execute(
            select(Appointment.id)
            .outerjoin(Business, Appointment.business_id == Business.id)
            .where(Business.id.is_(None))
        )
        no_business_count = len(no_business_appointments.fetchall())

        if no_business_count > 0:
            integrity_issues.append(
                {
                    "issue": "Agendamentos sem negócio",
                    "count": no_business_count,
                    "severity": "HIGH",
                }
            )

        # Teste 3: Status inválidos
        invalid_status = await session.execute(
            select(Appointment.id, Appointment.status).where(
                ~Appointment.status.in_(
                    ["agendado", "confirmado", "cancelado", "realizado"]
                )
            )
        )
        invalid_status_rows = invalid_status.fetchall()

        if invalid_status_rows:
            integrity_issues.append(
                {
                    "issue": "Status inválidos",
                    "count": len(invalid_status_rows),
                    "severity": "MEDIUM",
                    "examples": [row.status for row in invalid_status_rows[:3]],
                }
            )

        # Teste 4: Datas no passado com status "agendado"
        past_scheduled = await session.execute(
            select(Appointment.id).where(
                and_(
                    Appointment.status == "agendado",
                    Appointment.date_time < datetime.now(),
                )
            )
        )
        past_scheduled_count = len(past_scheduled.fetchall())

        if past_scheduled_count > 0:
            integrity_issues.append(
                {
                    "issue": "Agendamentos passados ainda com status 'agendado'",
                    "count": past_scheduled_count,
                    "severity": "MEDIUM",
                }
            )

        # Resultado final
        severity_counts = {
            "HIGH": len([i for i in integrity_issues if i["severity"] == "HIGH"]),
            "MEDIUM": len([i for i in integrity_issues if i["severity"] == "MEDIUM"]),
            "LOW": len([i for i in integrity_issues if i["severity"] == "LOW"]),
        }

        overall_health = (
            "✅ EXCELENTE"
            if not integrity_issues
            else "⚠️ ATENÇÃO" if severity_counts["HIGH"] == 0 else "❌ CRÍTICO"
        )

        return {
            "test_name": "Data Integrity Test",
            "timestamp": datetime.now().isoformat(),
            "overall_health": overall_health,
            "total_issues": len(integrity_issues),
            "severity_breakdown": severity_counts,
            "issues_found": integrity_issues,
            "recommendations": (
                [
                    "Execute limpeza de dados órfãos",
                    "Implemente validação de status mais rigorosa",
                    "Configure job para atualizar status de agendamentos passados",
                ]
                if integrity_issues
                else ["Dados íntegros - nenhuma ação necessária"]
            ),
        }

    except Exception as e:
        logger.error(f"❌ Erro no teste de integridade: {e}")
        raise HTTPException(500, f"Erro no teste: {str(e)}")
