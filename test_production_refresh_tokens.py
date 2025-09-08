#!/usr/bin/env python3
"""
🧪 Teste End-to-End Completo - Sistema de Refresh Tokens
=======================================================

Testa todos os cenários do sistema de refresh tokens em produção:
1. Login com credenciais válidas -> recebe access_token + refresh_token
2. Uso do access_token para acessar endpoint protegido
3. Renovação usando refresh_token
4. Revogação de tokens (logout)
5. Tentativa de uso de token revogado (deve falhar)
"""

import requests
import time
import json
from datetime import datetime

# Configurações
BASE_URL = "https://wppagent-production.up.railway.app"
ADMIN_CREDENTIALS = {
    "username": "admin", 
    "password": "admin123"  # Credential padrão ou testar com existente
}

class RefreshTokenTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.access_token = None
        self.refresh_token = None
        self.session = requests.Session()
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TEST": "🧪"
        }
        icon = status_icons.get(status, "📝")
        print(f"{timestamp} {icon} {message}")
    
    def test_health_check(self):
        """Teste 0: Verificar se servidor está rodando"""
        self.log("=== TESTE 0: Health Check ===", "TEST")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log("Servidor está online e respondendo", "SUCCESS")
                return True
            else:
                self.log(f"Servidor respondeu com status {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Falha na conexão com servidor: {e}", "ERROR")
            return False
    
    def test_login_with_token_pair(self):
        """Teste 1: Login retorna access_token + refresh_token"""
        self.log("=== TESTE 1: Login com Token Pair ===", "TEST")
        
        try:
            response = self.session.post(
                f"{self.base_url}/admin/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )
            
            self.log(f"Status Code: {response.status_code}")
            self.log(f"Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar se retorna refresh_token (novo sistema)
                if "refresh_token" in data and "access_token" in data:
                    self.access_token = data["access_token"]
                    self.refresh_token = data["refresh_token"]
                    self.log("✅ Login com REFRESH TOKEN implementado!", "SUCCESS")
                    self.log(f"Access Token: {self.access_token[:50]}...")
                    self.log(f"Refresh Token: {self.refresh_token[:50]}...")
                    self.log(f"Expires in: {data.get('expires_in', 'N/A')} segundos")
                    return True
                
                # Sistema antigo (só access_token)
                elif "access_token" in data:
                    self.access_token = data["access_token"]
                    self.log("⚠️ Sistema ANTIGO - só access_token", "WARNING")
                    self.log("Refresh tokens ainda não deployados em produção", "WARNING")
                    return "OLD_SYSTEM"
                
                else:
                    self.log("Resposta não contém tokens esperados", "ERROR")
                    return False
                    
            elif response.status_code == 401:
                self.log("Credenciais inválidas - tentando criar admin", "WARNING")
                return self.try_create_admin()
                
            else:
                self.log(f"Login falhou: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Erro no login: {e}", "ERROR")
            return False
    
    def try_create_admin(self):
        """Tenta criar admin inicial se não existe"""
        self.log("Tentando criar admin inicial...", "INFO")
        
        try:
            response = self.session.post(
                f"{self.base_url}/admin/create-initial-admin",
                json={
                    "username": "admin",
                    "password": "admin123",
                    "email": "admin@test.com",
                    "full_name": "Admin Test"
                }
            )
            
            if response.status_code in [200, 201]:
                self.log("Admin inicial criado, tentando login novamente", "SUCCESS")
                return self.test_login_with_token_pair()
            else:
                self.log(f"Falha ao criar admin: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Erro ao criar admin: {e}", "ERROR")
            return False
    
    def test_protected_endpoint(self):
        """Teste 2: Usar access_token em endpoint protegido"""
        self.log("=== TESTE 2: Endpoint Protegido ===", "TEST")
        
        if not self.access_token:
            self.log("Sem access_token para testar", "ERROR")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(f"{self.base_url}/admin/me", headers=headers)
            
            self.log(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Acesso autorizado para usuário: {data.get('username', 'N/A')}", "SUCCESS")
                return True
            else:
                self.log(f"Acesso negado: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Erro no teste de endpoint protegido: {e}", "ERROR")
            return False
    
    def test_refresh_token_endpoint(self):
        """Teste 3: Renovar access_token usando refresh_token"""
        self.log("=== TESTE 3: Refresh Token ===", "TEST")
        
        if not self.refresh_token:
            self.log("Sem refresh_token para testar (sistema antigo?)", "WARNING")
            return "SKIP"
        
        try:
            response = self.session.post(
                f"{self.base_url}/admin/refresh",
                json={"refresh_token": self.refresh_token}
            )
            
            self.log(f"Status Code: {response.status_code}")
            self.log(f"Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    old_token = self.access_token[:30] + "..."
                    self.access_token = data["access_token"]  # Atualizar token
                    new_token = self.access_token[:30] + "..."
                    
                    self.log("✅ Refresh token funcionando!", "SUCCESS")
                    self.log(f"Token antigo: {old_token}")
                    self.log(f"Token novo: {new_token}")
                    return True
                else:
                    self.log("Resposta não contém access_token", "ERROR")
                    return False
            else:
                self.log(f"Falha no refresh: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Erro no teste de refresh token: {e}", "ERROR")
            return False
    
    def test_revoke_tokens(self):
        """Teste 4: Revogar todos os tokens (logout)"""
        self.log("=== TESTE 4: Logout/Revoke Tokens ===", "TEST")
        
        if not self.access_token:
            self.log("Sem access_token para testar logout", "ERROR")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Testar endpoint de revoke primeiro (se existir)
            response = self.session.post(f"{self.base_url}/admin/revoke", headers=headers)
            
            if response.status_code == 200:
                self.log("✅ Tokens revogados via /admin/revoke", "SUCCESS")
                return True
            
            # Fallback para logout tradicional
            response = self.session.post(f"{self.base_url}/admin/logout", headers=headers)
            
            self.log(f"Logout Status Code: {response.status_code}")
            
            if response.status_code == 200:
                self.log("✅ Logout realizado com sucesso", "SUCCESS") 
                return True
            else:
                self.log(f"Falha no logout: {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Erro no teste de logout: {e}", "ERROR")
            return False
    
    def test_revoked_token_access(self):
        """Teste 5: Tentar usar token revogado (deve falhar)"""
        self.log("=== TESTE 5: Token Revogado ===", "TEST")
        
        if not self.access_token:
            self.log("Sem token para testar", "ERROR")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(f"{self.base_url}/admin/me", headers=headers)
            
            self.log(f"Status Code: {response.status_code}")
            
            if response.status_code == 401:
                self.log("✅ Token revogado corretamente (401 Unauthorized)", "SUCCESS")
                return True
            elif response.status_code == 200:
                self.log("⚠️ Token ainda funciona (logout pode não ter revogado)", "WARNING")
                return "PARTIAL"
            else:
                self.log(f"Resposta inesperada: {response.text}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Erro no teste de token revogado: {e}", "ERROR")
            return False
    
    def run_complete_test(self):
        """Executa bateria completa de testes"""
        self.log("🚀 INICIANDO TESTE END-TO-END SISTEMA REFRESH TOKENS", "INFO")
        self.log(f"Target: {self.base_url}", "INFO")
        self.log("=" * 60, "INFO")
        
        results = {}
        
        # Teste 0: Health Check
        results["health"] = self.test_health_check()
        if not results["health"]:
            self.log("❌ FALHA CRÍTICA: Servidor não responde", "ERROR")
            return results
        
        # Teste 1: Login
        results["login"] = self.test_login_with_token_pair()
        if not results["login"]:
            self.log("❌ FALHA CRÍTICA: Login não funcionou", "ERROR")
            return results
        
        # Sistema antigo vs novo
        if results["login"] == "OLD_SYSTEM":
            self.log("⚠️ DETECTADO SISTEMA ANTIGO - Pulando testes de refresh", "WARNING")
            results["protected"] = self.test_protected_endpoint()
            results["logout"] = self.test_revoke_tokens()
            results["revoked"] = self.test_revoked_token_access()
            return results
        
        # Testes completos do novo sistema
        results["protected"] = self.test_protected_endpoint()
        results["refresh"] = self.test_refresh_token_endpoint()
        results["logout"] = self.test_revoke_tokens()
        results["revoked"] = self.test_revoked_token_access()
        
        return results
    
    def print_summary(self, results):
        """Imprime resumo dos testes"""
        self.log("=" * 60, "INFO")
        self.log("📊 RESUMO DOS TESTES", "INFO")
        self.log("=" * 60, "INFO")
        
        test_names = {
            "health": "🏥 Health Check",
            "login": "🔐 Login",
            "protected": "🛡️ Endpoint Protegido", 
            "refresh": "🔄 Refresh Token",
            "logout": "🚪 Logout",
            "revoked": "🚫 Token Revogado"
        }
        
        passed = 0
        total = 0
        
        for test_key, test_name in test_names.items():
            if test_key in results:
                result = results[test_key]
                total += 1
                
                if result is True:
                    self.log(f"{test_name}: ✅ PASSOU", "SUCCESS")
                    passed += 1
                elif result == "SKIP":
                    self.log(f"{test_name}: ⏭️ PULADO", "WARNING")
                elif result == "OLD_SYSTEM":
                    self.log(f"{test_name}: ⚠️ SISTEMA ANTIGO", "WARNING") 
                elif result == "PARTIAL":
                    self.log(f"{test_name}: ⚠️ PARCIAL", "WARNING")
                else:
                    self.log(f"{test_name}: ❌ FALHOU", "ERROR")
        
        self.log("=" * 60, "INFO")
        self.log(f"📈 RESULTADO: {passed}/{total} testes passaram", "INFO")
        
        if passed == total:
            self.log("🎉 SISTEMA DE REFRESH TOKENS FUNCIONANDO PERFEITAMENTE!", "SUCCESS")
        elif passed >= total * 0.7:
            self.log("⚠️ SISTEMA PARCIALMENTE FUNCIONAL - Revisar falhas", "WARNING")
        else:
            self.log("❌ SISTEMA COM PROBLEMAS CRÍTICOS", "ERROR")


if __name__ == "__main__":
    tester = RefreshTokenTester()
    results = tester.run_complete_test()
    tester.print_summary(results)
    
    # Status de saída
    if results.get("login") and results.get("protected"):
        exit(0)  # Sucesso básico
    else:
        exit(1)  # Falha crítica
