"""
📋 Schemas Pydantic para Appointments - PADRONIZADO
===================================================

Schemas unificados que eliminam inconsistências entre:
- Backend SQLAlchemy model
- Frontend TypeScript interfaces  
- API responses e requests

Todos os campos seguem a mesma nomenclatura e tipos.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class AppointmentBase(BaseModel):
    """Schema base com campos comuns"""
    user_id: int
    business_id: int
    service_id: Optional[int] = None
    # ✅ C002: Campo com alias para API camelCase
    date_time: datetime = Field(serialization_alias="dateTime", description="Data e hora do agendamento")
    duration_minutes: int = Field(default=60, ge=15, le=480, serialization_alias="durationMinutes")  # 15min a 8h
    price: Decimal = Field(default=0.00, ge=0, decimal_places=2)
    status: str = Field(default="agendado")  # ✅ C001: Padrão unificado
    notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        # ✅ C001: Usando enum unificado do schemas/unified.py
        allowed_statuses = ['agendado', 'confirmado', 'realizado', 'cancelado', 'pendente']
        if v not in allowed_statuses:
            raise ValueError(f'Status deve ser um de: {allowed_statuses}')
        return v
    
    @validator('price', pre=True)
    def validate_price(cls, v):
        if isinstance(v, str):
            v = v.replace('R$', '').replace(' ', '').replace(',', '.')
        return float(v)
    
    class Config:
        # ✅ C002: Habilita aliases para conversão snake_case/camelCase
        populate_by_name = True  # Aceita tanto snake_case quanto camelCase
        use_enum_values = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class AppointmentCreate(AppointmentBase):
    """Schema para criar novos appointments"""
    # Campos específicos para criação
    customer_notes: Optional[str] = None
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "user_id": 1,
                "business_id": 1, 
                "service_id": 1,
                "date_time": "2025-09-08T14:30:00-03:00",
                "duration_minutes": 60,
                "price": 50.00,
                "notes": "Cliente prefere horário da tarde",
                "customer_notes": "Primeira vez no salão"
            }
        }


class AppointmentUpdate(BaseModel):
    """Schema para atualizar appointments (campos opcionais)"""
    # ✅ C002: Campos com aliases para API camelCase
    date_time: Optional[datetime] = Field(None, serialization_alias="dateTime")
    duration_minutes: Optional[int] = Field(None, ge=15, le=480, serialization_alias="durationMinutes")
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    status: Optional[str] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ['pendente', 'confirmado', 'cancelado', 'concluido', 'bloqueado']
            if v not in allowed_statuses:
                raise ValueError(f'Status deve ser um de: {allowed_statuses}')
        return v


class AppointmentResponse(AppointmentBase):
    """Schema para responses da API - PADRONIZADO com frontend"""
    id: int
    end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Campos relacionados (JOINs com outras tabelas)
    cliente_nome: Optional[str] = None  # user.nome
    cliente_telefone: Optional[str] = None  # user.telefone  
    cliente_email: Optional[str] = None  # user.email
    
    servico_nome: Optional[str] = None  # service.name
    servico_descricao: Optional[str] = None  # service.description
    
    business_name: Optional[str] = None  # business.name
    
    # Campos de auditoria opcionais
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class AppointmentSummary(BaseModel):
    """Schema resumido para listas e dashboards"""
    id: int
    date_time: datetime
    duration_minutes: int
    price: Decimal
    status: str
    cliente_nome: Optional[str] = None
    servico_nome: Optional[str] = None
    
    class Config:
        from_attributes = True


class AppointmentsListResponse(BaseModel):
    """Response padronizado para listas de appointments"""
    appointments: List[AppointmentResponse]
    total: int
    page: int = 1
    per_page: int = 10
    has_more: bool
    
    @validator('has_more', pre=True, always=True)
    def calculate_has_more(cls, v, values):
        if 'total' in values and 'page' in values and 'per_page' in values:
            return (values['page'] * values['per_page']) < values['total']
        return False


class AppointmentStats(BaseModel):
    """Estatísticas de appointments para dashboard"""
    total_appointments: int
    appointments_today: int
    appointments_week: int
    appointments_month: int
    
    pending_count: int
    confirmed_count: int
    completed_count: int
    cancelled_count: int
    
    total_revenue: Decimal
    revenue_today: Decimal
    revenue_week: Decimal
    revenue_month: Decimal
    
    avg_appointment_value: Decimal
    most_popular_service: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
