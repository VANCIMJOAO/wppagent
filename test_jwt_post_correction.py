#!/usr/bin/env python3
"""
🧪 TESTE JWT PÓS-CORREÇÃO
=========================

Script para testar se as correções JWT funcionaram.
Deve ser executado após deploy das correções.

Correções aplicadas:
1. ✅ JWT Manager simplificado (sem Redis/rotação)
2. ✅ Admin Auth usando JWT Manager 
3. ✅ Middleware com fallback para compatibilidade
"""

import asyncio
import httpx
import json
import jwt as jwt_lib
from datetime import datetime

class JWTTester:
    """Testa sistema JWT após correções"""
    
    def __init__(self):
        self.railway_url = "https://wppagent-production.up.railway.app"
        self.results = {}
    
    async def run_complete_test(self):
        """Executa teste completo"""
        print("🧪 TESTE JWT PÓS-CORREÇÃO")
        print("=" * 50)
        
        # 1. Testar login
        token = await self.test_login()
        
        if token:
            # 2. Analisar token
            await self.analyze_token(token)
            
            # 3. Testar endpoints protegidos
            await self.test_protected_endpoints(token)
            
            # 4. Testar diferentes tipos de request
            await self.test_various_requests(token)
        
        # 5. Gerar relatório final
        self.generate_final_report()
    
    async def test_login(self) -> str:
        """Testa login e obtém token"""
        print("\n🔐 1. TESTE DE LOGIN")
        print("-" * 30)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    f"{self.railway_url}/admin/login",
                    json={
                        "username": "admin",
                        "password": "senha_admin_segura"
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    print(f"✅ Login bem-sucedido")
                    print(f"🔑 Token: {token[:30]}...")
                    
                    self.results["login"] = {
                        "success": True,
                        "token_received": True,
                        "token": token
                    }
                    
                    return token
                else:
                    print(f"❌ Login falhou: {response.status_code}")
                    print(f"Resposta: {response.text}")
                    
                    self.results["login"] = {
                        "success": False,
                        "status_code": response.status_code,
                        "response": response.text
                    }
                    
            except Exception as e:
                print(f"❌ Erro no login: {e}")
                self.results["login"] = {"success": False, "error": str(e)}
        
        return None
    
    async def analyze_token(self, token: str):
        """Analisa estrutura do token JWT"""
        print("\n🔬 2. ANÁLISE DO TOKEN")
        print("-" * 30)
        
        try:
            # Decodificar sem verificação para ver estrutura
            payload = jwt_lib.decode(token, options={"verify_signature": False})
            
            print(f"📋 Payload completo:")
            print(json.dumps(payload, indent=2, default=str))
            
            # Verificar campos críticos
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
            missing_fields = []
            present_fields = []
            
            for field, description in critical_fields.items():
                if field in payload:
                    print(f"   ✅ {field}: {payload[field]} ({description})")
                    present_fields.append(field)
                else:
                    print(f"   ❌ {field}: AUSENTE ({description})")
                    missing_fields.append(field)
            
            # Análise de compatibilidade
            middleware_compatible = len(missing_fields) == 0
            print(f"\n🔧 Compatibilidade com middleware: {'✅ SIM' if middleware_compatible else '❌ NÃO'}")
            
            if missing_fields:
                print(f"   Campos ausentes: {', '.join(missing_fields)}")
            
            self.results["token_analysis"] = {
                "payload": payload,
                "present_fields": present_fields,
                "missing_fields": missing_fields,
                "middleware_compatible": middleware_compatible
            }
            
        except Exception as e:
            print(f"❌ Erro ao analisar token: {e}")
            self.results["token_analysis"] = {"error": str(e)}
    
    async def test_protected_endpoints(self, token: str):
        """Testa endpoints protegidos"""
        print("\n🛡️  3. TESTE DE ENDPOINTS PROTEGIDOS")
        print("-" * 40)
        
        test_endpoints = [
            {"path": "/appointments", "description": "Agendamentos"},
            {"path": "/conversations", "description": "Conversas"}, 
            {"path": "/admin/me", "description": "Info do admin"},
            {"path": "/health", "description": "Health check (público)"}
        ]
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            for endpoint in test_endpoints:
                path = endpoint["path"]
                desc = endpoint["description"]
                
                print(f"\n📡 Testando: {path} ({desc})")
                
                try:
                    # Para endpoint público, não enviar token
                    headers = {}
                    if path != "/health":
                        headers["Authorization"] = f"Bearer {token}"
                    
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            allow_redirects=True  # Seguir redirecionamentos automaticamente
        )                    print(f"   Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"   ✅ FUNCIONANDO!")
                        try:
                            data = response.json()
                            if isinstance(data, dict) and len(data) > 0:
                                print(f"   📦 Dados recebidos: {list(data.keys())}")
                        except:
                            pass
                            
                    elif response.status_code == 401:
                        print(f"   ❌ 401 Unauthorized - Token rejeitado pelo middleware")
                    elif response.status_code == 403:
                        print(f"   ⚠️  403 Forbidden - Token aceito mas sem permissão")
                    elif response.status_code == 404:
                        print(f"   ⚠️  404 Not Found - Endpoint não existe")
                    else:
                        print(f"   ⚠️  Status inesperado: {response.status_code}")
                    
                    if not self.results.get("endpoint_tests"):
                        self.results["endpoint_tests"] = {}
                    
                    self.results["endpoint_tests"][path] = {
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "description": desc,
                        "response_preview": response.text[:100]
                    }
                    
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
                    if not self.results.get("endpoint_tests"):
                        self.results["endpoint_tests"] = {}
                    self.results["endpoint_tests"][path] = {"error": str(e)}
    
    async def test_various_requests(self, token: str):
        """Testa diferentes tipos de request"""
        print("\n🎯 4. TESTE DE DIFERENTES REQUESTS")
        print("-" * 40)
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Teste com query parameters
            print("\n📊 Testando com query parameters...")
            try:
                response = await client.get(
                    f"{self.railway_url}/appointments?limit=5&offset=0",
                    headers={"Authorization": f"Bearer {token}"}
                )
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ Query parameters funcionando")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
            
            # Teste POST (se endpoint existir)
            print("\n📝 Testando método POST...")
            try:
                response = await client.post(
                    f"{self.railway_url}/appointments",
                    json={
                        "user_id": 1,
                        "business_id": 1,
                        "appointment_date": "2025-09-03T10:00:00Z",
                        "notes": "Teste de criação"
                    },
                    headers={"Authorization": f"Bearer {token}"}
                )
                print(f"   Status: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    print("   ✅ POST funcionando")
                elif response.status_code == 404:
                    print("   ⚠️  Endpoint POST não implementado")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
    
    def generate_final_report(self):
        """Gera relatório final"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL - TESTE JWT")
        print("=" * 60)
        
        # Status do login
        login_success = self.results.get("login", {}).get("success", False)
        print(f"\n🔐 LOGIN:")
        print(f"   Status: {'✅ FUNCIONANDO' if login_success else '❌ FALHANDO'}")
        
        # Análise do token
        token_analysis = self.results.get("token_analysis", {})
        middleware_compatible = token_analysis.get("middleware_compatible", False)
        print(f"\n🔬 TOKEN:")
        print(f"   Compatível com middleware: {'✅ SIM' if middleware_compatible else '❌ NÃO'}")
        
        missing_fields = token_analysis.get("missing_fields", [])
        if missing_fields:
            print(f"   Campos ausentes: {', '.join(missing_fields)}")
        
        # Endpoints protegidos
        endpoint_tests = self.results.get("endpoint_tests", {})
        successful_endpoints = [k for k, v in endpoint_tests.items() if v.get("success")]
        failed_endpoints = [k for k, v in endpoint_tests.items() if not v.get("success")]
        
        print(f"\n🛡️  ENDPOINTS PROTEGIDOS:")
        print(f"   Funcionando: {len(successful_endpoints)} | Falhando: {len(failed_endpoints)}")
        
        for endpoint in successful_endpoints:
            print(f"   ✅ {endpoint}")
        
        for endpoint in failed_endpoints:
            status = endpoint_tests[endpoint].get("status_code", "ERROR")
            print(f"   ❌ {endpoint} ({status})")
        
        # Status final
        all_working = login_success and middleware_compatible and len(failed_endpoints) == 0
        
        print(f"\n🎯 STATUS FINAL:")
        if all_working:
            print(f"   🎉 ✅ SISTEMA JWT FUNCIONANDO PERFEITAMENTE!")
            print(f"   🎯 Dashboard pode se autenticar com sucesso")
            print(f"   🔑 Tokens são aceitos pelo middleware")
            print(f"   📱 Todas as requests autenticadas funcionam")
        else:
            print(f"   ⚠️  ❌ AINDA HÁ PROBLEMAS A RESOLVER")
            
            if not login_success:
                print(f"   🔧 Corrigir: Sistema de login")
            if not middleware_compatible:
                print(f"   🔧 Corrigir: Compatibilidade do token")
            if len(failed_endpoints) > 0:
                print(f"   🔧 Corrigir: Endpoints protegidos")
        
        # Próximos passos
        if not all_working:
            print(f"\n💡 PRÓXIMOS PASSOS:")
            print(f"   1. Verificar logs do Railway")
            print(f"   2. Confirmar que deploy foi aplicado")
            print(f"   3. Testar novamente em alguns minutos")
            print(f"   4. Se persistir, verificar variáveis de ambiente")

async def main():
    """Executa teste completo"""
    tester = JWTTester()
    await tester.run_complete_test()
    
    # Salvar resultados
    with open("jwt_test_results.json", "w") as f:
        json.dump({
            "test_results": tester.results,
            "timestamp": datetime.now().isoformat(),
            "railway_url": tester.railway_url
        }, f, indent=2, default=str)
    
    print(f"\n💾 Resultados salvos em jwt_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
