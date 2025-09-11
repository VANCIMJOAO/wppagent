"""
🔧 Middleware para Padronização Automática de Responses - C002
=============================================================

Middleware que aplica automaticamente o wrapper ApiResponse<T>
a todos os endpoints da aplicação, garantindo consistência total.

Funcionalidades:
- Intercepta todas as responses
- Aplica wrapper automático quando necessário
- Preserva responses já no formato correto
- Error handling global
- Logging estruturado

Autor: Claude AI
Data: 2025-09-11
Status: Implementação C002 - Middleware Global
"""

import time
import json
import uuid
from typing import Callable, Any
from datetime import datetime
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.schemas.response import ApiResponse, ErrorCode, ApiMeta
from app.utils.http_status import HTTPStatus, is_success, is_client_error, is_server_error
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ApiResponseMiddleware(BaseHTTPMiddleware):
    """
    🔧 Middleware para padronização automática de responses
    
    Aplica wrapper ApiResponse<T> a todas as respostas que não estejam
    já no formato padronizado.
    """
    
    def __init__(self, app, enable_auto_wrap: bool = True, measure_time: bool = True):
        super().__init__(app)
        self.enable_auto_wrap = enable_auto_wrap
        self.measure_time = measure_time
        
        # Paths que devem ser ignorados pelo middleware
        self.ignore_paths = {
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/favicon.ico",
            "/static",
            "/health",  # Health check pode ter formato próprio
            "/metrics", # Prometheus metrics têm formato próprio
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Processa requisição e response"""
        
        # Ignorar paths específicos
        if any(request.url.path.startswith(path) for path in self.ignore_paths):
            return await call_next(request)
        
        # Gerar request_id único
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Medir tempo de execução
        start_time = time.time() if self.measure_time else None
        
        # Log da requisição
        logger.info(f"🔄 {request.method} {request.url.path}", extra={
            "method": request.method,
            "path": request.url.path,
            "request_id": request_id,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        })
        
        try:
            # Executar próximo middleware/endpoint
            response = await call_next(request)
            
            # Calcular tempo de execução
            execution_time_ms = None
            if self.measure_time and start_time:
                execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Processar response
            wrapped_response = await self._process_response(
                request, response, execution_time_ms, request_id
            )
            
            # Log de sucesso
            logger.info(f"✅ {request.method} {request.url.path} -> {wrapped_response.status_code}", extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": wrapped_response.status_code,
                "execution_time_ms": execution_time_ms,
                "request_id": request_id
            })
            
            return wrapped_response
            
        except Exception as e:
            # Erro não tratado - criar response de erro
            execution_time_ms = None
            if self.measure_time and start_time:
                execution_time_ms = int((time.time() - start_time) * 1000)
            
            logger.error(f"❌ Erro não tratado em {request.method} {request.url.path}: {str(e)}", extra={
                "method": request.method,
                "path": request.url.path,
                "exception_type": type(e).__name__,
                "execution_time_ms": execution_time_ms,
                "request_id": request_id
            }, exc_info=True)
            
            # Criar response de erro padronizado
            error_response = ApiResponse.error_response(
                error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                message="Erro interno do servidor",
                details={
                    "exception_type": type(e).__name__,
                    "request_id": request_id
                }
            )
            
            if execution_time_ms and error_response.meta:
                error_response.meta.execution_time_ms = execution_time_ms
                error_response.meta.request_id = request_id
            
            return JSONResponse(
                content=error_response.dict(),
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    async def _process_response(
        self, 
        request: Request, 
        response: Response, 
        execution_time_ms: int,
        request_id: str
    ) -> Response:
        """Processa e padroniza response se necessário"""
        
        # Se não é JSON, retornar sem modificar
        if not isinstance(response, JSONResponse):
            return response
        
        # Se auto-wrap está desabilitado, apenas adicionar headers
        if not self.enable_auto_wrap:
            response.headers["X-Request-ID"] = request_id
            if execution_time_ms:
                response.headers["X-Execution-Time-Ms"] = str(execution_time_ms)
            return response
        
        try:
            # Ler conteúdo da response
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            if not body:
                # Response vazia - criar response padronizado
                api_response = ApiResponse.success_response(
                    data=None,
                    execution_time_ms=execution_time_ms
                )
                api_response.meta.request_id = request_id
                
                return JSONResponse(
                    content=api_response.dict(),
                    status_code=response.status_code,
                    headers=response.headers
                )
            
            # Parse do JSON
            content = json.loads(body.decode())
            
            # Verificar se já está no formato ApiResponse
            if self._is_api_response_format(content):
                # Já está no formato correto - apenas adicionar metadados se necessário
                if "meta" in content and execution_time_ms:
                    content["meta"]["execution_time_ms"] = execution_time_ms
                    content["meta"]["request_id"] = request_id
                
                return JSONResponse(
                    content=content,
                    status_code=response.status_code,
                    headers={**response.headers, "X-Request-ID": request_id}
                )
            
            # Aplicar wrapper automático baseado no status code
            if is_success(response.status_code):
                # Response de sucesso - wrapper data
                api_response = ApiResponse.success_response(
                    data=content,
                    execution_time_ms=execution_time_ms
                )
            elif is_client_error(response.status_code):
                # Erro do cliente - tentar extrair mensagem
                message = self._extract_error_message(content)
                error_code = self._map_status_to_error_code(response.status_code)
                
                api_response = ApiResponse.error_response(
                    error_code=error_code,
                    message=message,
                    details={"original_content": content}
                )
                
                if execution_time_ms and api_response.meta:
                    api_response.meta.execution_time_ms = execution_time_ms
            
            elif is_server_error(response.status_code):
                # Erro do servidor
                message = self._extract_error_message(content, default="Erro interno do servidor")
                
                api_response = ApiResponse.error_response(
                    error_code=ErrorCode.INTERNAL_SERVER_ERROR,
                    message=message,
                    details={"original_content": content}
                )
                
                if execution_time_ms and api_response.meta:
                    api_response.meta.execution_time_ms = execution_time_ms
            
            else:
                # Status code desconhecido - tratar como sucesso
                api_response = ApiResponse.success_response(
                    data=content,
                    execution_time_ms=execution_time_ms
                )
            
            # Adicionar request_id
            if api_response.meta:
                api_response.meta.request_id = request_id
            
            return JSONResponse(
                content=api_response.dict(),
                status_code=response.status_code,
                headers={**response.headers, "X-Request-ID": request_id}
            )
            
        except json.JSONDecodeError:
            # Response não é JSON válido - retornar sem modificar
            response.headers["X-Request-ID"] = request_id
            if execution_time_ms:
                response.headers["X-Execution-Time-Ms"] = str(execution_time_ms)
            return response
        
        except Exception as e:
            logger.error(f"Erro ao processar response: {e}", extra={
                "request_id": request_id,
                "status_code": response.status_code
            })
            
            # Em caso de erro, retornar response original
            response.headers["X-Request-ID"] = request_id
            return response
    
    def _is_api_response_format(self, content: Any) -> bool:
        """Verifica se o conteúdo já está no formato ApiResponse"""
        if not isinstance(content, dict):
            return False
        
        # Verifica se tem a estrutura básica {success, data, error}
        required_fields = {"success", "data", "error"}
        return all(field in content for field in required_fields)
    
    def _extract_error_message(self, content: Any, default: str = "Erro na requisição") -> str:
        """Extrai mensagem de erro do conteúdo"""
        if isinstance(content, dict):
            # Tentar vários campos comuns para mensagens de erro
            for field in ["detail", "message", "error", "msg"]:
                if field in content:
                    return str(content[field])
        
        if isinstance(content, str):
            return content
        
        return default
    
    def _map_status_to_error_code(self, status_code: int) -> ErrorCode:
        """Mapeia status HTTP para ErrorCode"""
        mapping = {
            400: ErrorCode.VALIDATION_ERROR,
            401: ErrorCode.AUTHENTICATION_REQUIRED,
            403: ErrorCode.PERMISSION_DENIED,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            409: ErrorCode.RESOURCE_CONFLICT,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
        }
        
        return mapping.get(status_code, ErrorCode.VALIDATION_ERROR)


# ========================================
# CONFIGURAÇÃO E ATIVAÇÃO
# ========================================

def setup_response_middleware(app, enable_auto_wrap: bool = True, measure_time: bool = True):
    """
    Configura o middleware de response padronizado
    
    Args:
        app: Instância do FastAPI
        enable_auto_wrap: Se deve aplicar wrapper automático
        measure_time: Se deve medir tempo de execução
    """
    middleware = ApiResponseMiddleware(
        app=app,
        enable_auto_wrap=enable_auto_wrap,
        measure_time=measure_time
    )
    
    app.add_middleware(ApiResponseMiddleware, 
                      enable_auto_wrap=enable_auto_wrap,
                      measure_time=measure_time)
    
    logger.info(f"✅ ApiResponseMiddleware configurado", extra={
        "enable_auto_wrap": enable_auto_wrap,
        "measure_time": measure_time
    })
    
    return middleware
