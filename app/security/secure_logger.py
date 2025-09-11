"""
S002 - Secure Logger Implementation
Sistema de logging seguro com sanitização de dados sensíveis
Implementação para conformidade LGPD e segurança
"""

import logging
import re
import json
from typing import Any, Dict, Optional, Union
from functools import wraps

class SecureFormatter(logging.Formatter):
    """Formatter seguro que sanitiza dados sensíveis"""
    
    # Padrões de dados sensíveis para sanitizar
    SENSITIVE_PATTERNS = [
        (re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE), '"password": "***REDACTED***"'),
        (re.compile(r'"token"\s*:\s*"[^"]*"', re.IGNORECASE), '"token": "***REDACTED***"'),
        (re.compile(r'"key"\s*:\s*"[^"]*"', re.IGNORECASE), '"key": "***REDACTED***"'),
        (re.compile(r'"secret"\s*:\s*"[^"]*"', re.IGNORECASE), '"secret": "***REDACTED***"'),
        (re.compile(r'"cpf"\s*:\s*"[^"]*"', re.IGNORECASE), '"cpf": "***REDACTED***"'),
        (re.compile(r'"rg"\s*:\s*"[^"]*"', re.IGNORECASE), '"rg": "***REDACTED***"'),
        (re.compile(r'"email"\s*:\s*"[^"]*"', re.IGNORECASE), '"email": "***REDACTED***"'),
        (re.compile(r'"phone"\s*:\s*"[^"]*"', re.IGNORECASE), '"phone": "***REDACTED***"'),
        (re.compile(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b'), '***CPF-REDACTED***'),
        (re.compile(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b'), '***CNPJ-REDACTED***'),
        (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '***EMAIL-REDACTED***'),
        (re.compile(r'\b\(\d{2}\)\s*\d{4,5}-\d{4}\b'), '***PHONE-REDACTED***'),
        (re.compile(r'\b\d{11}\b'), '***PHONE-REDACTED***'),
    ]
    
    def format(self, record):
        """Formatar log com sanitização de dados sensíveis"""
        # Aplicar formatação padrão
        formatted = super().format(record)
        
        # Sanitizar dados sensíveis
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            formatted = pattern.sub(replacement, formatted)
        
        return formatted

def sanitize_data(data: Any) -> Any:
    """Sanitiza dados sensíveis recursivamente"""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if key.lower() in ['password', 'token', 'key', 'secret', 'cpf', 'rg', 'email', 'phone']:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = sanitize_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, str):
        # Sanitizar strings com padrões sensíveis
        sanitized = data
        for pattern, replacement in SecureFormatter.SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized
    else:
        return data

def secure_log(logger: logging.Logger, level: int, message: str, data: Optional[Dict] = None):
    """Log seguro com sanitização automática"""
    if data:
        sanitized_data = sanitize_data(data)
        message = f"{message} | Data: {json.dumps(sanitized_data, default=str)}"
    
    logger.log(level, message)

def configure_secure_logging():
    """Configura logging seguro para toda a aplicação"""
    
    # Configurar formatter seguro
    secure_formatter = SecureFormatter(
        fmt='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "service": "whatsapp-agent", '
            '"logger_name": "%(name)s", "message": "%(message)s", "category": "security"}',
        datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
    )
    
    # Aplicar a todos os handlers do root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.setFormatter(secure_formatter)
    
    # Logger específico para segurança
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    
    return secure_formatter

def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[str] = None):
    """Log de eventos de segurança com sanitização"""
    security_logger = logging.getLogger('security')
    
    event_data = {
        "event_type": event_type,
        "user_id": user_id or "anonymous",
        "details": sanitize_data(details),
        "timestamp": "auto"
    }
    
    secure_log(security_logger, logging.INFO, f"Security Event: {event_type}", event_data)

def secure_logging_decorator(func):
    """Decorator para adicionar logging seguro a funções"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        func_logger = logging.getLogger(f"secure_call.{func.__module__}.{func.__name__}")
        
        try:
            # Log de entrada (sem dados sensíveis)
            func_logger.info(f"🔒 S002: Calling {func.__name__}")
            
            result = await func(*args, **kwargs)
            
            # Log de sucesso
            func_logger.info(f"✅ S002: {func.__name__} completed successfully")
            return result
            
        except Exception as e:
            # Log de erro (sem exposição de dados sensíveis)
            func_logger.error(f"❌ S002: {func.__name__} failed: {type(e).__name__}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        func_logger = logging.getLogger(f"secure_call.{func.__module__}.{func.__name__}")
        
        try:
            func_logger.info(f"🔒 S002: Calling {func.__name__}")
            result = func(*args, **kwargs)
            func_logger.info(f"✅ S002: {func.__name__} completed successfully")
            return result
            
        except Exception as e:
            func_logger.error(f"❌ S002: {func.__name__} failed: {type(e).__name__}")
            raise
    
    # Retornar wrapper apropriado baseado na função
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# Configurar logging seguro na importação
logger = logging.getLogger(__name__)
logger.info("🔒 S002 Secure Logger: Módulo carregado com sucesso")
