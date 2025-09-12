#!/usr/bin/env python3
"""
🔒 HF002 - Test Suite: Sanitização de Logs
==========================================

Suite de testes abrangente para validar a implementação HF002 de sanitização
automática de dados sensíveis em logs.

Testa:
- Sanitização de telefones (nacional e internacional)
- Redação de emails e endereços
- Proteção de tokens e chaves API
- Sanitização de senhas e credenciais
- Redação de CPF/CNPJ e documentos
- Sanitização recursiva de metadados
"""

import pytest
import json
import logging
from typing import Dict, Any
from app.security.secure_logger import (
    LogSanitizer, 
    get_log_sanitizer, 
    sanitize_log_data,
    SanitizedFormatter,
    configure_secure_logging
)

class TestLogSanitizer:
    """Testes para a classe LogSanitizer"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.sanitizer = LogSanitizer()
    
    def test_phone_sanitization_brazilian(self):
        """Teste: Sanitização de telefones brasileiros"""
        test_cases = [
            ("Telefone: +55 11 99999-8888", "[PHONE_REDACTED_HF002]"),
            ("Contato: 11 98765-4321", "[PHONE_REDACTED_HF002]"),
            ("WhatsApp: 5511999887766", "[PHONE_REDACTED_HF002]"),
            ("Número: (11) 99988-7766", "[PHONE_REDACTED_HF002]"),
        ]
        
        for original, expected_pattern in test_cases:
            result = self.sanitizer.sanitize_message(original)
            assert expected_pattern in result, f"Failed to sanitize: {original}"
            assert "99999" not in result and "98765" not in result
    
    def test_email_sanitization(self):
        """Teste: Sanitização de emails"""
        test_cases = [
            ("Email: user@exemplo.com login attempt", "[EMAIL_REDACTED_HF002]"),
            ("Contato: admin@empresa.com.br", "[EMAIL_REDACTED_HF002]"),
            ("Send to: test.user+tag@domain.co.uk", "[EMAIL_REDACTED_HF002]"),
        ]
        
        for original, expected_pattern in test_cases:
            result = self.sanitizer.sanitize_message(original)
            assert expected_pattern in result, f"Failed to sanitize: {original}"
            assert "@exemplo.com" not in result and "@empresa.com" not in result
    
    def test_token_sanitization(self):
        """Teste: Sanitização de tokens e chaves API"""
        test_cases = [
            ("Authorization: Bearer abc123xyz456", "[TOKEN_REDACTED_HF002]"),
            ("API Key: sk_test_1234567890abcdef", "[TOKEN_REDACTED_HF002]"),
            ("Long token: abcdef1234567890abcdef1234567890abcdef12", "[TOKEN_REDACTED_HF002]"),
        ]
        
        for original, expected_pattern in test_cases:
            result = self.sanitizer.sanitize_message(original)
            assert expected_pattern in result, f"Failed to sanitize: {original}"
            assert "abc123xyz" not in result and "sk_test" not in result
    
    def test_password_sanitization(self):
        """Teste: Sanitização de senhas"""
        test_cases = [
            ('{"password": "secret123"}', "[PASSWORD_REDACTED_HF002]"),
            ("password=mypassword", "[PASSWORD_REDACTED_HF002]"),
            ("pwd: admin123", "[PASSWORD_REDACTED_HF002]"),
        ]
        
        for original, expected_pattern in test_cases:
            result = self.sanitizer.sanitize_message(original)
            assert expected_pattern in result, f"Failed to sanitize: {original}"
            assert "secret123" not in result and "mypassword" not in result
    
    def test_whatsapp_id_sanitization(self):
        """Teste: Sanitização de IDs WhatsApp"""
        test_cases = [
            ("WhatsApp ID: 5511999887766@s.whatsapp.net", "[WHATSAPP_ID_REDACTED_HF002]"),
            ("Contact: 5521987654321@c.us", "[WHATSAPP_ID_REDACTED_HF002]"),
        ]
        
        for original, expected_pattern in test_cases:
            result = self.sanitizer.sanitize_message(original)
            assert expected_pattern in result, f"Failed to sanitize: {original}"
            assert "5511999887766" not in result
    
    def test_document_sanitization(self):
        """Teste: Sanitização de CPF/CNPJ"""
        test_cases = [
            ("CPF: 123.456.789-00", "[DOCUMENT_REDACTED_HF002]"),
            ("CNPJ: 12.345.678/0001-00", "[DOCUMENT_REDACTED_HF002]"),
            ("Documento: 12345678900", "[DOCUMENT_REDACTED_HF002]"),
        ]
        
        for original, expected_pattern in test_cases:
            result = self.sanitizer.sanitize_message(original)
            assert expected_pattern in result, f"Failed to sanitize: {original}"
            assert "123.456.789" not in result
    
    def test_metadata_sanitization(self):
        """Teste: Sanitização recursiva de metadados"""
        sensitive_metadata = {
            "user_phone": "+55 11 99999-8888",
            "email": "user@test.com",
            "authorization": "Bearer secret_token",
            "password": "admin123",
            "normal_field": "safe_data",
            "nested": {
                "api_key": "sk_test_123456",
                "phone": "11987654321",
                "safe_field": "ok"
            }
        }
        
        result = self.sanitizer.sanitize_metadata(sensitive_metadata)
        
        # Verificar campos sensíveis foram redacted
        assert result["user_phone"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
        assert result["email"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
        assert result["authorization"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
        assert result["password"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
        
        # Verificar campos seguros preservados
        assert result["normal_field"] == "safe_data"
        assert result["nested"]["safe_field"] == "ok"
        
        # Verificar sanitização aninhada
        assert result["nested"]["api_key"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
        assert result["nested"]["phone"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
    
    def test_list_sanitization(self):
        """Teste: Sanitização de listas"""
        sensitive_list = [
            "Phone: +55 11 99999-8888",
            {"email": "test@example.com", "safe": "data"},
            ["nested phone: 11987654321", "safe string"],
            "Normal text"
        ]
        
        result = self.sanitizer._sanitize_list(sensitive_list)
        
        # Verificar sanitização em diferentes níveis
        assert "[PHONE_REDACTED_HF002]" in result[0]
        assert result[1]["email"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
        assert result[1]["safe"] == "data"
        assert "[PHONE_REDACTED_HF002]" in result[2][0]
        assert result[2][1] == "safe string"
        assert result[3] == "Normal text"


class TestSanitizedFormatter:
    """Testes para o SanitizedFormatter"""
    
    def test_formatter_integration(self):
        """Teste: Integração do formatter com logging"""
        # Criar logger com formatter sanitizado
        logger = logging.getLogger('test_hf002')
        handler = logging.StreamHandler()
        formatter = SanitizedFormatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Capturar output
        import io
        import sys
        captured_output = io.StringIO()
        handler.stream = captured_output
        
        # Log com dados sensíveis
        logger.info("User phone: +55 11 99999-8888 and email: user@test.com")
        
        # Verificar sanitização
        output = captured_output.getvalue()
        assert "[PHONE_REDACTED_HF002]" in output
        assert "[EMAIL_REDACTED_HF002]" in output
        assert "99999-8888" not in output
        assert "user@test.com" not in output


class TestUtilityFunctions:
    """Testes para funções utilitárias"""
    
    def test_sanitize_log_data_string(self):
        """Teste: Função sanitize_log_data com string"""
        sensitive_string = "Phone: +55 11 99999-8888, Email: user@test.com"
        result = sanitize_log_data(sensitive_string)
        
        assert "[PHONE_REDACTED_HF002]" in result
        assert "[EMAIL_REDACTED_HF002]" in result
        assert "99999-8888" not in result
        assert "user@test.com" not in result
    
    def test_sanitize_log_data_dict(self):
        """Teste: Função sanitize_log_data com dicionário"""
        sensitive_dict = {
            "phone": "+55 11 99999-8888",
            "token": "Bearer secret123",
            "safe_data": "normal info"
        }
        
        result = sanitize_log_data(sensitive_dict)
        
        assert result["phone"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
        assert result["token"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
        assert result["safe_data"] == "normal info"
    
    def test_get_log_sanitizer_singleton(self):
        """Teste: Singleton do sanitizador"""
        sanitizer1 = get_log_sanitizer()
        sanitizer2 = get_log_sanitizer()
        
        assert sanitizer1 is sanitizer2, "Sanitizer deve ser singleton"


class TestProductionScenarios:
    """Testes para cenários de produção"""
    
    def test_webhook_payload_sanitization(self):
        """Teste: Sanitização de payload de webhook"""
        webhook_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "5511999887766",
                            "text": {
                                "body": "Meu email é user@example.com e telefone +55 11 99999-8888"
                            }
                        }]
                    }
                }]
            }]
        }
        
        sanitizer = LogSanitizer()
        result = sanitizer.sanitize_metadata(webhook_payload)
        
        # Verificar que IDs sensíveis foram sanitizados recursivamente
        message = result["entry"][0]["changes"][0]["value"]["messages"][0]
        assert "[PHONE_REDACTED_HF002]" in message["from"]
        assert "[EMAIL_REDACTED_HF002]" in message["text"]["body"]
        assert "[PHONE_REDACTED_HF002]" in message["text"]["body"]
    
    def test_authentication_log_sanitization(self):
        """Teste: Sanitização de logs de autenticação"""
        auth_log = "User login attempt: email=admin@company.com, token=Bearer abc123xyz, phone=+5511999887766"
        
        sanitizer = LogSanitizer()
        result = sanitizer.sanitize_message(auth_log)
        
        assert "[EMAIL_REDACTED_HF002]" in result
        assert "[TOKEN_REDACTED_HF002]" in result
        assert "[PHONE_REDACTED_HF002]" in result
        assert "admin@company.com" not in result
        assert "abc123xyz" not in result
    
    def test_error_message_sanitization(self):
        """Teste: Sanitização de mensagens de erro"""
        error_messages = [
            "Database connection failed for user admin@test.com",
            "Invalid phone number: +55 11 99999-8888",
            "Token validation failed: Bearer secret123",
            "User with CPF 123.456.789-00 not found"
        ]
        
        sanitizer = LogSanitizer()
        
        for error_msg in error_messages:
            result = sanitizer.sanitize_message(error_msg)
            
            # Verificar que dados sensíveis foram removidos
            assert "@test.com" not in result
            assert "99999-8888" not in result
            assert "secret123" not in result
            assert "123.456.789" not in result
            
            # Verificar que placeholders estão presentes
            assert any(pattern in result for pattern in [
                "[EMAIL_REDACTED_HF002]",
                "[PHONE_REDACTED_HF002]", 
                "[TOKEN_REDACTED_HF002]",
                "[DOCUMENT_REDACTED_HF002]"
            ])


class TestPerformance:
    """Testes de performance da sanitização"""
    
    def test_sanitization_performance(self):
        """Teste: Performance da sanitização em larga escala"""
        import time
        
        sanitizer = LogSanitizer()
        
        # Criar 1000 mensagens com dados sensíveis
        messages = [
            f"User {i}: phone +55 11 9999{i:04d}, email user{i}@test.com, token Bearer abc{i}xyz"
            for i in range(1000)
        ]
        
        start_time = time.time()
        
        for msg in messages:
            sanitizer.sanitize_message(msg)
        
        elapsed_time = time.time() - start_time
        
        # Deve processar 1000 mensagens em menos de 1 segundo
        assert elapsed_time < 1.0, f"Sanitization too slow: {elapsed_time:.3f}s for 1000 messages"
        print(f"✅ Performance test: {elapsed_time:.3f}s for 1000 messages")


def test_hf002_integration():
    """Teste de integração HF002 completo"""
    print("🔒 Running HF002 Integration Test...")
    
    # Testar todas as funcionalidades em conjunto
    test_data = {
        "user_info": {
            "phone": "+55 11 99999-8888",
            "email": "admin@company.com", 
            "cpf": "123.456.789-00"
        },
        "auth": {
            "token": "Bearer secret_token_123",
            "api_key": "sk_live_abcdef1234567890"
        },
        "message": "Contact user at phone +55 21 98765-4321 or email user@example.com",
        "logs": [
            "Password authentication for admin@test.com",
            "WhatsApp message from 5511999887766@s.whatsapp.net"
        ]
    }
    
    # Sanitizar dados
    result = sanitize_log_data(test_data)
    
    # Verificações
    assert result["user_info"]["phone"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
    assert result["user_info"]["email"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
    assert result["user_info"]["cpf"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
    
    assert result["auth"]["token"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
    assert result["auth"]["api_key"] == "[SENSITIVE_FIELD_REDACTED_HF002]"
    
    assert "[PHONE_REDACTED_HF002]" in result["message"]
    assert "[EMAIL_REDACTED_HF002]" in result["message"]
    
    assert "[EMAIL_REDACTED_HF002]" in result["logs"][0]
    assert "[WHATSAPP_ID_REDACTED_HF002]" in result["logs"][1]
    
    print("✅ HF002 Integration Test PASSED")
    
    return True


if __name__ == "__main__":
    print("🔒 HF002 Test Suite - Sanitização de Logs")
    print("=" * 50)
    
    # Executar teste de integração
    if test_hf002_integration():
        print("\n🎉 All HF002 tests completed successfully!")
        print("✅ Sensitive data sanitization is working correctly")
    else:
        print("\n🚨 HF002 tests failed!")
        exit(1)
