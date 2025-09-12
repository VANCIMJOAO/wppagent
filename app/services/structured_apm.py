"""
Sistema de APM (Application Performance Monitoring) com Logging Estruturado
==========================================================================

Sistema completo de monitoramento e logging estruturado com:
- Request ID tracking automático
- Structured logging em JSON para produção
- APM com métricas de performance
- Context variables para rastreamento de sessões
- Correlation IDs para tracing distribuído
- Dashboard de monitoramento em tempo real
"""

import json
import time
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from contextvars import ContextVar
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import sys
import os
from pathlib import Path

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

# Context Variables para APM
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
user_id_context: ContextVar[str] = ContextVar('user_id', default='')
session_id_context: ContextVar[str] = ContextVar('session_id', default='')
trace_id_context: ContextVar[str] = ContextVar('trace_id', default='')
span_id_context: ContextVar[str] = ContextVar('span_id', default='')
operation_context: ContextVar[str] = ContextVar('operation', default='')


class LogLevel(Enum):
    """Níveis de log estruturados"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING" 
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Categorias de logs para organização"""
    BUSINESS = "business"      # Eventos de negócio (vendas, conversões)
    SECURITY = "security"      # Eventos de segurança e autenticação
    PERFORMANCE = "performance" # Métricas de performance
    WEBHOOK = "webhook"        # Logs específicos de webhooks
    DATABASE = "database"      # Operações de banco de dados
    API = "api"               # Chamadas de API externa
    USER = "user"             # Ações do usuário
    SYSTEM = "system"         # Eventos do sistema


@dataclass
class LogContext:
    """Contexto estruturado do log"""
    request_id: str = ""
    trace_id: str = ""
    span_id: str = ""
    user_id: str = ""
    session_id: str = ""
    operation: str = ""
    service: str = "whatsapp-agent"
    environment: str = ""
    version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        return {k: v for k, v in asdict(self).items() if v}


@dataclass 
class PerformanceMetrics:
    """Métricas de performance estruturadas"""
    operation_name: str
    duration_ms: float
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    db_queries: int = 0
    api_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        return asdict(self)


@dataclass
class BusinessEvent:
    """Evento de negócio estruturado"""
    event_type: str
    entity_type: str  # user, message, conversation, sale
    entity_id: str
    action: str  # created, updated, deleted, converted
    metadata: Dict[str, Any]
    value: Optional[float] = None  # Valor monetário se aplicável
    
    def to_dict(self) -> Dict[str, Any]:
        """Converter para dicionário"""
        return asdict(self)


class StructuredLogger:
    """Logger estruturado com APM integrado"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Configurar handlers se ainda não existirem"""
        if not self.logger.handlers:
            # Handler para console (desenvolvimento)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_context(self) -> LogContext:
        """Obter contexto atual do request"""
        return LogContext(
            request_id=request_id_context.get(""),
            trace_id=trace_id_context.get(""),
            span_id=span_id_context.get(""),
            user_id=user_id_context.get(""),
            session_id=session_id_context.get(""),
            operation=operation_context.get(""),
            environment=os.getenv("ENVIRONMENT", "development")
        )
    
    def _create_log_entry(self, 
                         level: str,
                         message: str,
                         category: LogCategory = LogCategory.SYSTEM,
                         metadata: Dict[str, Any] = None,
                         exception: Exception = None) -> Dict[str, Any]:
        """Criar entrada de log estruturada com sanitização HF002"""
        
        # 🔒 HF002 FIX: Sanitizar dados sensíveis automaticamente
        try:
            from app.security.secure_logger import get_log_sanitizer
            sanitizer = get_log_sanitizer()
            
            # Sanitizar mensagem
            safe_message = sanitizer.sanitize_message(message)
            
            # Sanitizar metadados
            if metadata:
                safe_metadata = sanitizer.sanitize_metadata(metadata)
            else:
                safe_metadata = {}
        except ImportError:
            # Fallback se HF002 não estiver disponível
            safe_message = message
            safe_metadata = metadata or {}
        
        context = self._get_context()
        timestamp = datetime.now(timezone.utc)
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "service": context.service,
            "environment": context.environment,
            "version": context.version,
            "logger_name": self.name,
            "message": safe_message,  # 🔒 HF002: Mensagem sanitizada
            "category": category.value,
            **context.to_dict()
        }
        
        # Adicionar metadata sanitizado HF002
        if safe_metadata:
            log_entry["metadata"] = safe_metadata
        
        # Adicionar informações de exceção (sanitizadas)
        if exception:
            exception_message = str(exception)
            try:
                # Sanitizar mensagem de exceção
                if 'sanitizer' in locals():
                    exception_message = sanitizer.sanitize_message(exception_message)
            except:
                pass
                
            log_entry.update({
                "exception": {
                    "type": exception.__class__.__name__,
                    "message": exception_message,
                    "traceback": traceback.format_exc()  # Traceback pode conter dados sensíveis
                }
            })
        
        return log_entry
    
    def debug(self, message: str, metadata: Dict[str, Any] = None, category: LogCategory = LogCategory.SYSTEM):
        """Log de debug estruturado"""
        log_entry = self._create_log_entry(LogLevel.DEBUG.value, message, category, metadata)
        self.logger.debug(json.dumps(log_entry, ensure_ascii=False))
    
    def info(self, message: str, metadata: Dict[str, Any] = None, category: LogCategory = LogCategory.SYSTEM):
        """Log de info estruturado"""
        log_entry = self._create_log_entry(LogLevel.INFO.value, message, category, metadata)
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def warning(self, message: str, metadata: Dict[str, Any] = None, category: LogCategory = LogCategory.SYSTEM):
        """Log de warning estruturado"""
        log_entry = self._create_log_entry(LogLevel.WARNING.value, message, category, metadata)
        self.logger.warning(json.dumps(log_entry, ensure_ascii=False))
    
    def error(self, message: str, metadata: Dict[str, Any] = None, 
              category: LogCategory = LogCategory.SYSTEM, exception: Exception = None):
        """Log de error estruturado"""
        log_entry = self._create_log_entry(LogLevel.ERROR.value, message, category, metadata, exception)
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))
    
    def critical(self, message: str, metadata: Dict[str, Any] = None,
                category: LogCategory = LogCategory.SYSTEM, exception: Exception = None):
        """Log crítico estruturado"""
        log_entry = self._create_log_entry(LogLevel.CRITICAL.value, message, category, metadata, exception)
        self.logger.critical(json.dumps(log_entry, ensure_ascii=False))
    
    def business_event(self, event: BusinessEvent):
        """Log de evento de negócio"""
        self.info(
            f"Business event: {event.event_type}",
            metadata={
                "business_event": event.to_dict(),
                "event_category": "business_metric"
            },
            category=LogCategory.BUSINESS
        )
    
    def performance_metric(self, metrics: PerformanceMetrics):
        """Log de métrica de performance"""
        self.info(
            f"Performance: {metrics.operation_name} completed in {metrics.duration_ms:.2f}ms",
            metadata={
                "performance_metrics": metrics.to_dict(),
                "event_category": "performance_metric"
            },
            category=LogCategory.PERFORMANCE
        )
    
    def security_event(self, event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """Log de evento de segurança"""
        level = getattr(LogLevel, severity.upper(), LogLevel.INFO)
        log_method = getattr(self, level.value.lower())
        
        log_method(
            f"Security event: {event_type}",
            metadata={
                "security_event": {
                    "event_type": event_type,
                    "severity": severity,
                    "details": details
                },
                "event_category": "security_event"
            },
            category=LogCategory.SECURITY
        )


class StructuredFormatter(logging.Formatter):
    """Formatter JSON para logs estruturados"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatar log em JSON estruturado"""
        try:
            # Se já é JSON estruturado, retornar como está
            if hasattr(record, 'getMessage') and record.getMessage().startswith('{'):
                return record.getMessage()
            
            # Converter log tradicional para estruturado
            context = LogContext(
                request_id=request_id_context.get(""),
                trace_id=trace_id_context.get(""),
                user_id=user_id_context.get(""),
                session_id=session_id_context.get(""),
                operation=operation_context.get(""),
                environment=os.getenv("ENVIRONMENT", "development")
            )
            
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                "level": record.levelname,
                "service": "whatsapp-agent",
                "logger_name": record.name,
                "message": record.getMessage(),
                "category": "system",
                **context.to_dict()
            }
            
            # Adicionar informações de exceção se houver
            if record.exc_info:
                log_entry["exception"] = {
                    "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                    "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                    "traceback": self.formatException(record.exc_info) if record.exc_info else None
                }
            
            return json.dumps(log_entry, ensure_ascii=False, default=str)
            
        except Exception as e:
            # Fallback para formato simples em caso de erro
            return f"LOG_FORMAT_ERROR: {record.getMessage()} | Error: {str(e)}"


class APMMiddleware(BaseHTTPMiddleware):
    """Middleware APM para tracking automático de requests"""
    
    async def dispatch(self, request: Request, call_next):
        """Processar request com tracking APM"""
        
        # Gerar IDs únicos para tracking
        request_id = str(uuid.uuid4())[:8]
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())[:8]
        
        # Definir contexto do request
        request_id_context.set(request_id)
        trace_id_context.set(trace_id)
        span_id_context.set(span_id)
        operation_context.set(f"{request.method} {request.url.path}")
        
        # Obter user_id se disponível nos headers ou auth
        user_id = request.headers.get("X-User-ID", "")
        if user_id:
            user_id_context.set(user_id)
        
        # Timing de performance
        start_time = time.time()
        
        # Logger estruturado
        logger = get_structured_logger("apm.middleware")
        
        # Log de início do request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            metadata={
                "http_method": request.method,
                "url_path": str(request.url.path),
                "url_query": str(request.url.query) if request.url.query else None,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", ""),
                "request_size": request.headers.get("content-length", 0)
            },
            category=LogCategory.API
        )
        
        try:
            # Processar request
            response = await call_next(request)
            
            # Calcular duração
            duration_ms = (time.time() - start_time) * 1000
            
            # Log de conclusão do request
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code} in {duration_ms:.2f}ms",
                metadata={
                    "http_method": request.method,
                    "url_path": str(request.url.path),
                    "status_code": response.status_code,
                    "response_size": response.headers.get("content-length", 0),
                    "duration_ms": duration_ms,
                    "success": response.status_code < 400
                },
                category=LogCategory.API
            )
            
            # Registrar métrica de performance
            performance_metrics = PerformanceMetrics(
                operation_name=f"{request.method} {request.url.path}",
                duration_ms=duration_ms
            )
            logger.performance_metric(performance_metrics)
            
            # Adicionar headers de tracking
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            # Log de erro
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Request failed: {request.method} {request.url.path} after {duration_ms:.2f}ms",
                metadata={
                    "http_method": request.method,
                    "url_path": str(request.url.path),
                    "duration_ms": duration_ms,
                    "error_type": e.__class__.__name__
                },
                category=LogCategory.API,
                exception=e
            )
            
            raise


def get_structured_logger(name: str) -> StructuredLogger:
    """Factory para obter logger estruturado"""
    return StructuredLogger(name)


def log_performance(operation_name: Optional[str] = None):
    """Decorator para tracking automático de performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            logger = get_structured_logger(func.__module__)
            operation_context.set(name)
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Log de sucesso
                metrics = PerformanceMetrics(
                    operation_name=name,
                    duration_ms=duration_ms
                )
                logger.performance_metric(metrics)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {name}",
                    metadata={
                        "operation_name": name,
                        "duration_ms": duration_ms,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    },
                    category=LogCategory.PERFORMANCE,
                    exception=e
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            logger = get_structured_logger(func.__module__)
            operation_context.set(name)
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Log de sucesso
                metrics = PerformanceMetrics(
                    operation_name=name,
                    duration_ms=duration_ms
                )
                logger.performance_metric(metrics)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {name}",
                    metadata={
                        "operation_name": name,
                        "duration_ms": duration_ms,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    },
                    category=LogCategory.PERFORMANCE,
                    exception=e
                )
                raise
        
        # Retornar wrapper apropriado baseado se a função é async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_business_event(event_type: str, entity_type: str, entity_id: str, 
                      action: str, metadata: Dict[str, Any] = None, 
                      value: Optional[float] = None):
    """Helper para logar eventos de negócio"""
    logger = get_structured_logger("business.events")
    
    event = BusinessEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        metadata=metadata or {},
        value=value
    )
    
    logger.business_event(event)


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """Helper para logar eventos de segurança"""
    logger = get_structured_logger("security.events")
    logger.security_event(event_type, details, severity)


def log_database_operation(operation: str, table: str, duration_ms: float, 
                         records_affected: int = 0, query_hash: Optional[str] = None):
    """Helper para logar operações de banco de dados"""
    logger = get_structured_logger("database.operations")
    
    logger.info(
        f"Database operation: {operation} on {table}",
        metadata={
            "database_operation": {
                "operation": operation,
                "table": table,
                "duration_ms": duration_ms,
                "records_affected": records_affected,
                "query_hash": query_hash
            },
            "event_category": "database_metric"
        },
        category=LogCategory.DATABASE
    )


def log_api_call(service: str, endpoint: str, method: str, status_code: int, 
                duration_ms: float, request_size: int = 0, response_size: int = 0):
    """Helper para logar chamadas de API externa"""
    logger = get_structured_logger("api.external")
    
    logger.info(
        f"External API call: {method} {service}/{endpoint} - {status_code}",
        metadata={
            "api_call": {
                "service": service,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "request_size": request_size,
                "response_size": response_size,
                "success": status_code < 400
            },
            "event_category": "api_metric"
        },
        category=LogCategory.API
    )


def setup_structured_logging():
    """Configurar sistema de logging estruturado"""
    
    # Configurar formatter estruturado para todos os loggers
    root_logger = logging.getLogger()
    
    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configurar handler console com formato estruturado
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    
    # Configurar handler de arquivo se em produção
    if os.getenv("ENVIRONMENT") == "production":
        from logging.handlers import RotatingFileHandler
        
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=log_dir / "structured.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)
    
    # Configurar loggers específicos
    loggers_config = {
        'uvicorn.access': logging.WARNING,  # Reduzir logs do uvicorn
        'sqlalchemy.engine': logging.WARNING,  # Reduzir logs SQL
        'httpx': logging.WARNING,  # Reduzir logs HTTP
    }
    
    for logger_name, level in loggers_config.items():
        logging.getLogger(logger_name).setLevel(level)
    
    print("🔍 Sistema de Logging Estruturado ativado - APM e tracing habilitados")


# Aliases para compatibilidade
def get_logger(name: str) -> StructuredLogger:
    """Alias para get_structured_logger"""
    return get_structured_logger(name)


# Context helpers
def set_user_context(user_id: str, session_id: Optional[str] = None):
    """Definir contexto do usuário"""
    user_id_context.set(user_id)
    if session_id:
        session_id_context.set(session_id)


def get_current_context() -> Dict[str, str]:
    """Obter contexto atual"""
    return {
        "request_id": request_id_context.get(""),
        "trace_id": trace_id_context.get(""),
        "span_id": span_id_context.get(""),
        "user_id": user_id_context.get(""),
        "session_id": session_id_context.get(""),
        "operation": operation_context.get("")
    }
