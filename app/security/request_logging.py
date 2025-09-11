"""
🔒 S002 - Request Logging Middleware
===================================

Middleware para logging seguro de requests com sanitização automática.

Funcionalidades:
- Log sanitizado de headers de request/response
- Redação automática de dados sensíveis em URLs
- Auditoria de compliance LGPD em tempo real
- Headers de segurança preservados

Autor: GitHub Copilot  
Data: 2025-09-11
Status: S002 - Auditoria de Logs Sensíveis
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from .log_sanitizer import log_sanitizer, sanitize_log_data
    from .secure_logger import get_secure_logger
    SANITIZATION_AVAILABLE = True
except ImportError:
    SANITIZATION_AVAILABLE = False


class SecureRequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging seguro de requests
    """
    
    def __init__(self, app, enable_sanitization: bool = True, log_level: str = "INFO"):
        super().__init__(app)
        self.enable_sanitization = enable_sanitization
        
        # Configurar logger específico para requests
        if SANITIZATION_AVAILABLE and enable_sanitization:
            self.logger = get_secure_logger(
                "whats_agent.requests",
                level=getattr(logging, log_level.upper(), logging.INFO),
                enable_sanitization=True,
                enable_audit=True,
                log_file="logs/requests.log"
            )
        else:
            self.logger = logging.getLogger("whats_agent.requests")
        
        # Headers sensíveis que devem ser redatados
        self.sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'x-access-token', 'x-refresh-token', 'x-whatsapp-token',
            'x-session-id', 'x-user-token'
        }
        
        # Parâmetros de URL sensíveis
        self.sensitive_url_params = {
            'token', 'api_key', 'secret', 'password', 'auth',
            'wa_id', 'phone', 'email', 'cpf', 'cnpj'
        }
    
    async def dispatch(self, request: Request, call_next):
        """
        Processar request com logging seguro
        """
        start_time = time.time()
        
        # Extrair informações do request (sanitizadas)
        request_info = self._extract_request_info(request)
        
        # Log do request (sanitizado)
        self.logger.info(
            "🔄 Request iniciado",
            extra={
                "event_type": "request_start",
                "request_info": request_info
            }
        )
        
        try:
            # Processar request
            response = await call_next(request)
            
            # Calcular tempo de processamento
            process_time = time.time() - start_time
            
            # Extrair informações da response (sanitizadas)
            response_info = self._extract_response_info(response, process_time)
            
            # Log da response (sanitizado)
            self.logger.info(
                "✅ Request completado",
                extra={
                    "event_type": "request_complete", 
                    "request_info": request_info,
                    "response_info": response_info,
                    "performance": {
                        "duration_ms": round(process_time * 1000, 2),
                        "status_code": response.status_code
                    }
                }
            )
            
            return response
            
        except Exception as e:
            # Calcular tempo até o erro
            process_time = time.time() - start_time
            
            # Log do erro (sanitizado)
            self.logger.error(
                "❌ Request falhou",
                extra={
                    "event_type": "request_error",
                    "request_info": request_info,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e)
                    },
                    "performance": {
                        "duration_ms": round(process_time * 1000, 2)
                    }
                }
            )
            
            raise
    
    def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """
        Extrair informações do request aplicando sanitização
        """
        # Informações básicas do request
        info = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
            "content_type": request.headers.get("content-type", "")
        }
        
        # Headers (sanitizados)
        sanitized_headers = {}
        for name, value in request.headers.items():
            if name.lower() in self.sensitive_headers:
                sanitized_headers[name] = "[REDACTED_HEADER]"
            else:
                sanitized_headers[name] = value
        
        info["headers"] = sanitized_headers
        
        # Query parameters (sanitizados)
        sanitized_params = {}
        for key, value in request.query_params.items():
            if key.lower() in self.sensitive_url_params:
                sanitized_params[key] = "[REDACTED_PARAM]"
            else:
                sanitized_params[key] = value
        
        info["query_params"] = sanitized_params
        
        # Aplicar sanitização adicional se disponível
        if self.enable_sanitization and SANITIZATION_AVAILABLE:
            info = sanitize_log_data(info)
        
        return info
    
    def _extract_response_info(self, response: Response, process_time: float) -> Dict[str, Any]:
        """
        Extrair informações da response aplicando sanitização
        """
        info = {
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "content_length": response.headers.get("content-length", ""),
            "duration_ms": round(process_time * 1000, 2)
        }
        
        # Headers de response (sanitizados)
        sanitized_headers = {}
        for name, value in response.headers.items():
            if name.lower() in self.sensitive_headers:
                sanitized_headers[name] = "[REDACTED_HEADER]"
            else:
                sanitized_headers[name] = value
        
        info["headers"] = sanitized_headers
        
        # Aplicar sanitização adicional se disponível
        if self.enable_sanitization and SANITIZATION_AVAILABLE:
            info = sanitize_log_data(info)
        
        return info


class WebhookLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware especializado para logging de webhooks com sanitização
    """
    
    def __init__(self, app, enable_sanitization: bool = True):
        super().__init__(app)
        self.enable_sanitization = enable_sanitization
        
        # Logger específico para webhooks
        if SANITIZATION_AVAILABLE and enable_sanitization:
            self.logger = get_secure_logger(
                "whats_agent.webhook",
                enable_sanitization=True,
                enable_audit=True,
                log_file="logs/webhook.log"
            )
        else:
            self.logger = logging.getLogger("whats_agent.webhook")
    
    async def dispatch(self, request: Request, call_next):
        """
        Processar webhook request com logging especializado
        """
        # Verificar se é webhook
        if not request.url.path.startswith(('/webhook', '/api/webhook')):
            return await call_next(request)
        
        start_time = time.time()
        
        # Body do webhook (sanitizado)
        body = await self._get_sanitized_body(request)
        
        # Log do webhook recebido
        self.logger.info(
            "📨 Webhook recebido",
            extra={
                "event_type": "webhook_received",
                "path": request.url.path,
                "method": request.method,
                "body_size": len(body) if body else 0,
                "sanitized_body": body[:500] if body else None  # Primeiros 500 chars
            }
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            self.logger.info(
                "✅ Webhook processado",
                extra={
                    "event_type": "webhook_processed",
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time * 1000, 2)
                }
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            self.logger.error(
                "❌ Webhook falhou",
                extra={
                    "event_type": "webhook_error",
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(process_time * 1000, 2)
                }
            )
            
            raise
    
    async def _get_sanitized_body(self, request: Request) -> Optional[str]:
        """
        Obter body do request sanitizado
        """
        try:
            body = await request.body()
            if not body:
                return None
            
            body_str = body.decode('utf-8', errors='ignore')
            
            # Aplicar sanitização se disponível
            if self.enable_sanitization and SANITIZATION_AVAILABLE:
                body_str = log_sanitizer.sanitize_text(body_str)
            
            return body_str
            
        except Exception:
            return "[BODY_READ_ERROR]"


def configure_request_logging_middleware(app, 
                                       enable_sanitization: bool = True,
                                       log_requests: bool = True,
                                       log_webhooks: bool = True):
    """
    Configurar middlewares de logging para a aplicação
    
    Args:
        app: Aplicação FastAPI
        enable_sanitization: Habilitar sanitização de logs
        log_requests: Habilitar logging de requests
        log_webhooks: Habilitar logging especializado de webhooks
    """
    
    if log_webhooks:
        app.add_middleware(
            WebhookLoggingMiddleware,
            enable_sanitization=enable_sanitization
        )
    
    if log_requests:
        app.add_middleware(
            SecureRequestLoggingMiddleware,
            enable_sanitization=enable_sanitization,
            log_level="INFO"
        )
    
    # Log de configuração
    logger = logging.getLogger("whats_agent.config")
    logger.info(
        f"🔒 S002: Middlewares de logging configurados - "
        f"Sanitização: {enable_sanitization}, "
        f"Requests: {log_requests}, "
        f"Webhooks: {log_webhooks}"
    )
