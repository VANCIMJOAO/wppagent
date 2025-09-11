"""
🔄 Response Schemas Padronizados - C002
=======================================

Wrapper ApiResponse<T> consistente para todas as APIs.
Garante estrutura uniforme de resposta com error handling padronizado.

Estrutura: {success, data, error, meta}
- success: boolean indicando se operação foi bem-sucedida
- data: conteúdo da resposta (quando success=true)
- error: detalhes do erro (quando success=false)
- meta: metadados opcionais (paginação, timing, etc.)

Autor: Claude AI  
Data: 2025-09-11
Status: Implementação C002 - Padronizar Response Schemas
"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
import uuid


# =================================================================================
#                              TIPOS BASE
# =================================================================================

T = TypeVar('T')  # Tipo genérico para o conteúdo de data


class ErrorCode(str, Enum):
    """Códigos de erro padronizados"""
    # Validation errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Business logic errors (4xx)
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    
    # Server errors (5xx)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"


class PaginationMeta(BaseModel):
    """Metadados de paginação padronizados"""
    total: int = Field(..., description="Total de itens")
    limit: int = Field(..., description="Limite por página")
    offset: int = Field(..., description="Offset atual")
    page: int = Field(..., description="Página atual (1-indexed)")
    pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Tem próxima página")
    has_prev: bool = Field(..., description="Tem página anterior")
    
    @classmethod
    def create(cls, total: int, limit: int, offset: int) -> "PaginationMeta":
        """Factory method para criar metadados de paginação"""
        page = (offset // limit) + 1
        pages = (total + limit - 1) // limit  # Ceiling division
        
        return cls(
            total=total,
            limit=limit,
            offset=offset,
            page=page,
            pages=pages,
            has_next=offset + limit < total,
            has_prev=offset > 0
        )


class ErrorDetail(BaseModel):
    """Detalhes padronizados de erro"""
    code: ErrorCode = Field(..., description="Código do erro")
    message: str = Field(..., description="Mensagem do erro")
    field: Optional[str] = Field(None, description="Campo relacionado ao erro")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Campo obrigatório não informado",
                "field": "nome",
                "details": {"expected_type": "string", "received": "null"}
            }
        }


class ApiMeta(BaseModel):
    """Metadados opcionais da resposta"""
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp da resposta"
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="ID único da requisição"
    )
    execution_time_ms: Optional[int] = Field(None, description="Tempo de execução em ms")
    pagination: Optional[PaginationMeta] = Field(None, description="Metadados de paginação")
    version: str = Field(default="1.0", description="Versão da API")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "timestamp": "2025-09-11T16:45:00.123Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "execution_time_ms": 150,
                "version": "1.0"
            }
        }


# =================================================================================
#                        WRAPPER PRINCIPAL ApiResponse<T>
# =================================================================================

class ApiResponse(BaseModel, Generic[T]):
    """
    🔄 Wrapper padronizado para todas as respostas da API
    
    Estrutura consistente:
    - success: boolean indicando sucesso/falha
    - data: conteúdo quando success=true  
    - error: detalhes quando success=false
    - meta: metadados opcionais (paginação, timing, etc.)
    """
    success: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    data: Optional[T] = Field(None, description="Dados da resposta (quando success=true)")
    error: Optional[ErrorDetail] = Field(None, description="Detalhes do erro (quando success=false)")
    meta: Optional[ApiMeta] = Field(default_factory=ApiMeta, description="Metadados da resposta")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 1, "name": "Example"},
                "error": None,
                "meta": {
                    "timestamp": "2025-09-11T16:45:00.123Z",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000",
                    "version": "1.0"
                }
            }
        }
    
    @classmethod
    def success_response(
        cls, 
        data: T, 
        meta: Optional[ApiMeta] = None,
        execution_time_ms: Optional[int] = None
    ) -> "ApiResponse[T]":
        """Factory method para respostas de sucesso"""
        if meta is None:
            meta = ApiMeta()
        
        if execution_time_ms is not None:
            meta.execution_time_ms = execution_time_ms
            
        return cls(success=True, data=data, error=None, meta=meta)
    
    @classmethod
    def error_response(
        cls,
        error_code: ErrorCode,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        meta: Optional[ApiMeta] = None
    ) -> "ApiResponse[None]":
        """Factory method para respostas de erro"""
        if meta is None:
            meta = ApiMeta()
            
        error = ErrorDetail(
            code=error_code,
            message=message,
            field=field,
            details=details
        )
        
        return cls(success=False, data=None, error=error, meta=meta)
    
    @classmethod
    def paginated_response(
        cls,
        data: List[Any],
        total: int,
        limit: int,
        offset: int,
        execution_time_ms: Optional[int] = None
    ) -> "ApiResponse[List[Any]]":
        """Factory method para respostas paginadas"""
        pagination = PaginationMeta.create(total, limit, offset)
        meta = ApiMeta(pagination=pagination)
        
        if execution_time_ms is not None:
            meta.execution_time_ms = execution_time_ms
            
        return cls(success=True, data=data, error=None, meta=meta)


# =================================================================================
#                           SHORTCUTS E ALIASES
# =================================================================================

# Type aliases para melhor legibilidade
SuccessResponse = ApiResponse[T]
ErrorResponse = ApiResponse[None]
PaginatedResponse = ApiResponse[List[T]]

# Shortcuts para respostas comuns
class CommonResponses:
    """Respostas comuns pré-definidas"""
    
    @staticmethod
    def success(data: T = None, message: str = "Operação realizada com sucesso") -> ApiResponse[T]:
        """Resposta de sucesso genérica"""
        return ApiResponse.success_response(data)
    
    @staticmethod
    def created(data: T, message: str = "Recurso criado com sucesso") -> ApiResponse[T]:
        """Resposta para recursos criados (201)"""
        return ApiResponse.success_response(data)
    
    @staticmethod
    def not_found(resource: str = "Recurso") -> ApiResponse[None]:
        """Resposta para recurso não encontrado (404)"""
        return ApiResponse.error_response(
            ErrorCode.RESOURCE_NOT_FOUND,
            f"{resource} não encontrado"
        )
    
    @staticmethod
    def validation_error(message: str, field: str = None) -> ApiResponse[None]:
        """Resposta para erro de validação (400)"""
        return ApiResponse.error_response(
            ErrorCode.VALIDATION_ERROR,
            message,
            field=field
        )
    
    @staticmethod
    def permission_denied(message: str = "Permissão negada") -> ApiResponse[None]:
        """Resposta para permissão negada (403)"""
        return ApiResponse.error_response(
            ErrorCode.PERMISSION_DENIED,
            message
        )
    
    @staticmethod
    def internal_error(message: str = "Erro interno do servidor") -> ApiResponse[None]:
        """Resposta para erro interno (500)"""
        return ApiResponse.error_response(
            ErrorCode.INTERNAL_SERVER_ERROR,
            message
        )


# =================================================================================
#                        SCHEMAS ESPECÍFICOS COMUNS
# =================================================================================

class HealthCheckData(BaseModel):
    """Dados para health check"""
    status: str = Field(..., description="Status da aplicação")
    timestamp: str = Field(..., description="Timestamp da verificação")
    service: str = Field(..., description="Nome do serviço")
    version: str = Field(..., description="Versão da aplicação")
    components: Dict[str, Any] = Field(default_factory=dict, description="Status dos componentes")


class OperationResult(BaseModel):
    """Resultado de operações simples"""
    operation: str = Field(..., description="Tipo de operação")
    affected_count: int = Field(default=0, description="Número de registros afetados")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")


# Type aliases para responses específicos
HealthCheckResponse = ApiResponse[HealthCheckData]
OperationResponse = ApiResponse[OperationResult]
