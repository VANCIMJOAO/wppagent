"""
Serviço dinâmico para coleta de dados do cliente
"""
import re
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.database import (
    User, CustomerDataCollection, BotConfiguration, 
    MessageTemplate, ConversationContext, Conversation
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DynamicDataCollectionService:
    """Serviço para coleta dinâmica de dados do cliente baseado em configurações do banco"""
    
    def __init__(self, db_session: AsyncSession, business_id: int = 1):
        self.db_session = db_session
        self.business_id = business_id
    
    async def get_bot_config(self) -> Optional[BotConfiguration]:
        """Obter configurações do bot"""
        result = await self.db_session.execute(
            select(BotConfiguration).where(BotConfiguration.business_id == self.business_id)
        )
        return result.scalar_one_or_none()
    
    async def get_message_template(self, template_key: str) -> Optional[str]:
        """Obter template de mensagem"""
        result = await self.db_session.execute(
            select(MessageTemplate).where(
                MessageTemplate.business_id == self.business_id,
                MessageTemplate.template_key == template_key,
                MessageTemplate.is_active == True
            )
        )
        template = result.scalar_one_or_none()
        return template.template_content if template else None
    
    async def get_or_create_data_collection(self, user_id: int) -> CustomerDataCollection:
        """Obter ou criar registro de coleta de dados"""
        result = await self.db_session.execute(
            select(CustomerDataCollection).where(CustomerDataCollection.user_id == user_id)
        )
        data_collection = result.scalar_one_or_none()
        
        if not data_collection:
            data_collection = CustomerDataCollection(
                user_id=user_id,
                collection_method="whatsapp"
            )
            self.db_session.add(data_collection)
            await self.db_session.flush()
        
        return data_collection
    
    async def check_user_data_completeness(self, user_id: int) -> Dict[str, Any]:
        """Verificar completude dos dados do usuário"""
        # Obter usuário
        result = await self.db_session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {"complete": False, "missing": ["user_not_found"]}
        
        # Obter configurações do bot
        bot_config = await self.get_bot_config()
        if not bot_config:
            # Usar configurações padrão se não houver no banco
            bot_config = BotConfiguration(
                require_full_name=True,
                require_email=True,
                require_phone_confirmation=False
            )
        
        missing_data = []
        
        # Verificar nome
        if bot_config.require_full_name and not user.nome:
            missing_data.append("name")
        
        # Verificar email  
        if bot_config.require_email and not user.email:
            missing_data.append("email")
        
        # Verificar telefone (se requerido)
        if bot_config.require_phone_confirmation and not user.telefone:
            missing_data.append("phone")
        
        return {
            "complete": len(missing_data) == 0,
            "missing": missing_data,
            "user": user,
            "config": bot_config
        }
    
    async def request_missing_data(self, user_id: int, missing_field: str) -> str:
        """Solicitar dados faltantes com templates dinâmicos"""
        # Obter template apropriado
        template_key = f"data_collection_{missing_field}"
        template = await self.get_message_template(template_key)
        
        # Fallback para mensagens padrão
        fallback_messages = {
            "name": "Para continuar, preciso do seu nome completo. Por favor, me informe como gostaria de ser chamado(a):",
            "email": "Agora preciso do seu email para enviar a confirmação. Por favor, digite seu email:",
            "phone": "Para finalizar, confirme seu número de telefone:"
        }
        
        message = template or fallback_messages.get(missing_field, "Por favor, forneça a informação solicitada:")
        
        # Atualizar registro de coleta
        data_collection = await self.get_or_create_data_collection(user_id)
        data_collection.last_attempt_at = datetime.utcnow()
        
        if missing_field == "name":
            data_collection.name_attempts += 1
        elif missing_field == "email":
            data_collection.email_attempts += 1
        elif missing_field == "phone":
            data_collection.phone_attempts += 1
        
        await self.db_session.commit()
        
        return message
    
    async def validate_and_save_data(self, user_id: int, field: str, value: str) -> Tuple[bool, str]:
        """Validar e salvar dados fornecidos pelo usuário"""
        # Obter usuário
        result = await self.db_session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return False, "Usuário não encontrado"
        
        # Validar dados
        if field == "name":
            if len(value.strip()) < 2:
                return False, "Por favor, forneça um nome válido com pelo menos 2 caracteres."
            
            user.nome = value.strip().title()
            
        elif field == "email":
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, value):
                return False, "Por favor, forneça um email válido (exemplo: nome@email.com)"
            
            user.email = value.strip().lower()
            
        elif field == "phone":
            # Limpar telefone e validar
            phone_cleaned = re.sub(r'[^\d]', '', value)
            if len(phone_cleaned) < 10:
                return False, "Por favor, forneça um telefone válido com DDD."
            
            user.telefone = phone_cleaned
        
        # Atualizar timestamp
        user.updated_at = datetime.utcnow()
        
        # Atualizar registro de coleta
        data_collection = await self.get_or_create_data_collection(user_id)
        
        if field == "name":
            data_collection.has_name = True
        elif field == "email":
            data_collection.has_email = True
        elif field == "phone":
            data_collection.has_phone = True
        
        # Verificar se coleta está completa
        completeness = await self.check_user_data_completeness(user_id)
        if completeness["complete"]:
            data_collection.collection_status = "complete"
            data_collection.completed_at = datetime.utcnow()
        
        await self.db_session.commit()
        
        return True, "Dados salvos com sucesso!"
    
    async def get_collection_progress(self, user_id: int) -> Dict[str, Any]:
        """Obter progresso da coleta de dados"""
        data_collection = await self.get_or_create_data_collection(user_id)
        completeness = await self.check_user_data_completeness(user_id)
        
        return {
            "status": data_collection.collection_status,
            "complete": completeness["complete"],
            "missing": completeness["missing"],
            "attempts": {
                "name": data_collection.name_attempts,
                "email": data_collection.email_attempts,
                "phone": data_collection.phone_attempts
            },
            "max_retries": (await self.get_bot_config()).max_retries_data_collection if await self.get_bot_config() else 3
        }
    
    async def should_retry_collection(self, user_id: int, field: str) -> bool:
        """Verificar se deve tentar coletar dados novamente"""
        progress = await self.get_collection_progress(user_id)
        attempts = progress["attempts"].get(field, 0)
        max_retries = progress["max_retries"]
        
        return attempts < max_retries
    
    async def get_welcome_message(self, customer_name: str = None) -> str:
        """Obter mensagem de boas-vindas personalizada"""
        template = await self.get_message_template("welcome")
        
        if template and customer_name:
            # Substituir variáveis no template
            # Para implementar: sistema completo de substituição de variáveis
            return template.replace("{customer_name}", customer_name).replace("{company_name}", "Barbearia do João")
        
        return template or "Olá! 👋 Bem-vindo à nossa empresa! Como posso ajudá-lo hoje?"
