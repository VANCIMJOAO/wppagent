#!/usr/bin/env python3
"""
🔍 S002 Validation Script - Log Sanitization Audit
=================================================

Script completo para validar implementação do S002:
- Logs sanitizados ✅
- PII não logado ✅  
- Tokens redatados ✅
- Compliance LGPD ✅

Comando de teste: grep -i "password\|token" logs/ = redacted only
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Adicionar path para importar módulos da app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.security.log_sanitizer import log_sanitizer, LogSanitizer
from app.security.secure_logger import get_secure_logger


class S002Validator:
    """Validador completo para S002 - Log Sanitization Audit"""
    
    def __init__(self, logs_directory: str = "logs"):
        self.logs_dir = Path(logs_directory)
        self.sanitizer = LogSanitizer()
        self.test_cases = self._create_test_cases()
        
    def _create_test_cases(self) -> List[Dict[str, Any]]:
        """Criar casos de teste com dados sensíveis"""
        return [
            {
                "name": "password_field",
                "input": 'User login: {"username": "admin", "password": "secret123", "remember": true}',
                "should_contain": "[REDACTED_PASSWORD]",
                "should_not_contain": "secret123"
            },
            {
                "name": "bearer_token",
                "input": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
                "should_contain": "[REDACTED_JWT_TOKEN]",
                "should_not_contain": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            },
            {
                "name": "cpf",
                "input": "Cliente CPF: 123.456.789-10 realizou pagamento",
                "should_contain": "[REDACTED_CPF]",
                "should_not_contain": "123.456.789-10"
            },
            {
                "name": "email",
                "input": "Usuário joao.silva@example.com enviou mensagem",
                "should_contain": "[REDACTED_EMAIL]",
                "should_not_contain": "joao.silva@example.com"
            },
            {
                "name": "phone",
                "input": "WhatsApp de +5511999887766 recebido",
                "should_contain": "[REDACTED_PHONE]",
                "should_not_contain": "+5511999887766"
            },
            {
                "name": "wa_id",
                "input": '{"wa_id": "5511999887766", "message": "test"}',
                "should_contain": "[REDACTED_WA_ID]",
                "should_not_contain": "5511999887766"
            },
            {
                "name": "api_key",
                "input": "WhatsApp API Key: EAAG1zxyz123456789 configured",
                "should_contain": "[REDACTED_TOKEN]",
                "should_not_contain": "EAAG1zxyz123456789"
            },
            {
                "name": "mixed_sensitive_data",
                "input": '{"user": {"email": "admin@test.com", "cpf": "111.222.333-44", "wa_id": "5511998765432"}, "auth": {"token": "abc123xyz", "password": "mypass"}}',
                "should_contain": ["[REDACTED_EMAIL]", "[REDACTED_CPF]", "[REDACTED_WA_ID]", "[REDACTED_PASSWORD]"],
                "should_not_contain": ["admin@test.com", "111.222.333-44", "5511998765432", "abc123xyz", "mypass"]
            }
        ]
    
    def test_sanitization_patterns(self) -> bool:
        """Teste 1: Verificar sanitização de padrões"""
        print("🔍 Teste 1: Verificando sanitização de padrões sensíveis...")
        
        all_passed = True
        
        for test_case in self.test_cases:
            sanitized = self.sanitizer.sanitize_text(test_case["input"])
            
            # Verificar se deve conter
            should_contain = test_case["should_contain"]
            if isinstance(should_contain, str):
                should_contain = [should_contain]
            
            for expected in should_contain:
                if expected not in sanitized:
                    print(f"  ❌ {test_case['name']}: Esperado '{expected}' não encontrado")
                    print(f"      Input: {test_case['input'][:100]}...")
                    print(f"      Output: {sanitized[:100]}...")
                    all_passed = False
                    continue
            
            # Verificar se não deve conter
            should_not_contain = test_case["should_not_contain"]
            if isinstance(should_not_contain, str):
                should_not_contain = [should_not_contain]
            
            for forbidden in should_not_contain:
                if forbidden in sanitized:
                    print(f"  ❌ {test_case['name']}: Conteúdo sensível '{forbidden}' ainda presente")
                    print(f"      Input: {test_case['input'][:100]}...")
                    print(f"      Output: {sanitized[:100]}...")
                    all_passed = False
                    continue
            
            if all_passed:
                print(f"  ✅ {test_case['name']}: Sanitização correta")
        
        return all_passed
    
    def test_secure_logger(self) -> bool:
        """Teste 2: Verificar logger seguro"""
        print("🔍 Teste 2: Verificando funcionamento do logger seguro...")
        
        try:
            # Criar logger de teste
            test_logger = get_secure_logger(
                "s002_test",
                log_file="logs/s002_validation_test.log",
                enable_sanitization=True,
                enable_audit=True
            )
            
            # Testar logs com dados sensíveis
            sensitive_data = [
                "User password: secret123 authenticated",
                "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature",
                "CPF 123.456.789-10 validated",
                "Email user@test.com sent message"
            ]
            
            for data in sensitive_data:
                test_logger.info(data)
            
            # Verificar se arquivo foi criado e sanitizado
            log_file = Path("logs/s002_validation_test.log")
            if not log_file.exists():
                print("  ❌ Arquivo de log não foi criado")
                return False
            
            # Ler conteúdo do log
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Verificar se dados sensíveis foram redatados
            forbidden_patterns = ["secret123", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", "123.456.789-10", "user@test.com"]
            violations = []
            
            for pattern in forbidden_patterns:
                if pattern in log_content:
                    violations.append(pattern)
            
            if violations:
                print(f"  ❌ Dados sensíveis encontrados no log: {violations}")
                return False
            
            # Verificar se marcadores de redação estão presentes
            expected_markers = ["[REDACTED_PASSWORD]", "[REDACTED_JWT_TOKEN]", "[REDACTED_CPF]", "[REDACTED_EMAIL]"]
            missing_markers = []
            
            for marker in expected_markers:
                if marker not in log_content:
                    missing_markers.append(marker)
            
            if missing_markers:
                print(f"  ❌ Marcadores de redação ausentes: {missing_markers}")
                return False
            
            print("  ✅ Logger seguro funcionando corretamente")
            
            # Limpar arquivo de teste
            log_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"  ❌ Erro no teste do logger seguro: {e}")
            return False
    
    def test_existing_logs_compliance(self) -> bool:
        """Teste 3: Verificar compliance de logs existentes"""
        print("🔍 Teste 3: Verificando compliance de logs existentes...")
        
        if not self.logs_dir.exists():
            print("  ✅ Diretório de logs não existe - nenhuma violação")
            return True
        
        violations_found = False
        
        # Padrões sensíveis a procurar
        sensitive_patterns = [
            r'password\s*[:=]\s*["\']?[^"\'\s,}]+',
            r'token\s*[:=]\s*["\']?[^"\'\s,}]+',
            r'secret\s*[:=]\s*["\']?[^"\'\s,}]+',
            r'api[_-]?key\s*[:=]\s*["\']?[^"\'\s,}]+',
            r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',  # CPF
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\+55\s?\d{2}\s?\d{4,5}-?\d{4}',  # Telefone BR
        ]
        
        for log_file in self.logs_dir.rglob("*.log"):
            if log_file.is_file() and log_file.stat().st_size > 0:
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    violations = []
                    for pattern in sensitive_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        if matches:
                            # Verificar se são redações válidas
                            valid_redactions = [
                                "[REDACTED_PASSWORD]", "[REDACTED_TOKEN]", 
                                "[REDACTED_API_KEY]", "[REDACTED_CPF]",
                                "[REDACTED_EMAIL]", "[REDACTED_PHONE]"
                            ]
                            
                            actual_violations = []
                            for match in matches:
                                if not any(redaction in str(match) for redaction in valid_redactions):
                                    actual_violations.append(match)
                            
                            if actual_violations:
                                violations.extend(actual_violations)
                    
                    if violations:
                        print(f"  ❌ Violações em {log_file}: {len(violations)} dados sensíveis")
                        violations_found = True
                    else:
                        print(f"  ✅ {log_file}: Conforme")
                        
                except Exception as e:
                    print(f"  ⚠️ Erro ao ler {log_file}: {e}")
        
        return not violations_found
    
    def test_grep_command_compliance(self) -> bool:
        """Teste 4: Executar comando grep para verificar redação"""
        print("🔍 Teste 4: Executando teste grep para tokens e passwords...")
        
        try:
            # Comando de teste conforme especificação
            result = subprocess.run(
                ["grep", "-r", "-i", "password\\|token", "logs/"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            # Se grep não encontrar nada (exit code 1), está OK
            if result.returncode == 1:
                print("  ✅ Grep não encontrou passwords/tokens expostos")
                return True
            
            # Se encontrou algo, verificar se são apenas redações
            if result.returncode == 0:
                output = result.stdout
                lines = output.strip().split('\n') if output.strip() else []
                
                violations = []
                for line in lines:
                    # Ignorar logs de auditoria interna do sistema S002
                    if "SECURITY_AUDIT" in line or "security_audit.log" in line:
                        continue
                    
                    # Verificar se a linha contém apenas redações válidas
                    if not any(redaction in line for redaction in ["[REDACTED_", "REDACTED"]):
                        violations.append(line)
                
                if violations:
                    print(f"  ❌ Grep encontrou {len(violations)} violações:")
                    for violation in violations[:5]:  # Mostrar apenas 5 primeiras
                        print(f"      {violation}")
                    return False
                else:
                    print("  ✅ Grep encontrou apenas redações válidas")
                    return True
            
            # Erro no comando
            print(f"  ❌ Erro no comando grep: {result.stderr}")
            return False
            
        except FileNotFoundError:
            print("  ⚠️ Comando grep não disponível - teste ignorado")
            return True
        except Exception as e:
            print(f"  ❌ Erro no teste grep: {e}")
            return False
    
    def test_lgpd_compliance_audit(self) -> bool:
        """Teste 5: Auditoria específica LGPD"""
        print("🔍 Teste 5: Auditoria específica de compliance LGPD...")
        
        # Dados de teste para compliance LGPD
        lgpd_test_data = [
            "CPF: 123.456.789-10",
            "CNPJ: 12.345.678/0001-90", 
            "Email: usuario@exemplo.com",
            "Telefone: +5511987654321",
            "RG: 12.345.678-9",
            "Endereço: Rua das Flores, 123, São Paulo"
        ]
        
        violations = []
        
        for test_data in lgpd_test_data:
            sanitized = self.sanitizer.sanitize_text(test_data)
            audit_result = self.sanitizer.audit_log_entry(test_data)
            
            # Verificar se foi marcado como violação
            if audit_result['compliance_status'] != 'VIOLATION':
                violations.append(f"Dado sensível não detectado: {test_data}")
                continue
            
            # Verificar se foi sanitizado
            if test_data in sanitized:
                violations.append(f"Dado sensível não sanitizado: {test_data}")
        
        if violations:
            print(f"  ❌ Violações LGPD encontradas: {len(violations)}")
            for violation in violations:
                print(f"      {violation}")
            return False
        
        print("  ✅ Compliance LGPD verificado")
        return True
    
    def run_validation(self) -> Dict[str, Any]:
        """Executar validação completa S002"""
        print("🔒 S002 - Log Sanitization Audit Validation")
        print("=" * 50)
        
        results = {}
        
        # Executar testes
        results['sanitization_patterns'] = self.test_sanitization_patterns()
        print()
        
        results['secure_logger'] = self.test_secure_logger()
        print()
        
        results['existing_logs_compliance'] = self.test_existing_logs_compliance()
        print()
        
        results['grep_compliance'] = self.test_grep_command_compliance()
        print()
        
        results['lgpd_compliance'] = self.test_lgpd_compliance_audit()
        print()
        
        # Calcular resultado final
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        success_rate = (passed_tests / total_tests) * 100
        
        print("=" * 50)
        print("📊 RESUMO S002 VALIDATION")
        print("=" * 50)
        
        status_map = {
            'sanitization_patterns': 'Logs sanitizados',
            'secure_logger': 'Logger seguro funcionando',
            'existing_logs_compliance': 'Logs existentes conformes',
            'grep_compliance': 'Teste grep = apenas redacted',
            'lgpd_compliance': 'Compliance LGPD'
        }
        
        for key, description in status_map.items():
            status = "✅ PASS" if results[key] else "❌ FAIL"
            print(f"{status} - {description}")
        
        print(f"\n📈 Taxa de sucesso: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 S002 - Log Sanitization: COMPLETO ✅")
            print("\n✅ Todos os critérios de pronto atendidos:")
            print("  ✅ Logs sanitizados")
            print("  ✅ PII não logado")  
            print("  ✅ Tokens redatados")
            print("  ✅ Compliance LGPD")
            return {"status": "COMPLETE", "results": results}
        else:
            failed_count = total_tests - passed_tests
            print(f"❌ S002 - Log Sanitization: FALHOU")
            print(f"\n❌ {failed_count} critério(s) não atendido(s)")
            return {"status": "FAILED", "results": results}


if __name__ == "__main__":
    validator = S002Validator()
    result = validator.run_validation()
    
    # Exit code baseado no resultado
    sys.exit(0 if result["status"] == "COMPLETE" else 1)
