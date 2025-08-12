"""
Sistema de Workflow de Agendamentos com Validações Robustas
"""
from datetime import datetime, timedelta
from datetime import date as Date
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import asyncio
from app.models.database import Service, Appointment, User, Business
from app.utils.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
logger = get_logger(__name__)
from sqlalchemy import select, and_, or_
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Erro de validação de agendamento"""
    pass

class BookingStep(Enum):
    """Estados do processo de agendamento"""
    INITIAL = "initial"
    COLLECTING_SERVICE = "collecting_service"
    COLLECTING_DATE = "collecting_date"
    COLLECTING_TIME = "collecting_time"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_PHONE = "collecting_phone"
    COLLECTING_EMAIL = "collecting_email"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class BookingData:
    """Dados do agendamento em construção"""
    user_id: Optional[int] = None
    service_id: Optional[int] = None
    service_name: Optional[str] = None
    date: Optional[Date] = None
    time: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    notes: Optional[str] = None
    step: BookingStep = BookingStep.INITIAL
    attempts: int = 0
    errors: List[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def update_activity(self):
        """Atualiza timestamp da última atividade"""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Verifica se o booking expirou por inatividade"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def get_age_minutes(self) -> float:
        """Retorna idade do booking em minutos"""
        return (datetime.now() - self.created_at).total_seconds() / 60

@dataclass
class ValidationResult:
    """Resultado da validação de horário"""
    valid: bool
    errors: List[str]
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

class BookingWorkflow:
    """Sistema de workflow para agendamentos"""
    
    def __init__(self):
        # Armazenar agendamentos ativos em memória (cache temporário)
        self.active_bookings: Dict[str, BookingData] = {}
        
        # Configuração de limpeza automática
        self.cleanup_interval_minutes = 10  # Limpar a cada 10 minutos
        self.booking_timeout_minutes = 30   # Timeout de inatividade: 30 min
        self.max_booking_age_minutes = 120  # Idade máxima: 2 horas
        self.max_cache_size = 1000         # Máximo de bookings em cache
        
        # Referência para task de limpeza (previne race conditions)
        self.cleanup_task = None
        self._cleanup_started = False
        
        # Stats para monitoramento
        self.cleanup_stats = {
            'last_cleanup': datetime.now(),
            'total_cleanups': 0,
            'expired_removed': 0,
            'old_removed': 0,
            'size_limit_removed': 0
        }
        
        # Horários de funcionamento (configurável)
        self.business_hours = {
            0: {'open': '09:00', 'close': '18:00'},  # Segunda
            1: {'open': '09:00', 'close': '18:00'},  # Terça
            2: {'open': '09:00', 'close': '18:00'},  # Quarta
            3: {'open': '09:00', 'close': '18:00'},  # Quinta
            4: {'open': '09:00', 'close': '18:00'},  # Sexta
            5: {'open': '09:00', 'close': '15:00'},  # Sábado
            6: {'closed': True}  # Domingo
        }
        
        # Serviços disponíveis (padrão)
        self.default_services = {
            'corte masculino': {'id': 1, 'duration': 30, 'price': 'R$ 50,00'},
            'corte feminino': {'id': 2, 'duration': 45, 'price': 'R$ 150,00'},
            'barba': {'id': 3, 'duration': 20, 'price': 'R$ 30,00'},
            'manicure': {'id': 4, 'duration': 30, 'price': 'R$ 30,00'}
        }
        
        # Iniciar limpeza automática de forma segura
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Inicia task de limpeza com tratamento de erro e controle de race condition"""
        if self._cleanup_started or self.cleanup_task is not None:
            logger.warning("⚠️ Task de limpeza já iniciada, ignorando nova inicialização")
            return
        
        try:
            # Guardar referência da task para evitar garbage collection
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._cleanup_started = True
            logger.info("🧹 Sistema de limpeza automática de bookings iniciado")
        except RuntimeError as e:
            # Se não há event loop, agendar para depois
            logger.warning(f"⏰ Event loop não disponível, limpeza será iniciada depois: {e}")
            self._cleanup_started = False
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sistema de limpeza: {e}")
            self._cleanup_started = False
    
    def _ensure_cleanup_started(self):
        """Garante que o cleanup está rodando (chamado sob demanda)"""
        if not self._cleanup_started and self.cleanup_task is None:
            self._start_cleanup_task()
    
    def stop_cleanup_task(self):
        """Para a task de limpeza de forma segura"""
        if self.cleanup_task and not self.cleanup_task.done():
            try:
                self.cleanup_task.cancel()
                logger.info("🛑 Task de limpeza automática cancelada")
            except Exception as e:
                logger.error(f"❌ Erro ao cancelar task de limpeza: {e}")
        
        self.cleanup_task = None
        self._cleanup_started = False
    
    def get_cleanup_status(self) -> dict:
        """Retorna status da task de limpeza"""
        return {
            "started": self._cleanup_started,
            "task_active": self.cleanup_task is not None and not self.cleanup_task.done() if self.cleanup_task else False,
            "task_cancelled": self.cleanup_task.cancelled() if self.cleanup_task else False,
            "last_cleanup": self.cleanup_stats.get('last_cleanup'),
            "total_cleanups": self.cleanup_stats.get('total_cleanups', 0)
        }
    
    async def _cleanup_loop(self):
        """Loop de limpeza automática executado em background"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_minutes * 60)  # Converter para segundos
                await self._cleanup_expired_bookings()
            except Exception as e:
                logger.error(f"❌ Erro na limpeza automática: {e}")
                # Continuar loop mesmo com erro
    
    async def _cleanup_expired_bookings(self):
        """Remove bookings expirados e antigos da memória"""
        try:
            initial_count = len(self.active_bookings)
            
            if initial_count == 0:
                return  # Nada para limpar
            
            current_time = datetime.now()
            expired_users = []
            old_users = []
            
            # Identificar bookings para remoção
            for user_id, booking in self.active_bookings.items():
                # Remover por inatividade (timeout)
                if booking.is_expired(self.booking_timeout_minutes):
                    expired_users.append(user_id)
                
                # Remover por idade máxima
                elif booking.get_age_minutes() > self.max_booking_age_minutes:
                    old_users.append(user_id)
            
            # Remover bookings expirados
            for user_id in expired_users:
                del self.active_bookings[user_id]
                self.cleanup_stats['expired_removed'] += 1
            
            # Remover bookings antigos
            for user_id in old_users:
                del self.active_bookings[user_id]
                self.cleanup_stats['old_removed'] += 1
            
            # Se ainda há muitos bookings, remover os mais antigos
            if len(self.active_bookings) > self.max_cache_size:
                # Ordenar por data de criação (mais antigos primeiro)
                sorted_bookings = sorted(
                    self.active_bookings.items(), 
                    key=lambda x: x[1].created_at
                )
                
                # Remover os mais antigos até atingir o limite
                excess_count = len(self.active_bookings) - self.max_cache_size
                for i in range(excess_count):
                    user_id_to_remove = sorted_bookings[i][0]
                    del self.active_bookings[user_id_to_remove]
                    self.cleanup_stats['size_limit_removed'] += 1
            
            # Atualizar estatísticas
            final_count = len(self.active_bookings)
            removed_count = initial_count - final_count
            
            if removed_count > 0:
                self.cleanup_stats['total_cleanups'] += 1
                self.cleanup_stats['last_cleanup'] = current_time
                
                logger.info(
                    f"🧹 Limpeza automática executada: "
                    f"{removed_count} bookings removidos "
                    f"({len(expired_users)} expirados, {len(old_users)} antigos, "
                    f"{self.cleanup_stats['size_limit_removed'] - (self.cleanup_stats['size_limit_removed'] - min(excess_count if 'excess_count' in locals() else 0, removed_count))} por limite). "
                    f"Restam: {final_count}"
                )
            
        except Exception as e:
            logger.error(f"❌ Erro durante limpeza automática: {e}")
    
    def get_memory_stats(self) -> dict:
        """Retorna estatísticas de uso de memória"""
        return {
            'active_bookings_count': len(self.active_bookings),
            'cleanup_stats': self.cleanup_stats.copy(),
            'memory_config': {
                'cleanup_interval_minutes': self.cleanup_interval_minutes,
                'booking_timeout_minutes': self.booking_timeout_minutes,
                'max_booking_age_minutes': self.max_booking_age_minutes,
                'max_cache_size': self.max_cache_size
            }
        }
    
    async def manual_cleanup(self, force: bool = False) -> dict:
        """Executa limpeza manual e retorna estatísticas"""
        initial_count = len(self.active_bookings)
        
        if force:
            # Limpeza forçada - remove todos
            self.active_bookings.clear()
            removed_count = initial_count
            logger.info(f"🧹 Limpeza FORÇADA: {removed_count} bookings removidos")
        else:
            # Limpeza normal
            await self._cleanup_expired_bookings()
            removed_count = initial_count - len(self.active_bookings)
        
        return {
            'initial_count': initial_count,
            'removed_count': removed_count,
            'final_count': len(self.active_bookings),
            'cleanup_type': 'forced' if force else 'normal'
        }
    
    async def start_booking(self, user_id: str, message: str) -> Tuple[str, Optional[dict]]:
        """Inicia processo de agendamento"""
        try:
            # Garantir que cleanup está rodando
            self._ensure_cleanup_started()
            
            booking = BookingData(step=BookingStep.COLLECTING_SERVICE)
            self.active_bookings[user_id] = booking
            
            # Tentar extrair serviço da mensagem inicial
            extracted_service = self._extract_service_from_message(message)
            if extracted_service:
                booking.service_name = extracted_service['name']
                booking.service_id = extracted_service['id']
                booking.step = BookingStep.COLLECTING_DATE
                
                return self._generate_date_request(extracted_service['name']), None
            
            return self._generate_service_selection(), self._get_service_buttons()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar agendamento: {e}")
            return "❌ Erro interno. Tente novamente.", None
    
    async def process_booking_step(self, user_id: str, message: str, db: AsyncSession) -> Tuple[str, Optional[dict]]:
        """Processa uma etapa do agendamento"""
        try:
            if user_id not in self.active_bookings:
                return await self.start_booking(user_id, message)
            
            booking = self.active_bookings[user_id]
            booking.attempts += 1
            booking.update_activity()  # 🔧 ATUALIZAR ATIVIDADE
            
            # Limitar tentativas
            if booking.attempts > 5:
                del self.active_bookings[user_id]
                return "❌ Muitas tentativas. Vamos começar novamente. Digite 'agendar' para tentar de novo.", None
            
            if booking.step == BookingStep.COLLECTING_SERVICE:
                return await self._process_service_selection(user_id, message, booking)
            
            elif booking.step == BookingStep.COLLECTING_DATE:
                return await self._process_date_selection(user_id, message, booking)
            
            elif booking.step == BookingStep.COLLECTING_TIME:
                return await self._process_time_selection(user_id, message, booking, db)
            
            elif booking.step == BookingStep.COLLECTING_NAME:
                return await self._process_name_collection(user_id, message, booking)
            
            elif booking.step == BookingStep.COLLECTING_PHONE:
                return await self._process_phone_collection(user_id, message, booking)
            
            elif booking.step == BookingStep.COLLECTING_EMAIL:
                return await self._process_email_collection(user_id, message, booking)
            
            elif booking.step == BookingStep.CONFIRMING:
                return await self._process_confirmation(user_id, message, booking, db)
            
            else:
                return "❌ Estado inválido. Vamos começar novamente.", None
                
        except Exception as e:
            logger.error(f"Erro no processo de agendamento: {e}")
            if user_id in self.active_bookings:
                del self.active_bookings[user_id]
            return "❌ Erro interno. Vamos começar novamente. Digite 'agendar' para tentar de novo.", None

    def _extract_service_from_message(self, message: str) -> Optional[dict]:
        """Extrai serviço da mensagem usando patterns"""
        message_lower = message.lower()
        
        patterns = {
            'corte masculino': ['corte masculino', 'corte homem', 'corte masc', 'corte de cabelo masculino'],
            'corte feminino': ['corte feminino', 'corte mulher', 'corte fem', 'corte de cabelo feminino'],
            'barba': ['barba', 'fazer barba', 'aparar barba'],
            'manicure': ['manicure', 'unha', 'manicure']
        }
        
        for service, keywords in patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                return {
                    'name': service,
                    'id': self.default_services[service]['id']
                }
        
        return None
    
    def _generate_service_selection(self) -> str:
        return "🔸 **Qual serviço você gostaria de agendar?**\n\nEscolha uma das opções abaixo:"

    def _generate_date_request(self, service_name: str) -> str:
        return f"✅ **{service_name.title()}** selecionado!\n\n📅 **Para qual data você gostaria de agendar?**\n\nVocê pode dizer:\n• Hoje, amanhã\n• 15/08, 15/08/2024\n• Segunda-feira, terça-feira, etc."

    def _get_service_buttons(self) -> dict:
        """Gera botões para seleção de serviços"""
        return {
            "type": "button",
            "body": {"text": "Escolha o serviço desejado:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "corte_masc", "title": "Corte Masculino"}},
                    {"type": "reply", "reply": {"id": "corte_fem", "title": "Corte Feminino"}},
                    {"type": "reply", "reply": {"id": "barba", "title": "Barba"}}
                ]
            }
        }

    async def _process_service_selection(self, user_id: str, message: str, booking: BookingData) -> Tuple[str, Optional[dict]]:
        """Processa seleção de serviço"""
        booking.update_activity()  # 🔧 ATUALIZAR ATIVIDADE
        service = self._extract_service_from_message(message)
        
        if service:
            booking.service_name = service['name']
            booking.service_id = service['id']
            booking.step = BookingStep.COLLECTING_DATE
            booking.attempts = 0  # Reset attempts
            
            return self._generate_date_request(service['name']), None
        else:
            booking.errors.append("Serviço não identificado")
            if booking.attempts >= 3:
                return "❌ Não consegui identificar o serviço. Vamos começar novamente?", None
            
            return self._generate_service_selection_retry(), self._get_service_buttons()

    def _generate_service_selection_retry(self) -> str:
        return "❌ Não consegui identificar o serviço.\n\n🔸 **Escolha uma das opções:**"

    def _parse_date_from_message(self, message: str) -> Optional[Date]:
        """Extrai data da mensagem com validações"""
        message_lower = message.lower().strip()
        today = Date.today()
        
        # Padrões de linguagem natural
        if 'hoje' in message_lower:
            return today
        elif 'amanha' in message_lower or 'amanhã' in message_lower:
            return today + timedelta(days=1)
        elif 'depois de amanha' in message_lower or 'depois de amanhã' in message_lower:
            return today + timedelta(days=2)
        
        # Padrões de data
        patterns = [
            # DD/MM/AAAA
            (r'(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})', lambda m: Date(int(m.group(3)), int(m.group(2)), int(m.group(1)))),
            # DD/MM (ano atual)
            (r'(\d{1,2})[/\-.](\d{1,2})(?:[/\-.](\d{2}))?$', lambda m: Date(today.year, int(m.group(2)), int(m.group(1)))),
        ]
        
        # Testar padrões de data
        for pattern, date_parser in patterns:
            match = re.search(pattern, message)
            if match:
                try:
                    parsed_date = date_parser(match)
                    if parsed_date >= today:
                        return parsed_date
                except (ValueError, TypeError):
                    continue
        
        # Dias da semana
        weekdays = {
            'segunda': 0, 'segunda-feira': 0,
            'terca': 1, 'terça': 1, 'terça-feira': 1,
            'quarta': 2, 'quarta-feira': 2,
            'quinta': 3, 'quinta-feira': 3,
            'sexta': 4, 'sexta-feira': 4,
            'sabado': 5, 'sábado': 5, 'sábado-feira': 5,
            'domingo': 6
        }
        
        for day_name, weekday in weekdays.items():
            if day_name in message_lower:
                days_ahead = weekday - today.weekday()
                if days_ahead <= 0:  # Se já passou essa semana
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
        
        return None

    async def _process_date_selection(self, user_id: str, message: str, booking: BookingData) -> Tuple[str, Optional[dict]]:
        """Processa seleção de data e opcionalmente horário na mesma mensagem"""
        try:
            booking.update_activity()  # 🔧 ATUALIZAR ATIVIDADE
            logger.info(f"DEBUG: Processing date selection for message: '{message}'")
            parsed_date = self._parse_date_from_message(message)
            
            if parsed_date:
                booking.date = parsed_date
                booking.attempts = 0  # Reset attempts
                logger.info(f"DEBUG: Date parsed successfully: {parsed_date}")
                
                # Tentar extrair horário da mesma mensagem
                parsed_time = self._parse_time_from_message(message)
                logger.info(f"DEBUG: Time parsing result: '{parsed_time}'")
                
                if parsed_time:
                    # Data e horário fornecidos na mesma mensagem
                    booking.time = parsed_time
                    booking.step = BookingStep.COLLECTING_NAME
                    logger.info(f"DEBUG: Both date and time found - moving to name collection")
                    
                    return self._generate_date_time_confirmed_message(parsed_date, parsed_time), None
                else:
                    # Apenas data fornecida, continuar para horário
                    booking.step = BookingStep.COLLECTING_TIME
                    logger.info(f"DEBUG: Only date found - moving to time collection")
                    return self._generate_time_request(parsed_date), self._get_time_buttons()
            else:
                booking.errors.append("Data não identificada")
                if booking.attempts >= 3:
                    return "❌ Não consegui entender a data. Vamos começar novamente?", None
                
                return self._generate_date_request_retry(), None
                
        except Exception as e:
            logger.error(f"Erro ao processar data: {e}")
            return "❌ Erro ao processar data. Tente novamente.", None

    def _generate_date_request_retry(self) -> str:
        return "❌ Não consegui entender a data.\n\n📅 **Tente novamente:**\n• Hoje, amanhã\n• 15/08, 15/08/2024\n• Segunda-feira, etc."

    def _generate_date_time_confirmed_message(self, date: Date, time: str) -> str:
        """Gera mensagem quando data e horário são confirmados simultaneamente"""
        date_str = date.strftime('%d/%m/%Y')
        weekday = self._get_weekday_name_pt(date.weekday())
        return f"✅ **Data e horário confirmados!**\n\n📅 **Data:** {weekday}, {date_str}\n🕐 **Horário:** {time}\n\n👤 **Qual é o seu nome completo?**"

    def _generate_time_request(self, date: Date) -> str:
        date_str = date.strftime('%d/%m/%Y')
        weekday = self._get_weekday_name_pt(date.weekday())
        return f"📅 Data escolhida: **{weekday}, {date_str}**\n\n🕐 **Que horário você prefere?**\n\nVocê pode dizer:\n• 14:30, 15h00\n• 9 da manhã, 2 da tarde"

    def _get_weekday_name_pt(self, weekday: int) -> str:
        """Converte número do dia da semana para nome em português"""
        days = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 
                'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
        return days[weekday]

    def _get_time_buttons(self) -> dict:
        """Gera botões para seleção de horários"""
        return {
            "type": "button", 
            "body": {"text": "Horários disponíveis:"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "morning", "title": "Manhã (9h-12h)"}},
                    {"type": "reply", "reply": {"id": "afternoon", "title": "Tarde (14h-18h)"}},
                    {"type": "reply", "reply": {"id": "custom", "title": "Outro horário"}}
                ]
            }
        }

    def _parse_time_from_message(self, message: str) -> Optional[str]:
        """Extrai horário da mensagem"""
        message_clean = message.lower().strip()
        logger.info(f"DEBUG: Parsing time from message: '{message_clean}'")
        
        # Padrões de horário - CORRIGIDO e APRIMORADO para reconhecer todos os formatos
        patterns = [
            # Padrão "às" e "as" com diferentes variações - PRIORIDADE ALTA
            r'[àa]s?\s*(\d{1,2})[:h](\d{2})',      # às 14:30, as 14h30, às 14h30
            r'[àa]s?\s*(\d{1,2})\s*h\s*(\d{2})',   # às 14 h 30, as 14h 30  
            r'[àa]s?\s*(\d{1,2})\s*[:\.](\d{2})',  # às 14.30, as 14:30
            r'[àa]s?\s*(\d{1,2})\s*h(?:oras?)?',   # às 14h, as 14 horas
            r'[àa]s?\s*(\d{1,2})(?:\s*h)?',        # às 14, as 14h
            
            # Padrões tradicionais de horário
            r'(\d{1,2})[:h](\d{2})',               # 14:30, 14h30
            r'(\d{1,2})[:h](\d{2})\s*h',           # 14:30h, 14h30h
            r'(\d{1,2})\s*h\s*(\d{2})',            # 14 h 30
            r'(\d{1,2})\s*[:\.](\d{2})',           # 14.30, 14 : 30
            
            # Padrões com período do dia
            r'(\d{1,2})\s*da\s*(manha|manhã|tarde|noite)',  # 9 da manhã
            r'(\d{1,2})\s*h(?:\s*da\s*(manha|manhã|tarde|noite))?',  # 9h da manhã
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, message_clean)
            logger.info(f"DEBUG: Pattern {i} '{pattern}' -> Match: {match.groups() if match else None}")
            if match:
                try:
                    hour = int(match.group(1))
                    minute = 0
                    period = None
                    
                    # Verificar se há minutos especificados
                    if len(match.groups()) > 1 and match.group(2):
                        if match.group(2).isdigit():
                            minute = int(match.group(2))
                        else:
                            # Se o segundo grupo não for dígito, pode ser período do dia
                            period = match.group(2)
                    
                    # Verificar período do dia no terceiro grupo
                    if len(match.groups()) > 2 and match.group(3):
                        period = match.group(3)
                    
                    # Ajustar período se especificado
                    if period:
                        if period in ['tarde'] and hour < 12:
                            hour += 12
                        elif period in ['noite']:
                            if hour == 12:
                                hour = 0  # 12 da noite = 00:00 (meia-noite)
                            elif hour < 12:
                                hour += 12  # 8 da noite = 20:00
                        elif period in ['manha', 'manhã'] and hour == 12:
                            hour = 0  # 12 da manhã = 00:00
                    
                    # Validar horário
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        result = f"{hour:02d}:{minute:02d}"
                        logger.info(f"DEBUG: Time parsing successful: '{result}' from pattern {i}")
                        return result
                except (ValueError, IndexError, TypeError) as e:
                    logger.info(f"DEBUG: Error parsing pattern {i}: {e}")
                    continue
        
        # Horários em formato numérico simples (assumir que é a hora)
        if message_clean.isdigit():
            hour = int(message_clean)
            if 6 <= hour <= 22:  # Horário comercial razoável
                result = f"{hour:02d}:00"
                logger.info(f"DEBUG: Time parsing from numeric: '{result}'")
                return result
        
        logger.info(f"DEBUG: No time pattern matched for: '{message_clean}'")
        return None

    async def _process_time_selection(self, user_id: str, message: str, booking: BookingData, db: AsyncSession) -> Tuple[str, Optional[dict]]:
        """Processa seleção de horário"""
        booking.update_activity()  # 🔧 ATUALIZAR ATIVIDADE
        parsed_time = self._parse_time_from_message(message)
        
        if parsed_time:
            booking.time = parsed_time
            booking.step = BookingStep.COLLECTING_NAME
            booking.attempts = 0
            
            return self._generate_name_request(), None
        else:
            booking.errors.append("Horário não identificado")
            if booking.attempts >= 3:
                return "❌ Não consegui entender o horário. Vamos começar novamente?", None
            
            return self._generate_time_request_retry(booking.date), self._get_time_buttons()

    def _generate_time_request_retry(self, date: Date) -> str:
        return "❌ Horário não disponível.\n\n🕐 **Escolha outro horário:**"

    def _generate_name_request(self) -> str:
        return "✅ **Horário confirmado!**\n\n👤 **Qual é o seu nome completo?**"

    async def _process_name_collection(self, user_id: str, message: str, booking: BookingData) -> Tuple[str, Optional[dict]]:
        """Processa coleta de nome"""
        booking.update_activity()  # 🔧 ATUALIZAR ATIVIDADE
        name = message.strip()
        
        # Validar nome
        if len(name) < 2:
            return "❌ Por favor, me diga seu nome completo.", None
        
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', name):
            return "❌ Nome deve conter apenas letras. Por favor, digite novamente.", None
        
        booking.customer_name = name.title()
        booking.step = BookingStep.COLLECTING_PHONE
        booking.attempts = 0
        
        return self._generate_phone_request(), None

    def _generate_phone_request(self) -> str:
        return "👤 **Nome registrado!**\n\n📞 **Qual é o seu telefone para contato?**\n\nEx: (11) 99999-9999"

    async def _process_phone_collection(self, user_id: str, message: str, booking: BookingData) -> Tuple[str, Optional[dict]]:
        """Processa coleta de telefone"""
        booking.update_activity()  # 🔧 ATUALIZAR ATIVIDADE
        phone = re.sub(r'[^\d]', '', message.strip())
        
        # Validar telefone brasileiro
        if len(phone) < 10 or len(phone) > 11:
            return "❌ Telefone deve ter 10 ou 11 dígitos. Ex: (11) 99999-9999", None
        
        # Formatar telefone
        if len(phone) == 11:
            formatted_phone = f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
        else:
            formatted_phone = f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        
        booking.customer_phone = formatted_phone
        booking.step = BookingStep.COLLECTING_EMAIL
        booking.attempts = 0
        
        return self._generate_email_request(), None

    def _generate_email_request(self) -> str:
        return "📞 **Telefone registrado!**\n\n📧 **Qual é o seu email?**\n\nEx: seu@email.com"

    async def _process_email_collection(self, user_id: str, message: str, booking: BookingData) -> Tuple[str, Optional[dict]]:
        """Processa coleta de email"""
        booking.update_activity()  # 🔧 ATUALIZAR ATIVIDADE
        email = message.strip().lower()
        
        # Validar email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return "❌ Email inválido. Por favor, digite um email válido.", None
        
        booking.customer_email = email
        booking.step = BookingStep.CONFIRMING
        booking.attempts = 0
        
        return self._generate_confirmation_message(booking), self._get_confirmation_buttons()

    def _generate_confirmation_message(self, booking: BookingData) -> str:
        """Gera mensagem de confirmação com proteção contra erros"""
        date_str = booking.date.strftime('%d/%m/%Y')
        weekday = self._get_weekday_name_pt(booking.date.weekday())
        
        # Debug logs para capturar o problema
        logger.info(f"DEBUG: booking.service_name = '{booking.service_name}' (type: {type(booking.service_name)})")
        logger.info(f"DEBUG: default_services keys = {list(self.default_services.keys())}")
        
        service_info = self.default_services.get(booking.service_name, {})
        logger.info(f"DEBUG: service_info = {service_info} (type: {type(service_info)})")
        
        # Verificar se service_info é um dicionário antes de chamar .get()
        if isinstance(service_info, dict):
            price = service_info.get('price', 'Consultar')
        else:
            logger.error(f"ERROR: service_info não é um dicionário! É {type(service_info)}: {service_info}")
            price = 'Consultar'
        
        return f"""✅ **Confirme seu agendamento:**

👤 **Nome:** {booking.customer_name}
📞 **Telefone:** {booking.customer_phone}
📧 **Email:** {booking.customer_email}
🔸 **Serviço:** {booking.service_name.title()}
💰 **Preço:** {price}
📅 **Data:** {weekday}, {date_str}
🕐 **Horário:** {booking.time}

Confirma este agendamento?"""

    def _get_confirmation_buttons(self) -> dict:
        """Gera botões para confirmação"""
        return {
            "type": "button",
            "body": {"text": "Confirmar agendamento?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "confirm_yes", "title": "✅ Sim, confirmar"}},
                    {"type": "reply", "reply": {"id": "confirm_no", "title": "❌ Cancelar"}}
                ]
            }
        }

    async def _process_confirmation(self, user_id: str, message: str, booking: BookingData, db: AsyncSession) -> Tuple[str, Optional[dict]]:
        """Processa confirmação do agendamento"""
        booking.update_activity()  # 🔧 ATUALIZAR ATIVIDADE
        message_lower = message.lower().strip()
        logger.info(f"DEBUG: Processing confirmation with message: '{message}'")
        
        # Verificar confirmação (texto ou botão)
        confirm_patterns = [
            'sim', 's', 'confirmar', 'ok', 'confirmo', 
            '✅ sim, confirmar', 'sim, confirmar',
            'confirm_yes',  # ID do botão
            '✅'  # Emoji apenas
        ]
        is_confirmation = any(pattern in message_lower for pattern in confirm_patterns)
        
        if is_confirmation:
            try:
                logger.info(f"DEBUG: Confirmation detected, saving booking to database for user {user_id}")
                
                # Buscar o usuário na database
                user_result = await db.execute(select(User).where(User.wa_id == user_id))
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"User not found: {user_id}")
                    return "❌ Erro: usuário não encontrado.", None
                
                # Atualizar dados do usuário se necessário
                if booking.customer_name and not user.nome:
                    user.nome = booking.customer_name
                if booking.customer_email and not user.email:
                    user.email = booking.customer_email  
                if booking.customer_phone and not user.telefone:
                    user.telefone = booking.customer_phone
                
                # Combinar data e horário para appointment_datetime
                appointment_datetime = datetime.combine(booking.date, datetime.strptime(booking.time, "%H:%M").time())
                
                # Gerar protocolo único
                protocol = f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}{user.id}"
                
                # Buscar business_id padrão (assumindo que existe um business principal)
                business_result = await db.execute(select(Business).limit(1))
                business = business_result.scalar_one_or_none()
                
                if not business:
                    logger.error("No business found in database")
                    return "❌ Erro: configuração de negócio não encontrada.", None
                
                business_id = business.id
                
                # Preparar notes com dados completos
                notes_data = {
                    "protocol": protocol,
                    "customer_name": booking.customer_name,
                    "customer_phone": booking.customer_phone,
                    "customer_email": booking.customer_email,
                    "service_name": booking.service_name,
                    "created_via": "WhatsApp Bot",
                    "booking_datetime": datetime.now().isoformat()
                }
                
                # Criar o agendamento na database
                appointment = Appointment(
                    user_id=user.id,
                    business_id=business_id,
                    service_id=booking.service_id,
                    date_time=appointment_datetime,
                    status='confirmado',
                    notes=f"Protocolo: {protocol}\nNome: {booking.customer_name}\nTelefone: {booking.customer_phone}\nEmail: {booking.customer_email}\nServiço: {booking.service_name}\nAgendado via WhatsApp Bot",
                    customer_notes=f"Agendamento realizado via WhatsApp",
                    confirmed_at=datetime.now(),
                    confirmed_by='customer'
                )
                
                db.add(appointment)
                await db.commit()
                await db.refresh(appointment)
                
                logger.info(f"✅ Appointment saved successfully: ID {appointment.id}, Protocol {protocol}")
                
                # Remover do cache ativo APENAS APÓS salvar com sucesso
                del self.active_bookings[user_id]
                
                return self._generate_success_message_with_protocol(booking, protocol), None
                    
            except Exception as e:
                logger.error(f"Erro ao salvar agendamento na database: {e}")
                await db.rollback()
                return "❌ Erro ao confirmar agendamento. Tente novamente.", self._get_confirmation_buttons()
        
        # Verificar cancelamento (texto ou botão)
        cancel_patterns = [
            'não', 'nao', 'n', 'cancelar', 'não quero', 
            '❌ cancelar', 'cancelar',
            'confirm_no',  # ID do botão
            '❌'  # Emoji apenas
        ]
        is_cancellation = any(pattern in message_lower for pattern in cancel_patterns)
        
        if is_cancellation:
            logger.info(f"DEBUG: Cancellation detected for user {user_id}")
            del self.active_bookings[user_id]
            return "❌ Agendamento cancelado. Digite 'agendar' se quiser tentar novamente.", None
        
        else:
            logger.info(f"DEBUG: Unrecognized confirmation response: '{message}'")
            return "Por favor, responda 'sim' para confirmar ou 'não' para cancelar.", self._get_confirmation_buttons()

    def _generate_success_message(self, booking: BookingData) -> str:
        date_str = booking.date.strftime('%d/%m/%Y')
        weekday = self._get_weekday_name_pt(booking.date.weekday())
        
        return f"""🎉 **Agendamento confirmado com sucesso!**

📋 **Resumo do seu agendamento:**
👤 **Nome:** {booking.customer_name}
🔸 **Serviço:** {booking.service_name.title()}
📅 **Data:** {weekday}, {date_str}
🕐 **Horário:** {booking.time}

📞 Entraremos em contato caso necessário.
⏰ **Lembre-se:** Chegue 10 minutos antes do horário.

✅ **Agendamento realizado!** Muito obrigado!"""

    def _generate_success_message_with_protocol(self, booking: BookingData, protocol: str) -> str:
        """Gera mensagem de sucesso com protocolo do agendamento"""
        date_str = booking.date.strftime('%d/%m/%Y')
        weekday = self._get_weekday_name_pt(booking.date.weekday())
        
        return f"""🎉 **Agendamento confirmado com sucesso!**

📋 **Resumo do seu agendamento:**
👤 **Nome:** {booking.customer_name}
🔸 **Serviço:** {booking.service_name.title()}
📅 **Data:** {weekday}, {date_str}
🕐 **Horário:** {booking.time}
🆔 **Protocolo:** {protocol}

📞 Entraremos em contato caso necessário.
⏰ **Lembre-se:** Chegue 10 minutos antes do horário.

✅ **Agendamento salvo na database!** Muito obrigado!"""
