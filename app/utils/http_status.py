"""
📋 HTTP Status Codes Padronizados - C002  
=========================================

Mapeamento consistente entre ErrorCode e HTTP Status Codes.
Garante status codes uniformes em toda a aplicação.

Autor: Claude AI
Data: 2025-09-11  
Status: Implementação C002 - Padronizar Response Schemas
"""

from typing import Dict
from enum import Enum
from app.schemas.response import ErrorCode


class HTTPStatus(int, Enum):
    """Status codes HTTP padronizados"""
    # Success (2xx)
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    
    # Client Error (4xx)
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Server Error (5xx)
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


# Mapeamento automático ErrorCode -> HTTPStatus
ERROR_CODE_TO_HTTP_STATUS: Dict[ErrorCode, HTTPStatus] = {
    # Validation errors (4xx)
    ErrorCode.VALIDATION_ERROR: HTTPStatus.BAD_REQUEST,
    ErrorCode.AUTHENTICATION_REQUIRED: HTTPStatus.UNAUTHORIZED,
    ErrorCode.PERMISSION_DENIED: HTTPStatus.FORBIDDEN,
    ErrorCode.RESOURCE_NOT_FOUND: HTTPStatus.NOT_FOUND,
    ErrorCode.RESOURCE_CONFLICT: HTTPStatus.CONFLICT,
    ErrorCode.RATE_LIMIT_EXCEEDED: HTTPStatus.TOO_MANY_REQUESTS,
    
    # Business logic errors (4xx)
    ErrorCode.BUSINESS_RULE_VIOLATION: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.INSUFFICIENT_BALANCE: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.OPERATION_NOT_ALLOWED: HTTPStatus.FORBIDDEN,
    
    # Server errors (5xx)
    ErrorCode.INTERNAL_SERVER_ERROR: HTTPStatus.INTERNAL_SERVER_ERROR,
    ErrorCode.DATABASE_ERROR: HTTPStatus.INTERNAL_SERVER_ERROR,
    ErrorCode.EXTERNAL_SERVICE_ERROR: HTTPStatus.BAD_GATEWAY,
    ErrorCode.TIMEOUT_ERROR: HTTPStatus.GATEWAY_TIMEOUT,
}


def get_http_status_for_error(error_code: ErrorCode) -> HTTPStatus:
    """
    Retorna o status HTTP apropriado para um ErrorCode
    
    Args:
        error_code: Código de erro da aplicação
        
    Returns:
        HTTPStatus correspondente
    """
    return ERROR_CODE_TO_HTTP_STATUS.get(error_code, HTTPStatus.INTERNAL_SERVER_ERROR)


def is_client_error(status_code: int) -> bool:
    """Verifica se é erro do cliente (4xx)"""
    return 400 <= status_code < 500


def is_server_error(status_code: int) -> bool:
    """Verifica se é erro do servidor (5xx)"""
    return 500 <= status_code < 600


def is_success(status_code: int) -> bool:
    """Verifica se é resposta de sucesso (2xx)"""
    return 200 <= status_code < 300
