from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema de Logging Estruturado para Produção
============================================

Implementa logging estruturado com:
- Rotação automática de logs
- Formatação JSON para análise
- Níveis de log apropriados
- Contexto de requisições
- Performance tracking
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from contextvars import ContextVar
from pathlib import Path
import traceback
import sys
from functools import wraps
import time

# Context variables para tracking de requisições
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
user_id_context: ContextVar[str] = ContextVar('user_id', default='')
session_id_context: ContextVar[str] = ContextVar('session_id', default='')


class StructuredFormatter(logging.Formatter):
    """
    Formatter que produz logs em formato JSON estruturado
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatar log record em JSON estruturado"""
        
        # Dados básicos do log
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Adicionar contexto da requisição se disponível
        if request_id := request_id_context.get(''):
            log_data['request_id'] = request_id
        
        if user_id := user_id_context.get(''):
            log_data['user_id'] = user_id
        
        if session_id := session_id_context.get(''):
            log_data['session_id'] = session_id
        
        # Adicionar dados extras do record
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Adicionar informações de exceção se presente
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }
        
        # Adicionar dados personalizados
        for key, value in record.__dict__.items():
            if key.startswith('custom_'):
                log_data[key[7:]] = value  # Remove 'custom_' prefix
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class ContextLogger:
    """
    Logger com contexto automático para tracking de requisições
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log_with_context(self, level: int, message: str, extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Log com contexto automático"""
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=level,
            fn='',
            lno=0,
            msg=message,
            args=(),
            exc_info=kwargs.get('exc_info'),
            extra={'extra_data': extra_data or {}}
        )
        
        # Adicionar frame info
        frame = sys._getframe(2)
        record.pathname = frame.f_code.co_filename
        record.lineno = frame.f_lineno
        record.funcName = frame.f_code.co_name
        record.module = os.path.splitext(os.path.basename(record.pathname))[0]
        
        self.logger.handle(record)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug com contexto"""
        self._log_with_context(logging.DEBUG, message, extra_data)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info com contexto"""
        self._log_with_context(logging.INFO, message, extra_data)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning com contexto"""
        self._log_with_context(logging.WARNING, message, extra_data)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error com contexto"""
        self._log_with_context(logging.ERROR, message, extra_data, exc_info=exc_info)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical com contexto"""
        self._log_with_context(logging.CRITICAL, message, extra_data, exc_info=exc_info)


class ProductionLoggerSetup:
    """
    Configuração completa de logging para produção
    """
    
    def __init__(self, 
                 log_dir: str = "logs",
                 max_bytes: int = 50 * 1024 * 1024,  # 50MB
                 backup_count: int = 10,
                 log_level: str = "INFO"):
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.log_level = getattr(logging, log_level.upper())
        
        # Configurar loggers
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Configurar todos os loggers do sistema"""
        
        # Configurar formatter estruturado
        structured_formatter = StructuredFormatter()
        
        # Configurar formatter simples para console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler para console (desenvolvimento)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Handler para log geral da aplicação
        app_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "app.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        app_handler.setFormatter(structured_formatter)
        app_handler.setLevel(self.log_level)
        
        # Handler para erros críticos
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "errors.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setFormatter(structured_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Handler para auditoria de segurança
        security_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "security.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        security_handler.setFormatter(structured_formatter)
        security_handler.setLevel(logging.INFO)
        
        # Handler para performance
        performance_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "performance.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        performance_handler.setFormatter(structured_formatter)
        performance_handler.setLevel(logging.INFO)
        
        # Handler para negócio/analytics
        business_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "business.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        business_handler.setFormatter(structured_formatter)
        business_handler.setLevel(logging.INFO)
        
        # Handler para webhook específico
        webhook_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "webhook.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        webhook_handler.setFormatter(structured_formatter)
        webhook_handler.setLevel(logging.DEBUG)
        
        # Configurar logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        root_logger.addHandler(app_handler)
        root_logger.addHandler(error_handler)
        
        # Configurar loggers específicos
        
        # Logger de segurança
        security_logger = logging.getLogger('security')
        security_logger.addHandler(security_handler)
        security_logger.propagate = False
        
        # Logger de performance
        performance_logger = logging.getLogger('performance')
        performance_logger.addHandler(performance_handler)
        performance_logger.propagate = False
        
        # Logger de negócio
        business_logger = logging.getLogger('business')
        business_logger.addHandler(business_handler)
        business_logger.propagate = False
        
        # Logger de webhook
        webhook_logger = logging.getLogger('webhook')
        webhook_logger.addHandler(webhook_handler)
        webhook_logger.propagate = False
        
        # Logger de alertas
        alerts_logger = logging.getLogger('alerts')
        alerts_logger.addHandler(error_handler)
        alerts_logger.propagate = False
        
        # Suprimir logs verbosos de bibliotecas
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)


def log_execution_time(logger: ContextLogger, operation_name: str):
    """
    Decorator para logar tempo de execução de funções
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"Operation completed: {operation_name}",
                    extra_data={
                        'operation': operation_name,
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'success': True
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Operation failed: {operation_name}",
                    extra_data={
                        'operation': operation_name,
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"Operation completed: {operation_name}",
                    extra_data={
                        'operation': operation_name,
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'success': True
                    }
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Operation failed: {operation_name}",
                    extra_data={
                        'operation': operation_name,
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'success': False,
                        'error': str(e),
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                raise
        
        # Retornar wrapper apropriado baseado na função
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Loggers especializados pré-configurados
security_logger = ContextLogger('security')
performance_logger = ContextLogger('performance')
business_logger = ContextLogger('business')
webhook_logger = ContextLogger('webhook')
alerts_logger = ContextLogger('alerts')


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """
    Logar eventos de segurança
    """
    security_logger.info(
        f"Security event: {event_type}",
        extra_data={
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    )


def log_business_event(event_type: str, metrics: Dict[str, Any]):
    """
    Logar eventos de negócio para analytics
    """
    business_logger.info(
        f"Business event: {event_type}",
        extra_data={
            'event_type': event_type,
            'metrics': metrics,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    )


def log_performance_metric(operation: str, duration_ms: float, additional_data: Optional[Dict[str, Any]] = None):
    """
    Logar métricas de performance
    """
    performance_logger.info(
        f"Performance metric: {operation}",
        extra_data={
            'operation': operation,
            'duration_ms': duration_ms,
            'additional_data': additional_data or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    )


def set_request_context(request_id: str, user_id: str = "", session_id: str = ""):
    """
    Definir contexto da requisição para logs
    """
    request_id_context.set(request_id)
    if user_id:
        user_id_context.set(user_id)
    if session_id:
        session_id_context.set(session_id)


def clear_request_context():
    """
    Limpar contexto da requisição
    """
    request_id_context.set('')
    user_id_context.set('')
    session_id_context.set('')


# Instância global do setup de logging
logger_setup = None

def setup_production_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """
    Configurar logging para produção
    """
    global logger_setup
    logger_setup = ProductionLoggerSetup(log_dir=log_dir, log_level=log_level)
    
    # Logger principal da aplicação
    main_logger = ContextLogger('whatsapp_agent')
    main_logger.info("Production logging system initialized", extra_data={
        'log_dir': log_dir,
        'log_level': log_level,
        'system': 'whatsapp_agent'
    })
    
    return main_logger
