"""
Serviço de queries otimizadas para evitar problemas N+1
Versão 2 - Implementação melhorada
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload, joinedload
from app.models.database import (
    Conversation, User, Message, Appointment, 
    Business, Service, MetaLog, WebhookLog
)
import time
from structlog import get_logger

logger = get_logger(__name__)

class OptimizedQueriesV2:
    """Classe com queries otimizadas para evitar N+1"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_conversations_with_users_and_messages(
        self, 
        limit: int = 50, 
        offset: int = 0,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query otimizada para conversações com usuários e contagem de mensagens
        Evita N+1 usando JOIN e GROUP BY
        """
        start_time = time.time()
        
        # Query principal com JOIN e GROUP BY
        query = (
            select(
                Conversation,
                User,
                func.count(Message.id).label('message_count'),
                func.max(Message.timestamp).label('last_message_time')
            )
            .join(User, Conversation.user_id == User.id)
            .outerjoin(Message, Conversation.id == Message.conversation_id)
        )
        
        # Filtro por usuário se especificado
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        
        query = (
            query
            .group_by(Conversation.id, User.id)
            .order_by(desc('last_message_time'))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        # Construir resultado
        conversations = []
        for conv, user, msg_count, last_msg_time in rows:
            conversations.append({
                "id": conv.id,
                "user": {
                    "id": user.id,
                    "nome": user.nome,
                    "telefone": user.telefone,
                    "email": user.email
                },
                "message_count": msg_count or 0,
                "last_message_time": last_msg_time,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            })
        
        execution_time = time.time() - start_time
        logger.info(f"Query conversações executada em {execution_time:.3f}s", 
                   count=len(conversations), limit=limit, offset=offset)
        
        return conversations
    
    async def get_appointments_with_users_and_services(
        self,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query otimizada para agendamentos com usuários e serviços
        """
        start_time = time.time()
        
        # Query principal
        query = (
            select(Appointment, User, Business, Service)
            .join(User, Appointment.user_id == User.id)
            .outerjoin(Business, Appointment.business_id == Business.id)
            .outerjoin(Service, Appointment.service_id == Service.id)
        )
        
        # Filtros
        conditions = []
        if user_id:
            conditions.append(Appointment.user_id == user_id)
        if date_from:
            conditions.append(Appointment.date_time >= date_from)
        if date_to:
            conditions.append(Appointment.date_time <= date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = (
            query
            .order_by(desc(Appointment.date_time))
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        # Construir resultado
        appointments = []
        for apt, user, business, service in rows:
            appointments.append({
                "id": apt.id,
                "user": {
                    "id": user.id,
                    "nome": user.nome,
                    "telefone": user.telefone,
                    "email": user.email
                },
                "business": {
                    "id": business.id if business else None,
                    "name": business.name if business else None
                } if business else None,
                "service": {
                    "id": service.id if service else None,
                    "name": service.name if service else None,
                    "price": service.price if service else None
                } if service else None,
                "date_time": apt.date_time,
                "status": apt.status,
                "notes": apt.notes,
                "created_at": apt.created_at,
                "updated_at": apt.updated_at
            })
        
        execution_time = time.time() - start_time
        logger.info(f"Query agendamentos executada em {execution_time:.3f}s",
                   count=len(appointments), limit=limit, offset=offset)
        
        return appointments
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Query otimizada para estatísticas de usuários
        """
        start_time = time.time()
        
        # Query com múltiplas agregações
        query = (
            select(
                func.count(User.id).label('total_users'),
                func.count(Conversation.id).label('total_conversations'),
                func.count(Appointment.id).label('total_appointments'),
                func.count(
                    func.distinct(Conversation.user_id)
                ).label('active_users')
            )
            .select_from(User)
            .outerjoin(Conversation, User.id == Conversation.user_id)
            .outerjoin(Appointment, User.id == Appointment.user_id)
        )
        
        result = await self.session.execute(query)
        row = result.first()
        
        stats = {
            "total_users": row.total_users or 0,
            "total_conversations": row.total_conversations or 0,
            "total_appointments": row.total_appointments or 0,
            "active_users": row.active_users or 0
        }
        
        execution_time = time.time() - start_time
        logger.info(f"Query estatísticas executada em {execution_time:.3f}s", **stats)
        
        return stats
    
    async def get_recent_activity(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Query otimizada para atividade recente
        Combina conversações, agendamentos e logs
        """
        start_time = time.time()
        
        # Query para conversações recentes
        recent_conversations = (
            select(
                Conversation.id.label('id'),
                Conversation.created_at.label('timestamp'),
                func.literal('conversation').label('type'),
                User.nome.label('description')
            )
            .join(User, Conversation.user_id == User.id)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        
        # Query para agendamentos recentes
        recent_appointments = (
            select(
                Appointment.id.label('id'),
                Appointment.created_at.label('timestamp'),
                func.literal('appointment').label('type'),
                func.concat('Agendamento: ', User.nome).label('description')
            )
            .join(User, Appointment.user_id == User.id)
            .order_by(desc(Appointment.created_at))
            .limit(limit)
        )
        
        # Executar queries
        conv_result = await self.session.execute(recent_conversations)
        apt_result = await self.session.execute(recent_appointments)
        
        # Combinar resultados
        activities = []
        
        for row in conv_result:
            activities.append({
                "id": row.id,
                "type": row.type,
                "description": f"Nova conversa com {row.description}",
                "timestamp": row.timestamp
            })
        
        for row in apt_result:
            activities.append({
                "id": row.id,
                "type": row.type,
                "description": row.description,
                "timestamp": row.timestamp
            })
        
        # Ordenar por timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        activities = activities[:limit]
        
        execution_time = time.time() - start_time
        logger.info(f"Query atividade recente executada em {execution_time:.3f}s",
                   count=len(activities))
        
        return activities
