"""
Sistema de Logging Unificado e Otimizado
========================================

Sistema único de logging que elimina duplicações e otimiza para produção:
- Formato JSON estruturado em produção
- Emojis apenas em desenvolvimento
- Fases sequenciais de startup
- Métricas de performance
- Zero duplicação de logs
"""

import logging
import os
import sys
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog

# Context variables para tracing
trace_id_context: ContextVar[str] = ContextVar("trace_id", default="")
request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context", default={})
startup_phase_context: ContextVar[str] = ContextVar("startup_phase", default="")

# Configurações baseadas no ambiente
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None
IS_DEVELOPMENT = not IS_PRODUCTION and not IS_RAILWAY

# Emojis apenas para desenvolvimento
EMOJI_MAP = {
    "startup": "🚀" if IS_DEVELOPMENT else "",
    "success": "✅" if IS_DEVELOPMENT else "",
    "warning": "⚠️" if IS_DEVELOPMENT else "",
    "error": "❌" if IS_DEVELOPMENT else "",
    "info": "ℹ️" if IS_DEVELOPMENT else "",
    "database": "🗄️" if IS_DEVELOPMENT else "",
    "cache": "💾" if IS_DEVELOPMENT else "",
    "websocket": "🌐" if IS_DEVELOPMENT else "",
    "security": "🔒" if IS_DEVELOPMENT else "",
    "performance": "⚡" if IS_DEVELOPMENT else "",
    "cleanup": "🧹" if IS_DEVELOPMENT else "",
}


class StartupPhaseManager:
    """Gerenciador de fases de startup com métricas"""
    
    def __init__(self):
        self.phases = []
        self.start_time = time.time()
        self.current_phase = None
        
    def start_phase(self, phase_name: str, description: str = ""):
        """Iniciar uma fase de startup"""
        phase_start = time.time()
        self.current_phase = phase_name
        startup_phase_context.set(phase_name)
        
        self.phases.append({
            "name": phase_name,
            "description": description,
            "start_time": phase_start,
            "duration_ms": 0,
            "status": "running"
        })
        
        return phase_start
        
    def complete_phase(self, phase_name: str, status: str = "completed"):
        """Completar uma fase de startup"""
        current_time = time.time()
        
        for phase in self.phases:
            if phase["name"] == phase_name and phase["status"] == "running":
                phase["duration_ms"] = (current_time - phase["start_time"]) * 1000
                phase["status"] = status
                break
                
    def get_summary(self) -> Dict[str, Any]:
        """Obter resumo das fases de startup"""
        total_duration = (time.time() - self.start_time) * 1000
        completed_phases = [p for p in self.phases if p["status"] == "completed"]
        
        return {
            "total_duration_ms": total_duration,
            "phases_count": len(self.phases),
            "completed_count": len(completed_phases),
            "phases": self.phases,
            "average_phase_duration_ms": sum(p["duration_ms"] for p in completed_phases) / len(completed_phases) if completed_phases else 0
        }


# Instância global do gerenciador de fases
startup_manager = StartupPhaseManager()


def add_startup_context(logger, method_name, event_dict):
    """Adiciona contexto de startup aos logs"""
    phase = startup_phase_context.get()
    if phase:
        event_dict["startup_phase"] = phase
    
    # Adicionar trace_id se disponível
    trace_id = trace_id_context.get()
    if trace_id:
        event_dict["trace_id"] = trace_id
        
    return event_dict


def add_performance_metrics(logger, method_name, event_dict):
    """Adiciona métricas de performance aos logs"""
    if "startup_phase" in event_dict:
        # Para logs de startup, adicionar métricas da fase
        phase_name = event_dict["startup_phase"]
        for phase in startup_manager.phases:
            if phase["name"] == phase_name and phase["status"] == "completed":
                event_dict["phase_duration_ms"] = phase["duration_ms"]
                break
                
    return event_dict


def sanitize_sensitive_data(data: Any) -> Any:
    """Sanitiza dados sensíveis dos logs"""
    import re
    
    sensitive_patterns = [
        r"password|senha|token|secret|key|auth",
        r"access_token|refresh_token|api_key",
        r"authorization|bearer",
        r"cookie|session",
    ]
    
    sensitive_regex = re.compile("|".join(sensitive_patterns), re.IGNORECASE)
    
    if isinstance(data, dict):
        return {
            key: (
                "***REDACTED***"
                if sensitive_regex.search(str(key))
                else sanitize_sensitive_data(value)
            )
            for key, value in data.items()
        }
    elif isinstance(data, str):
        if sensitive_regex.search(data):
            return "***REDACTED***"
        # Mascarar JWTs
        if data.startswith("eyJ") and len(data) > 50:
            return f"JWT_TOKEN_***{data[-8:]}"
        return data
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    else:
        return data


def sanitize_processor(logger, method_name, event_dict):
    """Processa e sanitiza dados sensíveis"""
    return sanitize_sensitive_data(event_dict)


def setup_unified_logging():
    """Configurar sistema de logging unificado - ZERO DUPLICAÇÃO"""
    
    # Remover todos os handlers existentes de TODOS os loggers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Desabilitar propagação para evitar duplicação
    root_logger.propagate = False
    
    # Limpar handlers de loggers específicos que podem ter duplicação
    for logger_name in ["app.services.lgpd_scheduler", "app.services.realtime_websocket_manager"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = False
    
    # Configurar logging básico para redirecionar para structlog
    logging.basicConfig(
        level=logging.INFO if IS_PRODUCTION else logging.DEBUG,
        format="%(message)s",
        stream=sys.stdout,
        force=True
    )
    
    # Configurar structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        add_startup_context,
        add_performance_metrics,
        sanitize_processor,
    ]
    
    if IS_PRODUCTION or IS_RAILWAY:
        # Produção: JSON puro, sem emojis
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Desenvolvimento: formato legível com emojis
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Configurar níveis de log para bibliotecas externas
    external_loggers = {
        "uvicorn.access": logging.WARNING,
        "uvicorn.error": logging.WARNING,
        "sqlalchemy.engine": logging.WARNING,
        "sqlalchemy.pool": logging.WARNING,
        "httpx": logging.WARNING,
        "httpcore": logging.WARNING,
        "asyncio": logging.WARNING,
        "urllib3": logging.WARNING,
        "requests": logging.WARNING,
        "aiohttp": logging.WARNING,
        "redis": logging.WARNING,
        "aioredis": logging.WARNING,
        "apscheduler": logging.WARNING,  # Reduzir verbosidade do scheduler
        "apscheduler.scheduler": logging.WARNING,
        "apscheduler.executors": logging.WARNING,
        "apscheduler.jobstores": logging.WARNING,
    }
    
    for logger_name, level in external_loggers.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Configurar loggers da aplicação
    app_loggers = {
        "app.auth.middleware": logging.WARNING,
        "app.security.https_middleware": logging.WARNING,
        "app.middleware.user_rate_limit": logging.WARNING,
        "app.services.structured_apm": logging.INFO,
    }
    
    for logger_name, level in app_loggers.items():
        logging.getLogger(logger_name).setLevel(level)


def get_optimized_logger(name: str):
    """Obter logger otimizado"""
    return structlog.get_logger(name)


def log_startup_phase(phase_name: str, description: str = "", **kwargs):
    """Log otimizado para fases de startup"""
    logger = get_optimized_logger("startup")
    
    # Iniciar fase
    start_time = startup_manager.start_phase(phase_name, description)
    
    # Log de início
    emoji = EMOJI_MAP.get("startup", "")
    message = f"{emoji} {phase_name.title()}" if emoji else phase_name.title()
    if description:
        message += f": {description}"
    
    logger.info(
        message,
        phase=phase_name,
        description=description,
        **kwargs
    )
    
    return start_time


def log_startup_completion(phase_name: str, status: str = "completed", **kwargs):
    """Log de conclusão de fase de startup"""
    logger = get_optimized_logger("startup")
    
    # Completar fase
    startup_manager.complete_phase(phase_name, status)
    
    # Obter duração da fase
    phase_duration = 0
    for phase in startup_manager.phases:
        if phase["name"] == phase_name and phase["status"] == status:
            phase_duration = phase["duration_ms"]
            break
    
    # Log de conclusão
    emoji = EMOJI_MAP.get("success" if status == "completed" else "error", "")
    message = f"{emoji} {phase_name.title()} {status}" if emoji else f"{phase_name.title()} {status}"
    
    logger.info(
        message,
        phase=phase_name,
        status=status,
        duration_ms=phase_duration,
        **kwargs
    )


def log_startup_summary():
    """Log de resumo final do startup"""
    logger = get_optimized_logger("startup")
    summary = startup_manager.get_summary()
    
    emoji = EMOJI_MAP.get("success", "")
    message = f"{emoji} Startup completed" if emoji else "Startup completed"
    
    logger.info(
        message,
        **summary,
        event_type="startup_summary"
    )


def log_performance_metric(operation: str, duration_ms: float, **metadata):
    """Log de métrica de performance"""
    logger = get_optimized_logger("performance")
    
    emoji = EMOJI_MAP.get("performance", "")
    message = f"{emoji} {operation}: {duration_ms:.2f}ms" if emoji else f"{operation}: {duration_ms:.2f}ms"
    
    logger.info(
        message,
        operation=operation,
        duration_ms=duration_ms,
        event_type="performance_metric",
        **metadata
    )


def log_system_event(event_type: str, message: str, level: str = "info", **metadata):
    """Log de evento do sistema"""
    logger = get_optimized_logger("system")
    
    emoji = EMOJI_MAP.get(event_type, EMOJI_MAP.get("info", ""))
    formatted_message = f"{emoji} {message}" if emoji else message
    
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(
        formatted_message,
        event_type=event_type,
        **metadata
    )


# Configurar logging unificado na importação
setup_unified_logging()

# Logger principal
logger = get_optimized_logger("whatsapp-agent")