"""
🔒 S002 - Log Sanitization System
================================

Sistema de sanitização de logs para compliance LGPD e proteção de dados sensíveis.

Funcionalidades:
- Redação automática de PII (dados pessoais)
- Sanitização de tokens e credenciais
- Mascaramento de dados sensíveis
- Compliance LGPD/GDPR
- Auditoria de logs seguros

Autor: GitHub Copilot
Data: 2025-09-11
Status: S002 - Auditoria de Logs Sensíveis
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class SensitiveDataType(Enum):
    """Tipos de dados sensíveis identificados"""
    # Credenciais
    PASSWORD = "password"
    TOKEN = "token"
    SECRET = "secret"
    API_KEY = "api_key"
    AUTH_HEADER = "auth_header"
    
    # PII - Dados Pessoais (LGPD)
    CPF = "cpf"
    CNPJ = "cnpj"
    EMAIL = "email"
    PHONE = "phone"
    WA_ID = "wa_id"
    USER_ID = "user_id"
    
    # Dados Financeiros
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    PIX_KEY = "pix_key"
    
    # Dados Biométricos
    BIOMETRIC = "biometric"
    
    # Endereços
    ADDRESS = "address"
    ZIP_CODE = "zip_code"


@dataclass
class SensitivePattern:
    """Padrão de dado sensível"""
    name: str
    data_type: SensitiveDataType
    regex: str
    replacement: str
    description: str
    lgpd_category: str  # Categoria LGPD


class LogSanitizer:
    """
    Sistema de sanitização de logs com proteção LGPD
    """
    
    def __init__(self):
        self.patterns = self._init_sensitive_patterns()
        self.redaction_marker = "[REDACTED]"
        self.lgpd_compliance = True
        
    def _init_sensitive_patterns(self) -> List[SensitivePattern]:
        """Inicializar padrões de dados sensíveis"""
        return [
            # === CREDENCIAIS ===
            SensitivePattern(
                name="password_field",
                data_type=SensitiveDataType.PASSWORD,
                regex=r'(?i)(password|senha|pwd)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)',
                replacement=r'\1: "[REDACTED_PASSWORD]"',
                description="Campos de senha",
                lgpd_category="Dados de Autenticação"
            ),
            SensitivePattern(
                name="bearer_token",
                data_type=SensitiveDataType.TOKEN,
                regex=r'(?i)bearer\s+([a-zA-Z0-9\-_=]+\.[a-zA-Z0-9\-_=]+\.?[a-zA-Z0-9\-_=]*)',
                replacement=r'Bearer [REDACTED_JWT_TOKEN]',
                description="Tokens JWT Bearer",
                lgpd_category="Dados de Autenticação"
            ),
            SensitivePattern(
                name="jwt_token_standalone",
                data_type=SensitiveDataType.TOKEN,
                regex=r'\b[a-zA-Z0-9\-_=]+\.[a-zA-Z0-9\-_=]+\.?[a-zA-Z0-9\-_=]*\b',
                replacement=r'[REDACTED_JWT_TOKEN]',
                description="Tokens JWT independentes",
                lgpd_category="Dados de Autenticação"
            ),
            SensitivePattern(
                name="authorization_header",
                data_type=SensitiveDataType.AUTH_HEADER,
                regex=r'(?i)(authorization|auth)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)',
                replacement=r'\1: "[REDACTED_AUTH]"',
                description="Headers de autorização",
                lgpd_category="Dados de Autenticação"
            ),
            SensitivePattern(
                name="api_key",
                data_type=SensitiveDataType.API_KEY,
                regex=r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?key)["\']?\s*[:=]\s*["\']?([A-Za-z0-9]{8,})',
                replacement=r'\1: "[REDACTED_API_KEY]"',
                description="Chaves de API",
                lgpd_category="Dados de Autenticação"
            ),
            
            # === PII - DADOS PESSOAIS (LGPD) ===
            SensitivePattern(
                name="cpf",
                data_type=SensitiveDataType.CPF,
                regex=r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
                replacement=r'[REDACTED_CPF]',
                description="CPF (Cadastro de Pessoa Física)",
                lgpd_category="Dados Pessoais Sensíveis"
            ),
            SensitivePattern(
                name="cnpj",
                data_type=SensitiveDataType.CNPJ,
                regex=r'\b\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}\b',
                replacement=r'[REDACTED_CNPJ]',
                description="CNPJ (Cadastro Nacional da Pessoa Jurídica)",
                lgpd_category="Dados Pessoais Sensíveis"
            ),
            SensitivePattern(
                name="email",
                data_type=SensitiveDataType.EMAIL,
                regex=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                replacement=r'[REDACTED_EMAIL]',
                description="Endereços de email",
                lgpd_category="Dados Pessoais"
            ),
            SensitivePattern(
                name="phone_br",
                data_type=SensitiveDataType.PHONE,
                regex=r'(?:\+55\s?)?(?:\(?(?:1[1-9]|2[12478]|3[1234578]|4[1-9]|5[13-5]|6[1-9]|7[134579]|8[1-9]|9[1-9])\)?\s?)?9?\d{4}[-\s]?\d{4}',
                replacement=r'[REDACTED_PHONE]',
                description="Números de telefone brasileiros",
                lgpd_category="Dados Pessoais"
            ),
            SensitivePattern(
                name="wa_id_specific",
                data_type=SensitiveDataType.WA_ID,
                regex=r'(?i)("wa_id"|wa_id)["\']?\s*:\s*["\']?(\d{10,15})["\']?',
                replacement=r'\1: "[REDACTED_WA_ID]"',
                description="IDs do WhatsApp específicos",
                lgpd_category="Dados Pessoais"
            ),
            SensitivePattern(
                name="wa_id",
                data_type=SensitiveDataType.WA_ID,
                regex=r'(?i)(wa_id|whatsapp_id)["\']?\s*[:=]\s*["\']?(\d{10,15})',
                replacement=r'\1: "[REDACTED_WA_ID]"',
                description="IDs do WhatsApp",
                lgpd_category="Dados Pessoais"
            ),
            SensitivePattern(
                name="user_id_numeric",
                data_type=SensitiveDataType.USER_ID,
                regex=r'(?i)(user_id|usuario_id)["\']?\s*[:=]\s*["\']?(\d+)',
                replacement=r'\1: "[REDACTED_USER_ID]"',
                description="IDs numéricos de usuário",
                lgpd_category="Dados Pessoais"
            ),
            
            # === DADOS FINANCEIROS ===
            SensitivePattern(
                name="credit_card",
                data_type=SensitiveDataType.CREDIT_CARD,
                regex=r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                replacement=r'[REDACTED_CARD]',
                description="Números de cartão de crédito",
                lgpd_category="Dados Pessoais Sensíveis"
            ),
            SensitivePattern(
                name="pix_key",
                data_type=SensitiveDataType.PIX_KEY,
                regex=r'(?i)(pix[_-]?key|chave[_-]?pix)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)',
                replacement=r'\1: "[REDACTED_PIX]"',
                description="Chaves PIX",
                lgpd_category="Dados Pessoais Sensíveis"
            ),
            
            # === TOKENS E SECRETS ESPECÍFICOS ===
            SensitivePattern(
                name="whatsapp_token",
                data_type=SensitiveDataType.TOKEN,
                regex=r'(?i)(whatsapp[_-]?token|wa[_-]?token)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)',
                replacement=r'\1: "[REDACTED_WA_TOKEN]"',
                description="Tokens do WhatsApp",
                lgpd_category="Dados de Autenticação"
            ),
            SensitivePattern(
                name="session_token",
                data_type=SensitiveDataType.TOKEN,
                regex=r'(?i)(session[_-]?token|sessao[_-]?token)["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)',
                replacement=r'\1: "[REDACTED_SESSION]"',
                description="Tokens de sessão",
                lgpd_category="Dados de Autenticação"
            ),
            
            # === DADOS ADICIONAIS LGPD ===
            SensitivePattern(
                name="rg",
                data_type=SensitiveDataType.USER_ID,
                regex=r'\b\d{1,2}\.?\d{3}\.?\d{3}-?[\dX]\b',
                replacement=r'[REDACTED_RG]',
                description="RG (Registro Geral)",
                lgpd_category="Dados Pessoais Sensíveis"
            ),
            SensitivePattern(
                name="address",
                data_type=SensitiveDataType.ADDRESS,
                regex=r'(?i)(?:endereço|endereco):\s*[^,\n]{10,}',
                replacement=r'[REDACTED_ADDRESS]',
                description="Endereços residenciais",
                lgpd_category="Dados Pessoais"
            ),
            SensitivePattern(
                name="long_alphanumeric_token",
                data_type=SensitiveDataType.TOKEN,
                regex=r'\b[A-Za-z0-9]{15,}\b',
                replacement=r'[REDACTED_TOKEN]',
                description="Tokens alfanuméricos longos",
                lgpd_category="Dados de Autenticação"
            ),
            SensitivePattern(
                name="generic_token",
                data_type=SensitiveDataType.TOKEN,
                regex=r'(?i)(token|key)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]{8,})',
                replacement=r'\1: "[REDACTED_TOKEN]"',
                description="Tokens genéricos",
                lgpd_category="Dados de Autenticação"
            )
        ]
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitizar texto removendo dados sensíveis
        
        Args:
            text: Texto a ser sanitizado
            
        Returns:
            Texto sanitizado com dados sensíveis redatados
        """
        if not text:
            return text
            
        sanitized = text
        
        # Aplicar padrões em ordem de especificidade (mais específicos primeiro)
        pattern_order = [
            # 1. Credenciais específicas primeiro
            "bearer_token", "whatsapp_token", "session_token", "authorization_header",
            "password_field", "api_key",
            
            # 2. PII específicos
            "cpf", "cnpj", "email", "wa_id_specific", "wa_id", 
            "phone_br", "user_id_numeric", "rg",
            
            # 3. Tokens específicos
            "jwt_token_standalone",
            
            # 4. Dados financeiros
            "credit_card", "pix_key",
            
            # 5. Endereços (mais restritivo)
            "address",
            
            # 6. Tokens genéricos por último
            "generic_token"
        ]
        
        # Aplicar padrões na ordem especificada
        patterns_by_name = {p.name: p for p in self.patterns}
        
        for pattern_name in pattern_order:
            if pattern_name in patterns_by_name:
                pattern = patterns_by_name[pattern_name]
                try:
                    sanitized = re.sub(pattern.regex, pattern.replacement, sanitized)
                except Exception as e:
                    # Log interno (sem expor dados sensíveis)
                    logging.error(f"Erro na sanitização do padrão {pattern.name}: {e}")
        
        # Aplicar padrões restantes que não estão na ordem específica
        applied_patterns = set(pattern_order)
        for pattern in self.patterns:
            if pattern.name not in applied_patterns:
                try:
                    sanitized = re.sub(pattern.regex, pattern.replacement, sanitized)
                except Exception as e:
                    logging.error(f"Erro na sanitização do padrão {pattern.name}: {e}")
                
        return sanitized
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitizar dicionário recursivamente
        
        Args:
            data: Dicionário a ser sanitizado
            
        Returns:
            Dicionário sanitizado
        """
        if not isinstance(data, dict):
            return data
            
        sanitized = {}
        
        for key, value in data.items():
            # Sanitizar chave
            sanitized_key = self.sanitize_text(str(key))
            
            # Sanitizar valor baseado no tipo
            if isinstance(value, str):
                sanitized_value = self.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized_value = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized_value = [
                    self.sanitize_dict(item) if isinstance(item, dict)
                    else self.sanitize_text(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized_value = value
                
            sanitized[sanitized_key] = sanitized_value
            
        return sanitized
    
    def sanitize_json(self, json_str: str) -> str:
        """
        Sanitizar string JSON
        
        Args:
            json_str: String JSON a ser sanitizada
            
        Returns:
            String JSON sanitizada
        """
        try:
            data = json.loads(json_str)
            sanitized_data = self.sanitize_dict(data)
            return json.dumps(sanitized_data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            # Se não for JSON válido, sanitizar como texto
            return self.sanitize_text(json_str)
    
    def audit_log_entry(self, log_entry: str) -> Dict[str, Any]:
        """
        Auditar entrada de log para dados sensíveis
        
        Args:
            log_entry: Entrada de log para auditoria
            
        Returns:
            Relatório de auditoria com dados encontrados
        """
        found_patterns = []
        
        for pattern in self.patterns:
            matches = re.findall(pattern.regex, log_entry)
            if matches:
                found_patterns.append({
                    "pattern_name": pattern.name,
                    "data_type": pattern.data_type.value,
                    "lgpd_category": pattern.lgpd_category,
                    "matches_count": len(matches),
                    "description": pattern.description
                })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "original_length": len(log_entry),
            "sanitized_length": len(self.sanitize_text(log_entry)),
            "found_patterns": found_patterns,
            "compliance_status": "VIOLATION" if found_patterns else "COMPLIANT",
            "lgpd_risk_level": self._calculate_risk_level(found_patterns)
        }
    
    def _calculate_risk_level(self, found_patterns: List[Dict]) -> str:
        """Calcular nível de risco LGPD"""
        if not found_patterns:
            return "LOW"
            
        sensitive_categories = {
            "Dados Pessoais Sensíveis", 
            "Dados de Autenticação"
        }
        
        for pattern in found_patterns:
            if pattern["lgpd_category"] in sensitive_categories:
                return "HIGH"
        
        return "MEDIUM"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas do sanitizador"""
        return {
            "total_patterns": len(self.patterns),
            "patterns_by_type": {
                data_type.value: len([p for p in self.patterns if p.data_type == data_type])
                for data_type in SensitiveDataType
            },
            "lgpd_categories": list(set(p.lgpd_category for p in self.patterns)),
            "redaction_marker": self.redaction_marker,
            "compliance_enabled": self.lgpd_compliance
        }


# Instância global do sanitizador
log_sanitizer = LogSanitizer()


def sanitize_log_message(message: str) -> str:
    """
    Função helper para sanitizar mensagens de log
    
    Args:
        message: Mensagem a ser sanitizada
        
    Returns:
        Mensagem sanitizada
    """
    return log_sanitizer.sanitize_text(message)


def sanitize_log_data(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """
    Função helper para sanitizar dados de log
    
    Args:
        data: Dados a serem sanitizados
        
    Returns:
        Dados sanitizados
    """
    if isinstance(data, str):
        return log_sanitizer.sanitize_text(data)
    elif isinstance(data, dict):
        return log_sanitizer.sanitize_dict(data)
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    else:
        return data
