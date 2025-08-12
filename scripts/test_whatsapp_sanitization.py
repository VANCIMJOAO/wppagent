#!/usr/bin/env python3
"""
🧪 TESTES AVANÇADOS DE SANITIZAÇÃO WHATSAPP

Script para testar todas as funcionalidades do sistema de sanitização
de dados WhatsApp implementado.

Autor: WhatsApp Agent Security Team
Data: 08 de Agosto de 2025
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.whatsapp_sanitizer import (
    WhatsAppSanitizer, WhatsAppSecurityValidator,
    sanitize_whatsapp_data, sanitize_message, sanitize_phone, validate_security
)

class WhatsAppSanitizationTester:
    """Testador completo do sistema de sanitização WhatsApp"""
    
    def __init__(self):
        self.sanitizer = WhatsAppSanitizer()
        self.validator = WhatsAppSecurityValidator()
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Registra resultado de um teste"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASSOU"
        else:
            status = "❌ FALHOU"
        
        result = {
            'test': test_name,
            'status': status,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        print(f"{status} - {test_name}")
        if details:
            print(f"   📝 {details}")
    
    def test_phone_sanitization(self):
        """Testa sanitização de números de telefone"""
        print("\n📱 TESTANDO SANITIZAÇÃO DE NÚMEROS DE TELEFONE")
        
        # Casos válidos
        valid_cases = [
            ("5511999998888", "5511999998888"),
            ("11999998888", "5511999998888"),
            ("+55 (11) 99999-8888", "5511999998888"),
            ("55 11 9 9999-8888", "5511999998888"),
            ("(11) 99999-8888", "5511999998888")
        ]
        
        for input_phone, expected in valid_cases:
            try:
                result = sanitize_phone(input_phone)
                passed = result == expected
                self.log_test(
                    f"Número válido: {input_phone}",
                    passed,
                    f"Esperado: {expected}, Obtido: {result}"
                )
            except Exception as e:
                self.log_test(
                    f"Número válido: {input_phone}",
                    False,
                    f"Erro: {str(e)}"
                )
        
        # Casos inválidos
        invalid_cases = [
            "123456",
            "abc123def",
            "5511999@invalid",
            "55119999999999999",  # Muito longo
            "",
            None
        ]
        
        for invalid_phone in invalid_cases:
            try:
                result = sanitize_phone(invalid_phone)
                self.log_test(
                    f"Número inválido: {invalid_phone}",
                    False,
                    f"Deveria ter falhado, mas retornou: {result}"
                )
            except (ValueError, TypeError):
                self.log_test(
                    f"Número inválido: {invalid_phone}",
                    True,
                    "Rejeitado corretamente"
                )
            except Exception as e:
                self.log_test(
                    f"Número inválido: {invalid_phone}",
                    False,
                    f"Erro inesperado: {str(e)}"
                )
    
    def test_message_sanitization(self):
        """Testa sanitização de conteúdo de mensagens"""
        print("\n💬 TESTANDO SANITIZAÇÃO DE MENSAGENS")
        
        # Casos de SQL Injection
        sql_injection_cases = [
            ("Olá'; DROP TABLE users; --", "Olá"),
            ("SELECT * FROM users WHERE id=1", "SELECT  FROM users WHERE id=1"),
            ("/* Comentário */ Hello", " Hello"),
        ]
        
        for malicious, expected_clean in sql_injection_cases:
            result = sanitize_message(malicious, "text")
            # Verificar se caracteres perigosos foram removidos
            dangerous_removed = "';" not in result and "--" not in result and "/*" not in result
            self.log_test(
                f"SQL Injection: {malicious[:30]}...",
                dangerous_removed,
                f"Resultado: {result[:50]}..."
            )
        
        # Casos de XSS
        xss_cases = [
            "<script>alert('xss')</script>Olá",
            "Clique <a href='javascript:alert()'>aqui</a>",
            "<iframe src='malicious.com'></iframe>",
            "onload='malicious()' Hello"
        ]
        
        for xss_content in xss_cases:
            result = sanitize_message(xss_content, "text")
            # Verificar se tags perigosas foram removidas
            xss_removed = "<script" not in result.lower() and "javascript:" not in result.lower()
            self.log_test(
                f"XSS: {xss_content[:30]}...",
                xss_removed,
                f"Resultado: {result[:50]}..."
            )
        
        # Casos de tamanho
        oversized_message = "A" * 5000  # Maior que limite de 4096
        result = sanitize_message(oversized_message, "text")
        self.log_test(
            "Mensagem muito longa",
            len(result) <= 4096,
            f"Tamanho original: {len(oversized_message)}, Sanitizado: {len(result)}"
        )
    
    def test_payload_sanitization(self):
        """Testa sanitização de payload completo"""
        print("\n📦 TESTANDO SANITIZAÇÃO DE PAYLOAD")
        
        # Payload malicioso
        malicious_payload = {
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "id": "msg_123'; DROP TABLE messages; --",
                            "from": "5511999998888",
                            "type": "text",
                            "text": {
                                "body": "<script>alert('xss')</script>Olá mundo"
                            }
                        }],
                        "contacts": [{
                            "wa_id": "5511999998888",
                            "profile": {
                                "name": "João<script>alert()</script>Silva"
                            }
                        }]
                    }
                }]
            }]
        }
        
        try:
            sanitized = sanitize_whatsapp_data(malicious_payload)
            
            # Verificar se a estrutura foi mantida
            structure_ok = (
                "entry" in sanitized and
                len(sanitized["entry"]) > 0 and
                "changes" in sanitized["entry"][0]
            )
            
            self.log_test(
                "Estrutura do payload preservada",
                structure_ok,
                "Estrutura básica mantida após sanitização"
            )
            
            # Verificar se conteúdo malicioso foi removido
            payload_str = json.dumps(sanitized).lower()
            malicious_removed = (
                "drop table" not in payload_str and
                "<script>" not in payload_str and
                "alert(" not in payload_str
            )
            
            self.log_test(
                "Conteúdo malicioso removido",
                malicious_removed,
                "Scripts e SQL injection removidos"
            )
            
        except Exception as e:
            self.log_test(
                "Sanitização de payload",
                False,
                f"Erro: {str(e)}"
            )
    
    def test_security_validation(self):
        """Testa validações de segurança"""
        print("\n🛡️ TESTANDO VALIDAÇÕES DE SEGURANÇA")
        
        # Teste de detecção de spam
        spam_messages = [
            "CLIQUE AQUI AGORA!!! DINHEIRO GRÁTIS!!! 💰💰💰",
            "Você é o WINNER de um PRIZE incrível! Click here now!",
            "Free money! Limited time! Urgent action required!",
            "http://bit.ly/money-free telegram.me/spam"
        ]
        
        for spam_msg in spam_messages:
            is_spam = self.validator.is_potential_spam(spam_msg)
            self.log_test(
                f"Detecção de spam: {spam_msg[:30]}...",
                is_spam,
                "Spam detectado corretamente" if is_spam else "Spam NÃO detectado"
            )
        
        # Teste de detecção de phishing
        phishing_messages = [
            "Your account has been suspended. Click to verify account immediately.",
            "Bank verification required. Urgent security action needed.",
            "PayPal confirm your identity. Microsoft verify your account.",
            "Amazon security alert. Verify your account now."
        ]
        
        for phishing_msg in phishing_messages:
            is_phishing = self.validator.is_potential_phishing(phishing_msg)
            self.log_test(
                f"Detecção de phishing: {phishing_msg[:30]}...",
                is_phishing,
                "Phishing detectado" if is_phishing else "Phishing NÃO detectado"
            )
        
        # Teste de detecção de malware
        malware_files = [
            ("virus.exe", "application/x-executable"),
            ("malware.bat", "application/x-msdos-program"),
            ("trojan.scr", "application/x-executable"),
            ("safe_document.pdf", "application/pdf")  # Este deve ser seguro
        ]
        
        for filename, mime_type in malware_files:
            is_malware = self.validator.is_potential_malware(filename, mime_type)
            is_executable = filename.endswith(('.exe', '.bat', '.scr'))
            expected_result = is_executable
            
            self.log_test(
                f"Detecção de malware: {filename}",
                is_malware == expected_result,
                f"Resultado: {'Malware' if is_malware else 'Seguro'}"
            )
    
    def test_contact_sanitization(self):
        """Testa sanitização de informações de contato"""
        print("\n👤 TESTANDO SANITIZAÇÃO DE CONTATOS")
        
        # Contato com dados maliciosos
        malicious_contact = {
            "wa_id": "5511999998888",
            "profile": {
                "name": "João<script>alert('xss')</script>Silva'; DROP TABLE users; --"
            }
        }
        
        try:
            sanitized = self.sanitizer.sanitize_contact_info(malicious_contact)
            
            # Verificar se wa_id foi mantido
            wa_id_ok = sanitized.get("wa_id") == "5511999998888"
            
            # Verificar se nome foi sanitizado
            if "profile" in sanitized and "name" in sanitized["profile"]:
                name = sanitized["profile"]["name"]
                name_safe = "<script>" not in name and "DROP TABLE" not in name
            else:
                name_safe = True  # Nome removido completamente por ser muito inseguro
            
            self.log_test(
                "Sanitização de contato - wa_id",
                wa_id_ok,
                f"wa_id preservado: {sanitized.get('wa_id')}"
            )
            
            self.log_test(
                "Sanitização de contato - nome",
                name_safe,
                f"Nome sanitizado: {sanitized.get('profile', {}).get('name', 'REMOVIDO')}"
            )
            
        except Exception as e:
            self.log_test(
                "Sanitização de contato",
                False,
                f"Erro: {str(e)}"
            )
    
    def test_media_sanitization(self):
        """Testa sanitização de informações de mídia"""
        print("\n🎬 TESTANDO SANITIZAÇÃO DE MÍDIA")
        
        # Mídia com informações maliciosas
        malicious_media = {
            "id": "media_123'; DROP TABLE media; --",
            "mime_type": "image/jpeg",
            "filename": "../../../etc/passwd",
            "caption": "<script>alert('xss')</script>Foto da família",
            "filesize": "999999999999999999999"  # Tamanho inválido
        }
        
        try:
            sanitized = self.sanitizer.sanitize_media_info(malicious_media)
            
            # Verificar se ID foi sanitizado
            media_id = sanitized.get("id", "")
            id_safe = "DROP TABLE" not in media_id and ";" not in media_id
            
            # Verificar se filename foi sanitizado
            filename = sanitized.get("filename", "")
            filename_safe = "../" not in filename and "/" not in filename
            
            # Verificar se caption foi sanitizada
            caption = sanitized.get("caption", "")
            caption_safe = "<script>" not in caption
            
            # Verificar se mime_type foi preservado (é válido)
            mime_ok = sanitized.get("mime_type") == "image/jpeg"
            
            self.log_test(
                "Sanitização de mídia - ID",
                id_safe,
                f"ID sanitizado: {media_id}"
            )
            
            self.log_test(
                "Sanitização de mídia - filename",
                filename_safe,
                f"Filename: {filename if filename else 'REMOVIDO'}"
            )
            
            self.log_test(
                "Sanitização de mídia - caption",
                caption_safe,
                f"Caption: {caption}"
            )
            
            self.log_test(
                "Sanitização de mídia - mime_type",
                mime_ok,
                f"MIME type: {sanitized.get('mime_type', 'REMOVIDO')}"
            )
            
        except Exception as e:
            self.log_test(
                "Sanitização de mídia",
                False,
                f"Erro: {str(e)}"
            )
    
    def test_edge_cases(self):
        """Testa casos extremos e edge cases"""
        print("\n🔍 TESTANDO CASOS EXTREMOS")
        
        # Payload vazio
        try:
            empty_result = sanitize_whatsapp_data({})
            self.log_test(
                "Payload vazio",
                isinstance(empty_result, dict),
                "Payload vazio tratado corretamente"
            )
        except Exception as e:
            self.log_test(
                "Payload vazio",
                False,
                f"Erro: {str(e)}"
            )
        
        # Payload None
        try:
            none_result = sanitize_whatsapp_data(None)
            self.log_test(
                "Payload None",
                False,
                "None deveria ser rejeitado"
            )
        except (ValueError, TypeError):
            self.log_test(
                "Payload None",
                True,
                "None rejeitado corretamente"
            )
        
        # Mensagem vazia
        empty_message = sanitize_message("", "text")
        self.log_test(
            "Mensagem vazia",
            empty_message == "",
            f"Resultado: '{empty_message}'"
        )
        
        # Mensagem None
        try:
            none_message = sanitize_message(None, "text")
            self.log_test(
                "Mensagem None",
                none_message == "",
                f"Resultado: '{none_message}'"
            )
        except Exception as e:
            self.log_test(
                "Mensagem None",
                False,
                f"Erro: {str(e)}"
            )
        
        # String muito grande (ataque de DoS)
        huge_string = "A" * 100000  # 100KB
        try:
            result = sanitize_message(huge_string, "text")
            size_limited = len(result) <= 4096
            self.log_test(
                "String muito grande",
                size_limited,
                f"Tamanho limitado a {len(result)} caracteres"
            )
        except Exception as e:
            self.log_test(
                "String muito grande",
                False,
                f"Erro: {str(e)}"
            )
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🧪 INICIANDO TESTES AVANÇADOS DE SANITIZAÇÃO WHATSAPP")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Executar todos os testes
        self.test_phone_sanitization()
        self.test_message_sanitization()
        self.test_payload_sanitization()
        self.test_security_validation()
        self.test_contact_sanitization()
        self.test_media_sanitization()
        self.test_edge_cases()
        
        # Calcular resultados
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("=" * 60)
        print(f"⏱️  Duração: {duration:.2f} segundos")
        print(f"📈 Testes executados: {self.total_tests}")
        print(f"✅ Testes aprovados: {self.passed_tests}")
        print(f"❌ Testes falharam: {self.total_tests - self.passed_tests}")
        print(f"📊 Taxa de sucesso: {success_rate:.1f}%")
        
        if success_rate >= 95:
            print("\n🎉 EXCELENTE! Sistema de sanitização funcionando perfeitamente!")
        elif success_rate >= 80:
            print("\n✅ BOM! Sistema funcional com algumas melhorias necessárias.")
        else:
            print("\n⚠️ ATENÇÃO! Sistema precisa de correções importantes.")
        
        # Salvar relatório detalhado
        self.save_detailed_report()
        
        return success_rate >= 95
    
    def save_detailed_report(self):
        """Salva relatório detalhado em arquivo"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tests": self.total_tests,
                    "passed_tests": self.passed_tests,
                    "failed_tests": self.total_tests - self.passed_tests,
                    "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
                },
                "detailed_results": self.test_results
            }
            
            # Salvar em arquivo
            filename = f"sanitization_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(os.path.dirname(__file__), "..", "tests", "logs", filename)
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Relatório detalhado salvo em: {filepath}")
            
        except Exception as e:
            print(f"\n⚠️ Erro ao salvar relatório: {e}")


def main():
    """Função principal"""
    print("🧹 SISTEMA DE TESTES DE SANITIZAÇÃO WHATSAPP")
    print("Versão: 1.0.0")
    print("Data: 08 de Agosto de 2025")
    print()
    
    # Criar e executar tester
    tester = WhatsAppSanitizationTester()
    success = tester.run_all_tests()
    
    # Código de saída
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
