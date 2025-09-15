"""
🔒 HF002 - Secure Logger Implementation
=======================================

Sistema de logging seguro com sanitização automática de dados sensíveis.
Implementação para conformidade LGPD/GDPR e segurança de dados.

Funcionalidades:
- Sanitização automática de PII (telefones, emails, CPF, etc.)
- Redação de tokens, senhas e chaves API
- Sanitização recursiva de metadados estruturados
- Formatter global para todos os logs do sistema
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union


class LogSanitizer:
    """
    HF002 FIX: Sanitizador avançado de logs para remover dados sensíveis
    """

    # Padrões regex para detectar dados sensíveis
    SENSITIVE_PATTERNS = {
        # WhatsApp IDs primeiro (mais específico)
        "whatsapp_id": [
            r"(55\d{10,11}@[sc]\.whatsapp\.net)",
            r"(55\d{10,11}@c\.us)",
        ],
        "phone": [
            r"(\+55\s?\d{2}\s?\d{4,5}[-\s]?\d{4})",  # +55 11 99999-9999
            r"(\d{2}\s?\d{4,5}[-\s]?\d{4})",  # 11 99999-9999
            r"(\b\d{11}\b)",  # 11999887766 (standalone)
        ],
        "email": [
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        ],
        "token": [
            r"(Bearer\s+[A-Za-z0-9\-_\.]+)",
            r"([A-Za-z0-9]{32,128})",
        ],
        "password": [
            r'("password[^"]*":\s*"[^"]*")',
            r'(password["\s]*[:=]["\s]*[^"\s]+)',
        ],
        "document": [
            r"(\d{3}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-]?\d{2})",  # CPF
            r"(\d{2}[\.\-]?\d{3}[\.\-]?\d{3}[\.\-]?\d{4}[\.\-]?\d{2})",  # CNPJ
        ],
    }

    SENSITIVE_FIELDS = {
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "phone",
        "email",
        "cpf",
        "cnpj",
        "documento",
    }

    def __init__(self):
        """Inicializar sanitizador HF002"""
        self.compiled_patterns = {}
        # Processar na ordem específica para evitar sobreposição
        for category in [
            "whatsapp_id",
            "phone",
            "email",
            "token",
            "password",
            "document",
        ]:
            if category in self.SENSITIVE_PATTERNS:
                patterns = self.SENSITIVE_PATTERNS[category]
                self.compiled_patterns[category] = [
                    re.compile(pattern, re.IGNORECASE) for pattern in patterns
                ]

    def sanitize_message(self, message: str) -> str:
        """Remove padrões sensíveis da mensagem de log"""
        if not isinstance(message, str):
            message = str(message)

        sanitized = message
        for category, compiled_patterns in self.compiled_patterns.items():
            for pattern in compiled_patterns:
                placeholder = f"[{category.upper()}_REDACTED_HF002]"
                sanitized = pattern.sub(placeholder, sanitized)

        return sanitized

    def sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza metadados recursivamente"""
        if not isinstance(metadata, dict):
            return metadata

        sanitized = {}
        for key, value in metadata.items():
            if self._is_sensitive_field(key):
                sanitized[key] = "[SENSITIVE_FIELD_REDACTED_HF002]"
            elif isinstance(value, str):
                sanitized[key] = self.sanitize_message(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_metadata(value)
            elif isinstance(value, list):
                sanitized[key] = self._sanitize_list(value)
            else:
                sanitized[key] = value

        return sanitized

    def _is_sensitive_field(self, field_name: str) -> bool:
        """Verifica se nome do campo indica dados sensíveis"""
        field_lower = field_name.lower()
        return any(sensitive in field_lower for sensitive in self.SENSITIVE_FIELDS)

    def _sanitize_list(self, data_list: List[Any]) -> List[Any]:
        """Sanitiza lista recursivamente"""
        sanitized = []
        for item in data_list:
            if isinstance(item, str):
                sanitized.append(self.sanitize_message(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_metadata(item))
            elif isinstance(item, list):
                sanitized.append(self._sanitize_list(item))
            else:
                sanitized.append(item)
        return sanitized


# Instância global do sanitizador HF002
_global_sanitizer: Optional[LogSanitizer] = None


def get_log_sanitizer() -> LogSanitizer:
    """Obter instância global do sanitizador de logs HF002"""
    global _global_sanitizer
    if _global_sanitizer is None:
        _global_sanitizer = LogSanitizer()
    return _global_sanitizer


class SanitizedFormatter(logging.Formatter):
    """HF002 FIX: Formatter de logging que sanitiza automaticamente dados sensíveis"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sanitizer = get_log_sanitizer()

    def format(self, record):
        """Formatar log com sanitização HF002"""
        formatted = super().format(record)
        sanitized = self.sanitizer.sanitize_message(formatted)
        return sanitized


def sanitize_log_data(data: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
    """HF002 FIX: Função utilitária para sanitizar dados de log"""
    sanitizer = get_log_sanitizer()

    if isinstance(data, str):
        return sanitizer.sanitize_message(data)
    elif isinstance(data, dict):
        return sanitizer.sanitize_metadata(data)
    else:
        return data


def configure_secure_logging():
    """HF002 FIX: Configurar logging seguro global com sanitização automática"""
    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        if not isinstance(handler.formatter, SanitizedFormatter):
            current_format = getattr(
                handler.formatter, "_fmt", "%(levelname)s:%(name)s:%(message)s"
            )
            sanitized_formatter = SanitizedFormatter(current_format)
            handler.setFormatter(sanitized_formatter)

    sanitizer_logger = logging.getLogger("hf002.sanitizer")
    sanitizer_logger.info(
        "🔒 HF002 PROTECTION: Secure logging configured with data sanitization"
    )


def secure_log(
    logger: logging.Logger,
    level: int,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
    sanitize: bool = True,
):
    """HF002 FIX: Log seguro com sanitização automática de dados sensíveis"""
    if sanitize:
        sanitizer = get_log_sanitizer()
        safe_message = sanitizer.sanitize_message(message)

        if metadata:
            safe_metadata = sanitizer.sanitize_metadata(metadata)
            final_message = (
                f"{safe_message} | Metadata: {json.dumps(safe_metadata, default=str)}"
            )
        else:
            final_message = safe_message
    else:
        final_message = message
        if metadata:
            final_message = f"{message} | Metadata: {json.dumps(metadata, default=str)}"

    logger.log(level, final_message)


# Backward compatibility
SecureFormatter = SanitizedFormatter
sanitize_data = sanitize_log_data
