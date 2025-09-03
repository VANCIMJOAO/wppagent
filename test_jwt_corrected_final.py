#!/usr/bin/env python3
"""
🧪 TESTE JWT PÓS-CORREÇÃO - VERSÃO FINAL
========================================

Testa o sistema após todas as correções de campo do banco de dados:
- User.name → User.nome
- User.phone → User.telefone  
- Remoção de campos phone_number inexistentes
- Atualização de schemas
"""

import requests
import json
import jwt
from datetime import datetime
from urllib.parse import urljoin

# 🌐 Configuração
BASE_URL = "https://wppagent-production.up.railway.app"
ADMIN_USER = "admin"
ADMIN_PASS = "senha_admin_segura"

class JWTTester:
    def __init__(self):
        self.token = None
        self.results = {
            "login": {"status": "not_tested"},
            "token_analysis": {},
            "endpoint_tests": {},
            "timestamp": datetime.now().isoformat()
        }
    
    def print_header(self, title, char="="):
        print(f"\n{char * 50}")
        print(f"🧪 {title}")
        print(f"{char * 50}")
    
    def print_section(self, title):
        print(f"\n{title}")
        print("-" * 30)
    
    def test_login(self):
        """🔐 Testa login do admin"""
        self.print_section("🔐 1. TESTE DE LOGIN")
        
        try:
            response = requests.post(
                f"{BASE_URL}/admin/login",
                json={"username": ADMIN_USER, "password": ADMIN_PASS},
                allow_redirects=True
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print("✅ Login bem-sucedido")
                print(f"🔑 Token: {self.token[:50]}...")
                
                self.results["login"] = {
                    "status": "success", 
                    "token_received": bool(self.token)
                }
                return True
            else:
                print(f"❌ Falha no login: {response.status_code}")
                print(f"📄 Resposta: {response.text}")
                self.results["login"] = {"status": "failed", "code": response.status_code}
                return False
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            self.results["login"] = {"status": "error", "error": str(e)}
            return False
    
    def analyze_token(self):
        """🔬 Analisa o token JWT"""
        if not self.token:
            print("⚠️ Token não disponível para análise")
            return False
        
        self.print_section("🔬 2. ANÁLISE DO TOKEN")
        
        try:
            # Decodifica sem verificação para análise
            payload = jwt.decode(self.token, options={"verify_signature": False})
            
            print("📋 Payload completo:")
            print(json.dumps(payload, indent=2, default=str))
            
            # Verifica campos críticos
            critical_fields = {
                "sub": "ID do usuário",
                "exp": "Expiração", 
                "iat": "Emitido em",
                "type": "Tipo do token (obrigatório para middleware)",
                "role": "Role do usuário (obrigatório para middleware)",
                "permissions": "Permissões (obrigatório para middleware)",
                "jti": "Token ID único (obrigatório para middleware)"
            }
            
            print(f"\n📋 Verificação de campos críticos:")
            all_present = True
            
            for field, description in critical_fields.items():
                if field in payload:
                    value = payload[field]
                    print(f"   ✅ {field}: {value} ({description})")
                else:
                    print(f"   ❌ {field}: AUSENTE ({description})")
                    all_present = False
            
            # Verifica compatibilidade com middleware
            middleware_compatible = all(
                field in payload for field in ["type", "role", "permissions", "jti"]
            )
            
            print(f"\n🔧 Compatibilidade com middleware: {'✅ SIM' if middleware_compatible else '❌ NÃO'}")
            
            self.results["token_analysis"] = {
                "payload": payload,
                "critical_fields_present": all_present,
                "middleware_compatible": middleware_compatible
            }
            
            return middleware_compatible
            
        except Exception as e:
            print(f"❌ Erro ao analisar token: {e}")
            self.results["token_analysis"] = {"error": str(e)}
            return False
    
    def test_protected_endpoints(self):
        """🛡️ Testa endpoints protegidos"""
        if not self.token:
            print("⚠️ Token não disponível para teste de endpoints")
            return
        
        self.print_section("🛡️ 3. TESTE DE ENDPOINTS PROTEGIDOS")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        endpoints = [
            ("/appointments", "Agendamentos"),
            ("/conversations", "Conversas"),
            ("/admin/me", "Info do admin"),
            ("/health", "Health check (público)")
        ]
        
        working_count = 0
        
        for endpoint, description in endpoints:
            print(f"\n📡 Testando: {endpoint} ({description})")
            
            try:
                response = requests.get(
                    f"{BASE_URL}{endpoint}",
                    headers=headers,
                    allow_redirects=True  # Seguir redirecionamentos
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ FUNCIONANDO!")
                    working_count += 1
                    
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            keys = list(data.keys())[:5]  # Primeiras 5 chaves
                            print(f"   📦 Dados recebidos: {keys}")
                        elif isinstance(data, list):
                            print(f"   📦 Lista recebida com {len(data)} itens")
                    except:
                        print("   📦 Resposta não JSON")
                        
                    self.results["endpoint_tests"][endpoint] = {
                        "status": "success",
                        "code": response.status_code
                    }
                else:
                    print(f"   ⚠️ Status inesperado: {response.status_code}")
                    self.results["endpoint_tests"][endpoint] = {
                        "status": "failed", 
                        "code": response.status_code
                    }
                    
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                self.results["endpoint_tests"][endpoint] = {"error": str(e)}
        
        print(f"\n🛡️ ENDPOINTS PROTEGIDOS:")
        print(f"   Funcionando: {working_count} | Falhando: {len(endpoints) - working_count}")
        
        for endpoint, description in endpoints:
            result = self.results["endpoint_tests"].get(endpoint, {})
            if result.get("status") == "success":
                print(f"   ✅ {endpoint}")
            else:
                code = result.get("code", "ERR")
                print(f"   ❌ {endpoint} ({code})")
    
    def test_different_requests(self):
        """🎯 Testa diferentes tipos de requests"""
        if not self.token:
            return
        
        self.print_section("🎯 4. TESTE DE DIFERENTES REQUESTS")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Teste com query parameters
        print(f"\n📊 Testando com query parameters...")
        try:
            response = requests.get(
                f"{BASE_URL}/appointments?limit=5",
                headers=headers,
                allow_redirects=True
            )
            print(f"   Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
        
        # Teste POST (se houver endpoint)
        print(f"\n📝 Testando método POST...")
        try:
            response = requests.post(
                f"{BASE_URL}/conversations/1/messages",
                headers=headers,
                json={"message": "teste"},
                allow_redirects=True
            )
            print(f"   Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    def generate_report(self):
        """📊 Gera relatório final"""
        self.print_header("📊 RELATÓRIO FINAL - TESTE JWT")
        
        login_ok = self.results["login"]["status"] == "success"
        token_ok = self.results["token_analysis"].get("middleware_compatible", False)
        
        endpoints_working = sum(
            1 for result in self.results["endpoint_tests"].values() 
            if result.get("status") == "success"
        )
        endpoints_total = len(self.results["endpoint_tests"])
        
        print(f"\n🔐 LOGIN:")
        print(f"   Status: {'✅ FUNCIONANDO' if login_ok else '❌ FALHANDO'}")
        
        print(f"\n🔬 TOKEN:")
        print(f"   Compatível com middleware: {'✅ SIM' if token_ok else '❌ NÃO'}")
        
        print(f"\n🛡️ ENDPOINTS PROTEGIDOS:")
        print(f"   Funcionando: {endpoints_working} | Falhando: {endpoints_total - endpoints_working}")
        
        for endpoint, result in self.results["endpoint_tests"].items():
            if result.get("status") == "success":
                print(f"   ✅ {endpoint}")
            else:
                code = result.get("code", "ERR")
                print(f"   ❌ {endpoint} ({code})")
        
        # Status final
        if login_ok and token_ok and endpoints_working > endpoints_total // 2:
            status = "✅ SISTEMA FUNCIONANDO"
            next_steps = "Sistema operacional! Dashboard pode ser testado."
        else:
            status = "⚠️ ❌ AINDA HÁ PROBLEMAS A RESOLVER"
            next_steps = [
                "1. Verificar logs do Railway",
                "2. Confirmar que deploy foi aplicado",
                "3. Testar novamente em alguns minutos", 
                "4. Se persistir, verificar variáveis de ambiente"
            ]
        
        print(f"\n🎯 STATUS FINAL:")
        print(f"   {status}")
        if isinstance(next_steps, list):
            print(f"   🔧 Corrigir: Endpoints protegidos")
            print(f"\n💡 PRÓXIMOS PASSOS:")
            for step in next_steps:
                print(f"   {step}")
        else:
            print(f"   🎉 {next_steps}")
        
        # Salvar resultados
        with open("jwt_test_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Resultados salvos em jwt_test_results.json")
    
    def run_full_test(self):
        """🚀 Executa teste completo"""
        self.print_header("TESTE JWT PÓS-CORREÇÃO")
        
        # 1. Login
        if not self.test_login():
            print("❌ Não é possível continuar sem login")
            return
        
        # 2. Análise do token
        self.analyze_token()
        
        # 3. Teste de endpoints
        self.test_protected_endpoints()
        
        # 4. Testes adicionais
        self.test_different_requests()
        
        # 5. Relatório final
        self.generate_report()

if __name__ == "__main__":
    tester = JWTTester()
    tester.run_full_test()
