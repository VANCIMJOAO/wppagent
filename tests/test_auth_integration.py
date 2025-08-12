#!/usr/bin/env python3
"""
🔒 Teste de Integração Completa do Sistema de Autenticação

Este script testa todo o fluxo de autenticação:
1. Login básico
2. Configuração de 2FA
3. Login com 2FA  
4. Acesso a recursos protegidos
5. Gerenciamento de secrets
"""

import asyncio
import httpx
import json
import qrcode
from io import BytesIO
import base64
from datetime import datetime

# Configuração do servidor
BASE_URL = "http://localhost:8000"

class AuthIntegrationTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_data = {
            "username": "admin",
            "password": "SECURE_PASSWORD_FROM_ENV"
        }
        
    async def test_complete_flow(self):
        """Testa o fluxo completo de autenticação"""
        print("🔒 TESTE DE INTEGRAÇÃO - SISTEMA DE AUTENTICAÇÃO")
        print("=" * 60)
        
        async with httpx.AsyncClient() as client:
            # 1. Testar health check
            await self._test_health_check(client)
            
            # 2. Testar login básico
            await self._test_basic_login(client)
            
            # 3. Testar configuração de 2FA
            await self._test_2fa_setup(client)
            
            # 4. Testar login com 2FA
            await self._test_2fa_login(client)
            
            # 5. Testar acesso a recursos protegidos
            await self._test_protected_resources(client)
            
            # 6. Testar gerenciamento de secrets
            await self._test_secrets_management(client)
            
            # 7. Testar rate limiting
            await self._test_rate_limiting(client)
            
        print("\n🎉 TESTE DE INTEGRAÇÃO CONCLUÍDO!")
        
    async def _test_health_check(self, client):
        """Testa se a API está funcionando"""
        print("\n1. 🏥 Testando Health Check...")
        
        try:
            response = await client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("   ✅ API está funcionando")
                data = response.json()
                print(f"   📊 Status: {data.get('status')}")
            else:
                print(f"   ❌ Erro: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erro de conexão: {e}")
            return False
        return True
        
    async def _test_basic_login(self, client):
        """Testa login básico"""
        print("\n2. 🔑 Testando Login Básico...")
        
        try:
            response = await client.post(
                f"{self.base_url}/auth/login",
                json=self.user_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print("   ✅ Login realizado com sucesso")
                print(f"   🎫 Token obtido: {self.token[:20]}...")
            else:
                print(f"   ❌ Erro no login: {response.status_code}")
                print(f"   📝 Resposta: {response.text}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            
    async def _test_2fa_setup(self, client):
        """Testa configuração de 2FA"""
        print("\n3. 🔐 Testando Configuração de 2FA...")
        
        if not self.token:
            print("   ⚠️ Token não disponível, pulando teste")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Configurar 2FA
            response = await client.post(
                f"{self.base_url}/auth/2fa/setup",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ 2FA configurado com sucesso")
                print(f"   🔑 Secret: {data.get('secret')}")
                print(f"   📱 QR Code disponível: {bool(data.get('qr_code'))}")
                
                # Salvar dados do 2FA para próximo teste
                self.totp_secret = data.get('secret')
                
            else:
                print(f"   ❌ Erro na configuração: {response.status_code}")
                print(f"   📝 Resposta: {response.text}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            
    async def _test_2fa_login(self, client):
        """Testa login com 2FA"""
        print("\n4. 🔓 Testando Login com 2FA...")
        
        if not hasattr(self, 'totp_secret'):
            print("   ⚠️ 2FA não configurado, pulando teste")
            return
            
        try:
            # Simular código TOTP (para teste, usar código fixo)
            import pyotp
            totp = pyotp.TOTP(self.totp_secret)
            code = totp.now()
            
            response = await client.post(
                f"{self.base_url}/auth/2fa/verify",
                json={
                    "code": code,
                    "type": "totp"
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ 2FA verificado com sucesso")
                print(f"   🎫 Novo token: {data.get('access_token', 'N/A')[:20]}...")
            else:
                print(f"   ❌ Erro na verificação: {response.status_code}")
                print(f"   📝 Resposta: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            
    async def _test_protected_resources(self, client):
        """Testa acesso a recursos protegidos"""
        print("\n5. 🛡️ Testando Recursos Protegidos...")
        
        if not self.token:
            print("   ⚠️ Token não disponível, pulando teste")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Testar status da autenticação
            response = await client.get(
                f"{self.base_url}/auth/status",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Acesso autorizado a recurso protegido")
                print(f"   👤 Usuário: {data.get('user', 'N/A')}")
                print(f"   📊 Status: {data.get('authenticated', False)}")
            else:
                print(f"   ❌ Acesso negado: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            
    async def _test_secrets_management(self, client):
        """Testa gerenciamento de secrets"""
        print("\n6. 🔐 Testando Gerenciamento de Secrets...")
        
        if not self.token:
            print("   ⚠️ Token não disponível, pulando teste")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Listar secrets
            response = await client.get(
                f"{self.base_url}/secrets/list",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Secrets listados com sucesso")
                print(f"   📝 Total de secrets: {len(data.get('secrets', []))}")
            else:
                print(f"   ❌ Erro ao listar: {response.status_code}")
                
            # Criar um secret de teste
            test_secret = {
                "secret_id": "test_secret",
                "secret_type": "api_key",
                "value": "test_value_123"
            }
            
            response = await client.post(
                f"{self.base_url}/secrets/create",
                json=test_secret,
                headers=headers
            )
            
            if response.status_code == 200:
                print("   ✅ Secret criado com sucesso")
            else:
                print(f"   ❌ Erro ao criar: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            
    async def _test_rate_limiting(self, client):
        """Testa rate limiting"""
        print("\n7. 🚦 Testando Rate Limiting...")
        
        try:
            # Fazer várias requisições rápidas
            successful_requests = 0
            rate_limited_requests = 0
            
            for i in range(10):
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    successful_requests += 1
                elif response.status_code == 429:
                    rate_limited_requests += 1
                    
            print(f"   ✅ Requisições bem-sucedidas: {successful_requests}")
            print(f"   🚫 Requisições limitadas: {rate_limited_requests}")
            
            if rate_limited_requests > 0:
                print("   ✅ Rate limiting está funcionando")
            else:
                print("   ℹ️ Rate limiting não ativado ou limite não atingido")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")


async def main():
    """Função principal"""
    test = AuthIntegrationTest()
    await test.test_complete_flow()


if __name__ == "__main__":
    print("🚀 Iniciando teste de integração...")
    print("⚠️ Certifique-se de que o servidor está rodando em http://localhost:8000")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
