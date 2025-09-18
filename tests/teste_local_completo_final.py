#!/usr/bin/env python3
"""
TESTE COMPLETO LOCAL - CLIENTE-SERVIDOR
========================================
Inicia servidor local e executa simulação completa de cliente
com configuração robusta e fallback para Railway DB
"""

import os
import sys
import time
import json
import signal
import socket
import requests
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

# Configuração do ambiente para Railway DB
os.environ.update({
    "DATABASE_URL": "postgresql://postgres:SlhTrYWUOLSdGSCXKqyLjXCOTrhCWAWT@autorack.proxy-production.alloydb.com:5432/railway",
    "REDIS_URL": "redis://default:DxJSpJqpPSZxjOgkePNSSCKsLONZVqUD@junction.proxy.rlwy.net:42070",
    "ENVIRONMENT": "development",
    "LOG_LEVEL": "warning",
    "DEBUG": "false"
})

# Configurações
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8002
BASE_URL = f"http://{LOCAL_HOST}:{LOCAL_PORT}"
TIMEOUT_STARTUP = 45
TIMEOUT_REQUEST = 30

class ServerManager:
    """Gerencia o ciclo de vida do servidor local"""
    
    def __init__(self):
        self.process = None
        self.server_ready = False
        
    def is_port_free(self, port: int) -> bool:
        """Verifica se a porta está livre"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((LOCAL_HOST, port))
                return True
        except OSError:
            return False
    
    def wait_for_server(self, timeout: int = TIMEOUT_STARTUP) -> bool:
        """Aguarda o servidor ficar disponível"""
        start_time = time.time()
        attempts = 0
        
        while time.time() - start_time < timeout:
            attempts += 1
            try:
                response = requests.get(
                    f"{BASE_URL}/health/basic",
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"    ✅ Servidor disponível após {attempts} tentativas")
                    self.server_ready = True
                    return True
            except requests.exceptions.RequestException:
                pass
            
            if attempts % 5 == 0:
                print(f"    ⏳ Tentativa {attempts}/{timeout//2}")
            
            time.sleep(2)
        
        return False
    
    def start_server(self) -> bool:
        """Inicia o servidor local"""
        if not self.is_port_free(LOCAL_PORT):
            print(f"    ⚠️ Porta {LOCAL_PORT} ocupada, tentando matar processos...")
            try:
                subprocess.run(f"pkill -f 'uvicorn.*{LOCAL_PORT}'", shell=True, timeout=10)
                time.sleep(3)
            except:
                pass
        
        print("🚀 INICIANDO SERVIDOR LOCAL")
        print("--" * 25)
        
        # Comando para iniciar o servidor
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", LOCAL_HOST,
            "--port", str(LOCAL_PORT),
            "--log-level", "warning",
            "--no-access-log"
        ]
        
        print(f"    Comando: {' '.join(cmd)}")
        print(f"    Aguardando servidor ficar disponível...")
        
        try:
            # Inicia o processo
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd="/home/vancim/whats_agent"
            )
            
            # Aguarda disponibilidade
            if self.wait_for_server():
                print(f"    ✅ Servidor rodando em {BASE_URL}")
                return True
            else:
                print(f"    ❌ Timeout na inicialização ({TIMEOUT_STARTUP}s)")
                self.stop_server()
                return False
                
        except Exception as e:
            print(f"    ❌ Erro ao iniciar servidor: {e}")
            return False
    
    def stop_server(self):
        """Para o servidor"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                print("    🛑 Servidor parado")
            except subprocess.TimeoutExpired:
                self.process.kill()
                print("    🔫 Servidor forçado a parar")
            except:
                pass
            self.process = None
        self.server_ready = False

class ClientSimulator:
    """Simula interações completas de cliente"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = TIMEOUT_REQUEST
        self.results = []
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Registra resultado do teste"""
        status = "✅ SUCESSO" if success else "❌ FALHA"
        print(f"    {status} - {name}")
        if details and not success:
            print(f"        {details}")
        
        self.results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        return success
    
    def test_basic_endpoints(self) -> bool:
        """Testa endpoints básicos"""
        print("\n🔍 TESTANDO ENDPOINTS BÁSICOS")
        print("--" * 25)
        
        tests = [
            ("/health/basic", "Health Check Básico"),
            ("/health/detailed", "Health Check Detalhado"),
            ("/docs", "Documentação API"),
            ("/metrics", "Métricas Prometheus"),
            ("/", "Endpoint Root")
        ]
        
        success_count = 0
        for endpoint, name in tests:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                success = response.status_code in [200, 307]  # 307 para redirects
                self.log_test(name, success, 
                             f"Status: {response.status_code}" if not success else "")
                if success:
                    success_count += 1
            except Exception as e:
                self.log_test(name, False, f"Erro: {str(e)}")
        
        return success_count >= 3  # Pelo menos 3 dos 5 devem funcionar
    
    def test_auth_flow(self) -> bool:
        """Testa fluxo de autenticação"""
        print("\n🔐 TESTANDO AUTENTICAÇÃO")
        print("--" * 25)
        
        try:
            # Teste 1: Endpoint sem auth deve retornar 401/403
            response = self.session.get(f"{self.base_url}/api/v1/auth/profile")
            success_1 = response.status_code in [401, 403, 422]
            self.log_test("Proteção de Rota", success_1,
                         f"Status: {response.status_code}" if not success_1 else "")
            
            # Teste 2: Login endpoint deve existir
            response = self.session.post(f"{self.base_url}/api/v1/auth/login", 
                                       json={"username": "test", "password": "test"})
            success_2 = response.status_code in [400, 401, 422]  # Credenciais inválidas esperadas
            self.log_test("Endpoint de Login", success_2,
                         f"Status: {response.status_code}" if not success_2 else "")
            
            # Teste 3: Registro endpoint deve existir
            response = self.session.post(f"{self.base_url}/api/v1/auth/register",
                                       json={"email": "test@test.com", "password": "test"})
            success_3 = response.status_code in [400, 422, 409]  # Dados inválidos esperados
            self.log_test("Endpoint de Registro", success_3,
                         f"Status: {response.status_code}" if not success_3 else "")
            
            return success_1 and success_2 and success_3
            
        except Exception as e:
            self.log_test("Fluxo de Autenticação", False, f"Erro: {str(e)}")
            return False
    
    def test_api_exploration(self) -> bool:
        """Explora endpoints da API"""
        print("\n🗺️ EXPLORANDO API")
        print("--" * 25)
        
        api_endpoints = [
            "/api/v1/health",
            "/api/v1/appointments",
            "/api/v1/conversations", 
            "/api/v1/clients",
            "/api/v1/business",
            "/api/v1/analytics",
            "/api/v1/webhooks"
        ]
        
        success_count = 0
        for endpoint in api_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                # 401/403 também é sucesso (endpoint existe mas precisa auth)
                success = response.status_code in [200, 401, 403, 422]
                name = endpoint.split('/')[-1].title()
                self.log_test(f"Endpoint {name}", success,
                             f"Status: {response.status_code}" if not success else "")
                if success:
                    success_count += 1
            except Exception as e:
                self.log_test(f"Endpoint {endpoint}", False, f"Erro: {str(e)}")
        
        return success_count >= 5  # Pelo menos 5 endpoints devem responder
    
    def test_websocket_connection(self) -> bool:
        """Testa conectividade WebSocket"""
        print("\n🌐 TESTANDO WEBSOCKET")
        print("--" * 25)
        
        try:
            # Teste básico de disponibilidade de WebSocket endpoints
            ws_endpoints = [
                "/ws",
                "/ws/chat",
                "/ws/notifications"
            ]
            
            success_count = 0
            for endpoint in ws_endpoints:
                try:
                    # Tentativa de GET em endpoint WS deve retornar erro específico
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    # WebSocket endpoints normalmente retornam 426 (Upgrade Required) ou 400
                    success = response.status_code in [400, 426, 405]
                    name = f"WebSocket {endpoint}"
                    self.log_test(name, success,
                                 f"Status: {response.status_code}" if not success else "")
                    if success:
                        success_count += 1
                except Exception as e:
                    self.log_test(f"WebSocket {endpoint}", False, f"Erro: {str(e)}")
            
            return success_count >= 1  # Pelo menos 1 endpoint WS deve responder
            
        except Exception as e:
            self.log_test("WebSocket Connectivity", False, f"Erro: {str(e)}")
            return False
    
    def test_performance_basic(self) -> bool:
        """Teste básico de performance"""
        print("\n⚡ TESTE DE PERFORMANCE")
        print("--" * 25)
        
        try:
            # Múltiplas requisições rápidas
            start_time = time.time()
            success_count = 0
            
            for i in range(10):
                try:
                    response = self.session.get(f"{self.base_url}/health/basic")
                    if response.status_code == 200:
                        success_count += 1
                except:
                    pass
            
            elapsed = time.time() - start_time
            avg_response_time = elapsed / 10
            
            success_rate = success_count / 10
            performance_ok = success_rate >= 0.8 and avg_response_time < 1.0
            
            self.log_test("Performance Básica", performance_ok,
                         f"Taxa sucesso: {success_rate:.1%}, "
                         f"Tempo médio: {avg_response_time:.3f}s")
            
            return performance_ok
            
        except Exception as e:
            self.log_test("Performance Básica", False, f"Erro: {str(e)}")
            return False
    
    def run_complete_simulation(self) -> Dict[str, Any]:
        """Executa simulação completa"""
        print(f"\n👤 INICIANDO SIMULAÇÃO DE CLIENTE")
        print(f"🎯 URL: {self.base_url}")
        print("=" * 50)
        
        # Executa todos os testes
        test_results = {
            "basic_endpoints": self.test_basic_endpoints(),
            "auth_flow": self.test_auth_flow(),
            "api_exploration": self.test_api_exploration(),
            "websocket_connection": self.test_websocket_connection(),
            "performance_basic": self.test_performance_basic()
        }
        
        # Calcula estatísticas
        total_tests = len([r for r in self.results])
        successful_tests = len([r for r in self.results if r["success"]])
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Resultado geral
        overall_success = sum(test_results.values()) >= 3  # Pelo menos 3 categorias devem passar
        
        return {
            "overall_success": overall_success,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "test_categories": test_results,
            "detailed_results": self.results
        }

def main():
    """Função principal do teste"""
    print("🔄 TESTE REAL CLIENTE-SERVIDOR LOCAL")
    print(f"🎯 URL: {BASE_URL}")
    print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 70)
    
    server = ServerManager()
    
    try:
        # Inicia servidor
        if not server.start_server():
            print("❌ FALHA CRÍTICA: Não foi possível iniciar servidor local")
            return False
        
        # Aguarda estabilização
        time.sleep(3)
        
        # Executa simulação
        client = ClientSimulator(BASE_URL)
        results = client.run_complete_simulation()
        
        # Relatório final
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL")
        print("=" * 70)
        
        status = "✅ SUCESSO" if results["overall_success"] else "❌ FALHA"
        print(f"{status} - Teste Geral: {results['success_rate']:.1%}")
        print(f"📈 Estatísticas: {results['successful_tests']}/{results['total_tests']} testes passaram")
        
        print("\n🎯 Resultados por Categoria:")
        for category, success in results["test_categories"].items():
            status = "✅" if success else "❌"
            name = category.replace("_", " ").title()
            print(f"  {status} {name}")
        
        # Salva relatório detalhado
        report_file = f"/home/vancim/whats_agent/temp_reports/teste_local_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Relatório salvo: {report_file}")
        
        return results["overall_success"]
        
    except KeyboardInterrupt:
        print("\n⚠️ Teste interrompido pelo usuário")
        return False
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        return False
    finally:
        # Sempre para o servidor
        server.stop_server()
        print("\n🏁 Teste finalizado")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)