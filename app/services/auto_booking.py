"""
📅 AUTO BOOKING SERVICE
=======================

Serviço para criar agendamentos automaticamente quando tiver dados completos.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Appointment, Business, Service, User, ConversationContext
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AutoBookingService:
    """Serviço de agendamento automático"""
    
    def __init__(self):
        self.default_business_id = 3  # ID do negócio padrão (WhatsApp Agent Teste)
    
    async def can_create_appointment(
        self,
        db: AsyncSession,
        collected_data: Dict
    ) -> Tuple[bool, str]:
        """
        Verifica se tem dados suficientes para criar agendamento.
        
        Returns:
            (pode_criar, mensagem)
        """
        required_fields = {
            'service_id': 'serviço',
            'appointment_date': 'data',
            'appointment_time': 'horário'
        }
        
        missing = []
        for field, label in required_fields.items():
            if not collected_data.get(field):
                missing.append(label)
        
        if missing:
            return False, f"Faltam: {', '.join(missing)}"
        
        return True, "Dados completos"
    
    async def check_availability(
        self,
        db: AsyncSession,
        service_id: int,
        date_str: str,
        time_str: str
    ) -> Tuple[bool, str]:
        """
        Verifica se horário está disponível.
        
        Args:
            service_id: ID do serviço
            date_str: Data no formato "YYYY-MM-DD"
            time_str: Hora no formato "HH:MM"
            
        Returns:
            (disponível, mensagem)
        """
        try:
            # 🔴 CORREÇÃO: Combinar data e hora COM timezone Brasil (igual ao create_appointment)
            from zoneinfo import ZoneInfo
            
            date_time = datetime.fromisoformat(f"{date_str} {time_str}:00").replace(
                tzinfo=ZoneInfo('America/Sao_Paulo')
            )
            
            # Verificar se não é no passado (comparar com now() timezone-aware)
            now_br = datetime.now(ZoneInfo('America/Sao_Paulo'))
            if date_time < now_br:
                return False, "Horário já passou"
            
            # Buscar serviço para pegar duração
            result = await db.execute(
                select(Service).where(Service.id == service_id)
            )
            service = result.scalar_one_or_none()
            
            if not service:
                return False, "Serviço não encontrado"
            
            # Calcular horário de término
            duration = service.duration_minutes or 60
            end_time = date_time + timedelta(minutes=duration)
            
            # Verificar conflitos
            result = await db.execute(
                select(Appointment).where(
                    and_(
                        Appointment.service_id == service_id,
                        Appointment.date_time >= date_time,
                        Appointment.date_time < end_time,
                        Appointment.status.in_(['pending', 'confirmed'])
                    )
                )
            )
            conflicts = result.scalars().all()
            
            if conflicts:
                return False, "Horário já está ocupado"
            
            return True, "Horário disponível"
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar disponibilidade: {e}")
            return False, f"Erro ao verificar: {str(e)}"
    
    async def create_appointment(
        self,
        db: AsyncSession,
        user_id: int,
        service_id: int,
        date_str: str,
        time_str: str,
        notes: Optional[str] = None
    ) -> Optional[Appointment]:
        """
        Cria um agendamento no banco.
        
        Returns:
            Appointment criado ou None se falhar
        """
        try:
            # 🔴 CORREÇÃO: Combinar data e hora com timezone Brasil (BRT/UTC-3)
            from zoneinfo import ZoneInfo
            
            # Criar datetime com timezone Brasil
            date_time = datetime.fromisoformat(f"{date_str} {time_str}:00").replace(
                tzinfo=ZoneInfo('America/Sao_Paulo')
            )
            
            logger.info(f"🕐 Timezone Debug: Input={date_str} {time_str}, Brasil={date_time}, UTC={date_time.astimezone(ZoneInfo('UTC'))}")
            
            # Buscar serviço para pegar preço e duração
            result = await db.execute(
                select(Service).where(Service.id == service_id)
            )
            service = result.scalar_one_or_none()
            
            if not service:
                logger.error(f"❌ Serviço {service_id} não encontrado")
                return None
            
            # Calcular end_time
            duration = service.duration_minutes or 60
            end_time = date_time + timedelta(minutes=duration)
            
            # Criar appointment
            appointment = Appointment(
                user_id=user_id,
                business_id=self.default_business_id,
                service_id=service_id,
                date_time=date_time,
                end_time=end_time,
                status='pending',  # Aguardando confirmação
                price=service.price or 0.0,
                duration_minutes=duration,
                customer_notes=notes,
                notes=f"Agendamento automático via WhatsApp"
            )
            
            db.add(appointment)
            await db.commit()
            await db.refresh(appointment)
            
            logger.info(f"✅ Appointment #{appointment.id} criado: {service.name} em {date_time}")
            
            return appointment
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar appointment: {e}")
            import traceback
            logger.error(traceback.format_exc())
            await db.rollback()
            return None
    
    async def try_auto_book(
        self,
        db: AsyncSession,
        user_id: int,
        conversation_id: int,
        collected_data: Dict
    ) -> Tuple[bool, str, Optional[Appointment]]:
        """
        Tenta criar agendamento automaticamente.
        
        Returns:
            (sucesso, mensagem, appointment)
        """
        try:
            # 🔴 VALIDAÇÃO CRÍTICA #1: Intent DEVE ser "agendar"
            intent = collected_data.get("_intent") or collected_data.get("intent")
            if intent != "agendar":
                logger.debug(f"⏸️ Intent '{intent}' - não criar appointment (apenas para 'agendar')")
                return False, f"Intent é '{intent}', não 'agendar'", None
            
            # 🔴 VALIDAÇÃO CRÍTICA #2: Confidence DEVE ser >= 0.7
            confidence = collected_data.get("_confidence", 0)
            if confidence < 0.7:
                logger.debug(f"⏸️ Confidence {confidence} muito baixa - não criar appointment")
                return False, f"Confidence {confidence} < 0.7", None
            
            # 1. Verificar se tem dados suficientes
            can_create, msg = await self.can_create_appointment(db, collected_data)
            
            if not can_create:
                logger.debug(f"⚠️ Não pode criar appointment: {msg}")
                return False, msg, None
            
            service_id = collected_data['service_id']
            date_str = collected_data['appointment_date']
            time_str = collected_data['appointment_time']
            
            # 🔴 VALIDAÇÃO CRÍTICA #3: Horário de Funcionamento
            from datetime import datetime as dt
            date_obj = dt.fromisoformat(date_str)
            hour = int(time_str.split(':')[0])
            day_of_week = date_obj.weekday()  # 0=Segunda, 5=Sábado, 6=Domingo
            
            # Segunda a sexta: 8h-18h
            if 0 <= day_of_week <= 4:
                if not (8 <= hour < 18):
                    logger.warning(f"⚠️ Horário {time_str} fora do expediente (Seg-Sex: 8h-18h)")
                    return False, f"Horário fora do expediente. Atendemos de segunda a sexta das 8h às 18h", None
            # Sábado: 8h-14h
            elif day_of_week == 5:
                if not (8 <= hour < 14):
                    logger.warning(f"⚠️ Horário {time_str} fora do expediente (Sáb: 8h-14h)")
                    return False, f"Aos sábados atendemos apenas das 8h às 14h", None
            # Domingo: fechado
            else:
                logger.warning(f"⚠️ Tentativa de agendar no domingo")
                return False, "Não atendemos aos domingos", None
            
            # 2. Verificar disponibilidade
            available, msg = await self.check_availability(
                db, service_id, date_str, time_str
            )
            
            if not available:
                logger.warning(f"⚠️ Horário indisponível: {msg}")
                return False, f"Desculpe, {msg}", None
            
            # 3. Criar appointment
            notes = collected_data.get('notes', '')
            appointment = await self.create_appointment(
                db, user_id, service_id, date_str, time_str, notes
            )
            
            if not appointment:
                return False, "Erro ao criar agendamento", None
            
            # 4. Atualizar ConversationContext
            result = await db.execute(
                select(ConversationContext).where(
                    ConversationContext.conversation_id == conversation_id
                )
            )
            context = result.scalar_one_or_none()
            
            if context:
                if context.booking_data is None:
                    context.booking_data = {}
                
                context.booking_data['appointment_id'] = appointment.id
                context.booking_data['status'] = 'created'
                context.booking_data['created_at'] = datetime.now().isoformat()
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(context, "booking_data")
                
                await db.commit()
            
            logger.info(f"🎉 Agendamento automático criado! ID: {appointment.id}")
            
            return True, "Agendamento criado com sucesso!", appointment
            
        except Exception as e:
            logger.error(f"❌ Erro em try_auto_book: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, "Erro ao processar agendamento", None
    
    def format_confirmation_message(
        self,
        appointment: Appointment,
        service_name: str,
        user_name: Optional[str] = None
    ) -> str:
        """Formata mensagem de confirmação"""
        
        # Formatar data
        date_obj = appointment.date_time
        date_formatted = date_obj.strftime("%d/%m/%Y")
        time_formatted = date_obj.strftime("%H:%M")
        
        # Dia da semana
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        dia_semana = dias_semana[date_obj.weekday()]
        
        # Montar mensagem
        greeting = f"Olá{', ' + user_name if user_name else ''}! "
        
        message = f"""{greeting}🎉 Seu agendamento foi confirmado!

📋 **Detalhes do Agendamento:**
━━━━━━━━━━━━━━━━━━━━━
🔹 **Serviço:** {service_name}
📅 **Data:** {date_formatted} ({dia_semana})
🕒 **Horário:** {time_formatted}
⏱️ **Duração:** {appointment.duration_minutes} minutos
💰 **Valor:** R$ {appointment.price:.2f}
━━━━━━━━━━━━━━━━━━━━━

📍 **Local:** Studio Beleza Bem-Estar
Rua das Flores, 123 - Centro

📱 **Contato:** (16) 3333-4444

⚠️ **Importante:**
• Chegue com 10 minutos de antecedência
• Cancelamentos com até 2h de antecedência
• Reagendamentos: até 2x por mês

🔖 **Código do Agendamento:** #{appointment.id}

Nos vemos em breve! 😊✨"""
        
        return message


# Instância global
auto_booking_service = AutoBookingService()

