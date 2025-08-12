"""
Sistema de Logging Estruturado e Consistente
===========================================

Sistema unificado de logging que elimina inconsistências e fornece:
- Logging estruturado com JSON para produção
- Rotação automática de logs
- Contexto de requisições
- Performance tracking
- Eliminação de print statements
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from contextvars import ContextVar
from pathlib import Path
import traceback
import sys
from functools import wraps
import time
from enum import Enum

from app.config.config_factory import ConfigFactory

# Context variables para tracking
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
user_id_context: ContextVar[str] = ContextVar('user_id', default='')
session_id_context: ContextVar[str] = ContextVar('session_id', default='')
performance_context: ContextVar[Dict[str, Any]] = ContextVar('performance', default={})


class LogLevel(Enum):
    """Níveis de log padronizados"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PerformanceTimer:
    """Context manager para tracking de performance"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        perf_data = performance_context.get({})
        perf_data[self.operation_name] = {
            'duration_ms': round(duration * 1000, 2),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        performance_context.set(perf_data)


class StructuredFormatter(logging.Formatter):
    """Formatter que produz logs em formato JSON estruturado"""
    
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
            'process_id': os.getpid(),
            'thread_id': record.thread,
            'thread_name': record.threadName,
        }
        
        # Adicionar contexto da requisição
        if request_id := request_id_context.get(''):
            log_data['request_id'] = request_id
        
        if user_id := user_id_context.get(''):
            log_data['user_id'] = user_id
        
        if session_id := session_id_context.get(''):
            log_data['session_id'] = session_id
        
        # Adicionar dados de performance
        if perf_data := performance_context.get({}):
            log_data['performance'] = perf_data
        
        # Adicionar dados extras do record
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Adicionar informações de exceção
        if record.exc_info and record.exc_info != True:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': ''.join(traceback.format_exception(*record.exc_info))
            }
        
        # Adicionar dados personalizados com prefixo custom_
        for key, value in record.__dict__.items():
            if key.startswith('custom_'):
                log_data[key[7:]] = value  # Remove 'custom_' prefix
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class PlainFormatter(logging.Formatter):
    """Formatter simples para desenvolvimento"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


class ContextLogger:
    """
    Logger com contexto automático e métodos convenientes
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._original_name = name
    
    def _log_with_context(self, level: int, message: str, 
                         extra_data: Optional[Dict[str, Any]] = None, 
                         exc_info: Optional[bool] = None):
        """Log com contexto automático"""
        
        # Preparar dados extras
        extra = {'extra_data': extra_data or {}}
        
        # Criar o record manualmente para melhores informações de stack
        frame = sys._getframe(2)
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=level,
            fn=frame.f_code.co_filename,
            lno=frame.f_lineno,
            msg=message,
            args=(),
            exc_info=exc_info,
            extra=extra
        )
        
        # Adicionar informações de módulo e função
        record.module = os.path.splitext(os.path.basename(record.pathname))[0]
        record.funcName = frame.f_code.co_name
        
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
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, 
              exc_info: bool = False):
        """Log error com contexto"""
        self._log_with_context(logging.ERROR, message, extra_data, exc_info)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None, 
                 exc_info: bool = False):
        """Log critical com contexto"""
        self._log_with_context(logging.CRITICAL, message, extra_data, exc_info)
    
    def exception(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log exception com traceback automático"""
        self._log_with_context(logging.ERROR, message, extra_data, exc_info=True)
    
    def performance(self, operation: str, duration_ms: float, 
                   extra_data: Optional[Dict[str, Any]] = None):
        """Log específico para performance"""
        perf_data = {
            'operation': operation,
            'duration_ms': duration_ms,
            'performance_log': True
        }
        if extra_data:
            perf_data.update(extra_data)
        
        self.info(f"Performance: {operation} took {duration_ms:.2f}ms", perf_data)


class LoggerSetup:
    """
    Configuração e setup do sistema de logging
    """
    
    def __init__(self):
        self.config = ConfigFactory.get_singleton_config()
        self.log_dir = Path(self.config.log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_bytes = self._parse_size(self.config.log_rotation_size)
        self.backup_count = self.config.log_backup_count
        
    def _parse_size(self, size_str: str) -> int:
        """Converter string de tamanho para bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)  # Assume bytes
        
    def setup_logging(self) -> None:
        """Configurar sistema de logging baseado na configuração"""
        
        # Limpar configurações anteriores
        logging.getLogger().handlers.clear()
        
        # Nível de log
        log_level = getattr(logging, self.config.log_level.upper())
        
        # Configurar root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Escolher formatter baseado no formato configurado
        if self.config.log_format == "json":
            formatter = StructuredFormatter()
        else:
            formatter = PlainFormatter()
        
        # Handler para console (sempre presente)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Handlers para arquivo apenas em produção/staging
        if self.config.environment.value in ['staging', 'production']:
            self._setup_file_handlers(formatter, log_level)
        
        # Configurar loggers de terceiros
        self._configure_third_party_loggers()
        
        # Log da inicialização
        logger = get_logger(__name__)
        logger.info("Sistema de logging configurado", {
            'environment': self.config.environment.value,
            'log_level': self.config.log_level,
            'log_format': self.config.log_format,
            'log_dir': str(self.log_dir)
        })
    
    def _setup_file_handlers(self, formatter: logging.Formatter, log_level: int) -> None:
        """Configurar handlers de arquivo com rotação"""
        
        # Handler principal da aplicação
        app_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "app.log",
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        app_handler.setFormatter(formatter)
        app_handler.setLevel(log_level)
        
        # Handler para erros (apenas ERROR e CRITICAL)
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "error.log",
            maxBytes=self.max_bytes,
            backupCount=max(5, self.backup_count // 2),
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Handler para performance (apenas se habilitado)
        handlers_to_add = [app_handler, error_handler]
        
        if self.config.log_performance:
            performance_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / "performance.log",
                maxBytes=self.max_bytes,
                backupCount=max(5, self.backup_count // 2),
                encoding='utf-8'
            )
            performance_handler.setFormatter(formatter)
            performance_handler.addFilter(self._performance_filter)
            handlers_to_add.append(performance_handler)
        
        # Handler para business logs (apenas se habilitado)
        if self.config.log_business:
            business_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_dir / "business.log",
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            business_handler.setFormatter(formatter)
            business_handler.addFilter(self._business_filter)
            handlers_to_add.append(business_handler)
        
        # Adicionar handlers ao root logger
        root_logger = logging.getLogger()
        for handler in handlers_to_add:
            root_logger.addHandler(handler)
    
    def _performance_filter(self, record: logging.LogRecord) -> bool:
        """Filtro para logs de performance"""
        return (hasattr(record, 'extra_data') and 
                record.extra_data.get('performance_log', False))
    
    def _business_filter(self, record: logging.LogRecord) -> bool:
        """Filtro para logs de negócio (WhatsApp, usuários, etc.)"""
        business_loggers = ['webhook', 'whatsapp', 'user', 'message', 'auth']
        return any(business_logger in record.name.lower() for business_logger in business_loggers)
    
    def _configure_third_party_loggers(self) -> None:
        """Configurar níveis de log para bibliotecas de terceiros"""
        
        # Nível configurável para bibliotecas externas
        third_party_level = getattr(logging, self.config.log_third_party_level.upper())
        
        # Bibliotecas que devem ter logging reduzido
        external_loggers = {
            'uvicorn': third_party_level,
            'uvicorn.access': third_party_level,
            'uvicorn.error': min(third_party_level, logging.INFO),
            'fastapi': third_party_level,
            'sqlalchemy': third_party_level,
            'sqlalchemy.engine': third_party_level,
            'httpx': third_party_level,
            'asyncio': third_party_level,
            'urllib3': third_party_level,
            'requests': third_party_level,
            'pydantic': third_party_level,
        }
        
        for logger_name, level in external_loggers.items():
            logging.getLogger(logger_name).setLevel(level)


# Funções convenientes para obter loggers
def get_logger(name: str) -> ContextLogger:
    """Obter logger com contexto para um módulo"""
    return ContextLogger(name)


def get_performance_timer(operation_name: str) -> PerformanceTimer:
    """Obter timer de performance"""
    return PerformanceTimer(operation_name)


# Decorators úteis
def log_performance(operation_name: Optional[str] = None):
    """Decorator para logging automático de performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            logger = get_logger(func.__module__)
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.performance(name, duration)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Erro em {name} após {duration:.2f}ms: {e}", 
                           {'operation': name, 'duration_ms': duration}, exc_info=True)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            logger = get_logger(func.__module__)
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.performance(name, duration)
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"Erro em {name} após {duration:.2f}ms: {e}", 
                           {'operation': name, 'duration_ms': duration}, exc_info=True)
                raise
        
        # Retornar wrapper apropriado baseado se a função é async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_function_call(include_args: bool = False, include_result: bool = False):
    """Decorator para logging automático de chamadas de função"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            log_data = {'function': func_name}
            if include_args:
                log_data['args'] = str(args)
                log_data['kwargs'] = str(kwargs)
            
            logger.debug(f"Chamando função {func_name}", log_data)
            
            try:
                result = await func(*args, **kwargs)
                if include_result:
                    log_data['result'] = str(result)
                logger.debug(f"Função {func_name} executada com sucesso", log_data)
                return result
            except Exception as e:
                logger.error(f"Erro na função {func_name}: {e}", log_data, exc_info=True)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            log_data = {'function': func_name}
            if include_args:
                log_data['args'] = str(args)
                log_data['kwargs'] = str(kwargs)
            
            logger.debug(f"Chamando função {func_name}", log_data)
            
            try:
                result = func(*args, **kwargs)
                if include_result:
                    log_data['result'] = str(result)
                logger.debug(f"Função {func_name} executada com sucesso", log_data)
                return result
            except Exception as e:
                logger.error(f"Erro na função {func_name}: {e}", log_data, exc_info=True)
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Context managers para contexto de requisição
class RequestContext:
    """Context manager para contexto de requisição"""
    
    def __init__(self, request_id: str, user_id: str = "", session_id: str = ""):
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self.tokens = {}
    
    def __enter__(self):
        self.tokens['request_id'] = request_id_context.set(self.request_id)
        if self.user_id:
            self.tokens['user_id'] = user_id_context.set(self.user_id)
        if self.session_id:
            self.tokens['session_id'] = session_id_context.set(self.session_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in self.tokens.values():
            token.var.set(token.old_value)


# Função de inicialização principal
def init_logging():
    """Inicializar sistema de logging"""
    setup = LoggerSetup()
    setup.setup_logging()


# Função para substituir print statements
def safe_print(*args, level: LogLevel = LogLevel.INFO, logger_name: str = "app", **kwargs):
    """
    Substituição segura para print() que usa o sistema de logging
    Usado para migração gradual de print statements
    """
    logger = get_logger(logger_name)
    message = " ".join(str(arg) for arg in args)
    
    level_methods = {
        LogLevel.DEBUG: logger.debug,
        LogLevel.INFO: logger.info,
        LogLevel.WARNING: logger.warning,
        LogLevel.ERROR: logger.error,
        LogLevel.CRITICAL: logger.critical,
    }
    
    level_methods[level](message)


if __name__ == "__main__":
    # Teste do sistema de logging
    init_logging()
    
    logger = get_logger(__name__)
    
    logger.info("Teste do sistema de logging")
    logger.warning("Teste de warning")
    
    try:
        raise ValueError("Teste de exception")
    except Exception as e:
        logger.exception("Teste de exception logging")
    
    # Teste de performance
    with get_performance_timer("teste_operacao"):
        time.sleep(0.1)
    
    logger.performance("operacao_manual", 150.5, {"teste": True})
