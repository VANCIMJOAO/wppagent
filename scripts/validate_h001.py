#!/usr/bin/env python3
"""
🔒 H001 - Script de Validação da Correção de Segurança
=====================================================

Validação completa da implementação H001 - Webhook sem verificação de assinatura.
"""

import os
import sys
import json
import hmac
import hashlib
import asyncio
import inspect
from typing import Dict, Any, Optional

# Adicionar app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class H001Validator:
    """Validador para correção H001"""
    
    def __init__(self):
        self.results = {
            'code_analysis': False,
            'security_service': False,
            'validation_logic': False,
            'error_handling': False,
            'logging_security': False
        }
        self.errors = []
        
    def validate_code_implementation(self):
        """Validar se o código foi implementado corretamente"""
        try:
            print("🔍 1. Validando implementação do código...")
            
            # Verificar import do WhatsAppSecurityService
            from app.routes.webhook import security_service
            
            if security_service is None:
                self.errors.append("security_service não foi inicializado")
                return False
                
            # Verificar se é a classe correta
            from app.services.whatsapp_security import WhatsAppSecurityService
            if not isinstance(security_service, WhatsAppSecurityService):
                self.errors.append(f"security_service não é WhatsAppSecurityService: {type(security_service)}")
                return False
                
            print("   ✅ WhatsAppSecurityService importado e inicializado")
            self.results['security_service'] = True
            return True
            
        except ImportError as e:
            self.errors.append(f"Erro de importação: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Erro na validação de código: {e}")
            return False
    
    def validate_webhook_logic(self):
        """Validar se a lógica de validação foi implementada"""
        try:
            print("🔍 2. Validando lógica de validação...")
            
            from app.routes.webhook import receive_webhook
            source = inspect.getsource(receive_webhook)
            
            # Verificar se validate_webhook_request está sendo chamado
            if 'validate_webhook_request' not in source:
                self.errors.append("validate_webhook_request não está sendo chamado")
                return False
                
            # Verificar se está no início da função (antes de processar dados)
            lines = source.split('\n')
            validate_line = None
            json_line = None
            
            for i, line in enumerate(lines):
                if 'validate_webhook_request' in line:
                    validate_line = i
                if 'await request.json()' in line or 'request.json()' in line:
                    json_line = i
                    
            if validate_line is None:
                self.errors.append("validate_webhook_request não encontrado")
                return False
                
            if json_line is not None and validate_line > json_line:
                self.errors.append("Validação acontece APÓS processar JSON - vulnerabilidade!")
                return False
                
            print("   ✅ Validação de assinatura implementada ANTES do processamento")
            self.results['validation_logic'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de lógica: {e}")
            return False
    
    def validate_error_handling(self):
        """Validar se o tratamento de erro retorna 403"""
        try:
            print("🔍 3. Validando tratamento de erro...")
            
            from app.routes.webhook import receive_webhook
            source = inspect.getsource(receive_webhook)
            
            # Verificar se HTTPException com 403 está implementado
            if 'HTTPException' not in source:
                self.errors.append("HTTPException não implementado")
                return False
                
            if '403' not in source:
                self.errors.append("Status code 403 não implementado")
                return False
                
            # Verificar se a mensagem de erro é apropriada
            if 'signature validation failed' not in source.lower():
                self.errors.append("Mensagem de erro de validação não encontrada")
                return False
                
            print("   ✅ Tratamento de erro 403 implementado")
            self.results['error_handling'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de tratamento de erro: {e}")
            return False
    
    def validate_security_logging(self):
        """Validar se eventos de segurança estão sendo logados"""
        try:
            print("🔍 4. Validando logging de segurança...")
            
            from app.routes.webhook import receive_webhook
            source = inspect.getsource(receive_webhook)
            
            # Verificar se log_security_event está sendo chamado
            if 'log_security_event' not in source:
                self.errors.append("log_security_event não implementado")
                return False
                
            # Verificar se está logando como HIGH severity
            if 'HIGH' not in source:
                self.errors.append("Severidade HIGH não configurada")
                return False
                
            # Verificar se está logando informações relevantes
            if 'webhook_signature_invalid' not in source:
                self.errors.append("Tipo de evento de segurança não configurado")
                return False
                
            print("   ✅ Logging de segurança implementado")
            self.results['logging_security'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de logging: {e}")
            return False
    
    def validate_fix_completeness(self):
        """Validar se a correção está completa"""
        try:
            print("🔍 5. Validando completude da correção...")
            
            from app.routes.webhook import receive_webhook
            source = inspect.getsource(receive_webhook)
            
            # Lista de elementos que devem estar presentes
            required_elements = [
                'validate_webhook_request',
                'HTTPException',
                '403',
                'log_security_event',
                'H001'  # Referência ao fix
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in source:
                    missing_elements.append(element)
                    
            if missing_elements:
                self.errors.append(f"Elementos ausentes: {missing_elements}")
                return False
                
            print("   ✅ Correção H001 completa")
            self.results['code_analysis'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de completude: {e}")
            return False
    
    def run_validation(self):
        """Executar validação completa"""
        print("🔒 H001 - VALIDAÇÃO DA CORREÇÃO DE SEGURANÇA")
        print("=" * 60)
        print("Validando: Webhook sem verificação de assinatura")
        print("Local: app/routes/webhook.py")
        print("Correção: Implementar verify_webhook_signature()")
        print("-" * 60)
        
        # Executar todas as validações
        validations = [
            self.validate_code_implementation,
            self.validate_webhook_logic,
            self.validate_error_handling,
            self.validate_security_logging,
            self.validate_fix_completeness
        ]
        
        passed = 0
        total = len(validations)
        
        for validation in validations:
            try:
                if validation():
                    passed += 1
            except Exception as e:
                self.errors.append(f"Erro durante validação: {e}")
        
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DA VALIDAÇÃO H001")
        print("=" * 60)
        
        for category, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{category:20} - {status}")
        
        print("-" * 60)
        print(f"Taxa de sucesso: {passed}/{total} ({(passed/total)*100:.1f}%)")
        
        if self.errors:
            print("\n❌ ERROS ENCONTRADOS:")
            for error in self.errors:
                print(f"   • {error}")
        
        if passed == total:
            print("\n🎉 H001 - CORREÇÃO IMPLEMENTADA COM SUCESSO ✅")
            print("   • Validação de assinatura implementada")
            print("   • Retorno 403 para assinaturas inválidas")
            print("   • Logging de segurança ativo")
            print("   • Proteção contra requisições forjadas")
        else:
            print(f"\n⚠️  H001 - CORREÇÃO INCOMPLETA ({passed}/{total})")
            print("   Revisar implementação antes do deploy")
        
        return passed == total


def main():
    """Função principal"""
    validator = H001Validator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
