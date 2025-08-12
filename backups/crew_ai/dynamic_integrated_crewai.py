"""
Sistema Integrado CrewAI Dinâmico para WhatsApp Agent
Versão completamente baseada em banco de dados
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import (
    User, Conversation, Message, ConversationContext as DBConversationContext,
    CompanyInfo, Service, Appointment
)
from app.services.dynamic_data_collection import DynamicDataCollectionService
from app.services.dynamic_scheduling import DynamicSchedulingService

logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    """Estado atual da conversa"""
    state: str
    user_complete: bool
    missing_data: List[str]
    awaiting_response_for: Optional[str]
    temp_data: Dict


class DynamicIntegratedCrewAIService:
    """Serviço integrado dinâmico baseado em banco de dados"""
    
    def __init__(self, business_id: int = 1):
        self.business_id = business_id
    
    async def process_message(self, message: str, context: Dict, db_session: AsyncSession) -> str:
        """Processar mensagem com sistema dinâmico completo"""
        try:
            # Inicializar serviços dinâmicos
            data_service = DynamicDataCollectionService(db_session, self.business_id)
            scheduling_service = DynamicSchedulingService(db_session, self.business_id)
            
            # Obter ou criar usuário
            user = await self._get_or_create_user(
                context.get('customer_phone', '').replace('+', ''),
                context.get('customer_name'),
                db_session
            )
            
            # Obter ou criar conversa
            conversation = await self._get_or_create_conversation(user.id, db_session)
            
            # Salvar mensagem recebida
            await self._save_message(user.id, conversation.id, message, "in", db_session)
            
            # Obter contexto da conversa
            conv_context = await self._get_conversation_context(conversation.id, db_session)
            
            # Verificar completude dos dados do usuário
            data_completeness = await data_service.check_user_data_completeness(user.id)
            
            # Determinar resposta baseada no estado da conversa
            response = await self._determine_response(
                message, user, conv_context, data_completeness, 
                data_service, scheduling_service, db_session
            )
            
            # Salvar resposta
            await self._save_message(user.id, conversation.id, response, "out", db_session)
            
            # Atualizar contexto da conversa
            await self._update_conversation_context(conv_context, message, response, db_session)
            
            return response
            
        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {e}")
            return "Desculpe, ocorreu um erro. Tente novamente em alguns instantes."
    
    async def _get_or_create_user(self, wa_id: str, name: Optional[str], db_session: AsyncSession) -> User:
        """Obter ou criar usuário"""
        result = await db_session.execute(
            select(User).where(User.wa_id == wa_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                wa_id=wa_id,
                nome=name,
                telefone=wa_id if wa_id.isdigit() else None
            )
            db_session.add(user)
            await db_session.flush()
        
        return user
    
    async def _get_or_create_conversation(self, user_id: int, db_session: AsyncSession) -> Conversation:
        """Obter ou criar conversa ativa"""
        result = await db_session.execute(
            select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.status == "active"
            ).order_by(Conversation.created_at.desc())
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            conversation = Conversation(
                user_id=user_id,
                status="active"
            )
            db_session.add(conversation)
            await db_session.flush()
        
        return conversation
    
    async def _save_message(self, user_id: int, conversation_id: int, content: str, 
                           direction: str, db_session: AsyncSession) -> Message:
        """Salvar mensagem no banco"""
        message = Message(
            user_id=user_id,
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            message_type="text"
        )
        db_session.add(message)
        await db_session.flush()
        return message
    
    async def _get_conversation_context(self, conversation_id: int, db_session: AsyncSession) -> DBConversationContext:
        """Obter contexto da conversa"""
        result = await db_session.execute(
            select(DBConversationContext).where(
                DBConversationContext.conversation_id == conversation_id
            )
        )
        context = result.scalar_one_or_none()
        
        if not context:
            context = DBConversationContext(
                conversation_id=conversation_id,
                current_state="initial",
                temp_data={},
                collected_data={}
            )
            db_session.add(context)
            await db_session.flush()
        
        return context
    
    async def _determine_response(self, message: str, user: User, context: DBConversationContext,
                                 data_completeness: Dict, data_service: DynamicDataCollectionService,
                                 scheduling_service: DynamicSchedulingService, 
                                 db_session: AsyncSession) -> str:
        """Determinar resposta baseada no estado atual"""
        
        message_lower = message.lower().strip()
        
        # 1. Se dados do usuário estão incompletos, priorizar coleta
        if not data_completeness["complete"] and context.current_state != "collecting_data":
            return await self._handle_data_collection(
                user.id, data_completeness["missing"][0], data_service, context, db_session
            )
        
        # 2. Se estamos no meio da coleta de dados
        if context.current_state == "collecting_data" and context.awaiting_response_for:
            return await self._handle_data_response(
                message, user.id, context.awaiting_response_for, 
                data_service, context, db_session
            )
        
        # 3. Classificar intenção da mensagem
        intent = await self._classify_intent(message_lower)
        
        # 4. Responder baseado na intenção
        if intent == "greeting":
            return await self._handle_greeting(user, data_service)
        
        elif intent == "information":
            return await self._handle_information_request(message_lower, scheduling_service, db_session)
        
        elif intent == "scheduling":
            return await self._handle_scheduling_request(
                message, user, context, scheduling_service, db_session
            )
        
        elif intent == "appointment_status":
            return await self._handle_appointment_status(user.id, scheduling_service)
        
        elif intent == "complaint":
            return await self._handle_complaint(message)
        
        else:
            return await self._handle_general_inquiry(message, scheduling_service)
    
    async def _classify_intent(self, message: str) -> str:
        """Classificar intenção da mensagem"""
        # Palavras-chave para classificação (pode ser expandido com ML no futuro)
        intents = {
            "greeting": ["oi", "olá", "bom dia", "boa tarde", "boa noite", "hello", "hi"],
            "information": ["preço", "valor", "custa", "serviço", "horário", "funcionamento", "trabalha", "abre", "fecha"],
            "scheduling": ["agendar", "marcar", "reservar", "horário", "quando", "disponível", "vaga"],
            "appointment_status": ["meu agendamento", "minha consulta", "cancelar", "reagendar", "confirmar"],
            "complaint": ["problema", "reclamação", "insatisfeito", "ruim", "péssimo", "demora"]
        }
        
        for intent, keywords in intents.items():
            if any(keyword in message for keyword in keywords):
                return intent
        
        return "general"
    
    async def _handle_data_collection(self, user_id: int, missing_field: str, 
                                     data_service: DynamicDataCollectionService,
                                     context: DBConversationContext, db_session: AsyncSession) -> str:
        """Iniciar coleta de dados faltantes"""
        # Atualizar contexto
        context.current_state = "collecting_data"
        context.awaiting_response = True
        context.awaiting_response_for = missing_field
        await db_session.commit()
        
        return await data_service.request_missing_data(user_id, missing_field)
    
    async def _handle_data_response(self, message: str, user_id: int, field: str,
                                   data_service: DynamicDataCollectionService,
                                   context: DBConversationContext, db_session: AsyncSession) -> str:
        """Processar resposta de coleta de dados"""
        success, result_message = await data_service.validate_and_save_data(user_id, field, message)
        
        if success:
            # Limpar estado de coleta
            context.awaiting_response = False
            context.awaiting_response_for = None
            
            # Verificar se ainda há dados faltantes
            data_completeness = await data_service.check_user_data_completeness(user_id)
            
            if data_completeness["complete"]:
                context.current_state = "initial"
                await db_session.commit()
                
                welcome_msg = await data_service.get_welcome_message(
                    data_completeness["user"].nome
                )
                return f"✅ Obrigado! Seus dados foram salvos.\n\n{welcome_msg}"
            else:
                # Ainda há dados faltantes, continuar coleta
                next_field = data_completeness["missing"][0]
                context.awaiting_response_for = next_field
                await db_session.commit()
                
                return f"✅ Obrigado!\n\n{await data_service.request_missing_data(user_id, next_field)}"
        else:
            # Erro na validação, tentar novamente
            return f"❌ {result_message}\n\nTente novamente:"
    
    async def _handle_greeting(self, user: User, data_service: DynamicDataCollectionService) -> str:
        """Lidar com saudações"""
        welcome_msg = await data_service.get_welcome_message(user.nome)
        return welcome_msg
    
    async def _handle_information_request(self, message: str, scheduling_service: DynamicSchedulingService,
                                         db_session: AsyncSession) -> str:
        """Lidar com solicitações de informação"""
        if any(word in message for word in ["preço", "valor", "custa", "serviço"]):
            return await self._get_services_info(db_session)
        
        elif any(word in message for word in ["horário", "funcionamento", "abre", "fecha"]):
            return await scheduling_service.get_business_hours_formatted()
        
        else:
            return await self._get_general_info(db_session)
    
    async def _get_services_info(self, db_session: AsyncSession) -> str:
        """Obter informações dos serviços da database"""
        from app.services.business_data import business_data_service
        
        try:
            # Buscar serviços reais da database
            services = await business_data_service.get_active_services(refresh_cache=True)
            
            if not services:
                return "No momento não temos serviços cadastrados. Entre em contato conosco!"
            
            services_info = "📋 *Nossos Serviços e Preços:*\n\n"
            for service in services:
                services_info += f"• *{service['name']}*: {service['price']}"
                if service['duration_minutes']:
                    services_info += f" - {service['duration_minutes']}min"
                services_info += "\n"
            
            services_info += "\n📞 Para agendar, me informe:\n"
            services_info += "- Qual serviço deseja\n"
            services_info += "- Data preferida\n"
            services_info += "- Horário desejado"
            
            return services_info
            
        except Exception as e:
            logger.error(f"Erro ao buscar serviços da database: {e}")
            # Fallback para mensagem genérica
            return "Oferecemos diversos serviços! Entre em contato para mais informações sobre preços e horários."
    
    async def _get_active_services(self, db_session: AsyncSession) -> List[Service]:
        """Obter serviços ativos do banco"""
        result = await db_session.execute(
            select(Service).where(
                Service.business_id == self.business_id,
                Service.is_active == True
            ).order_by(Service.name)
        )
        return result.scalars().all()
    
    async def _get_general_info(self, db_session: AsyncSession) -> str:
        """Obter informações gerais da empresa"""
        result = await db_session.execute(
            select(CompanyInfo).where(CompanyInfo.business_id == self.business_id)
        )
        company_info = result.scalar_one_or_none()
        
        if company_info:
            info = f"🏢 *{company_info.company_name}*\n\n"
            if company_info.slogan:
                info += f"_{company_info.slogan}_\n\n"
            if company_info.about_us:
                info += f"{company_info.about_us}\n\n"
            
            info += "📱 Entre em contato conosco ou faça seu agendamento!"
            return info
        
        return "Somos uma empresa especializada em oferecer os melhores serviços! Como posso ajudá-lo?"
    
    async def _handle_scheduling_request(self, message: str, user: User, context: DBConversationContext,
                                        scheduling_service: DynamicSchedulingService, 
                                        db_session: AsyncSession) -> str:
        """Lidar com solicitações de agendamento"""
        # Simplificado - implementação completa requereria análise mais sofisticada da mensagem
        services = await self._get_active_services(db_session)
        
        if not services:
            return "Desculpe, no momento não temos serviços disponíveis para agendamento."
        
        services_list = "\n".join([f"{i+1}. {s.name} - {s.price} ({s.duration_minutes}min)" 
                                  for i, s in enumerate(services)])
        
        return f"📅 *Vamos fazer seu agendamento!*\n\nEscolha o serviço desejado:\n\n{services_list}\n\nResponda com o número do serviço desejado."
    
    async def _handle_appointment_status(self, user_id: int, scheduling_service: DynamicSchedulingService) -> str:
        """Lidar com consultas sobre agendamentos"""
        appointments = await scheduling_service.get_user_appointments(user_id)
        
        if not appointments:
            return "Você não possui agendamentos ativos. Gostaria de fazer um novo agendamento?"
        
        response = "📅 *Seus Agendamentos:*\n\n"
        for app in appointments[:3]:  # Mostrar apenas os 3 próximos
            service_name = "Serviço" # Seria necessário join com Service
            response += f"• {app.date_time.strftime('%d/%m/%Y às %H:%M')} - {service_name}\n"
            response += f"  Status: {app.status.title()}\n\n"
        
        return response
    
    async def _handle_complaint(self, message: str) -> str:
        """Lidar com reclamações"""
        return ("😔 Lamento que tenha tido uma experiência ruim.\n\n"
                "Sua opinião é muito importante para nós. "
                "Um de nossos atendentes entrará em contato em breve para resolver sua situação.\n\n"
                "Obrigado pela paciência!")
    
    async def _handle_general_inquiry(self, message: str, scheduling_service: DynamicSchedulingService) -> str:
        """Lidar com consultas gerais"""
        return ("Obrigado pela sua mensagem! 😊\n\n"
                "Posso ajudá-lo com:\n"
                "📋 Informações sobre serviços e preços\n"
                "🕒 Horários de funcionamento\n"
                "📅 Agendamentos\n"
                "❓ Outras dúvidas\n\n"
                f"{await scheduling_service.get_business_hours_formatted()}")
    
    async def _update_conversation_context(self, context: DBConversationContext, 
                                          user_message: str, bot_response: str, 
                                          db_session: AsyncSession):
        """Atualizar contexto da conversa"""
        context.last_interaction_at = datetime.utcnow()
        
        # Atualizar dados temporários se necessário
        if context.temp_data is None:
            context.temp_data = {}
        
        # Adicionar à história da conversa (limitada)
        if "recent_messages" not in context.temp_data:
            context.temp_data["recent_messages"] = []
        
        context.temp_data["recent_messages"].append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Manter apenas as últimas 10 mensagens
        if len(context.temp_data["recent_messages"]) > 10:
            context.temp_data["recent_messages"] = context.temp_data["recent_messages"][-10:]
        
        await db_session.commit()
