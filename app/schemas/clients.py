from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int

class ClientBase(BaseModel):
    nome: Optional[str] = Field(None, max_length=255)
    telefone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None

class ClientCreate(ClientBase):
    wa_id: str = Field(..., max_length=50)
    telefone: str = Field(..., max_length=20)
    nome: str = Field(..., max_length=255)

class ClientUpdate(ClientBase):
    pass

class ClientStatistics(BaseModel):
    total_conversations: int = 0
    total_messages: int = 0
    total_appointments: int = 0
    last_interaction: Optional[datetime] = None
    avg_response_time_seconds: float = 0.0

class ClientResponse(ClientBase):
    id: int
    wa_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_conversations: int = 0
    total_messages: int = 0
    total_appointments: int = 0
    last_interaction: Optional[datetime] = None
    status: str = "active"  # active, inactive, new, vip
    
    class Config:
        from_attributes = True

class ClientDetailResponse(ClientResponse):
    statistics: ClientStatistics

class ClientStats(BaseModel):
    total: int = 0
    active: int = 0
    new_this_month: int = 0
    inactive: int = 0
