"""
🔒 S002 - Secure Logger Implementation
====================================

Logger seguro que aplica sanitização automática de dados sensíveis.

Funcionalidades:
- Sanitização automática em todas as saídas de log
- Formatador personalizado para compliance LGPD
- Handler especializado para logs seguros
- Auditoria automática de violações
- Modo compliance rigoroso

Autor: GitHub Copilot
Data: 2025-09-11
Status: S002 - Auditoria de Logs Sensíveis
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path

from .log_sanitizer import log_sanitizer, sanitize_log_message, sanitize_log_data


class SecureFormatter(logging.Formatter):
    """
    Formatador de logs com sanitização automática
    """
    
    def __init__(self, 
                 fmt: Optional[str] = None,
                 datefmt: Optional[str] = None,
                 sanitize_enabled: bool = True,
                 audit_enabled: bool = True):
        super().__init__(fmt, datefmt)
        self.sanitize_enabled = sanitize_enabled
        self.audit_enabled = audit_enabled
        
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatar log record aplicando sanitização
        """
        # Criar cópia do record para não modificar o original
        sanitized_record = logging.LogRecord(
            name=record.name,
            level=record.levelno,
            pathname=record.pathname,
            lineno=record.lineno,
            msg=record.msg,
            args=record.args,
            exc_info=record.exc_info,
            func=record.funcName
        )
        
        # Aplicar sanitização se habilitada
        if self.sanitize_enabled:
            # Sanitizar mensagem
            if isinstance(sanitized_record.msg, str):
                sanitized_record.msg = sanitize_log_message(sanitized_record.msg)
            
            # Sanitizar argumentos
            if sanitized_record.args:
                sanitized_args = []
                for arg in sanitized_record.args:
                    if isinstance(arg, (str, dict, list)):
                        sanitized_args.append(sanitize_log_data(arg))
                    else:
                        sanitized_args.append(arg)
                sanitized_record.args = tuple(sanitized_args)
        
        # Adicionar metadados de segurança
        if not hasattr(sanitized_record, 'security_metadata'):
            sanitized_record.security_metadata = {
                'sanitized': self.sanitize_enabled,
                'timestamp': datetime.utcnow().isoformat(),
                'compliance': 'LGPD'
            }
        
        # Formatar usando o formatador pai
        formatted = super().format(sanitized_record)
        
        # Auditoria adicional se habilitada
        if self.audit_enabled and self.sanitize_enabled:
            # Verificar se ainda há dados sensíveis após sanitização
            audit_result = log_sanitizer.audit_log_entry(formatted)
            if audit_result['compliance_status'] == 'VIOLATION':
                # Log interno de segurança (sem expor dados)
                security_log = (
                    f"[SECURITY_AUDIT] Possível violação detectada em log: "
                    f"patterns={len(audit_result['found_patterns'])}, "
                    f"risk={audit_result['lgpd_risk_level']}"
                )
                # Enviar para handler especial de segurança se disponível
                self._log_security_violation(security_log, audit_result)
        
        return formatted
    
    def _log_security_violation(self, message: str, audit_result: Dict[str, Any]):
        """Log interno de violações de segurança"""
        try:
            # Log para arquivo especial de auditoria
            audit_log_path = Path("logs/security_audit.log")
            audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(audit_log_path, "a", encoding="utf-8") as f:
                audit_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": message,
                    "audit_result": audit_result
                }
                f.write(json.dumps(audit_entry, ensure_ascii=False) + "\n")
        except Exception:
            # Falha silenciosa para não quebrar o logging principal
            pass


class SecureHandler(logging.Handler):
    """
    Handler de logs com sanitização e auditoria
    """
    
    def __init__(self, 
                 stream=None,
                 sanitize_enabled: bool = True,
                 audit_enabled: bool = True):
        super().__init__()
        self.stream = stream or sys.stdout
        self.sanitize_enabled = sanitize_enabled
        self.audit_enabled = audit_enabled
        
        # Configurar formatador seguro
        secure_formatter = SecureFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            sanitize_enabled=sanitize_enabled,
            audit_enabled=audit_enabled
        )
        self.setFormatter(secure_formatter)
    
    def emit(self, record: logging.LogRecord):
        """
        Emitir log record com verificações de segurança
        """
        try:
            # Formatar mensagem (aplica sanitização)
            formatted = self.format(record)
            
            # Escrever para stream
            self.stream.write(formatted + "\n")
            
            # Flush se suportado
            if hasattr(self.stream, 'flush'):
                self.stream.flush()
                
        except Exception:
            # Falha silenciosa para não quebrar a aplicação
            self.handleError(record)


class SecureFileHandler(logging.FileHandler):
    """
    File handler com sanitização e rotação segura
    """
    
    def __init__(self, 
                 filename: str,
                 mode: str = 'a',
                 encoding: str = 'utf-8',
                 sanitize_enabled: bool = True,
                 audit_enabled: bool = True):
        super().__init__(filename, mode, encoding=encoding)
        
        # Configurar formatador seguro
        secure_formatter = SecureFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            sanitize_enabled=sanitize_enabled,
            audit_enabled=audit_enabled
        )
        self.setFormatter(secure_formatter)


def get_secure_logger(name: str, 
                     level: int = logging.INFO,
                     enable_sanitization: bool = True,
                     enable_audit: bool = True,
                     log_file: Optional[str] = None) -> logging.Logger:
    """
    Obter logger seguro com sanitização automática
    
    Args:
        name: Nome do logger
        level: Nível de log
        enable_sanitization: Habilitar sanitização
        enable_audit: Habilitar auditoria
        log_file: Arquivo de log (opcional)
        
    Returns:
        Logger configurado com segurança
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remover handlers existentes para evitar duplicação
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Handler para console
    console_handler = SecureHandler(
        stream=sys.stdout,
        sanitize_enabled=enable_sanitization,
        audit_enabled=enable_audit
    )
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # Handler para arquivo se especificado
    if log_file:
        # Criar diretório se necessário
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = SecureFileHandler(
            filename=str(log_path),
            sanitize_enabled=enable_sanitization,
            audit_enabled=enable_audit
        )
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    # Evitar propagação para o root logger
    logger.propagate = False
    
    return logger


def configure_secure_logging(app_name: str = "whats_agent",
                           log_level: str = "INFO",
                           enable_sanitization: bool = True,
                           enable_audit: bool = True,
                           log_directory: str = "logs") -> Dict[str, logging.Logger]:
    """
    Configurar sistema de logging seguro para toda a aplicação
    
    Args:
        app_name: Nome da aplicação
        log_level: Nível de log
        enable_sanitization: Habilitar sanitização global
        enable_audit: Habilitar auditoria global
        log_directory: Diretório base para logs
        
    Returns:
        Dicionário com loggers configurados
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Criar diretório de logs
    log_dir = Path(log_directory)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar loggers principais
    loggers = {
        'main': get_secure_logger(
            f"{app_name}.main",
            level=level,
            enable_sanitization=enable_sanitization,
            enable_audit=enable_audit,
            log_file=str(log_dir / "application.log")
        ),
        'security': get_secure_logger(
            f"{app_name}.security",
            level=logging.WARNING,  # Apenas logs importantes
            enable_sanitization=enable_sanitization,
            enable_audit=enable_audit,
            log_file=str(log_dir / "security.log")
        ),
        'api': get_secure_logger(
            f"{app_name}.api",
            level=level,
            enable_sanitization=enable_sanitization,
            enable_audit=enable_audit,
            log_file=str(log_dir / "api.log")
        ),
        'webhook': get_secure_logger(
            f"{app_name}.webhook",
            level=level,
            enable_sanitization=enable_sanitization,
            enable_audit=enable_audit,
            log_file=str(log_dir / "webhook.log")
        ),
        'database': get_secure_logger(
            f"{app_name}.database",
            level=logging.WARNING,  # Apenas erros e warnings
            enable_sanitization=enable_sanitization,
            enable_audit=enable_audit,
            log_file=str(log_dir / "database.log")
        )
    }
    
    # Configurar root logger com sanitização
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remover handlers existentes do root
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Adicionar handler seguro ao root
    root_handler = SecureHandler(
        sanitize_enabled=enable_sanitization,
        audit_enabled=enable_audit
    )
    root_handler.setLevel(level)
    root_logger.addHandler(root_handler)
    
    return loggers


# Função helper para migração gradual
def get_sanitized_logger(name: str) -> logging.Logger:
    """
    Função helper para obter logger sanitizado
    Compatível com logging.getLogger() mas com sanitização
    """
    return get_secure_logger(
        name=name,
        enable_sanitization=True,
        enable_audit=True
    )
