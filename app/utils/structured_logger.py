"""
OB-001: Sistema de Logs Estruturados com Structlog
==================================================

Implementação de logs estruturados conforme roadmap OB-001:
- Formato JSON válido para produção
- Campos obrigatórios: timestamp, level, service, trace_id
- Middleware de request logging com duração
- Filtros de segurança para dados sensíveis
"""

import os
import re
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from fastapi import Request

# Context variables para tracing
trace_id_context: ContextVar[str] = ContextVar("trace_id", default="")
request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context", default={})

# Padrões para filtrar dados sensíveis
SENSITIVE_PATTERNS = [
    r"password|senha|token|secret|key|auth",
    r"access_token|refresh_token|api_key",
    r"authorization|bearer",
    r"cookie|session",
]

SENSITIVE_REGEX = re.compile("|".join(SENSITIVE_PATTERNS), re.IGNORECASE)


def sanitize_sensitive_data(data: Any) -> Any:
    """
    Remove ou mascaras dados sensíveis dos logs
    """
    if isinstance(data, dict):
        return {
            key: (
                "***REDACTED***"
                if SENSITIVE_REGEX.search(str(key))
                else sanitize_sensitive_data(value)
            )
            for key, value in data.items()
        }
    elif isinstance(data, str):
        # Mascarar tokens e senhas em strings
        if SENSITIVE_REGEX.search(data):
            return "***REDACTED***"
        # Mascarar JWTs (padrão eyJ...)
        if data.startswith("eyJ") and len(data) > 50:
            return f"JWT_TOKEN_***{data[-8:]}"
        return data
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    else:
        return data


def add_trace_id(logger, method_name, event_dict):
    """
    Adiciona trace_id a todos os logs
    """
    trace_id = trace_id_context.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())[:8]
        trace_id_context.set(trace_id)

    event_dict["trace_id"] = trace_id
    return event_dict


def add_service_info(logger, method_name, event_dict):
    """
    Adiciona informações do serviço
    """
    event_dict["service"] = "whatsapp-agent"
    event_dict["version"] = "1.0.0"
    event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
    return event_dict


def add_request_context(logger, method_name, event_dict):
    """
    Adiciona contexto da requisição atual
    """
    context = request_context.get({})
    if context:
        event_dict.update(
            {
                "request_id": context.get("request_id"),
                "method": context.get("method"),
                "path": context.get("path"),
                "user_id": context.get("user_id"),
                "ip_address": context.get("ip_address"),
            }
        )
    return event_dict


def sanitize_processor(logger, method_name, event_dict):
    """
    Processa e sanitiza dados sensíveis
    """
    return sanitize_sensitive_data(event_dict)


def configure_structured_logging():
    """
    Configura structlog conforme especificação OB-001
    """
    # Determinar se estamos em produção
    is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        add_trace_id,
        add_service_info,
        add_request_context,
        sanitize_processor,
    ]

    if is_production:
        # Produção: JSON puro
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Desenvolvimento: formato legível
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_structured_logger(name: str = __name__):
    """
    Retorna logger estruturado configurado
    """
    return structlog.get_logger(name)


def set_request_context(
    request_id: str,
    method: str,
    path: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """
    Define contexto da requisição para logs
    """
    context = {
        "request_id": request_id,
        "method": method,
        "path": path,
        "user_id": user_id,
        "ip_address": ip_address,
    }
    request_context.set(context)


def set_trace_id(trace_id: str):
    """
    Define trace_id para correlação de logs
    """
    trace_id_context.set(trace_id)


def clear_context():
    """
    Limpa contexto de requisição
    """
    request_context.set({})
    trace_id_context.set("")


# Configurar logging estruturado na importação
configure_structured_logging()

# Logger padrão para uso geral
logger = get_structured_logger("whatsapp-agent")
