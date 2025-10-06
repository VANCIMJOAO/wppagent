"""
🧠 ENTITY EXTRACTOR SERVICE
============================

Serviço para extrair entidades (nome, serviço, data, hora) das conversas usando GPT-4.
Integrado ao webhook para captura automática de dados.
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import Service, User, ConversationContext, CustomerDataCollection
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EntityExtractor:
    """Extrator de entidades usando GPT-4"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "")
        )
        
        # Mapeamento de serviços (será carregado do banco)
        self.services_map = {}
    
    async def load_services(self, db: AsyncSession):
        """Carrega lista de serviços do banco para melhorar extração"""
        try:
            result = await db.execute(select(Service))
            services = result.scalars().all()
            
            self.services_map = {
                service.name.lower(): service.id
                for service in services
            }
            
            logger.info(f"📋 {len(self.services_map)} serviços carregados para extração")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar serviços: {e}")
    
    async def extract_from_messages(
        self,
        messages: List[Dict[str, str]],
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict:
        """
        Extrai entidades de uma ou mais mensagens.
        
        Args:
            messages: Lista de mensagens recentes (últimas 3-5)
            conversation_history: Histórico completo da conversa para contexto
            
        Returns:
            Dict com dados extraídos e confidence score
        """
        try:
            # Montar contexto para extração
            context = self._build_extraction_context(messages, conversation_history)
            
            extraction_prompt = self._get_extraction_prompt()
            
            # Chamar GPT-4 para extração
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": extraction_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.2,  # Baixa temperatura para extração precisa
                max_tokens=300,
            )
            
            # Parsear resposta JSON
            extracted_raw = response.choices[0].message.content.strip()
            
            # Extrair JSON se tiver texto antes/depois (```json...```)
            if "```json" in extracted_raw:
                extracted_raw = extracted_raw.split("```json")[1].split("```")[0].strip()
            elif "```" in extracted_raw:
                extracted_raw = extracted_raw.split("```")[1].split("```")[0].strip()
            
            extracted_data = json.loads(extracted_raw)
            
            # Normalizar e validar dados
            normalized = self._normalize_extracted_data(extracted_data)
            
            logger.info(f"✅ Dados extraídos: {normalized}")
            
            return normalized
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao parsear JSON da extração: {e}")
            return self._empty_extraction()
        except Exception as e:
            logger.error(f"❌ Erro na extração de entidades: {e}")
            return self._empty_extraction()
    
    def _build_extraction_context(
        self,
        messages: List[Dict[str, str]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Monta contexto para extração"""
        context = "MENSAGENS RECENTES:\n\n"
        
        for msg in messages[-5:]:  # Últimas 5 mensagens
            role = "CLIENTE" if msg.get("role") == "user" else "BOT"
            content = msg.get("content", "")
            context += f"{role}: {content}\n"
        
        return context
    
    def _get_extraction_prompt(self) -> str:
        """Retorna prompt para extração de entidades"""
        services_list = "\n".join([f"- {name.title()}" for name in self.services_map.keys()])
        
        hoje = datetime.now()
        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        
        return f"""Você é um extrator especializado de dados para agendamentos de clínica de estética.

CONTEXTO TEMPORAL:
- Hoje é {hoje.strftime('%d/%m/%Y')} ({dias_semana[hoje.weekday()]})
- Hora atual: {hoje.strftime('%H:%M')}

SERVIÇOS DISPONÍVEIS:
{services_list}

SUA TAREFA:
Analise as mensagens e extraia APENAS informações explicitamente mencionadas. NÃO INVENTE DADOS.

REGRAS DE EXTRAÇÃO:
1. **Nome**: Extrair se cliente se apresentar ("sou João", "meu nome é Maria")
2. **Telefone**: Extrair se fornecido
3. **Serviço**: Identificar se mencionar um dos serviços acima
4. **Data**: 
   - "amanhã" = {(hoje + timedelta(days=1)).strftime('%Y-%m-%d')}
   - "hoje" = {hoje.strftime('%Y-%m-%d')}
   - "próxima segunda" = próxima segunda-feira
   - Se não mencionar data: null
5. **Hora**: Extrair apenas se mencionar horário específico ("14h", "14:00", "duas da tarde")
6. **Intenção**: Classificar como "agendar", "reagendar", "cancelar", "informacao", "outro"

FORMATO DE SAÍDA (JSON OBRIGATÓRIO - RETORNE APENAS JSON VÁLIDO SEM TEXTO ADICIONAL):
{{
  "customer_name": "string ou null",
  "customer_phone": "string ou null",
  "service_name": "string ou null",
  "appointment_date": "YYYY-MM-DD ou null",
  "appointment_time": "HH:MM ou null",
  "intent": "agendar|reagendar|cancelar|informacao|outro",
  "confidence": 0.0,
  "notes": "observações relevantes"
}}

IMPORTANTE:
- RETORNE APENAS O JSON, SEM TEXTO ANTES OU DEPOIS
- Se NÃO tiver certeza, use null
- Confidence: 1.0 = certeza absoluta, 0.5 = provável, 0.3 = incerto
- NÃO invente dados que não foram mencionados
"""
    
    def _normalize_extracted_data(self, data: Dict) -> Dict:
        """Normaliza e valida dados extraídos"""
        normalized = {
            "customer_name": self._normalize_name(data.get("customer_name")),
            "customer_phone": self._normalize_phone(data.get("customer_phone")),
            "service_name": self._normalize_service(data.get("service_name")),
            "service_id": self._get_service_id(data.get("service_name")),
            "appointment_date": self._normalize_date(data.get("appointment_date")),
            "appointment_time": self._normalize_time(data.get("appointment_time")),
            "intent": data.get("intent", "outro"),
            "confidence": float(data.get("confidence", 0.5)),
            "notes": data.get("notes", ""),
            "raw_extraction": data
        }
        
        return normalized
    
    def _normalize_name(self, name: Optional[str]) -> Optional[str]:
        """Normaliza nome"""
        if not name:
            return None
        return name.strip().title()
    
    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Normaliza telefone"""
        if not phone:
            return None
        # Remove caracteres não numéricos
        phone_clean = re.sub(r'\D', '', phone)
        return phone_clean if len(phone_clean) >= 10 else None
    
    def _normalize_service(self, service: Optional[str]) -> Optional[str]:
        """Normaliza nome do serviço"""
        if not service:
            return None
        
        service_lower = service.lower().strip()
        
        # Buscar match exato ou similar
        for service_name in self.services_map.keys():
            if service_lower in service_name or service_name in service_lower:
                return service_name.title()
        
        return service.strip().title()
    
    def _get_service_id(self, service: Optional[str]) -> Optional[int]:
        """Obtém ID do serviço"""
        if not service:
            return None
        
        service_lower = service.lower().strip()
        return self.services_map.get(service_lower)
    
    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Normaliza data para formato YYYY-MM-DD"""
        if not date_str:
            return None
        
        # Se já está no formato correto
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
        
        return None
    
    def _normalize_time(self, time_str: Optional[str]) -> Optional[str]:
        """Normaliza hora para formato HH:MM"""
        if not time_str:
            return None
        
        # Tentar parsear diferentes formatos
        time_str = time_str.strip().lower()
        
        # Formato HH:MM
        match = re.match(r'(\d{1,2}):(\d{2})', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
        
        # Formato HHh ou HH
        match = re.match(r'(\d{1,2})h?', time_str)
        if match:
            hour = int(match.group(1))
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"
        
        return None
    
    def _empty_extraction(self) -> Dict:
        """Retorna extração vazia"""
        return {
            "customer_name": None,
            "customer_phone": None,
            "service_name": None,
            "service_id": None,
            "appointment_date": None,
            "appointment_time": None,
            "intent": "outro",
            "confidence": 0.0,
            "notes": "Falha na extração",
            "raw_extraction": {}
        }
    
    async def save_extraction(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        extracted_data: Dict
    ) -> Optional[ConversationContext]:
        """Salva dados extraídos usando tabelas existentes (conversation_contexts + customer_data_collection)"""
        try:
            # 1. Buscar ou criar ConversationContext
            result = await db.execute(
                select(ConversationContext).where(
                    ConversationContext.conversation_id == conversation_id
                )
            )
            context = result.scalar_one_or_none()
            
            if not context:
                # Criar novo contexto
                context = ConversationContext(
                    conversation_id=conversation_id,
                    current_state="collecting_data",
                    temp_data={},
                    collected_data={},
                    booking_data={}
                )
                db.add(context)
                await db.flush()
            
            # 2. Atualizar collected_data com novos dados extraídos
            if context.collected_data is None:
                context.collected_data = {}
            
            # Merge de dados (manter dados anteriores, adicionar novos)
            for key, value in extracted_data.items():
                if value is not None and key not in ["raw_extraction", "notes"]:  # ✅ REMOVIDO "confidence" da exclusão
                    context.collected_data[key] = value
            
            # 🔧 IMPORTANTE: Marcar campo JSON como modificado para SQLAlchemy persistir
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(context, "collected_data")
            
            # 3. Atualizar booking_data se tiver dados de agendamento
            if extracted_data.get("intent") == "agendar":
                if context.booking_data is None:
                    context.booking_data = {}
                
                booking_keys = ["service_name", "service_id", "appointment_date", "appointment_time"]
                for key in booking_keys:
                    if extracted_data.get(key):
                        context.booking_data[key] = extracted_data[key]
                
                # 🔧 Marcar booking_data como modificado
                flag_modified(context, "booking_data")
            
            # 4. Adicionar metadata
            context.collected_data["_last_extraction"] = datetime.now().isoformat()
            context.collected_data["_confidence"] = extracted_data.get("confidence", 0.5)
            context.collected_data["_intent"] = extracted_data.get("intent", "outro")
            
            # 5. Atualizar CustomerDataCollection
            result2 = await db.execute(
                select(CustomerDataCollection).where(
                    CustomerDataCollection.user_id == user_id
                )
            )
            data_collection = result2.scalar_one_or_none()
            
            if not data_collection:
                data_collection = CustomerDataCollection(
                    user_id=user_id,
                    collection_status="in_progress",
                    has_name=False,
                    has_email=False,
                    has_phone=False,
                    name_attempts=0,
                    email_attempts=0,
                    phone_attempts=0
                )
                db.add(data_collection)
                await db.flush()
            
            # Atualizar flags baseado em dados extraídos
            if extracted_data.get("customer_name"):
                data_collection.has_name = True
            if extracted_data.get("customer_phone"):
                data_collection.has_phone = True
            if extracted_data.get("customer_email"):
                data_collection.has_email = True
            
            # Atualizar status se tiver todos os dados
            if data_collection.has_name and data_collection.has_phone:
                data_collection.collection_status = "completed"
                data_collection.completed_at = datetime.now()
            
            # 6. Commit final
            await db.commit()
            await db.refresh(context)
            
            logger.info(f"✅ Dados salvos em conversation_contexts #{context.id}: {context.collected_data}")
            return context
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar extração: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await db.rollback()
            return None


# Instância global do extrator
entity_extractor = EntityExtractor()

