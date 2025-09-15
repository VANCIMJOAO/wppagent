from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.middleware import require_admin
from ..database import get_db
from ..models.database import Appointment, Conversation, Message, User
from ..schemas.clients import (ClientCreate, ClientDetailResponse,
                               ClientResponse, ClientStatistics, ClientUpdate,
                               PaginatedResponse)

router = APIRouter(prefix="/clients", tags=["Clients"])


def calculate_client_status(client) -> str:
    """Calcular status do cliente baseado na atividade"""
    if not client.last_interaction:
        return "new"

    days_since_last = (datetime.utcnow() - client.last_interaction).days

    if client.total_appointments > 10 or client.total_messages > 100:
        return "vip"
    elif days_since_last <= 30:
        return "active"
    else:
        return "inactive"


@router.get("/", response_model=PaginatedResponse[ClientResponse])
async def get_clients(
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),  # active, inactive, blocked
    created_after: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """Lista clientes com filtros avançados"""

    # Query base
    query = (
        select(
            User.id,
            User.wa_id,
            User.nome,
            User.telefone,
            User.email,
            User.created_at,
            func.count(Conversation.id.distinct()).label("total_conversations"),
            func.count(Message.id.distinct()).label("total_messages"),
            func.max(Message.created_at).label("last_interaction"),
            func.count(Appointment.id.distinct()).label("total_appointments"),
        )
        .select_from(User)
        .outerjoin(Conversation, User.id == Conversation.user_id)
        .outerjoin(Message, User.id == Message.user_id)
        .outerjoin(Appointment, User.id == Appointment.user_id)
    )

    # Aplicar filtros
    conditions = []
    if search:
        conditions.append(
            or_(
                User.nome.ilike(f"%{search}%"),
                User.telefone.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    if created_after:
        conditions.append(User.created_at >= created_after)

    if conditions:
        query = query.where(and_(*conditions))

    # Group by e paginação
    query = query.group_by(User.id)
    query = query.order_by(desc(User.created_at))
    query = query.offset(offset).limit(limit)

    # Executar
    result = await session.execute(query)
    clients = result.fetchall()

    # Count total
    count_query = select(func.count(User.id.distinct()))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await session.scalar(count_query)

    return {
        "items": [
            ClientResponse(
                id=client.id,
                wa_id=client.wa_id,
                nome=client.nome,
                telefone=client.telefone,
                email=client.email,
                created_at=client.created_at,
                total_conversations=client.total_conversations or 0,
                total_messages=client.total_messages or 0,
                last_interaction=client.last_interaction,
                total_appointments=client.total_appointments or 0,
                status=calculate_client_status(client),  # active/inactive/new
            )
            for client in clients
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/stats")
async def get_client_stats(
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """Estatísticas gerais dos clientes"""

    stats = await session.execute(
        text(
            """
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN last_msg.created_at > NOW() - INTERVAL '30 days' THEN 1 END) as active,
            COUNT(CASE WHEN u.created_at > NOW() - INTERVAL '30 days' THEN 1 END) as new_this_month,
            COUNT(CASE WHEN last_msg.created_at <= NOW() - INTERVAL '30 days' OR last_msg.created_at IS NULL THEN 1 END) as inactive
        FROM users u
        LEFT JOIN (
            SELECT user_id, MAX(created_at) as created_at
            FROM messages 
            GROUP BY user_id
        ) last_msg ON u.id = last_msg.user_id
    """
        )
    )

    result = stats.fetchone()

    return {
        "total": result.total or 0,
        "active": result.active or 0,
        "new_this_month": result.new_this_month or 0,
        "inactive": result.inactive or 0,
    }


@router.get("/{client_id}", response_model=ClientDetailResponse)
async def get_client_detail(
    client_id: int,
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """Detalhes completos de um cliente"""

    # Cliente básico
    client = await session.scalar(select(User).where(User.id == client_id))
    if not client:
        raise HTTPException(404, "Cliente não encontrado")

    # Estatísticas
    stats = await session.execute(
        text(
            """
        SELECT 
            COUNT(DISTINCT c.id) as conversations,
            COUNT(DISTINCT m.id) as messages,
            COUNT(DISTINCT a.id) as appointments,
            MAX(m.created_at) as last_message,
            AVG(CASE WHEN m.direction = 'out' THEN 
                EXTRACT(EPOCH FROM m.created_at - lag(m.created_at) OVER (ORDER BY m.created_at))
            END) as avg_response_time
        FROM users u
        LEFT JOIN conversations c ON u.id = c.user_id
        LEFT JOIN messages m ON u.id = m.user_id  
        LEFT JOIN appointments a ON u.id = a.user_id
        WHERE u.id = :client_id
    """
        ),
        {"client_id": client_id},
    )

    stats_row = stats.fetchone()

    return ClientDetailResponse(
        id=client.id,
        wa_id=client.wa_id,
        nome=client.nome,
        telefone=client.telefone,
        email=client.email,
        created_at=client.created_at,
        updated_at=client.updated_at,
        total_conversations=stats_row.conversations or 0,
        total_messages=stats_row.messages or 0,
        total_appointments=stats_row.appointments or 0,
        last_interaction=stats_row.last_message,
        status=calculate_client_status(stats_row),
        statistics=ClientStatistics(
            total_conversations=stats_row.conversations or 0,
            total_messages=stats_row.messages or 0,
            total_appointments=stats_row.appointments or 0,
            last_interaction=stats_row.last_message,
            avg_response_time_seconds=stats_row.avg_response_time or 0,
        ),
    )


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    update_data: ClientUpdate,
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """Atualizar dados do cliente"""

    client = await session.scalar(select(User).where(User.id == client_id))
    if not client:
        raise HTTPException(404, "Cliente não encontrado")

    # Atualizar campos fornecidos
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)

    client.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(client)

    return ClientResponse(
        id=client.id,
        wa_id=client.wa_id,
        nome=client.nome,
        telefone=client.telefone,
        email=client.email,
        created_at=client.created_at,
        updated_at=client.updated_at,
        total_conversations=0,
        total_messages=0,
        total_appointments=0,
        status="active",
    )


@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """Exclusão segura de cliente (soft delete)"""

    client = await session.scalar(select(User).where(User.id == client_id))
    if not client:
        raise HTTPException(404, "Cliente não encontrado")

    # Soft delete - marcar como inativo
    client.is_active = False
    client.updated_at = datetime.utcnow()

    await session.commit()

    return {"message": f"Cliente {client_id} desativado com sucesso"}


@router.post("/", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    session: AsyncSession = Depends(get_db),
    current_admin: Dict = Depends(require_admin),
):
    """Criar novo cliente"""

    # Verificar se wa_id já existe
    existing_client = await session.scalar(
        select(User).where(User.wa_id == client_data.wa_id)
    )
    if existing_client:
        raise HTTPException(400, "Cliente com este WhatsApp ID já existe")

    # Criar cliente
    client = User(
        wa_id=client_data.wa_id,
        nome=client_data.nome,
        telefone=client_data.telefone,
        email=client_data.email,
        created_at=datetime.utcnow(),
    )

    session.add(client)
    await session.commit()
    await session.refresh(client)

    return ClientResponse(
        id=client.id,
        wa_id=client.wa_id,
        nome=client.nome,
        telefone=client.telefone,
        email=client.email,
        created_at=client.created_at,
        total_conversations=0,
        total_messages=0,
        total_appointments=0,
        status="new",
    )
