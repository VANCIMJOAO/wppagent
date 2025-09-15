"""
OB-001: Middleware de Request Logging Estruturado
=================================================

Middleware para capturar todas as requisições com:
- Logs estruturados em JSON
- Métricas de performance (duração)
- Contexto de trace_id e request_id
- Informações de IP e User-Agent
- Headers de segurança
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import traceback

from app.utils.structured_logger import (
    get_structured_logger,
    set_request_context,
    set_trace_id,
    clear_context
)

logger = get_structured_logger('request-middleware')


class RequestLoggingMiddleware:
    """
    Middleware para logging estruturado de todas as requisições
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Gerar IDs únicos para tracking
        request_id = str(uuid.uuid4())
        trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4())[:8])
        
        # Definir contexto para logs
        set_trace_id(trace_id)
        set_request_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            user_id=None,  # Será preenchido pelo auth middleware se disponível
            ip_address=self._get_client_ip(request)
        )
        
        # Timestamp de início
        start_time = time.time()
        
        # Log da requisição inicial
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            headers=self._sanitize_headers(dict(request.headers)),
            user_agent=request.headers.get("user-agent", "unknown"),
            ip_address=self._get_client_ip(request),
            content_length=request.headers.get("content-length", 0),
        )
        
        # Variáveis para capturar response
        response_status = 500
        response_headers = {}
        response_body_size = 0
        error_details = None
        
        async def send_wrapper(message):
            nonlocal response_status, response_headers, response_body_size
            
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = dict(message.get("headers", []))
                
                # Adicionar headers de trace
                headers_list = list(message.get("headers", []))
                headers_list.extend([
                    (b"x-request-id", request_id.encode()),
                    (b"x-trace-id", trace_id.encode()),
                ])
                message["headers"] = headers_list
            
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    response_body_size += len(body)
            
            await send(message)
        
        try:
            # Processar requisição
            await self.app(scope, receive, send_wrapper)
            
        except Exception as e:
            response_status = 500
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            
            logger.error(
                "request_error",
                request_id=request_id,
                error=error_details,
                duration_ms=round((time.time() - start_time) * 1000, 2)
            )
            
            # Re-raise para permitir handling normal
            raise
        
        finally:
            # Log da resposta
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "status_code": response_status,
                "duration_ms": duration_ms,
                "response_size_bytes": response_body_size,
                "ip_address": self._get_client_ip(request),
            }
            
            if error_details:
                log_data["error"] = error_details
            
            # Definir nível do log baseado no status
            if response_status >= 500:
                logger.error("request_completed", **log_data)
            elif response_status >= 400:
                logger.warning("request_completed", **log_data)
            else:
                logger.info("request_completed", **log_data)
            
            # Performance warning para requests lentos
            if duration_ms > 1000:  # > 1 segundo
                logger.warning(
                    "slow_request",
                    request_id=request_id,
                    path=request.url.path,
                    duration_ms=duration_ms,
                    threshold_ms=1000
                )
            
            # Limpar contexto
            clear_context()
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extrai IP real do cliente considerando proxies
        """
        # Headers em ordem de prioridade
        forwarded_headers = [
            "x-forwarded-for",
            "x-real-ip", 
            "cf-connecting-ip",  # Cloudflare
            "x-forwarded-host",
        ]
        
        for header in forwarded_headers:
            ip = request.headers.get(header)
            if ip:
                # Pegar primeiro IP se há múltiplos (x-forwarded-for)
                return ip.split(',')[0].strip()
        
        # Fallback para IP direto
        return request.client.host if request.client else "unknown"
    
    def _sanitize_headers(self, headers: dict) -> dict:
        """
        Remove headers sensíveis dos logs
        """
        sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 
            'x-auth-token', 'proxy-authorization'
        }
        
        return {
            key: '***REDACTED***' if key.lower() in sensitive_headers else value
            for key, value in headers.items()
        }


def add_request_logging_middleware(app):
    """
    Adiciona middleware de logging estruturado à aplicação
    """
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info(
        "middleware_registered",
        middleware="RequestLoggingMiddleware",
        description="OB-001 structured request logging enabled"
    )