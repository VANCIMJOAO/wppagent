"""
🔒 HF002 - Secure Request Logging Middleware
=========
        # Capturar informações da requisição de forma segura HF002
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
            "headers": self._sanitize_headers(dict(request.headers)) if self.enable_hf002 else dict(request.headers),
            "query_params": sanitize_log_data(dict(request.query_params)) if self.enable_hf002 else dict(request.query_params),========================

Middleware para logging seguro de requisições HTTP com sanitização automática
de dados sensíveis em headers, parâmetros e payloads.

Funcionalidades HF002:
- Sanitização automática de headers Authorization
- Redação de dados PII em URLs e query parameters
- Logging estruturado para auditoria
- Performance tracking sem exposição de dados sensíveis
"""

import json
import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .secure_logger import get_log_sanitizer, sanitize_log_data

logger = logging.getLogger(__name__)


class SecureRequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HF002 FIX: Middleware para logging seguro de requisições com sanitização automática
    """

    def __init__(
        self, app, exclude_paths: Optional[list] = None, enable_hf002: bool = True
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/favicon.ico",
            "/static",
        ]
        self.enable_hf002 = enable_hf002
        self.sanitizer = get_log_sanitizer() if enable_hf002 else None

        # Headers sempre sensíveis HF002
        self.sensitive_headers = {
            "authorization",
            "x-api-key",
            "x-auth-token",
            "cookie",
            "x-hub-signature-256",
            "x-webhook-secret",
        }

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
            "query_params": (
                sanitize_log_data(dict(request.query_params))
                if self.enable_hf002
                else dict(request.query_params)
            ),
            "headers": safe_headers,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

        logger.info(
            f"🔍 S002 Request Start: {request.method} {request.url.path}",
            extra={"request_data": request_data},
        )

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
                "response_size": response.headers.get("content-length", "unknown"),
            }

            # Determinar nível de log baseado no status
            if response.status_code >= 500:
                log_level = logging.ERROR
                log_msg = f"❌ S002 Request Error: {request.method} {request.url.path}"
            elif response.status_code >= 400:
                log_level = logging.WARNING
                log_msg = (
                    f"⚠️ S002 Request Warning: {request.method} {request.url.path}"
                )
            else:
                log_level = logging.INFO
                log_msg = f"✅ S002 Request Success: {request.method} {request.url.path}"

            logger.log(log_level, log_msg, extra={"response_data": response_data})

            # Log de eventos de segurança para endpoints sensíveis
            if self._is_sensitive_endpoint(request.url.path):
                self._log_security_event(
                    "sensitive_endpoint_access",
                    {
                        "endpoint": request.url.path,
                        "method": request.method,
                        "status_code": response.status_code,
                        "client_ip": self._get_client_ip(request),
                        "process_time": process_time,
                    },
                )

            return response

        except Exception as e:
            # Log de erro na requisição
            process_time = time.time() - start_time

            error_data = {
                "request_id": request_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "process_time": round(process_time, 4),
            }

            logger.error(
                f"💥 S002 Request Exception: {request.method} {request.url.path}",
                extra={"error_data": error_data},
            )

            # Log de evento de segurança para erros
            self._log_security_event(
                "request_exception",
                {
                    "endpoint": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__,
                    "client_ip": self._get_client_ip(request),
                },
            )

            raise

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitiza headers removendo dados sensíveis"""
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "authentication",
            "proxy-authorization",
            "x-hub-signature-256",
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
            "/auth",
            "/login",
            "/webhook",
            "/admin",
            "/api/v1/users",
            "/api/v1/conversations",
            "/api/v1/messages",
            "/lgpd",
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


def configure_request_logging_middleware(
    app, enable_sanitization=True, log_requests=True, log_webhooks=True
):
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
        logger.info(
            f"🔒 S002 Request Logging Middleware: Configurado com sucesso - Sanitização: {enable_sanitization}"
        )
    except Exception as e:
        logger.error(f"❌ S002 Request Logging Middleware: Erro na configuração: {e}")
        raise

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        HF002 FIX: Sanitizar headers sensíveis
        """
        sanitized = {}

        for key, value in headers.items():
            key_lower = key.lower()

            if key_lower in self.sensitive_headers:
                sanitized[key] = "[SENSITIVE_HEADER_REDACTED_HF002]"
            elif self.sanitizer:
                sanitized[key] = self.sanitizer.sanitize_message(value)
            else:
                sanitized[key] = value

        return sanitized

    def _log_security_event(
        self, event_type: str, details: Dict[str, Any], severity: str = "INFO"
    ):
        """
        HF002 FIX: Log de eventos de segurança sanitizado
        """
        if self.enable_hf002 and self.sanitizer:
            details = self.sanitizer.sanitize_metadata(details)

        logger.log(
            getattr(logging, severity, logging.INFO),
            f"🔒 HF002 SECURITY EVENT: {event_type}",
            extra={"security_event": event_type, "details": details},
        )


def get_request_context_middleware():
    """Retorna middleware de contexto de requisição"""
    return RequestContextMiddleware


# Log de inicialização HF002
logger.info("🔒 HF002 Request Logging: Módulo carregado com sanitização automática")
