"""
Serviço dinâmico para gerenciamento de horários e agendamentos
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.database import (
    Business, Service, Appointment, BlockedTime, 
    AvailableSlot, BotConfiguration
)
from app.utils.logger import get_logger
import json

logger = get_logger(__name__)


class DynamicSchedulingService:
    """Serviço para gerenciamento dinâmico de horários e agendamentos"""
    
    def __init__(self, db_session: AsyncSession, business_id: int = 1):
        self.db_session = db_session
        self.business_id = business_id
    
    async def get_business_info(self) -> Optional[Business]:
        """Obter informações do negócio"""
        result = await self.db_session.execute(
            select(Business).where(Business.id == self.business_id)
        )
        return result.scalar_one_or_none()
    
    async def get_bot_config(self) -> Optional[BotConfiguration]:
        """Obter configurações do bot"""
        result = await self.db_session.execute(
            select(BotConfiguration).where(BotConfiguration.business_id == self.business_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_services(self) -> List[Service]:
        """Obter serviços ativos"""
        result = await self.db_session.execute(
            select(Service).where(
                Service.business_id == self.business_id,
                Service.is_active == True
            ).order_by(Service.name)
        )
        return result.scalars().all()
    
    async def is_business_open(self, check_datetime: datetime) -> bool:
        """Verificar se o negócio está aberto em uma data/hora específica"""
        business = await self.get_business_info()
        if not business or not business.business_hours:
            return False
        
        # Mapear dia da semana (0=segunda, 6=domingo)
        weekday_names = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
        weekday = check_datetime.weekday()
        day_name = weekday_names[weekday]
        
        day_hours = business.business_hours.get(day_name, {})
        
        # Verificar se está fechado
        if day_hours.get("closed", False):
            return False
        
        # Verificar horário
        open_time_str = day_hours.get("open", "09:00")
        close_time_str = day_hours.get("close", "18:00")
        
        try:
            open_time = datetime.strptime(open_time_str, "%H:%M").time()
            close_time = datetime.strptime(close_time_str, "%H:%M").time()
            check_time = check_datetime.time()
            
            return open_time <= check_time < close_time
        except ValueError:
            return False
    
    async def get_available_slots(self, date: datetime.date, service_id: Optional[int] = None) -> List[Dict]:
        """Obter slots disponíveis para uma data específica"""
        business = await self.get_business_info()
        bot_config = await self.get_bot_config()
        
        if not business:
            return []
        
        # Configurações padrão
        slot_duration = bot_config.slot_duration_minutes if bot_config else 30
        break_duration = bot_config.break_between_appointments_minutes if bot_config else 0
        
        # Obter horários de funcionamento do dia
        weekday_names = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
        weekday = date.weekday()
        day_name = weekday_names[weekday]
        
        day_hours = business.business_hours.get(day_name, {})
        if day_hours.get("closed", False):
            return []
        
        try:
            open_time = datetime.strptime(day_hours.get("open", "09:00"), "%H:%M").time()
            close_time = datetime.strptime(day_hours.get("close", "18:00"), "%H:%M").time()
        except ValueError:
            return []
        
        # Gerar slots
        slots = []
        current_time = datetime.combine(date, open_time)
        end_time = datetime.combine(date, close_time)
        
        while current_time + timedelta(minutes=slot_duration) <= end_time:
            slot_info = {
                "datetime": current_time,
                "time_str": current_time.strftime("%H:%M"),
                "available": True,
                "reason": None
            }
            
            # Verificar se está no passado
            if current_time < datetime.now():
                slot_info["available"] = False
                slot_info["reason"] = "past"
            
            # Verificar agendamentos existentes
            elif await self._is_slot_booked(current_time, slot_duration):
                slot_info["available"] = False
                slot_info["reason"] = "booked"
            
            # Verificar horários bloqueados
            elif await self._is_slot_blocked(current_time, slot_duration):
                slot_info["available"] = False
                slot_info["reason"] = "blocked"
            
            slots.append(slot_info)
            current_time += timedelta(minutes=slot_duration + break_duration)
        
        return slots
    
    async def _is_slot_booked(self, slot_datetime: datetime, duration_minutes: int) -> bool:
        """Verificar se um slot está ocupado"""
        slot_end = slot_datetime + timedelta(minutes=duration_minutes)
        
        result = await self.db_session.execute(
            select(Appointment).where(
                and_(
                    Appointment.business_id == self.business_id,
                    Appointment.status.in_(["pendente", "confirmado"]),
                    or_(
                        # Agendamento começa durante o slot
                        and_(
                            Appointment.date_time >= slot_datetime,
                            Appointment.date_time < slot_end
                        ),
                        # Agendamento termina durante o slot
                        and_(
                            Appointment.end_time > slot_datetime,
                            Appointment.end_time <= slot_end
                        ),
                        # Agendamento engloba o slot
                        and_(
                            Appointment.date_time <= slot_datetime,
                            Appointment.end_time >= slot_end
                        )
                    )
                )
            )
        )
        
        return result.scalar_one_or_none() is not None
    
    async def _is_slot_blocked(self, slot_datetime: datetime, duration_minutes: int) -> bool:
        """Verificar se um slot está bloqueado"""
        slot_end = slot_datetime + timedelta(minutes=duration_minutes)
        
        result = await self.db_session.execute(
            select(BlockedTime).where(
                and_(
                    BlockedTime.business_id == self.business_id,
                    or_(
                        and_(
                            BlockedTime.start_time <= slot_datetime,
                            BlockedTime.end_time > slot_datetime
                        ),
                        and_(
                            BlockedTime.start_time < slot_end,
                            BlockedTime.end_time >= slot_end
                        )
                    )
                )
            )
        )
        
        return result.scalar_one_or_none() is not None
    
    async def create_appointment(self, user_id: int, service_id: int, 
                               appointment_datetime: datetime, notes: str = None) -> Tuple[bool, str, Optional[Appointment]]:
        """Criar novo agendamento"""
        # Verificar se o serviço existe
        result = await self.db_session.execute(
            select(Service).where(
                Service.id == service_id,
                Service.business_id == self.business_id,
                Service.is_active == True
            )
        )
        service = result.scalar_one_or_none()
        
        if not service:
            return False, "Serviço não encontrado ou inativo", None
        
        # Verificar se o horário está disponível
        if not await self.is_business_open(appointment_datetime):
            return False, "Horário fora do funcionamento", None
        
        if await self._is_slot_booked(appointment_datetime, service.duration_minutes):
            return False, "Horário já ocupado", None
        
        if await self._is_slot_blocked(appointment_datetime, service.duration_minutes):
            return False, "Horário bloqueado", None
        
        # Verificar antecedência mínima
        bot_config = await self.get_bot_config()
        min_advance_hours = bot_config.min_advance_booking_hours if bot_config else 2
        
        if appointment_datetime < datetime.now() + timedelta(hours=min_advance_hours):
            return False, f"Agendamento deve ser feito com pelo menos {min_advance_hours} horas de antecedência", None
        
        # Criar agendamento
        appointment = Appointment(
            user_id=user_id,
            business_id=self.business_id,
            service_id=service_id,
            date_time=appointment_datetime,
            end_time=appointment_datetime + timedelta(minutes=service.duration_minutes),
            status="pendente" if not (bot_config and bot_config.auto_confirm_bookings) else "confirmado",
            notes=notes,
            price_at_booking=service.price
        )
        
        self.db_session.add(appointment)
        await self.db_session.commit()
        
        return True, "Agendamento criado com sucesso", appointment
    
    async def get_user_appointments(self, user_id: int, include_past: bool = False) -> List[Appointment]:
        """Obter agendamentos do usuário"""
        query = select(Appointment).where(
            Appointment.user_id == user_id,
            Appointment.business_id == self.business_id
        )
        
        if not include_past:
            query = query.where(Appointment.date_time >= datetime.now())
        
        query = query.order_by(Appointment.date_time.desc())
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def cancel_appointment(self, appointment_id: int, user_id: int, reason: str = None) -> Tuple[bool, str]:
        """Cancelar agendamento"""
        result = await self.db_session.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.user_id == user_id,
                Appointment.business_id == self.business_id
            )
        )
        appointment = result.scalar_one_or_none()
        
        if not appointment:
            return False, "Agendamento não encontrado"
        
        if appointment.status == "cancelado":
            return False, "Agendamento já está cancelado"
        
        if appointment.status == "concluido":
            return False, "Não é possível cancelar agendamento já concluído"
        
        # Cancelar
        appointment.status = "cancelado"
        appointment.cancelled_at = datetime.utcnow()
        appointment.cancellation_reason = reason or "Cancelado pelo cliente"
        appointment.cancelled_by = "customer"
        
        await self.db_session.commit()
        
        return True, "Agendamento cancelado com sucesso"
    
    async def get_business_hours_formatted(self) -> str:
        """Obter horários de funcionamento formatados"""
        business = await self.get_business_info()
        if not business or not business.business_hours:
            return "Horários não configurados"
        
        days_pt = {
            "segunda": "Segunda-feira",
            "terca": "Terça-feira", 
            "quarta": "Quarta-feira",
            "quinta": "Quinta-feira",
            "sexta": "Sexta-feira",
            "sabado": "Sábado",
            "domingo": "Domingo"
        }
        
        formatted_hours = "🕒 **Horários de Funcionamento:**\n\n"
        
        for day_key, day_name in days_pt.items():
            day_hours = business.business_hours.get(day_key, {})
            
            if day_hours.get("closed", False):
                formatted_hours += f"• {day_name}: Fechado\n"
            else:
                open_time = day_hours.get("open", "09:00")
                close_time = day_hours.get("close", "18:00")
                formatted_hours += f"• {day_name}: {open_time} às {close_time}\n"
        
        return formatted_hours
