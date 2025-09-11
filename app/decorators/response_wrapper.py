"""
🎯 Decoradores para Padronização de Responses - C002
==================================================

Decoradores para aplicar automaticamente o wrapper ApiResponse
a endpoints FastAPI, garantindo consistência em toda a aplicação.

Funcionalidades:
- Wrapping automático de responses em ApiResponse<T>
- Error handling padronizado 
- Medição de tempo de execução
- Logging estruturado
- Exception mapping para ErrorCodes

Autor: Claude AI
Data: 2025-09-11
Status: Implementação C002 - Padronizar Response Schemas
"""

import time
import logging
import asyncio
from functools import wraps
from typing import Any, Callable, Optional, Type, Union
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.schemas.response import ApiResponse, ErrorCode, ErrorDetail, ApiMeta
from app.utils.http_status import get_http_status_for_error, HTTPStatus


logger = logging.getLogger(__name__)


def api_response_wrapper(
    success_status: HTTPStatus = HTTPStatus.OK,
    measure_time: bool = True,
    log_requests: bool = True
):
    """
    Decorador para padronizar responses da API
    
    Args:
        success_status: Status HTTP para respostas de sucesso
        measure_time: Se deve medir tempo de execução
        log_requests: Se deve logar requisições
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> JSONResponse:
            start_time = time.time() if measure_time else None
            request_id = None
            
            try:
                # Log da requisição
                if log_requests:
                    logger.info(f"🔄 Iniciando {func.__name__}", extra={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    })
                
                # Executar função
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Calcular tempo de execução
                execution_time_ms = None
                if measure_time and start_time:
                    execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Se o resultado já é um ApiResponse, apenas retornamos
                if isinstance(result, ApiResponse):
                    if execution_time_ms and result.meta:
                        result.meta.execution_time_ms = execution_time_ms
                    
                    status_code = success_status if result.success else get_http_status_for_error(result.error.code)
                    return JSONResponse(content=result.dict(), status_code=status_code)
                
                # Wrapper automático para outros tipos
                response = ApiResponse.success_response(
                    data=result,
                    execution_time_ms=execution_time_ms
                )
                
                # Log de sucesso
                if log_requests:
                    logger.info(f"✅ {func.__name__} concluída", extra={
                        "function": func.__name__,
                        "execution_time_ms": execution_time_ms,
                        "success": True
                    })
                
                return JSONResponse(content=response.dict(), status_code=success_status)
                
            except HTTPException as e:
                # Mapear HTTPException para ErrorCode
                error_code = _map_http_exception_to_error_code(e.status_code)
                response = ApiResponse.error_response(
                    error_code=error_code,
                    message=str(e.detail),
                    details={"original_status_code": e.status_code}
                )
                
                if log_requests:
                    logger.warning(f"⚠️ HTTPException em {func.__name__}: {e.detail}", extra={
                        "function": func.__name__,
                        "status_code": e.status_code,
                        "detail": e.detail
                    })
                
                return JSONResponse(content=response.dict(), status_code=e.status_code)
                
            except ValidationError as e:
                # Erro de validação Pydantic
                response = ApiResponse.error_response(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="Erro de validação dos dados",
                    details={"validation_errors": e.errors()}
                )
                
                if log_requests:
                    logger.warning(f"⚠️ ValidationError em {func.__name__}", extra={
                        "function": func.__name__,
                        "errors": e.errors()
                    })
                
                return JSONResponse(content=response.dict(), status_code=HTTPStatus.BAD_REQUEST)
                
            except Exception as e:
                # Erro genérico
                execution_time_ms = None
                if measure_time and start_time:
                    execution_time_ms = int((time.time() - start_time) * 1000)
                
                response = ApiResponse.error_response(
                    error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                    message="Erro interno do servidor",
                    details={
                        "exception_type": type(e).__name__,
                        "exception_message": str(e)
                    }
                )
                
                if execution_time_ms and response.meta:
                    response.meta.execution_time_ms = execution_time_ms
                
                if log_requests:
                    logger.error(f"❌ Erro em {func.__name__}: {str(e)}", extra={
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                        "execution_time_ms": execution_time_ms
                    }, exc_info=True)
                
                return JSONResponse(content=response.dict(), status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> JSONResponse:
            start_time = time.time() if measure_time else None
            
            try:
                # Log da requisição
                if log_requests:
                    logger.info(f"🔄 Iniciando {func.__name__}", extra={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs)
                    })
                
                # Executar função
                result = func(*args, **kwargs)
                
                # Calcular tempo de execução
                execution_time_ms = None
                if measure_time and start_time:
                    execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Se o resultado já é um ApiResponse, apenas retornamos
                if isinstance(result, ApiResponse):
                    if execution_time_ms and result.meta:
                        result.meta.execution_time_ms = execution_time_ms
                    
                    status_code = success_status if result.success else get_http_status_for_error(result.error.code)
                    return JSONResponse(content=result.dict(), status_code=status_code)
                
                # Wrapper automático para outros tipos
                response = ApiResponse.success_response(
                    data=result,
                    execution_time_ms=execution_time_ms
                )
                
                # Log de sucesso
                if log_requests:
                    logger.info(f"✅ {func.__name__} concluída", extra={
                        "function": func.__name__,
                        "execution_time_ms": execution_time_ms,
                        "success": True
                    })
                
                return JSONResponse(content=response.dict(), status_code=success_status)
                
            except HTTPException as e:
                # Mapear HTTPException para ErrorCode
                error_code = _map_http_exception_to_error_code(e.status_code)
                response = ApiResponse.error_response(
                    error_code=error_code,
                    message=str(e.detail),
                    details={"original_status_code": e.status_code}
                )
                
                if log_requests:
                    logger.warning(f"⚠️ HTTPException em {func.__name__}: {e.detail}", extra={
                        "function": func.__name__,
                        "status_code": e.status_code,
                        "detail": e.detail
                    })
                
                return JSONResponse(content=response.dict(), status_code=e.status_code)
                
            except ValidationError as e:
                # Erro de validação Pydantic
                response = ApiResponse.error_response(
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="Erro de validação dos dados",
                    details={"validation_errors": e.errors()}
                )
                
                if log_requests:
                    logger.warning(f"⚠️ ValidationError em {func.__name__}", extra={
                        "function": func.__name__,
                        "errors": e.errors()
                    })
                
                return JSONResponse(content=response.dict(), status_code=HTTPStatus.BAD_REQUEST)
                
            except Exception as e:
                # Erro genérico
                execution_time_ms = None
                if measure_time and start_time:
                    execution_time_ms = int((time.time() - start_time) * 1000)
                
                response = ApiResponse.error_response(
                    error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                    message="Erro interno do servidor",
                    details={
                        "exception_type": type(e).__name__,
                        "exception_message": str(e)
                    }
                )
                
                if execution_time_ms and response.meta:
                    response.meta.execution_time_ms = execution_time_ms
                
                if log_requests:
                    logger.error(f"❌ Erro em {func.__name__}: {str(e)}", extra={
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                        "execution_time_ms": execution_time_ms
                    }, exc_info=True)
                
                return JSONResponse(content=response.dict(), status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        
        # Retornar wrapper apropriado baseado no tipo da função
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _map_http_exception_to_error_code(status_code: int) -> ErrorCode:
    """Mapeia status HTTP para ErrorCode"""
    mapping = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_REQUIRED,
        403: ErrorCode.PERMISSION_DENIED,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        409: ErrorCode.RESOURCE_CONFLICT,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_SERVER_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_ERROR,
        503: ErrorCode.EXTERNAL_SERVICE_ERROR,
        504: ErrorCode.TIMEOUT_ERROR,
    }
    
    return mapping.get(status_code, ErrorCode.INTERNAL_SERVER_ERROR)


# Decoradores especializados
def success_response(status: HTTPStatus = HTTPStatus.OK):
    """Decorador para endpoints de sucesso"""
    return api_response_wrapper(success_status=status)


def created_response():
    """Decorador para endpoints de criação"""
    return api_response_wrapper(success_status=HTTPStatus.CREATED)


def no_content_response():
    """Decorador para endpoints sem conteúdo"""
    return api_response_wrapper(success_status=HTTPStatus.NO_CONTENT)


def paginated_response():
    """Decorador para endpoints paginados"""
    return api_response_wrapper(success_status=HTTPStatus.OK, measure_time=True)
