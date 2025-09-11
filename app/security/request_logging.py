"""
S002 - Request Logging Middleware
Middleware seguro para logging de requisições com sanitização
Implementação para conformidade LGPD e auditoria de segurança
"""

import logging
import time
import uuid
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .secure_logger import sanitize_data, log_security_event

logger = logging.getLogger(__name__)

class SecureRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging seguro de requisições"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health", "/metrics", "/favicon.ico", "/static"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Gerar ID único para a requisição
        request_id = str(uuid.uuid4())
        
        # Verificar se deve logar esta requisição
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Início da requisição
        start_time = time.time()
        
        # Sanitizar headers (remover tokens e dados sensíveis)
        safe_headers = self._sanitize_headers(dict(request.headers))
        
        # Log de entrada da requisição
        request_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": sanitize_data(dict(request.query_params)),
            "headers": safe_headers,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        logger.info(f"🔍 S002 Request Start: {request.method} {request.url.path}", 
                   extra={"request_data": request_data})
        
        try:
            # Processar requisição
            response = await call_next(request)
            
            # Calcular tempo de processamento
            process_time = time.time() - start_time
            
            # Log de resposta
            response_data = {
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "response_size": response.headers.get("content-length", "unknown")
            }
            
            # Determinar nível de log baseado no status
            if response.status_code >= 500:
                log_level = logging.ERROR
                log_msg = f"❌ S002 Request Error: {request.method} {request.url.path}"
            elif response.status_code >= 400:
                log_level = logging.WARNING  
                log_msg = f"⚠️ S002 Request Warning: {request.method} {request.url.path}"
            else:
                log_level = logging.INFO
                log_msg = f"✅ S002 Request Success: {request.method} {request.url.path}"
            
            logger.log(log_level, log_msg, extra={"response_data": response_data})
            
            # Log de eventos de segurança para endpoints sensíveis
            if self._is_sensitive_endpoint(request.url.path):
                log_security_event(
                    "sensitive_endpoint_access",
                    {
                        "endpoint": request.url.path,
                        "method": request.method,
                        "status_code": response.status_code,
                        "client_ip": self._get_client_ip(request),
                        "process_time": process_time
                    }
                )
            
            return response
            
        except Exception as e:
            # Log de erro na requisição
            process_time = time.time() - start_time
            
            error_data = {
                "request_id": request_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "process_time": round(process_time, 4)
            }
            
            logger.error(f"💥 S002 Request Exception: {request.method} {request.url.path}",
                        extra={"error_data": error_data})
            
            # Log de evento de segurança para erros
            log_security_event(
                "request_exception",
                {
                    "endpoint": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__,
                    "client_ip": self._get_client_ip(request)
                }
            )
            
            raise
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitiza headers removendo dados sensíveis"""
        sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'authentication', 'proxy-authorization', 'x-hub-signature-256'
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtém IP do cliente considerando proxies"""
        # Verificar headers de proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # IP direto
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Verifica se o endpoint é sensível e requer log de segurança"""
        sensitive_patterns = [
            "/auth", "/login", "/webhook", "/admin", "/api/v1/users",
            "/api/v1/conversations", "/api/v1/messages", "/lgpd"
        ]
        
        return any(pattern in path for pattern in sensitive_patterns)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware para adicionar contexto de requisição aos logs"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Adicionar contexto à requisição
        request.state.start_time = time.time()
        request.state.request_id = str(uuid.uuid4())
        
        # Processar requisição
        response = await call_next(request)
        
        return response

def configure_request_logging_middleware(app, enable_sanitization=True, log_requests=True, log_webhooks=True):
    """
    Configura middleware de logging de requisições seguras
    
    Args:
        app: Aplicação FastAPI
        enable_sanitization: Habilitar sanitização de dados
        log_requests: Fazer log de requisições
        log_webhooks: Fazer log de webhooks
    """
    try:
        # Configurar middleware com opções
        middleware = SecureRequestLoggingMiddleware
        middleware.enable_sanitization = enable_sanitization
        middleware.log_requests = log_requests
        middleware.log_webhooks = log_webhooks
        
        app.add_middleware(middleware)
        logger.info(f"🔒 S002 Request Logging Middleware: Configurado com sucesso - Sanitização: {enable_sanitization}")
    except Exception as e:
        logger.error(f"❌ S002 Request Logging Middleware: Erro na configuração: {e}")
        raise

def get_request_context_middleware():
    """Retorna middleware de contexto de requisição"""
    return RequestContextMiddleware

# Log de inicialização
logger.info("🔒 S002 Request Logging: Módulo carregado com sucesso")
