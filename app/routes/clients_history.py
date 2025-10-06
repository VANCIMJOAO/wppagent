"""
Rotas para histórico de clientes

Endpoints:
- GET /api/clients/{client_id}/history - Buscar histórico completo do cliente
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.database import User, Conversation, Message, Appointment, Service
from app.auth.middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clients", tags=["clients-history"])


@router.get("/{client_id}/history")
async def get_client_history(
    client_id: int,
    days: int = Query(default=90, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Buscar histórico completo de um cliente
    
    Retorna:
    - conversations: Lista de conversas com mensagens
    - appointments: Lista de agendamentos (passados e futuros)
    - timeline: Linha do tempo de ações
    - stats: Estatísticas do cliente
    """
    try:
        # 1. Buscar dados básicos do cliente
        stmt = select(User).where(User.id == client_id)
        result = await db.execute(stmt)
        client = result.scalar_one_or_none()
        
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Data de corte para histórico
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 2. Buscar conversas do cliente
        conversations_stmt = (
            select(
                Conversation.id,
                Conversation.created_at,
                Conversation.status,
                Conversation.first_response_at,
                func.count(Message.id).label('message_count')
            )
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .where(
                and_(
                    Conversation.user_id == client_id,
                    Conversation.created_at >= cutoff_date
                )
            )
            .group_by(Conversation.id)
            .order_by(desc(Conversation.created_at))
            .limit(50)
        )
        
        conversations_result = await db.execute(conversations_stmt)
        conversations_data = conversations_result.all()
        
        conversations = []
        for conv in conversations_data:
            # Buscar última mensagem de cada conversa
            last_msg_stmt = (
                select(Message.content, Message.direction)
                .where(Message.conversation_id == conv.id)
                .order_by(desc(Message.created_at))
                .limit(1)
            )
            last_msg_result = await db.execute(last_msg_stmt)
            last_msg = last_msg_result.first()
            
            conversations.append({
                'id': conv.id,
                'created_at': conv.created_at.isoformat() if conv.created_at else None,
                'status': conv.status,
                'message_count': conv.message_count or 0,
                'last_message': last_msg.content if last_msg else None,
                'last_message_direction': last_msg.direction if last_msg else None,
                'first_response_at': conv.first_response_at.isoformat() if conv.first_response_at else None
            })
        
        # 3. Buscar agendamentos do cliente
        appointments_stmt = (
            select(
                Appointment.id,
                Appointment.date_time,
                Appointment.status,
                Appointment.notes,
                Service.name.label('service_name'),
                Service.duration_minutes
            )
            .join(Service, Service.id == Appointment.service_id)
            .where(
                and_(
                    Appointment.user_id == client_id,
                    Appointment.created_at >= cutoff_date
                )
            )
            .order_by(desc(Appointment.date_time))
            .limit(50)
        )
        
        appointments_result = await db.execute(appointments_stmt)
        appointments_data = appointments_result.all()
        
        appointments = []
        for apt in appointments_data:
            appointments.append({
                'id': apt.id,
                'date_time': apt.date_time.isoformat() if apt.date_time else None,
                'status': apt.status,
                'service_name': apt.service_name,
                'duration_minutes': apt.duration_minutes,
                'notes': apt.notes
            })
        
        # 4. Criar timeline de eventos
        timeline = []
        
        # Adicionar eventos de cadastro
        timeline.append({
            'event': 'client_created',
            'description': f'Cliente cadastrado no sistema',
            'timestamp': client.created_at.isoformat() if client.created_at else None,
            'icon': 'user-plus',
            'color': 'blue'
        })
        
        # Adicionar eventos de conversas
        for conv in conversations[:10]:  # Últimas 10 conversas
            timeline.append({
                'event': 'conversation_started',
                'description': f'Conversa iniciada ({conv["message_count"]} mensagens)',
                'timestamp': conv['created_at'],
                'icon': 'message-circle',
                'color': 'green',
                'metadata': {'conversation_id': conv['id']}
            })
        
        # Adicionar eventos de agendamentos
        for apt in appointments[:10]:  # Últimos 10 agendamentos
            timeline.append({
                'event': 'appointment_scheduled',
                'description': f'Agendamento: {apt["service_name"]}',
                'timestamp': apt['date_time'],
                'icon': 'calendar',
                'color': 'purple',
                'metadata': {'appointment_id': apt['id'], 'status': apt['status']}
            })
        
        # Ordenar timeline por data (mais recente primeiro)
        timeline.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        # 5. Calcular estatísticas
        # Total de conversas
        total_conversations_stmt = select(func.count(Conversation.id)).where(
            Conversation.user_id == client_id
        )
        total_conversations_result = await db.execute(total_conversations_stmt)
        total_conversations = total_conversations_result.scalar() or 0
        
        # Total de mensagens
        total_messages_stmt = (
            select(func.count(Message.id))
            .join(Conversation, Conversation.id == Message.conversation_id)
            .where(Conversation.user_id == client_id)
        )
        total_messages_result = await db.execute(total_messages_stmt)
        total_messages = total_messages_result.scalar() or 0
        
        # Total de agendamentos
        total_appointments_stmt = select(func.count(Appointment.id)).where(
            Appointment.user_id == client_id
        )
        total_appointments_result = await db.execute(total_appointments_stmt)
        total_appointments = total_appointments_result.scalar() or 0
        
        # Agendamentos por status
        appointments_by_status_stmt = (
            select(
                Appointment.status,
                func.count(Appointment.id).label('count')
            )
            .where(Appointment.user_id == client_id)
            .group_by(Appointment.status)
        )
        appointments_by_status_result = await db.execute(appointments_by_status_stmt)
        appointments_by_status = {
            row.status: row.count 
            for row in appointments_by_status_result.all()
        }
        
        stats = {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'total_appointments': total_appointments,
            'appointments_by_status': appointments_by_status,
            'client_since': client.created_at.isoformat() if client.created_at else None,
            'last_interaction': conversations[0]['created_at'] if conversations else None
        }
        
        return {
            'success': True,
            'data': {
                'client': {
                    'id': client.id,
                    'full_name': client.nome,
                    'phone': client.telefone,
                    'email': client.email
                },
                'conversations': conversations,
                'appointments': appointments,
                'timeline': timeline[:20],  # Últimos 20 eventos
                'stats': stats
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar histórico do cliente {client_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar histórico: {str(e)}"
        )

