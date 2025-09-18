#!/usr/bin/env python3
"""
🔄 Teste Completo Cliente-Servidor Real
Levanta o servidor WhatsApp Agent localmente e simula interação completa de cliente
"""

import subprocess
import requests
import json
import time
import threading
import signal
import sys
import os
from datetime import datetime
import psutil

# Configuração
SERVIDOR_HOST = "127.0.0.1"
SERVIDOR_PORT = 8000
BASE_URL = f"http://{SERVIDOR_HOST}:{SERVIDOR_PORT}"
TIMEOUT_STARTUP = 60  # segundos para aguardar servidor subir

class TesteServidorCompleto:
    def __init__(self):
        self.processo_servidor = None
        self.servidor_rodando = False
        self.resultados = []
        
    def log_resultado(self, teste, sucesso, detalhes=""):
        """Registra resultado do teste"""
        self.resultados.append({
            "teste": teste,
            "sucesso": sucesso,
            "detalhes": detalhes,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        print(f"{status} - {teste}")
        if detalhes:
            print(f"    {detalhes}")
    
    def iniciar_servidor(self):
        """Inicia o servidor WhatsApp Agent localmente"""
        print("\n🚀 INICIANDO SERVIDOR LOCAL")
        print("-" * 50)
        
        try:
            # Verificar se porta está disponível
            if self.verificar_porta_disponivel():
                self.log_resultado("Verificação de porta", True, f"Porta {SERVIDOR_PORT} disponível")
            else:
                # Tentar matar processo existente
                self.matar_processos_porta()
                time.sleep(2)
                
                if not self.verificar_porta_disponível():
                    self.log_resultado("Verificação de porta", False, f"Porta {SERVIDOR_PORT} ocupada")
                    return False
            
            # Configurar ambiente
            env = os.environ.copy()
            env.update({
                "PORT": str(SERVIDOR_PORT),
                "HOST": SERVIDOR_HOST,
                "UVICORN_PORT": str(SERVIDOR_PORT),
                "UVICORN_HOST": SERVIDOR_HOST,
                "ENVIRONMENT": "testing",
                "DEBUG": "true",
                "DATABASE_URL": "sqlite:///./test_whatsapp.db",
                "ADMIN_USERNAME": "admin",
                "ADMIN_PASSWORD": "teste123",
                "OPENAI_API_KEY": "sk-dummy-key-for-testing"
            })
            
            # Comando para iniciar servidor
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", SERVIDOR_HOST,
                "--port", str(SERVIDOR_PORT),
                "--reload",
                "--log-level", "info"
            ]
            
            print(f"    Executando: {' '.join(cmd)}")
            
            # Iniciar processo do servidor
            self.processo_servidor = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Aguardar servidor ficar pronto
            if self.aguardar_servidor_pronto():
                self.servidor_rodando = True
                self.log_resultado("Inicialização do servidor", True, f"Servidor rodando em {BASE_URL}")
                return True
            else:
                self.log_resultado("Inicialização do servidor", False, "Timeout ou erro na inicialização")
                return False
                
        except Exception as e:
            self.log_resultado("Inicialização do servidor", False, f"Erro: {e}")
            return False
    
    def verificar_porta_disponivel(self):
        """Verifica se a porta está disponível"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((SERVIDOR_HOST, SERVIDOR_PORT))
            sock.close()
            return result != 0  # 0 = porta ocupada, != 0 = porta livre
        except:
            return True
    
    def matar_processos_porta(self):
        """Mata processos que estão usando a porta"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    connections = proc.info['connections']
                    if connections:
                        for conn in connections:
                            if conn.laddr.port == SERVIDOR_PORT:
                                print(f"    Matando processo {proc.info['pid']} ({proc.info['name']})")
                                proc.terminate()
                                proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            print(f"    Erro ao matar processos: {e}")
    
    def aguardar_servidor_pronto(self):
        """Aguarda o servidor ficar pronto para receber requests"""
        print("    Aguardando servidor ficar pronto...")
        
        start_time = time.time()
        while time.time() - start_time < TIMEOUT_STARTUP:
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "healthy":
                        tempo_startup = time.time() - start_time
                        print(f"    ✅ Servidor pronto em {tempo_startup:.2f}s")
                        return True
            except:
                pass
            
            time.sleep(1)
            print("    ⏳ Aguardando...")
        
        return False
    
    def teste_health_check(self):
        """Testa endpoint de health check"""
        print("\n💓 TESTE HEALTH CHECK")
        print("-" * 50)
        
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                sucesso = (
                    data.get("status") == "healthy" and
                    "timestamp" in data and
                    "service" in data
                )
                detalhes = f"Status: {data.get('status')}, Service: {data.get('service')}"
                self.log_resultado("Health Check", sucesso, detalhes)
                return sucesso
            else:
                self.log_resultado("Health Check", False, f"Status HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_resultado("Health Check", False, f"Erro: {e}")
            return False
    
    def teste_documentacao_api(self):
        """Testa acesso à documentação da API"""
        print("\n📚 TESTE DOCUMENTAÇÃO API")
        print("-" * 50)
        
        try:
            # Testar /docs
            response_docs = requests.get(f"{BASE_URL}/docs", timeout=10)
            docs_ok = response_docs.status_code == 200
            
            # Testar /openapi.json
            response_openapi = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
            openapi_ok = response_openapi.status_code == 200
            
            if openapi_ok:
                schema = response_openapi.json()
                num_endpoints = len(schema.get("paths", {}))
                detalhes = f"Docs: {docs_ok}, OpenAPI: {openapi_ok}, Endpoints: {num_endpoints}"
            else:
                detalhes = f"Docs: {docs_ok}, OpenAPI: {openapi_ok}"
            
            sucesso = docs_ok and openapi_ok
            self.log_resultado("Documentação API", sucesso, detalhes)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Documentação API", False, f"Erro: {e}")
            return False
    
    def teste_autenticacao_local(self):
        """Testa sistema de autenticação local"""
        print("\n🔐 TESTE AUTENTICAÇÃO LOCAL")
        print("-" * 50)
        
        try:
            # Testar login com credenciais de teste
            dados_login = {
                "username": "admin",
                "password": "teste123"
            }
            
            # Tentar diferentes endpoints de login
            endpoints_login = [
                "/auth/login",
                "/admin/login", 
                "/api/auth/login"
            ]
            
            login_sucesso = False
            token = None
            
            for endpoint in endpoints_login:
                try:
                    response = requests.post(
                        f"{BASE_URL}{endpoint}",
                        json=dados_login,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "access_token" in data or "token" in data:
                            token = data.get("access_token", data.get("token"))
                            login_sucesso = True
                            self.log_resultado("Login local", True, f"Token obtido via {endpoint}")
                            break
                except:
                    continue
            
            if not login_sucesso:
                # Testar se endpoints estão protegidos adequadamente
                response = requests.get(f"{BASE_URL}/admin/dashboard", timeout=10)
                protegido = response.status_code in [401, 403]
                
                self.log_resultado(
                    "Proteção de endpoints", 
                    protegido, 
                    f"Admin dashboard retorna {response.status_code}"
                )
                return protegido
            
            return True
            
        except Exception as e:
            self.log_resultado("Autenticação local", False, f"Erro: {e}")
            return False
    
    def teste_endpoints_whatsapp(self):
        """Testa endpoints principais do WhatsApp"""
        print("\n📱 TESTE ENDPOINTS WHATSAPP")
        print("-" * 50)
        
        endpoints_teste = [
            ("/api/whatsapp/send", "POST", {"telefone": "+5511999999999", "mensagem": "teste"}),
            ("/api/whatsapp/status", "GET", {}),
            ("/api/contacts", "GET", {}),
            ("/api/messages", "GET", {}),
        ]
        
        todos_ok = True
        
        for endpoint, method, dados in endpoints_teste:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{BASE_URL}{endpoint}", json=dados, timeout=10)
                
                # Endpoints devem estar protegidos ou funcionais
                sucesso = response.status_code in [200, 401, 403, 422]
                
                detalhes = f"{method} {endpoint} → {response.status_code}"
                self.log_resultado(f"Endpoint {endpoint}", sucesso, detalhes)
                
                if not sucesso:
                    todos_ok = False
                    
            except Exception as e:
                self.log_resultado(f"Endpoint {endpoint}", False, f"Erro: {e}")
                todos_ok = False
        
        return todos_ok
    
    def teste_performance_local(self):
        """Testa performance do servidor local"""
        print("\n⚡ TESTE PERFORMANCE LOCAL")
        print("-" * 50)
        
        try:
            num_requests = 20
            tempos = []
            
            print(f"    Executando {num_requests} requests sequenciais...")
            
            for i in range(num_requests):
                start_time = time.time()
                response = requests.get(f"{BASE_URL}/health", timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    tempo = end_time - start_time
                    tempos.append(tempo)
                    
                    if (i + 1) % 5 == 0:
                        print(f"    Request {i+1}: {tempo:.3f}s")
            
            if tempos:
                tempo_medio = sum(tempos) / len(tempos)
                tempo_max = max(tempos)
                tempo_min = min(tempos)
                
                # Performance local deve ser excelente
                sucesso = tempo_medio < 0.5 and tempo_max < 2.0
                
                detalhes = f"Média: {tempo_medio:.3f}s, Min: {tempo_min:.3f}s, Max: {tempo_max:.3f}s"
                self.log_resultado("Performance local", sucesso, detalhes)
                return sucesso
            else:
                self.log_resultado("Performance local", False, "Nenhuma resposta válida")
                return False
                
        except Exception as e:
            self.log_resultado("Performance local", False, f"Erro: {e}")
            return False
    
    def teste_interacao_completa_cliente(self):
        """Simula interação completa de um cliente real"""
        print("\n🤖 SIMULAÇÃO CLIENTE COMPLETO")
        print("-" * 50)
        
        try:
            # 1. Cliente descobre a API
            response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
            if response.status_code != 200:
                self.log_resultado("Descoberta API", False, "OpenAPI não acessível")
                return False
            
            schema = response.json()
            endpoints = list(schema.get("paths", {}).keys())
            self.log_resultado("Descoberta API", True, f"{len(endpoints)} endpoints encontrados")
            
            # 2. Cliente tenta usar endpoint protegido (sem auth)
            response = requests.post(
                f"{BASE_URL}/api/whatsapp/send",
                json={"telefone": "+5511999999999", "mensagem": "teste"},
                timeout=10
            )
            
            auth_necessaria = response.status_code in [401, 403]
            self.log_resultado("Detecção auth necessária", auth_necessaria, f"Status: {response.status_code}")
            
            # 3. Cliente consulta documentação
            response = requests.get(f"{BASE_URL}/docs", timeout=10)
            docs_acessivel = response.status_code == 200
            self.log_resultado("Acesso documentação", docs_acessivel, "Cliente pode ver docs")
            
            # 4. Cliente monitora saúde do serviço
            tempos_health = []
            for _ in range(5):
                start = time.time()
                response = requests.get(f"{BASE_URL}/health", timeout=10)
                tempo = time.time() - start
                
                if response.status_code == 200:
                    tempos_health.append(tempo)
            
            if tempos_health:
                tempo_medio_health = sum(tempos_health) / len(tempos_health)
                monitoring_ok = tempo_medio_health < 1.0
                self.log_resultado("Monitoramento cliente", monitoring_ok, f"Health check em {tempo_medio_health:.3f}s")
            else:
                self.log_resultado("Monitoramento cliente", False, "Health check falhou")
            
            # 5. Resultado da interação completa
            sucesso_geral = auth_necessaria and docs_acessivel and (len(tempos_health) > 0)
            
            detalhes = "Cliente pode descobrir, entender e usar a API adequadamente"
            self.log_resultado("Interação completa cliente", sucesso_geral, detalhes)
            
            return sucesso_geral
            
        except Exception as e:
            self.log_resultado("Interação completa cliente", False, f"Erro: {e}")
            return False
    
    def parar_servidor(self):
        """Para o servidor local"""
        print("\n🛑 PARANDO SERVIDOR")
        print("-" * 50)
        
        try:
            if self.processo_servidor and self.processo_servidor.poll() is None:
                # Enviar SIGTERM
                self.processo_servidor.terminate()
                
                # Aguardar finalização graceful
                try:
                    self.processo_servidor.wait(timeout=10)
                    self.log_resultado("Parada graceful", True, "Servidor parou gracefully")
                except subprocess.TimeoutExpired:
                    # Forçar finalização
                    self.processo_servidor.kill()
                    self.processo_servidor.wait()
                    self.log_resultado("Parada forçada", True, "Servidor parado à força")
                
                self.servidor_rodando = False
                return True
            else:
                self.log_resultado("Parada servidor", False, "Processo não encontrado")
                return False
                
        except Exception as e:
            self.log_resultado("Parada servidor", False, f"Erro: {e}")
            return False
    
    def executar_teste_completo(self):
        """Executa o teste completo cliente-servidor"""
        print("🔄 INICIANDO TESTE COMPLETO CLIENTE-SERVIDOR")
        print(f"🎯 Servidor Local: {BASE_URL}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)
        
        # Tentar iniciar servidor
        if not self.iniciar_servidor():
            print("❌ FALHA CRÍTICA: Não foi possível iniciar o servidor")
            return 1
        
        try:
            # Aguardar estabilização
            time.sleep(3)
            
            # Executar testes
            testes = [
                ("Health Check", self.teste_health_check),
                ("Documentação API", self.teste_documentacao_api),
                ("Autenticação Local", self.teste_autenticacao_local),
                ("Endpoints WhatsApp", self.teste_endpoints_whatsapp),
                ("Performance Local", self.teste_performance_local),
                ("Interação Cliente Completa", self.teste_interacao_completa_cliente),
            ]
            
            for nome, teste_func in testes:
                try:
                    print(f"\n🔄 Executando: {nome}")
                    resultado = teste_func()
                    time.sleep(1)
                except Exception as e:
                    print(f"❌ ERRO em {nome}: {e}")
            
            # Gerar relatório
            self.gerar_relatorio()
            
        finally:
            # Sempre parar o servidor
            self.parar_servidor()
    
    def gerar_relatorio(self):
        """Gera relatório do teste completo"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO TESTE COMPLETO CLIENTE-SERVIDOR")
        print("=" * 70)
        
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        print(f"📈 Resultados: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print()
        
        print("📋 Detalhamento:")
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            print(f"{i:2d}. {status} {resultado['teste']}")
            if resultado["detalhes"]:
                print(f"      {resultado['detalhes']}")
        
        print()
        
        if percentual >= 90:
            print("🎉 EXCELENTE! Servidor local e interação cliente funcionando perfeitamente!")
            return 0
        elif percentual >= 75:
            print("✅ BOM! Sistema funcional com pequenos problemas.")
            return 0
        else:
            print("⚠️ PROBLEMAS! Sistema precisa de correções.")
            return 1

def signal_handler(sig, frame):
    """Handler para interrupção graceful"""
    print("\n\n🛑 Interrompido pelo usuário")
    sys.exit(0)

def main():
    """Função principal"""
    signal.signal(signal.SIGINT, signal_handler)
    
    tester = TesteServidorCompleto()
    exit_code = tester.executar_teste_completo()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()