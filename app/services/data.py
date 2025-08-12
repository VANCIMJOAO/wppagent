"""
Serviços de dados para operações no banco
"""
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func
from sqlalchemy.orm import selectinload
from app.models.database import User, Conversation, Message, Appointment, MetaLog, Business, Service
from app.utils.logger import get_logger
import logging
logger = get_logger(__name__)

logger = logging.getLogger(__name__)


class UserService:
    """Serviço para operações com usuários"""
    
    @staticmethod
    async def get_or_create_user(db: AsyncSession, wa_id: str, 
                               nome: str = None, telefone: str = None) -> User:
        """
        Obtém usuário existente ou cria novo
        
        Args:
            db: Sessão do banco
            wa_id: ID do WhatsApp
            nome: Nome do usuário
            telefone: Telefone do usuário
            
        Returns:
            Instância do usuário
        """
        # Buscar usuário existente
        result = await db.execute(select(User).where(User.wa_id == wa_id))
        user = result.scalar_one_or_none()
        
        if not user:
            # Criar novo usuário
            user = User(
                wa_id=wa_id,
                nome=nome,
                telefone=telefone
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Novo usuário criado: {wa_id}")
        
        return user
    
    @staticmethod
    async def update_user_info(db: AsyncSession, user_id: int, **kwargs) -> User:
        """Atualiza informações do usuário"""
        await db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        await db.commit()
        
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one()


class ConversationService:
    """Serviço para operações com conversas"""
    
    @staticmethod
    async def get_or_create_conversation(db: AsyncSession, user_id: int) -> Conversation:
        """
        Obtém conversa ativa ou cria nova
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            
        Returns:
            Instância da conversa
        """
        # Buscar conversa ativa
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.status.in_(["active", "human"]))
            .order_by(desc(Conversation.created_at))
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            # Criar nova conversa
            conversation = Conversation(
                user_id=user_id,
                status="active"
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    async def update_conversation_status(db: AsyncSession, conversation_id: int, 
                                       status: str) -> Conversation:
        """Atualiza status da conversa"""
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(status=status, last_message_at=datetime.utcnow())
        )
        await db.commit()
        
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one()
    
    @staticmethod
    async def get_conversations_for_dashboard(db: AsyncSession, 
                                            limit: int = 50) -> List[Dict]:
        """
        Obtém conversas para exibição no dashboard
        
        Args:
            db: Sessão do banco
            limit: Limite de conversas
            
        Returns:
            Lista de conversas com informações do usuário
        """
        result = await db.execute(
            select(Conversation, User)
            .join(User)
            .options(selectinload(Conversation.messages))
            .order_by(desc(Conversation.last_message_at))
            .limit(limit)
        )
        
        conversations = []
        for conversation, user in result.all():
            # Contar mensagens não lidas (simulado - em produção seria mais complexo)
            unread_count = len([m for m in conversation.messages if m.direction == "in"])
            
            conversations.append({
                "id": conversation.id,
                "user": {
                    "id": user.id,
                    "nome": user.nome or user.wa_id,
                    "telefone": user.telefone,
                    "wa_id": user.wa_id
                },
                "status": conversation.status,
                "last_message_at": conversation.last_message_at,
                "unread_count": unread_count,
                "message_count": len(conversation.messages)
            })
        
        return conversations


class MessageService:
    """Serviço para operações com mensagens"""
    
    @staticmethod
    async def create_message(db: AsyncSession, user_id: int, conversation_id: int,
                           direction: str, content: str, message_type: str = "text",
                           message_id: str = None, raw_payload: Dict = None, 
                           metadata: Dict = None) -> Message:
        """
        Cria nova mensagem
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            conversation_id: ID da conversa
            direction: 'in' ou 'out'
            content: Conteúdo da mensagem
            message_type: Tipo da mensagem
            message_id: ID da mensagem no WhatsApp
            raw_payload: Payload bruto da API
            metadata: Metadados adicionais
            
        Returns:
            Instância da mensagem
        """
        # Combinar raw_payload com metadata se ambos existirem
        final_payload = raw_payload or {}
        if metadata:
            final_payload.update({"metadata": metadata})
        
        message = Message(
            user_id=user_id,
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            message_type=message_type,
            message_id=message_id,
            raw_payload=final_payload if final_payload else None
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        # Atualizar timestamp da conversa
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(last_message_at=datetime.utcnow())
        )
        await db.commit()
        
        return message
    
    @staticmethod
    async def get_conversation_history(db: AsyncSession, conversation_id: int,
                                     limit: int = 20) -> List[Message]:
        """
        Obtém histórico da conversa
        
        Args:
            db: Sessão do banco
            conversation_id: ID da conversa
            limit: Limite de mensagens
            
        Returns:
            Lista de mensagens ordenadas por data
        """
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        
        return result.scalars().all()


class AppointmentService:
    """Serviço para operações com agendamentos"""
    
    @staticmethod
    async def create_appointment(db: AsyncSession, user_id: int, 
                               service: str = None, service_id: int = None,
                               date_time: datetime = None, 
                               appointment_date: str = None,
                               notes: str = None, status: str = "pendente") -> Appointment:
        """
        Cria novo agendamento
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            service: Nome do serviço (para busca)
            service_id: ID direto do serviço
            date_time: Data e hora do agendamento
            appointment_date: Data como string (alternativa)
            notes: Observações
            status: Status inicial
            
        Returns:
            Instância do agendamento
        """
        try:
            # Obter ou criar business padrão
            business_result = await db.execute(select(Business).limit(1))
            business = business_result.scalar_one_or_none()
            
            if not business:
                # Criar business padrão
                business = Business(
                    name="Negócio Principal",
                    created_at=datetime.now()
                )
                db.add(business)
                await db.flush()
                logger.info("Business padrão criado")
            
            # Obter service_id se não fornecido
            if not service_id and service:
                service_result = await db.execute(
                    select(Service).where(Service.name.ilike(f"%{service}%")).limit(1)
                )
                service_obj = service_result.scalar_one_or_none()
                
                if not service_obj:
                    # Criar serviço padrão
                    service_obj = Service(
                        business_id=business.id,
                        name=service,
                        price="R$ 50,00",
                        duration_minutes=60,
                        created_at=datetime.now()
                    )
                    db.add(service_obj)
                    await db.flush()
                    logger.info(f"Serviço '{service}' criado automaticamente")
                
                service_id = service_obj.id
            
            # Processar data/hora
            if not date_time and appointment_date:
                try:
                    # Tentar diferentes formatos de data
                    formats = [
                        "%Y-%m-%d %H:%M",
                        "%d/%m/%Y %H:%M", 
                        "%Y-%m-%d %H:%M:%S",
                        "%d/%m/%Y às %H:%M"
                    ]
                    
                    for fmt in formats:
                        try:
                            date_time = datetime.strptime(appointment_date, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not date_time:
                        # Fallback: usar data atual + 1 dia
                        from datetime import timedelta
                        date_time = datetime.now() + timedelta(days=1)
                        date_time = date_time.replace(hour=14, minute=0, second=0, microsecond=0)
                        logger.warning(f"Não foi possível parsear data '{appointment_date}', usando fallback")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar data: {e}")
                    date_time = datetime.now() + timedelta(days=1)
            
            if not date_time:
                from datetime import timedelta
                date_time = datetime.now() + timedelta(days=1)
                date_time = date_time.replace(hour=14, minute=0, second=0, microsecond=0)
            
            # Calcular end_time baseado na duração do serviço
            end_time = date_time
            if service_id:
                service_result = await db.execute(select(Service).where(Service.id == service_id))
                service_obj = service_result.scalar_one_or_none()
                if service_obj and service_obj.duration_minutes:
                    from datetime import timedelta
                    end_time = date_time + timedelta(minutes=service_obj.duration_minutes)
            
            # Criar agendamento
            appointment = Appointment(
                user_id=user_id,
                business_id=business.id,
                service_id=service_id,
                date_time=date_time,
                end_time=end_time,
                status=status,
                notes=notes,
                created_at=datetime.now()
            )
            
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            
            logger.info(f"Agendamento criado: ID={appointment.id}, User={user_id}, Service={service_id}, DateTime={date_time}")
            return appointment
            
        except Exception as e:
            logger.error(f"Erro ao criar agendamento: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def update_appointment_status(db: AsyncSession, appointment_id: int,
                                      status: str) -> Optional[Appointment]:
        """
        Atualiza status do agendamento
        
        Args:
            db: Sessão do banco
            appointment_id: ID do agendamento
            status: Novo status
            
        Returns:
            Agendamento atualizado ou None se não encontrado
        """
        result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        appointment = result.scalar_one_or_none()
        
        if appointment:
            await db.execute(
                update(Appointment)
                .where(Appointment.id == appointment_id)
                .values(status=status, updated_at=datetime.now())
            )
            await db.commit()
            await db.refresh(appointment)
        
        return appointment
    
    @staticmethod
    async def confirm_appointment(db: AsyncSession, appointment_id: int, 
                                confirmed_by: str = "customer") -> Optional[Appointment]:
        """
        Confirma um agendamento
        
        Args:
            db: Sessão do banco
            appointment_id: ID do agendamento
            confirmed_by: Quem confirmou ('customer', 'admin', 'auto')
            
        Returns:
            Agendamento confirmado ou None se não encontrado
        """
        try:
            result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
            appointment = result.scalar_one_or_none()
            
            if appointment:
                await db.execute(
                    update(Appointment)
                    .where(Appointment.id == appointment_id)
                    .values(
                        status="confirmado",
                        confirmed_at=datetime.now(),
                        confirmed_by=confirmed_by,
                        updated_at=datetime.now()
                    )
                )
                await db.commit()
                await db.refresh(appointment)
                logger.info(f"Agendamento {appointment_id} confirmado por {confirmed_by}")
                return appointment
            else:
                logger.warning(f"Agendamento {appointment_id} não encontrado para confirmação")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao confirmar agendamento {appointment_id}: {e}")
            await db.rollback()
            return None
    
    @staticmethod
    async def cancel_appointment(db: AsyncSession, appointment_id: int, 
                               reason: str = "Cancelado pelo cliente",
                               cancelled_by: str = "customer") -> Optional[Appointment]:
        """
        Cancela um agendamento
        
        Args:
            db: Sessão do banco
            appointment_id: ID do agendamento
            reason: Motivo do cancelamento
            cancelled_by: Quem cancelou ('customer', 'admin', 'system')
            
        Returns:
            Agendamento cancelado ou None se não encontrado
        """
        try:
            result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
            appointment = result.scalar_one_or_none()
            
            if appointment:
                await db.execute(
                    update(Appointment)
                    .where(Appointment.id == appointment_id)
                    .values(
                        status="cancelado",
                        cancelled_at=datetime.now(),
                        cancellation_reason=reason,
                        cancelled_by=cancelled_by,
                        updated_at=datetime.now()
                    )
                )
                await db.commit()
                await db.refresh(appointment)
                logger.info(f"Agendamento {appointment_id} cancelado por {cancelled_by}: {reason}")
                return appointment
            else:
                logger.warning(f"Agendamento {appointment_id} não encontrado para cancelamento")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao cancelar agendamento {appointment_id}: {e}")
            await db.rollback()
            return None
    
    @staticmethod
    async def reschedule_appointment(db: AsyncSession, appointment_id: int,
                                   new_date_time: datetime) -> Optional[Appointment]:
        """
        Reagenda um agendamento
        
        Args:
            db: Sessão do banco
            appointment_id: ID do agendamento
            new_date_time: Nova data e hora
            
        Returns:
            Agendamento reagendado ou None se não encontrado
        """
        try:
            result = await db.execute(
                select(Appointment, Service)
                .join(Service, Appointment.service_id == Service.id)
                .where(Appointment.id == appointment_id)
            )
            appointment_service = result.first()
            
            if appointment_service:
                appointment, service = appointment_service
                
                # Calcular novo end_time
                from datetime import timedelta
                new_end_time = new_date_time + timedelta(minutes=service.duration_minutes)
                
                await db.execute(
                    update(Appointment)
                    .where(Appointment.id == appointment_id)
                    .values(
                        date_time=new_date_time,
                        end_time=new_end_time,
                        status="reagendado",
                        updated_at=datetime.now()
                    )
                )
                await db.commit()
                await db.refresh(appointment)
                logger.info(f"Agendamento {appointment_id} reagendado para {new_date_time}")
                return appointment
            else:
                logger.warning(f"Agendamento {appointment_id} não encontrado para reagendamento")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao reagendar agendamento {appointment_id}: {e}")
            await db.rollback()
            return None
    
    @staticmethod
    async def get_appointment_by_id(db: AsyncSession, appointment_id: int) -> Optional[Appointment]:
        """
        Obtém agendamento por ID
        
        Args:
            db: Sessão do banco
            appointment_id: ID do agendamento
            
        Returns:
            Agendamento ou None se não encontrado
        """
        result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_appointments(db: AsyncSession, user_id: int,
                                  status: str = None) -> List[Appointment]:
        """
        Obtém agendamentos do usuário
        
        Args:
            db: Sessão do banco
            user_id: ID do usuário
            status: Filtrar por status (opcional)
            
        Returns:
            Lista de agendamentos
        """
        query = select(Appointment).where(Appointment.user_id == user_id)
        
        if status:
            query = query.where(Appointment.status == status)
        
        query = query.order_by(desc(Appointment.date_time))
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_all_appointments(db: AsyncSession, limit: int = 100) -> List[Dict]:
        """
        Obtém todos os agendamentos para dashboard
        
        Args:
            db: Sessão do banco
            limit: Limite de registros
            
        Returns:
            Lista de agendamentos com informações do usuário e serviço
        """
        result = await db.execute(
            select(Appointment, User, Service)
            .join(User, Appointment.user_id == User.id)
            .join(Service, Appointment.service_id == Service.id)
            .order_by(desc(Appointment.created_at))
            .limit(limit)
        )
        
        appointments = []
        for appointment, user, service in result.all():
            appointments.append({
                "id": appointment.id,
                "user": {
                    "id": user.id,
                    "nome": user.nome or user.wa_id,
                    "telefone": user.telefone
                },
                "service": {
                    "id": service.id,
                    "name": service.name,
                    "price": service.price,
                    "duration": service.duration_minutes
                },
                "date_time": appointment.date_time,
                "end_time": appointment.end_time,
                "status": appointment.status,
                "notes": appointment.notes,
                "price_at_booking": appointment.price_at_booking,
                "created_at": appointment.created_at
            })
        
        return appointments


class MetricsService:
    """Serviço para métricas do dashboard"""
    
    @staticmethod
    async def get_dashboard_metrics(db: AsyncSession) -> Dict:
        """
        Obtém métricas para o dashboard
        
        Returns:
            Dicionário com métricas
        """
        # Total de usuários
        total_users = await db.scalar(select(func.count(User.id)))
        
        # Total de conversas
        total_conversations = await db.scalar(select(func.count(Conversation.id)))
        
        # Total de mensagens hoje
        today = datetime.utcnow().date()
        messages_today = await db.scalar(
            select(func.count(Message.id))
            .where(func.date(Message.created_at) == today)
        )
        
        # Agendamentos pendentes
        pending_appointments = await db.scalar(
            select(func.count(Appointment.id))
            .where(Appointment.status == "pendente")
        )
        
        # Conversas que precisam de atenção humana
        human_conversations = await db.scalar(
            select(func.count(Conversation.id))
            .where(Conversation.status == "human")
        )
        
        return {
            "total_users": total_users or 0,
            "total_conversations": total_conversations or 0,
            "messages_today": messages_today or 0,
            "pending_appointments": pending_appointments or 0,
            "human_conversations": human_conversations or 0
        }
