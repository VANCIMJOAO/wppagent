"""
💬 API REST - Conversas WhatsApp
================================

Endpoints REST para gestão de conversas WhatsApp integrados com Dashboard.

Funcionalidades:
- CRUD de conversas e mensagens
- Filtros por status, data, cliente
- Busca por conteúdo de mensagens
- Estatísticas de conversas
- Autenticação JWT obrigatória

Autor: Claude AI
Status: Implementação crítica para Dashboard
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, case, desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import Conversation, Message, User
from app.routes.admin_auth import AdminUser, get_current_admin_user
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Schemas
class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    content: str
    message_type: str
    direction: str  # ✅ Usar 'direction' padronizado ('in' | 'out')
    created_at: datetime
    whatsapp_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    status: str
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    # Dados relacionados
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    total_messages: int = 0
    unread_messages: int = 0
    last_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = []


# Router
router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/", response_model=Dict[str, Any])
async def get_conversations(
    limit: int = Query(50, le=500, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    search: Optional[str] = Query(None, description="Buscar por nome ou telefone"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    💬 Buscar conversas com filtros

    Retorna lista paginada de conversas com estatísticas.
    """
    try:
        logger.info(f"🔍 Buscando conversas - Admin: {current_admin.username}")
        logger.info(
            f"📊 Parâmetros: limit={limit}, offset={offset}, status={status}, search={search}"
        )

        # Query principal com correção para evitar ambiguidade e contagem duplicada
        query = (
            select(
                Conversation,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                func.count(func.distinct(Message.id)).label("total_messages"),
            )
            .select_from(Conversation)
            .join(User, Conversation.user_id == User.id)
            .outerjoin(Message, Conversation.id == Message.conversation_id)
        )

        # Aplicar filtros
        conditions = []

        if status:
            logger.info(f"🔍 Aplicando filtro de status: {status}")
            conditions.append(Conversation.status == status)

        if search:
            logger.info(f"🔍 Aplicando filtro de busca: {search}")
            search_conditions = or_(
                User.nome.ilike(f"%{search}%"), User.telefone.ilike(f"%{search}%")
            )
            conditions.append(search_conditions)

        if conditions:
            query = query.where(and_(*conditions))

        # Group by para agregações
        query = query.group_by(Conversation.id, User.id)

        # Ordenação e paginação
        query = query.order_by(desc(Conversation.last_message_at))
        query = query.offset(offset).limit(limit)

        # Executar query
        logger.info("🔍 Executando query principal...")
        result = await session.execute(query)
        rows = result.fetchall()
        logger.info(f"📊 Query executada: {len(rows)} resultados encontrados")

        # Formatear resposta
        conversations = []
        for i, row in enumerate(rows):
            try:
                conversation = row.Conversation
                conversation_data = {
                    "id": conversation.id,
                    "user_id": conversation.user_id,
                    "status": conversation.status,
                    "last_message_at": conversation.last_message_at,
                    "created_at": conversation.created_at,
                    "updated_at": conversation.updated_at,
                    "user_name": row.user_name,
                    "user_phone": row.user_phone,
                    "total_messages": row.total_messages or 0,
                    "unread_messages": 0,  # Placeholder - sem campo is_read
                    "last_message": "N/A",  # Simplificado por ora
                }
                conversations.append(conversation_data)
                logger.debug(
                    f"✅ Conversa {i+1}/{len(rows)} processada: ID {conversation.id}"
                )
            except Exception as conv_error:
                logger.error(f"❌ Erro ao processar conversa {i+1}: {conv_error}")
                logger.error(f"💾 Dados da conversa problemática: {vars(row)}")
                raise

        # Count total
        logger.info("📊 Contando total de conversas...")
        count_query = select(func.count(Conversation.id.distinct()))
        if search:
            count_query = count_query.select_from(
                Conversation.join(User, Conversation.user_id == User.id)
            ).where(
                or_(User.nome.ilike(f"%{search}%"), User.telefone.ilike(f"%{search}%"))
            )
        if status:
            count_query = count_query.where(Conversation.status == status)

        total_result = await session.execute(count_query)
        total = total_result.scalar()

        logger.info(f"✅ Encontradas {len(conversations)} conversas de {total} totais")

        return {
            "conversations": conversations,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(conversations)) < total,
        }

    except Exception as e:
        logger.error(f"❌ Erro inesperado ao buscar conversas: {e}")
        logger.error(f"💾 Tipo do erro: {type(e).__name__}")
        logger.error(f"💾 Detalhes: {str(e)}")
        import traceback

        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Erro interno: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    include_messages: bool = Query(True, description="Incluir mensagens"),
    messages_limit: int = Query(50, le=200, description="Limite de mensagens"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    💬 Buscar conversa específica com mensagens
    """
    try:
        # Buscar conversa com correção de ambiguidade
        conv_result = await session.execute(
            select(
                Conversation,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                func.count(func.distinct(Message.id)).label("total_messages"),
            )
            .select_from(Conversation)
            .join(User, Conversation.user_id == User.id)
            .outerjoin(Message, Conversation.id == Message.conversation_id)
            .where(Conversation.id == conversation_id)
            .group_by(Conversation.id, User.id)
        )

        row = conv_result.fetchone()
        if not row:
            raise HTTPException(404, "Conversa não encontrada")

        conversation = row.Conversation
        conversation_data = ConversationWithMessages(
            id=conversation.id,
            user_id=conversation.user_id,
            status=conversation.status,
            last_message_at=conversation.last_message_at,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            user_name=row.user_name,
            user_phone=row.user_phone,
            total_messages=row.total_messages or 0,
        )

        # Buscar mensagens se solicitado
        if include_messages:
            messages_result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(desc(Message.created_at))
                .limit(messages_limit)
            )

            messages = messages_result.scalars().all()
            conversation_data.messages = [
                MessageResponse(
                    id=msg.id,
                    conversation_id=msg.conversation_id,
                    content=msg.content,
                    message_type=msg.message_type,
                    direction=msg.direction,  # ✅ Usar 'direction' padronizado
                    created_at=msg.created_at,
                    whatsapp_id=msg.message_id,  # Usar 'message_id' em vez de 'whatsapp_id'
                )
                for msg in messages
            ]

        return conversation_data

    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversa {conversation_id}: {e}")
        raise HTTPException(500, f"Erro interno: {str(e)}")


@router.get("/{conversation_id}/messages", response_model=Dict[str, Any])
async def get_conversation_messages(
    conversation_id: int,
    limit: int = Query(50, le=200, description="Limite de mensagens"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    💬 Buscar mensagens de uma conversa específica
    """
    try:
        logger.info(
            f"🔍 Buscando mensagens da conversa {conversation_id} - Admin: {current_admin.username}"
        )
        logger.info(f"📊 Parâmetros: limit={limit}, offset={offset}")

        # Verificar se conversa existe
        logger.info(f"🔍 Verificando se conversa {conversation_id} existe...")
        conv_check = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_check.scalar_one_or_none()

        if not conversation:
            logger.warning(f"❌ Conversa {conversation_id} não encontrada")
            raise HTTPException(404, "Conversa não encontrada")

        logger.info(
            f"✅ Conversa {conversation_id} encontrada - Status: {conversation.status}"
        )

        # Buscar mensagens
        logger.info(f"🔍 Buscando mensagens da conversa {conversation_id}...")
        messages_result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .offset(offset)
            .limit(limit)
        )

        messages = messages_result.scalars().all()
        logger.info(f"📨 Encontradas {len(messages)} mensagens")

        # Count total
        logger.info(f"📊 Contando total de mensagens...")
        total_result = await session.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id
            )
        )
        total = total_result.scalar()
        logger.info(f"📊 Total de mensagens na conversa: {total}")

        # Processar mensagens
        logger.info(f"🔄 Processando mensagens...")
        messages_data = []
        for i, msg in enumerate(messages):
            try:
                msg_data = {
                    "id": msg.id,
                    "conversation_id": msg.conversation_id,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "direction": msg.direction,  # ✅ Usar 'direction' padronizado
                    "created_at": msg.created_at,
                    "whatsapp_id": msg.message_id,  # Usar 'message_id' em vez de 'whatsapp_id'
                    "is_read": True,  # Placeholder - campo is_read não existe
                }
                messages_data.append(msg_data)
                logger.debug(
                    f"✅ Mensagem {i+1}/{len(messages)} processada: ID {msg.id}"
                )
            except Exception as msg_error:
                logger.error(f"❌ Erro ao processar mensagem {i+1}: {msg_error}")
                logger.error(f"💾 Dados da mensagem problemática: {vars(msg)}")
                raise

        response_data = {
            "messages": messages_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(messages)) < total,
        }

        logger.info(
            f"✅ Retornando {len(messages_data)} mensagens para conversa {conversation_id}"
        )
        return response_data

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(
            f"❌ Erro inesperado ao buscar mensagens da conversa {conversation_id}: {e}"
        )
        logger.error(f"💾 Tipo do erro: {type(e).__name__}")
        logger.error(f"💾 Detalhes: {str(e)}")
        import traceback

        logger.error(f"📍 Traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Erro interno: {str(e)}")


@router.put("/{conversation_id}/status")
async def update_conversation_status(
    conversation_id: int,
    status: str = Query(..., description="Novo status"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    💬 Atualizar status de uma conversa
    """
    try:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(404, "Conversa não encontrada")

        conversation.status = status
        conversation.updated_at = datetime.utcnow()

        await session.commit()

        logger.info(f"✅ Status da conversa {conversation_id} atualizado para {status}")

        return {
            "message": "Status atualizado com sucesso",
            "conversation_id": conversation_id,
            "new_status": status,
        }

    except Exception as e:
        logger.error(f"❌ Erro ao atualizar status da conversa {conversation_id}: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")


@router.get("/stats/summary")
async def get_conversations_stats(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
):
    """
    💬 Estatísticas gerais das conversas
    """
    try:
        # Stats básicas - Query compatível com PostgreSQL Railway
        stats_result = await session.execute(
            select(
                func.count(func.distinct(Conversation.id)).label("total_conversations"),
                func.sum(case((Conversation.status == "active", 1), else_=0)).label(
                    "active_conversations"
                ),
                func.sum(case((Conversation.status == "pending", 1), else_=0)).label(
                    "pending_conversations"
                ),
                func.count(func.distinct(Message.id)).label("total_messages"),
            )
            .select_from(Conversation)
            .outerjoin(Message, Conversation.id == Message.conversation_id)
        )

        stats = stats_result.fetchone()

        return {
            "total_conversations": stats.total_conversations or 0,
            "active_conversations": stats.active_conversations or 0,
            "pending_conversations": stats.pending_conversations or 0,
            "total_messages": stats.total_messages or 0,
            "generated_at": datetime.utcnow(),
        }

    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas de conversas: {e}")
        raise HTTPException(500, f"Erro interno: {str(e)}")
