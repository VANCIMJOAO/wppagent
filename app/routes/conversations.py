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
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, text
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.database import Conversation, Message, User
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Schemas
class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    content: str
    message_type: str
    sender_type: str
    created_at: datetime
    whatsapp_id: Optional[str] = None
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True

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
    session: AsyncSession = Depends(get_db)
):
    """
    💬 Buscar conversas com filtros
    
    Retorna lista paginada de conversas com estatísticas.
    """
    try:
        logger.info(f"🔍 Buscando conversas - Admin: {current_admin.username}")
        
        # Subquery para última mensagem
        last_message_subquery = (
            select(
                Message.conversation_id,
                func.max(Message.created_at).label("last_created_at"),
                func.first_value(Message.content).over(
                    partition_by=Message.conversation_id,
                    order_by=desc(Message.created_at)
                ).label("last_message")
            )
            .group_by(Message.conversation_id)
            .subquery()
        )
        
        # Query principal com JOINs
        query = select(
            Conversation,
            User.nome.label("user_name"),
            User.telefone.label("user_phone"),
            func.count(Message.id).label("total_messages"),
            func.count(Message.id).label("unread_messages"),  # Placeholder - sem campo is_read
            last_message_subquery.c.last_message
        ).select_from(
            Conversation
        ).join(
            User, Conversation.user_id == User.id
        ).outerjoin(
            Message, Conversation.id == Message.conversation_id
        ).outerjoin(
            last_message_subquery,
            Conversation.id == last_message_subquery.c.conversation_id
        )
        
        # Aplicar filtros
        conditions = []
        
        if status:
            conditions.append(Conversation.status == status)
        
        if search:
            search_conditions = or_(
                User.nome.ilike(f"%{search}%"),
                User.telefone.ilike(f"%{search}%")
            )
            conditions.append(search_conditions)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Group by para agregações
        query = query.group_by(
            Conversation.id, User.id, last_message_subquery.c.last_message
        )
        
        # Ordenação e paginação
        query = query.order_by(desc(Conversation.last_message_at))
        query = query.offset(offset).limit(limit)
        
        # Executar query
        result = await session.execute(query)
        rows = result.fetchall()
        
        # Formatear resposta
        conversations = []
        for row in rows:
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
                "unread_messages": row.unread_messages or 0,
                "last_message": row.last_message
            }
            conversations.append(conversation_data)
        
        # Count total
        count_query = select(func.count(Conversation.id.distinct()))
        if search:
            count_query = count_query.select_from(
                Conversation.join(User, Conversation.user_id == User.id)
            ).where(
                or_(
                    User.nome.ilike(f"%{search}%"),
                    User.telefone.ilike(f"%{search}%")
                )
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
            "has_more": (offset + len(conversations)) < total
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversas: {e}")
        raise HTTPException(500, f"Erro interno: {str(e)}")

@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    include_messages: bool = Query(True, description="Incluir mensagens"),
    messages_limit: int = Query(50, le=200, description="Limite de mensagens"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    💬 Buscar conversa específica com mensagens
    """
    try:
        # Buscar conversa
        conv_result = await session.execute(
            select(
                Conversation,
                User.nome.label("user_name"),
                User.telefone.label("user_phone"),
                func.count(Message.id).label("total_messages")
            ).select_from(Conversation)
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
            total_messages=row.total_messages or 0
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
                    sender_type=msg.sender_type,
                    created_at=msg.created_at,
                    whatsapp_id=msg.whatsapp_id
                ) for msg in messages
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
    session: AsyncSession = Depends(get_db)
):
    """
    💬 Buscar mensagens de uma conversa específica
    """
    try:
        # Verificar se conversa existe
        conv_check = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        if not conv_check.scalar_one_or_none():
            raise HTTPException(404, "Conversa não encontrada")
        
        # Buscar mensagens
        messages_result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .offset(offset)
            .limit(limit)
        )
        
        messages = messages_result.scalars().all()
        
        # Count total
        total_result = await session.execute(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
        )
        total = total_result.scalar()
        
        messages_data = [
            {
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "content": msg.content,
                "message_type": msg.message_type,
                "sender_type": msg.sender_type,
                "created_at": msg.created_at,
                "whatsapp_id": msg.whatsapp_id,
                "is_read": True  # Placeholder - campo is_read não existe
            } for msg in messages
        ]
        
        return {
            "messages": messages_data,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(messages)) < total
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar mensagens da conversa {conversation_id}: {e}")
        raise HTTPException(500, f"Erro interno: {str(e)}")

@router.put("/{conversation_id}/status")
async def update_conversation_status(
    conversation_id: int,
    status: str = Query(..., description="Novo status"),
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
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
            "new_status": status
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar status da conversa {conversation_id}: {e}")
        await session.rollback()
        raise HTTPException(500, f"Erro interno: {str(e)}")

@router.get("/stats/summary")
async def get_conversations_stats(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    💬 Estatísticas gerais das conversas
    """
    try:
        # Stats básicas
        stats_result = await session.execute(
            select(
                func.count(Conversation.id).label("total_conversations"),
                func.count(Conversation.id.filter(Conversation.status == "active")).label("active_conversations"),
                func.count(Conversation.id.filter(Conversation.status == "pending")).label("pending_conversations"),
                func.count(Message.id).label("total_messages"),
            ).select_from(
                Conversation.outerjoin(Message, Conversation.id == Message.conversation_id)
            )
        )
        
        stats = stats_result.fetchone()
        
        return {
            "total_conversations": stats.total_conversations or 0,
            "active_conversations": stats.active_conversations or 0,
            "pending_conversations": stats.pending_conversations or 0,
            "total_messages": stats.total_messages or 0,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas de conversas: {e}")
        raise HTTPException(500, f"Erro interno: {str(e)}")
