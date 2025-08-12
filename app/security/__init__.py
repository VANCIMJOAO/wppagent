"""
🔐 Sistema de Segurança e Criptografia - WhatsApp Agent
========================================================

Módulo completo de segurança com:
- Criptografia AES-256-GCM para dados sensíveis
- Gerenciamento seguro de certificados SSL
- Proteção de chaves privadas
- HTTPS obrigatório com HSTS
- Validação de certificados
"""

from .encryption_service import EncryptionService
from .ssl_manager import SSLManager
from .certificate_validator import CertificateValidator
from .data_encryption import DataEncryption

__all__ = [
    'EncryptionService',
    'SSLManager', 
    'CertificateValidator',
    'DataEncryption'
]
