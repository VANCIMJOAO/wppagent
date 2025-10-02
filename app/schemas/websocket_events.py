"""
Schemas de Validação para Eventos WebSocket
==========================================

CORREÇÃO: Schemas Pydantic para validação de dados dos eventos WebSocket.
Garante integridade dos dados e previne bugs silenciosos.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class AppointmentStatus(str, Enum):
    """Status de agendamento"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    RESCHEDULED = "rescheduled"


class MessageStatus(str, Enum):
    """Status de mensagem"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class UserPresence(str, Enum):
    """Status de presença do usuário"""
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


# ============= SCHEMAS BASE =============

class BaseEventData(BaseModel):
    """Schema base para todos os eventos"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="system", description="Origem do evento")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============= SCHEMAS DE AGENDAMENTOS =============

class AppointmentData(BaseModel):
    """Schema para dados de agendamento"""
    id: int = Field(..., description="ID do agendamento")
    client_name: str = Field(..., min_length=1, max_length=255, description="Nome do cliente")
    client_phone: Optional[str] = Field(None, description="Telefone do cliente")
    service_name: str = Field(..., min_length=1, max_length=255, description="Nome do serviço")
    business_name: str = Field(..., min_length=1, max_length=255, description="Nome do negócio")
    date_time: datetime = Field(..., description="Data e hora do agendamento")
    status: AppointmentStatus = Field(..., description="Status do agendamento")
    duration_minutes: Optional[int] = Field(None, ge=1, le=480, description="Duração em minutos")
    price: Optional[float] = Field(None, ge=0, description="Preço do serviço")
    notes: Optional[str] = Field(None, max_length=1000, description="Observações")
    created_by: str = Field(..., min_length=1, max_length=255, description="Criado por")
    updated_by: Optional[str] = Field(None, max_length=255, description="Atualizado por")
    
    @validator('client_phone')
    def validate_phone(cls, v):
        if v is not None:
            # Remove caracteres não numéricos
            phone_digits = ''.join(filter(str.isdigit, v))
            if len(phone_digits) < 10:
                raise ValueError('Telefone deve ter pelo menos 10 dígitos')
        return v


class AppointmentCreatedData(BaseEventData):
    """Schema para evento de agendamento criado"""
    appointment: AppointmentData = Field(..., description="Dados do agendamento")
    message: str = Field(..., min_length=1, max_length=500, description="Mensagem do evento")


class AppointmentUpdatedData(BaseEventData):
    """Schema para evento de agendamento atualizado"""
    appointment: AppointmentData = Field(..., description="Dados do agendamento")
    changes: Dict[str, Any] = Field(..., description="Campos alterados")
    message: str = Field(..., min_length=1, max_length=500, description="Mensagem do evento")


class AppointmentCancelledData(BaseEventData):
    """Schema para evento de agendamento cancelado"""
    appointment_id: int = Field(..., description="ID do agendamento")
    client_name: str = Field(..., min_length=1, max_length=255, description="Nome do cliente")
    reason: Optional[str] = Field(None, max_length=500, description="Motivo do cancelamento")
    message: str = Field(..., min_length=1, max_length=500, description="Mensagem do evento")


class AppointmentConfirmedData(BaseEventData):
    """Schema para evento de agendamento confirmado"""
    appointment: AppointmentData = Field(..., description="Dados do agendamento")
    confirmation_method: str = Field(..., description="Método de confirmação")
    message: str = Field(..., min_length=1, max_length=500, description="Mensagem do evento")


class AppointmentReminderData(BaseEventData):
    """Schema para evento de lembrete de agendamento"""
    appointment: AppointmentData = Field(..., description="Dados do agendamento")
    reminder_type: str = Field(..., description="Tipo de lembrete")
    reminder_time: datetime = Field(..., description="Horário do lembrete")
    message: str = Field(..., min_length=1, max_length=500, description="Mensagem do evento")


# ============= SCHEMAS DE MENSAGENS =============

class MessageData(BaseModel):
    """Schema para dados de mensagem"""
    id: str = Field(..., min_length=1, max_length=255, description="ID da mensagem")
    content: str = Field(..., min_length=1, max_length=4000, description="Conteúdo da mensagem")
    sender_id: str = Field(..., min_length=1, max_length=255, description="ID do remetente")
    sender_name: str = Field(..., min_length=1, max_length=255, description="Nome do remetente")
    conversation_id: str = Field(..., min_length=1, max_length=255, description="ID da conversa")
    message_type: str = Field(default="text", description="Tipo da mensagem")
    status: MessageStatus = Field(default=MessageStatus.SENT, description="Status da mensagem")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Data de criação")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados da mensagem")


class NewMessageData(BaseEventData):
    """Schema para evento de nova mensagem"""
    message: MessageData = Field(..., description="Dados da mensagem")
    conversation_title: Optional[str] = Field(None, max_length=255, description="Título da conversa")


class MessageStatusUpdateData(BaseEventData):
    """Schema para evento de atualização de status de mensagem"""
    message_id: str = Field(..., min_length=1, max_length=255, description="ID da mensagem")
    status: MessageStatus = Field(..., description="Novo status")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Data da atualização")


class TypingData(BaseEventData):
    """Schema para evento de digitação"""
    user_id: str = Field(..., min_length=1, max_length=255, description="ID do usuário")
    user_name: str = Field(..., min_length=1, max_length=255, description="Nome do usuário")
    conversation_id: str = Field(..., min_length=1, max_length=255, description="ID da conversa")
    is_typing: bool = Field(..., description="Se está digitando")


# ============= SCHEMAS DE SISTEMA =============

class UserPresenceData(BaseEventData):
    """Schema para evento de presença do usuário"""
    user_id: str = Field(..., min_length=1, max_length=255, description="ID do usuário")
    user_name: str = Field(..., min_length=1, max_length=255, description="Nome do usuário")
    status: UserPresence = Field(..., description="Status de presença")
    last_seen: Optional[datetime] = Field(None, description="Última vez visto")


class SystemNotificationData(BaseEventData):
    """Schema para evento de notificação do sistema"""
    title: str = Field(..., min_length=1, max_length=255, description="Título da notificação")
    message: str = Field(..., min_length=1, max_length=1000, description="Mensagem da notificação")
    notification_type: str = Field(..., description="Tipo da notificação")
    priority: int = Field(default=1, ge=1, le=5, description="Prioridade da notificação")
    action_url: Optional[str] = Field(None, description="URL de ação")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração")


class HeartbeatData(BaseEventData):
    """Schema para evento de heartbeat"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do heartbeat")
    server_time: datetime = Field(default_factory=datetime.utcnow, description="Hora do servidor")


class HeartbeatResponseData(BaseEventData):
    """Schema para resposta de heartbeat"""
    client_timestamp: datetime = Field(..., description="Timestamp do cliente")
    server_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do servidor")
    latency_ms: Optional[int] = Field(None, ge=0, description="Latência em milissegundos")


# ============= SCHEMAS DE CACHE =============

class CacheInvalidationData(BaseEventData):
    """Schema para evento de invalidação de cache"""
    cache_key: str = Field(..., min_length=1, max_length=255, description="Chave do cache")
    invalidation_type: str = Field(..., description="Tipo de invalidação")
    affected_entities: List[str] = Field(..., description="Entidades afetadas")
    reason: Optional[str] = Field(None, max_length=500, description="Motivo da invalidação")


# ============= SCHEMAS DE ERRO =============

class ErrorData(BaseEventData):
    """Schema para evento de erro"""
    error_code: str = Field(..., min_length=1, max_length=50, description="Código do erro")
    error_message: str = Field(..., min_length=1, max_length=1000, description="Mensagem do erro")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detalhes do erro")
    request_id: Optional[str] = Field(None, description="ID da requisição")


# ============= MAPEAMENTO DE EVENTOS =============

EVENT_SCHEMA_MAP = {
    # Agendamentos
    "appointment_created": AppointmentCreatedData,
    "appointment_updated": AppointmentUpdatedData,
    "appointment_cancelled": AppointmentCancelledData,
    "appointment_confirmed": AppointmentConfirmedData,
    "appointment_reminder": AppointmentReminderData,
    
    # Mensagens
    "new_message": NewMessageData,
    "message_sent": MessageStatusUpdateData,
    "message_delivered": MessageStatusUpdateData,
    "message_read": MessageStatusUpdateData,
    "typing_start": TypingData,
    "typing_stop": TypingData,
    "conversation_updated": NewMessageData,
    
    # Sistema
    "user_presence": UserPresenceData,
    "system_notification": SystemNotificationData,
    "heartbeat": HeartbeatData,
    "heartbeat_response": HeartbeatResponseData,
    "cache_invalidation": CacheInvalidationData,
    "error": ErrorData,
}


def validate_event_data(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    CORREÇÃO: Valida dados do evento usando schema Pydantic
    
    Args:
        event_type: Tipo do evento
        data: Dados do evento
        
    Returns:
        Dados validados e serializados
        
    Raises:
        ValidationError: Se os dados são inválidos
    """
    if event_type not in EVENT_SCHEMA_MAP:
        # Para eventos sem schema, retorna os dados como estão
        return data
    
    schema_class = EVENT_SCHEMA_MAP[event_type]
    
    try:
        # Valida e serializa os dados
        validated_data = schema_class(**data)
        return validated_data.model_dump()
    except Exception as e:
        raise ValueError(f"Erro de validação para evento '{event_type}': {e}")


def get_event_schema(event_type: str) -> Optional[BaseModel]:
    """
    CORREÇÃO: Retorna o schema para um tipo de evento
    
    Args:
        event_type: Tipo do evento
        
    Returns:
        Classe do schema ou None se não existir
    """
    return EVENT_SCHEMA_MAP.get(event_type)


def list_available_schemas() -> Dict[str, str]:
    """
    CORREÇÃO: Lista todos os schemas disponíveis
    
    Returns:
        Dicionário com tipos de eventos e suas classes de schema
    """
    return {
        event_type: schema_class.__name__ 
        for event_type, schema_class in EVENT_SCHEMA_MAP.items()
    }
