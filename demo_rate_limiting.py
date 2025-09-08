#!/usr/bin/env python3
"""
🚫 Demonstração do Sistema de Rate Limiting por Usuário
==================================================

Este script demonstra o funcionamento completo do sistema de rate limiting
implementado, incluindo:

1. Configuração e inicialização
2. Diferentes limites por tipo de usuário
3. Rate limiting por endpoint
4. Gerenciamento via API endpoints
5. Monitoramento e métricas

"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# URLs base (ajustar para ambiente)
BASE_URL = "http://localhost:8000"
ADMIN_BASE_URL = f"{BASE_URL}/admin"

class RateLimitDemo:
    """Demonstração completa do sistema de rate limiting"""
    
    def __init__(self):
        self.session = None
        self.admin_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log(self, message: str, level: str = "INFO"):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "\033[94m",     # Azul
            "SUCCESS": "\033[92m",  # Verde
            "WARNING": "\033[93m",  # Amarelo
            "ERROR": "\033[91m",    # Vermelho
            "DEMO": "\033[95m"      # Magenta
        }
        reset = "\033[0m"
        
        color = colors.get(level, "")
        print(f"{color}[{timestamp}] {level}: {message}{reset}")
    
    async def login_admin(self) -> bool:
        """Login como admin para acessar endpoints de gerenciamento"""
        try:
            self.log("Fazendo login admin para demonstração...", "DEMO")
            
            # Tentar login com credenciais padrão
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            async with self.session.post(
                f"{BASE_URL}/admin/login",
                json=login_data,
                timeout=10
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.admin_token = data.get("access_token")
                    self.log("✅ Login admin realizado com sucesso", "SUCCESS")
                    return True
                else:
                    self.log(f"❌ Falha no login admin: {response.status}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"❌ Erro no login admin: {e}", "ERROR")
            return False
    
    async def get_admin_headers(self) -> Dict[str, str]:
        """Headers com token admin"""
        if not self.admin_token:
            await self.login_admin()
        
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    async def demo_rate_limit_status(self):
        """Demonstrar status do sistema de rate limiting"""
        self.log("=== DEMONSTRAÇÃO: STATUS DO SISTEMA ===", "DEMO")
        
        try:
            headers = await self.get_admin_headers()
            
            async with self.session.get(
                f"{ADMIN_BASE_URL}/rate-limit/status",
                headers=headers,
                timeout=10
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    self.log("✅ Status do sistema obtido:", "SUCCESS")
                    self.log(f"   Sistema ativo: {data.get('system_status')}", "INFO")
                    self.log(f"   Total de endpoints: {data.get('total_limits', 0)}", "INFO")
                    self.log(f"   Tipos de usuário: {data.get('user_types', [])}", "INFO")
                    
                    return data
                else:
                    self.log(f"❌ Erro ao obter status: {response.status}", "ERROR")
                    return None
                    
        except Exception as e:
            self.log(f"❌ Erro na demonstração de status: {e}", "ERROR")
            return None
    
    async def demo_rate_limit_config(self):
        """Demonstrar configuração do sistema"""
        self.log("=== DEMONSTRAÇÃO: CONFIGURAÇÃO DO SISTEMA ===", "DEMO")
        
        try:
            headers = await self.get_admin_headers()
            
            async with self.session.get(
                f"{ADMIN_BASE_URL}/rate-limit/config",
                headers=headers,
                timeout=10
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    self.log("✅ Configuração obtida:", "SUCCESS")
                    
                    # Mostrar alguns endpoints importantes
                    endpoint_limits = data.get('endpoint_limits', {})
                    important_endpoints = [
                        'POST /webhook',
                        'POST /auth/login', 
                        'GET /health',
                        'default'
                    ]
                    
                    self.log("   Limites por endpoint (principais):", "INFO")
                    for endpoint in important_endpoints:
                        if endpoint in endpoint_limits:
                            config = endpoint_limits[endpoint]
                            self.log(f"     {endpoint}: {config['requests']} req/{config['window']}s", "INFO")
                    
                    # Mostrar multiplicadores por tipo de usuário
                    multipliers = data.get('user_type_multipliers', {})
                    self.log("   Multiplicadores por tipo de usuário:", "INFO")
                    for user_type, mult in multipliers.items():
                        self.log(f"     {user_type}: {mult}x", "INFO")
                    
                    return data
                else:
                    self.log(f"❌ Erro ao obter configuração: {response.status}", "ERROR")
                    return None
                    
        except Exception as e:
            self.log(f"❌ Erro na demonstração de config: {e}", "ERROR")
            return None
    
    async def demo_health_check(self):
        """Demonstrar health check do sistema"""
        self.log("=== DEMONSTRAÇÃO: HEALTH CHECK ===", "DEMO")
        
        try:
            headers = await self.get_admin_headers()
            
            async with self.session.get(
                f"{ADMIN_BASE_URL}/rate-limit/health",
                headers=headers,
                timeout=10
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    overall_status = data.get('overall_status', 'unknown')
                    health_details = data.get('health_details', {})
                    
                    if overall_status == 'healthy':
                        self.log("✅ Sistema de rate limiting saudável", "SUCCESS")
                    elif overall_status == 'degraded':
                        self.log("⚠️ Sistema de rate limiting degradado", "WARNING")
                    else:
                        self.log("❌ Sistema de rate limiting com problemas", "ERROR")
                    
                    self.log(f"   Conexão Redis: {health_details.get('redis_connection', 'unknown')}", "INFO")
                    self.log(f"   Limites configurados: {health_details.get('total_limits_configured', 0)}", "INFO")
                    self.log(f"   Middleware ativo: {health_details.get('middleware_active', False)}", "INFO")
                    
                    # Mostrar recomendações se houver
                    recommendations = data.get('recommendations', [])
                    if recommendations:
                        self.log("   Recomendações:", "INFO")
                        for rec in recommendations[:3]:  # Mostrar apenas 3
                            self.log(f"     • {rec}", "INFO")
                    
                    return data
                else:
                    self.log(f"❌ Erro no health check: {response.status}", "ERROR")
                    return None
                    
        except Exception as e:
            self.log(f"❌ Erro no health check: {e}", "ERROR")
            return None
    
    async def demo_simulate_requests(self):
        """Simular requisições para testar rate limiting"""
        self.log("=== DEMONSTRAÇÃO: SIMULAÇÃO DE REQUISIÇÕES ===", "DEMO")
        
        try:
            # Testar endpoint público (health check)
            self.log("Testando endpoint público (/health)...", "INFO")
            
            success_count = 0
            blocked_count = 0
            
            # Fazer várias requisições rapidamente
            for i in range(10):
                try:
                    async with self.session.get(
                        f"{BASE_URL}/health",
                        timeout=5
                    ) as response:
                        
                        if response.status == 200:
                            success_count += 1
                        elif response.status == 429:  # Too Many Requests
                            blocked_count += 1
                        
                        # Headers de rate limiting
                        limit = response.headers.get('X-RateLimit-Limit', 'N/A')
                        remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
                        reset = response.headers.get('X-RateLimit-Reset', 'N/A')
                        
                        status_icon = "✅" if response.status == 200 else ("🚫" if response.status == 429 else "❓")
                        self.log(f"   Req {i+1}: {status_icon} Status {response.status} | Limit: {limit} | Remaining: {remaining}", "INFO")
                        
                except Exception as e:
                    self.log(f"   Req {i+1}: ❌ Erro: {e}", "ERROR")
                
                # Pequena pausa entre requisições
                await asyncio.sleep(0.1)
            
            self.log(f"Resultado: {success_count} sucessos, {blocked_count} bloqueadas", "SUCCESS" if blocked_count == 0 else "WARNING")
            
        except Exception as e:
            self.log(f"❌ Erro na simulação: {e}", "ERROR")
    
    async def demo_user_rate_limit_management(self):
        """Demonstrar gerenciamento de rate limiting por usuário"""
        self.log("=== DEMONSTRAÇÃO: GERENCIAMENTO POR USUÁRIO ===", "DEMO")
        
        try:
            headers = await self.get_admin_headers()
            
            # Testar reset de rate limit para usuário fictício
            test_user = "demo_user_123"
            
            self.log(f"Resetando rate limit para usuário: {test_user}", "INFO")
            
            async with self.session.post(
                f"{ADMIN_BASE_URL}/rate-limit/reset",
                headers=headers,
                params={"user_id": test_user},
                timeout=10
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    self.log("✅ Rate limit resetado com sucesso", "SUCCESS")
                    self.log(f"   Usuário: {data.get('user_id', 'N/A')}", "INFO")
                    self.log(f"   Resetado por: {data.get('reset_by', 'N/A')}", "INFO")
                else:
                    self.log(f"❌ Erro ao resetar rate limit: {response.status}", "ERROR")
                    
        except Exception as e:
            self.log(f"❌ Erro no gerenciamento por usuário: {e}", "ERROR")
    
    async def demo_rate_limit_test_endpoint(self):
        """Demonstrar endpoint de teste de rate limiting"""
        self.log("=== DEMONSTRAÇÃO: ENDPOINT DE TESTE ===", "DEMO")
        
        try:
            headers = await self.get_admin_headers()
            
            # Testar rate limiting para usuário específico
            test_user = "demo_user_test"
            
            self.log(f"Testando rate limiting para usuário: {test_user}", "INFO")
            
            async with self.session.get(
                f"{ADMIN_BASE_URL}/rate-limit/test/{test_user}",
                headers=headers,
                params={
                    "endpoint": "GET /test",
                    "requests": 5
                },
                timeout=10
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    self.log("✅ Teste de rate limiting executado", "SUCCESS")
                    
                    test_config = data.get('test_config', {})
                    self.log(f"   Endpoint testado: {test_config.get('endpoint', 'N/A')}", "INFO")
                    self.log(f"   Requests simuladas: {test_config.get('requests_simulated', 0)}", "INFO")
                    
                    # Mostrar resultados
                    results = data.get('results', [])
                    exceeded_count = sum(1 for r in results if r.get('exceeded', False))
                    
                    self.log(f"   Requests bloqueadas: {exceeded_count}/{len(results)}", "INFO")
                    
                    # Mostrar algumas tentativas
                    for i, result in enumerate(results[:3]):
                        status = "🚫 BLOQUEADA" if result.get('exceeded', False) else "✅ PERMITIDA"
                        current = result.get('current', 0)
                        limit = result.get('limit', 0)
                        self.log(f"     Req {i+1}: {status} ({current}/{limit})", "INFO")
                    
                else:
                    self.log(f"❌ Erro no teste: {response.status}", "ERROR")
                    
        except Exception as e:
            self.log(f"❌ Erro no endpoint de teste: {e}", "ERROR")
    
    async def run_complete_demo(self):
        """Executar demonstração completa"""
        self.log("🚫 INICIANDO DEMONSTRAÇÃO COMPLETA DO RATE LIMITING 🚫", "DEMO")
        self.log("=" * 60, "DEMO")
        
        try:
            # 1. Login administrativo
            if not await self.login_admin():
                self.log("❌ Não foi possível fazer login admin - parando demo", "ERROR")
                return False
            
            # 2. Status do sistema
            await self.demo_rate_limit_status()
            await asyncio.sleep(1)
            
            # 3. Configuração do sistema
            await self.demo_rate_limit_config()
            await asyncio.sleep(1)
            
            # 4. Health check
            await self.demo_health_check()
            await asyncio.sleep(1)
            
            # 5. Simulação de requisições
            await self.demo_simulate_requests()
            await asyncio.sleep(1)
            
            # 6. Gerenciamento por usuário
            await self.demo_user_rate_limit_management()
            await asyncio.sleep(1)
            
            # 7. Endpoint de teste
            await self.demo_rate_limit_test_endpoint()
            
            self.log("=" * 60, "DEMO")
            self.log("🎉 DEMONSTRAÇÃO COMPLETA FINALIZADA COM SUCESSO! 🎉", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erro na demonstração completa: {e}", "ERROR")
            return False

async def main():
    """Função principal"""
    print("\n🚫 Sistema de Rate Limiting por Usuário - DEMO 🚫")
    print("=" * 50)
    print("Este demo requer que o servidor esteja executando.")
    print("Inicie o servidor com: uvicorn app.main:app --reload")
    print("=" * 50)
    
    # Aguardar confirmação
    try:
        input("\nPressione ENTER para iniciar a demonstração... ")
    except KeyboardInterrupt:
        print("\n❌ Demonstração cancelada pelo usuário")
        return
    
    async with RateLimitDemo() as demo:
        success = await demo.run_complete_demo()
        
        if success:
            print("\n✅ Demonstração concluída com sucesso!")
            print("\n📊 RESUMO DOS RECURSOS DEMONSTRADOS:")
            print("   • Sistema de rate limiting por usuário")
            print("   • Configuração flexível por endpoint")
            print("   • Diferentes limites por tipo de usuário")
            print("   • API de gerenciamento administrativo")
            print("   • Monitoramento e health checks")
            print("   • Simulação e testes de rate limiting")
            print("\n🔥 Sistema pronto para produção!")
        else:
            print("\n❌ Houve problemas na demonstração.")
            print("Verifique se o servidor está executando e tente novamente.")

if __name__ == "__main__":
    asyncio.run(main())
