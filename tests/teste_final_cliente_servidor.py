#!/usr/bin/env python3
"""
🔄 TESTE FINAL CLIENTE-SERVIDOR REAL - VERSÃO ROBUSTA
Levanta servidor WhatsApp Agent localmente e executa simulação completa
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
from concurrent.futures import ThreadPoolExecutor
import tempfile

# Configuração
SERVIDOR_HOST = "127.0.0.1"
SERVIDOR_PORT = 8003  # Nova porta
BASE_URL = f"http://{SERVIDOR_HOST}:{SERVIDOR_PORT}"
TIMEOUT_STARTUP = 45
TIMEOUT_REQUEST = 10

class TestadorFinalClienteServidor:
    """Testador final robusto para cliente-servidor"""
    
    def __init__(self):
        self.processo_servidor = None
        self.servidor_rodando = False
        self.resultados = []
        self.log_file = None
        
    def log_resultado(self, categoria, teste, sucesso, detalhes="", duracao=None):
        """Registra resultado do teste"""
        resultado = {
            "categoria": categoria,
            "teste": teste,
            "sucesso": sucesso,
            "detalhes": detalhes,
            "duracao": duracao,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        self.resultados.append(resultado)
        
        status = "✅" if sucesso else "❌"
        duracao_str = f" ({duracao:.3f}s)" if duracao else ""
        
        print(f"[{resultado['timestamp']}] {status} [{categoria}] {teste}{duracao_str}")
        if detalhes:
            for linha in detalhes.split('\n'):
                if linha.strip():
                    print(f"    └─ {linha.strip()}")
    
    def verificar_porta_livre(self):
        """Verifica se a porta está livre"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((SERVIDOR_HOST, SERVIDOR_PORT))
            sock.close()
            return result != 0
        except:
            return True
    
    def iniciar_servidor_robusto(self):
        """Inicia servidor com configuração robusta"""
        print("\n🚀 INICIANDO SERVIDOR LOCAL ROBUSTO")
        print("-" * 60)
        
        # Verificar porta
        if not self.verificar_porta_livre():
            self.log_resultado("Inicialização", "Verificação porta", False, f"Porta {SERVIDOR_PORT} ocupada")
            return False
        
        # Criar arquivo de log temporário
        self.log_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log')
        
        try:
            # Ambiente simplificado mas funcional
            env = os.environ.copy()
            env.update({
                'PORT': str(SERVIDOR_PORT),
                'HOST': SERVIDOR_HOST,
                'ENVIRONMENT': 'testing',  # Ambiente de teste
                'SKIP_DATABASE_INIT': 'true',  # Pular inicialização do banco
                'REDIS_ENABLED': 'false',
                'LOG_LEVEL': 'WARNING',
                'OPENAI_API_KEY': 'sk-test-key',
                'ADMIN_USERNAME': 'admin',
                'ADMIN_PASSWORD': 'admin123'
            })
            
            # Comando simplificado
            cmd = [
                sys.executable, '-m', 'uvicorn',
                'app.main:app',
                '--host', SERVIDOR_HOST,
                '--port', str(SERVIDOR_PORT),
                '--log-level', 'warning'
            ]
            
            print(f"    Comando: {' '.join(cmd[:5])}...")
            print(f"    Log: {self.log_file.name}")
            
            # Iniciar processo
            self.processo_servidor = subprocess.Popen(
                cmd,
                env=env,
                stdout=self.log_file,
                stderr=subprocess.STDOUT,
                cwd=os.getcwd()
            )
            
            # Aguardar servidor
            start_time = time.time()
            if self.aguardar_servidor_responder():
                startup_time = time.time() - start_time
                self.servidor_rodando = True
                self.log_resultado("Inicialização", "Servidor local", True, 
                                 f"Operacional em {BASE_URL}", startup_time)
                return True
            else:
                # Mostrar logs de erro
                self.mostrar_logs_erro()
                self.log_resultado("Inicialização", "Servidor local", False, "Falha na inicialização")
                return False
                
        except Exception as e:
            self.log_resultado("Inicialização", "Servidor local", False, f"Erro: {e}")
            return False
    
    def aguardar_servidor_responder(self):
        """Aguarda servidor responder"""
        print("    Aguardando servidor responder...")
        
        for tentativa in range(TIMEOUT_STARTUP):
            # Verificar se processo está vivo
            if self.processo_servidor.poll() is not None:
                print(f"    ❌ Processo morreu (exit code: {self.processo_servidor.returncode})")
                return False
            
            # Testar conectividade
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=3)
                if response.status_code < 500:
                    print(f"    ✅ Servidor respondeu em {tentativa + 1}s")
                    return True
            except:
                pass
            
            # Testar endpoint raiz
            try:
                response = requests.get(BASE_URL, timeout=3)
                if response.status_code < 500:
                    print(f"    ✅ Servidor respondeu (raiz) em {tentativa + 1}s")
                    return True
            except:
                pass
            
            time.sleep(1)
            if tentativa % 10 == 9:
                print(f"    ⏳ Tentativa {tentativa + 1}/{TIMEOUT_STARTUP}")
        
        return False
    
    def mostrar_logs_erro(self):
        """Mostra logs de erro do servidor"""
        try:
            if self.log_file:
                self.log_file.flush()
                with open(self.log_file.name, 'r') as f:
                    logs = f.read().strip()
                    if logs:
                        print("    📋 Logs do servidor:")
                        for linha in logs.split('\n')[-10:]:  # Últimas 10 linhas
                            if linha.strip():
                                print(f"       {linha}")
        except:
            pass
    
    def testar_conectividade_basica(self):
        """Teste básico de conectividade"""
        print("\n🔌 TESTE CONECTIVIDADE BÁSICA")
        print("-" * 60)
        
        endpoints = [
            ("/", "Endpoint raiz"),
            ("/health", "Health check"),
            ("/docs", "Documentação")
        ]
        
        conectados = 0
        for endpoint, desc in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT_REQUEST)
                duracao = time.time() - start_time
                
                sucesso = response.status_code < 500
                if sucesso:
                    conectados += 1
                
                self.log_resultado("Conectividade", desc, sucesso, 
                                 f"HTTP {response.status_code}", duracao)
                
            except Exception as e:
                self.log_resultado("Conectividade", desc, False, f"Erro: {e}")
        
        return conectados >= 2  # Pelo menos 2 endpoints devem responder
    
    def descobrir_api_cliente(self):
        """Cliente descobre a API"""
        print("\n🔍 DESCOBERTA DA API PELO CLIENTE")
        print("-" * 60)
        
        descobertas = 0
        
        # 1. Documentação
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            docs_ok = response.status_code == 200
            if docs_ok:
                descobertas += 1
            
            self.log_resultado("Descoberta", "Documentação", docs_ok, 
                             f"HTTP {response.status_code}", duracao)
            
        except Exception as e:
            self.log_resultado("Descoberta", "Documentação", False, f"Erro: {e}")
        
        # 2. Schema OpenAPI
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    schema = response.json()
                    endpoints = len(schema.get("paths", {}))
                    descobertas += 1
                    
                    self.log_resultado("Descoberta", "Schema OpenAPI", True, 
                                     f"{endpoints} endpoints descobertos", duracao)
                except:
                    self.log_resultado("Descoberta", "Schema OpenAPI", False, 
                                     "JSON inválido", duracao)
            else:
                self.log_resultado("Descoberta", "Schema OpenAPI", False, 
                                 f"HTTP {response.status_code}", duracao)
                
        except Exception as e:
            self.log_resultado("Descoberta", "Schema OpenAPI", False, f"Erro: {e}")
        
        # 3. Health check
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            health_ok = response.status_code == 200
            if health_ok:
                descobertas += 1
                
                try:
                    data = response.json()
                    status = data.get("status", "unknown")
                    detalhes = f"Status: {status}"
                except:
                    detalhes = "Resposta OK"
            else:
                detalhes = f"HTTP {response.status_code}"
            
            self.log_resultado("Descoberta", "Health check", health_ok, detalhes, duracao)
            
        except Exception as e:
            self.log_resultado("Descoberta", "Health check", False, f"Erro: {e}")
        
        return descobertas >= 2
    
    def testar_comportamento_cliente(self):
        """Simula comportamento real de cliente"""
        print("\n🤖 SIMULAÇÃO COMPORTAMENTO CLIENTE")
        print("-" * 60)
        
        comportamentos_ok = 0
        
        # 1. Cliente tenta usar API sem autenticação
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/whatsapp/send",
                json={"telefone": "+5511999999999", "mensagem": "teste"},
                timeout=TIMEOUT_REQUEST
            )
            duracao = time.time() - start_time
            
            # Deve ser rejeitado ou aceito com validação
            protegido = response.status_code in [401, 403, 422]
            if protegido:
                comportamentos_ok += 1
            
            self.log_resultado("Cliente", "Teste sem auth", protegido, 
                             f"API protegida (HTTP {response.status_code})", duracao)
            
        except Exception as e:
            self.log_resultado("Cliente", "Teste sem auth", False, f"Erro: {e}")
        
        # 2. Cliente monitora saúde
        try:
            tempos = []
            for i in range(3):
                start_time = time.time()
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                tempo = time.time() - start_time
                
                if response.status_code == 200:
                    tempos.append(tempo)
                time.sleep(0.5)
            
            if len(tempos) >= 2:
                comportamentos_ok += 1
                tempo_medio = sum(tempos) / len(tempos)
                self.log_resultado("Cliente", "Monitoramento", True, 
                                 f"Tempo médio: {tempo_medio:.3f}s")
            else:
                self.log_resultado("Cliente", "Monitoramento", False, "Falhas no monitoramento")
                
        except Exception as e:
            self.log_resultado("Cliente", "Monitoramento", False, f"Erro: {e}")
        
        # 3. Cliente explora endpoints
        endpoints_teste = ["/api/contacts", "/api/messages", "/admin/health"]
        explorados = 0
        
        for endpoint in endpoints_teste:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if response.status_code < 500:
                    explorados += 1
            except:
                pass
        
        if explorados > 0:
            comportamentos_ok += 1
            self.log_resultado("Cliente", "Exploração", True, 
                             f"Explorou {explorados}/{len(endpoints_teste)} endpoints")
        else:
            self.log_resultado("Cliente", "Exploração", False, "Nenhum endpoint explorado")
        
        return comportamentos_ok >= 2
    
    def testar_performance_local(self):
        """Teste de performance local"""
        print("\n⚡ TESTE PERFORMANCE LOCAL")
        print("-" * 60)
        
        # Teste sequencial
        tempos = []
        for i in range(10):
            try:
                start_time = time.time()
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                tempo = time.time() - start_time
                
                if response.status_code == 200:
                    tempos.append(tempo)
            except:
                pass
        
        if tempos:
            tempo_medio = sum(tempos) / len(tempos)
            tempo_max = max(tempos)
            
            performance_ok = tempo_medio < 1.0 and len(tempos) >= 8
            
            detalhes = [
                f"Sucessos: {len(tempos)}/10",
                f"Tempo médio: {tempo_medio:.3f}s",
                f"Tempo máximo: {tempo_max:.3f}s"
            ]
            
            self.log_resultado("Performance", "Teste sequencial", performance_ok, 
                             "\n".join(detalhes), tempo_medio)
            return performance_ok
        else:
            self.log_resultado("Performance", "Teste sequencial", False, "Nenhuma resposta")
            return False
    
    def testar_integracao_completa(self):
        """Teste de integração final"""
        print("\n🎯 TESTE INTEGRAÇÃO FINAL")
        print("-" * 60)
        
        integracao_ok = True
        
        # 1. Verificar estabilidade
        try:
            for i in range(5):
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                if response.status_code != 200:
                    integracao_ok = False
                    break
                time.sleep(0.2)
            
            self.log_resultado("Integração", "Estabilidade", integracao_ok, 
                             "Servidor mantém resposta consistente")
        except:
            integracao_ok = False
            self.log_resultado("Integração", "Estabilidade", False, "Servidor instável")
        
        # 2. Teste de erro 404
        try:
            response = requests.get(f"{BASE_URL}/endpoint-inexistente", timeout=5)
            erro_ok = response.status_code == 404
            
            self.log_resultado("Integração", "Tratamento 404", erro_ok, 
                             f"HTTP {response.status_code}")
            
            if not erro_ok:
                integracao_ok = False
        except:
            self.log_resultado("Integração", "Tratamento 404", False, "Erro na request")
            integracao_ok = False
        
        return integracao_ok
    
    def parar_servidor(self):
        """Para o servidor"""
        print("\n🛑 FINALIZANDO SERVIDOR")
        print("-" * 60)
        
        try:
            if self.processo_servidor and self.processo_servidor.poll() is None:
                self.processo_servidor.terminate()
                
                try:
                    self.processo_servidor.wait(timeout=10)
                    self.log_resultado("Finalização", "Término graceful", True, "Servidor parado")
                except subprocess.TimeoutExpired:
                    self.processo_servidor.kill()
                    self.log_resultado("Finalização", "Término forçado", True, "Servidor morto")
            else:
                self.log_resultado("Finalização", "Servidor", True, "Já estava parado")
            
            # Limpar log file
            if self.log_file:
                try:
                    self.log_file.close()
                    os.unlink(self.log_file.name)
                except:
                    pass
            
            return True
            
        except Exception as e:
            self.log_resultado("Finalização", "Erro", False, f"Erro: {e}")
            return False
    
    def executar_teste_final(self):
        """Executa o teste final completo"""
        print("🔄 TESTE FINAL CLIENTE-SERVIDOR REAL")
        print(f"🎯 URL: {BASE_URL}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)
        
        try:
            # Inicializar servidor
            if not self.iniciar_servidor_robusto():
                print("❌ FALHA CRÍTICA: Servidor não iniciou")
                return 1
            
            # Aguardar estabilização
            time.sleep(3)
            
            # Executar testes
            testes = [
                ("Conectividade Básica", self.testar_conectividade_basica),
                ("Descoberta da API", self.descobrir_api_cliente),
                ("Comportamento Cliente", self.testar_comportamento_cliente),
                ("Performance Local", self.testar_performance_local),
                ("Integração Final", self.testar_integracao_completa)
            ]
            
            print(f"\n🔄 Executando {len(testes)} baterias de teste...")
            
            for nome, funcao in testes:
                print(f"\n▶️  {nome}...")
                try:
                    funcao()
                    time.sleep(1)
                except Exception as e:
                    print(f"❌ ERRO em {nome}: {e}")
            
            # Relatório final
            return self.gerar_relatorio_final()
            
        finally:
            self.parar_servidor()
    
    def gerar_relatorio_final(self):
        """Gera relatório final"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL - TESTE CLIENTE-SERVIDOR")
        print("=" * 70)
        
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        print(f"📈 RESULTADO: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print()
        
        # Resultados por categoria
        categorias = {}
        for resultado in self.resultados:
            cat = resultado['categoria']
            if cat not in categorias:
                categorias[cat] = {'total': 0, 'sucessos': 0}
            categorias[cat]['total'] += 1
            if resultado['sucesso']:
                categorias[cat]['sucessos'] += 1
        
        print("📋 Por categoria:")
        for categoria, dados in categorias.items():
            perc = (dados['sucessos'] / dados['total'] * 100) if dados['total'] > 0 else 0
            status = "✅" if perc >= 80 else "⚠️" if perc >= 60 else "❌"
            print(f"   {status} {categoria}: {dados['sucessos']}/{dados['total']} ({perc:.1f}%)")
        print()
        
        # Detalhamento
        print("📝 Detalhes:")
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            duracao = f" ({resultado['duracao']:.3f}s)" if resultado['duracao'] else ""
            print(f"{i:2d}. {status} [{resultado['categoria']}] {resultado['teste']}{duracao}")
            
            if resultado["detalhes"]:
                for linha in resultado["detalhes"].split('\n'):
                    if linha.strip():
                        print(f"       └─ {linha.strip()}")
        print()
        
        # Avaliação
        if percentual >= 90:
            print("🎉 EXCELENTE! Sistema funcionando perfeitamente!")
            print("   ✓ Servidor local operacional")
            print("   ✓ Cliente pode descobrir e usar a API")
            print("   ✓ Performance adequada")
            print("   ✓ Integração completa funcional")
            print("   🚀 APROVADO para uso!")
            return 0
        elif percentual >= 75:
            print("✅ BOM! Sistema funcional com qualidade!")
            print("   ✓ Funcionalidades principais OK")
            print("   ⚠️  Alguns aspectos podem melhorar")
            print("   👍 RECOMENDADO para uso")
            return 0
        elif percentual >= 60:
            print("⚠️  ACEITÁVEL! Sistema funciona mas tem problemas.")
            print("   ⚠️  Várias funcionalidades com issues")
            print("   🔧 PRECISA de melhorias")
            return 1
        else:
            print("❌ PROBLEMÁTICO! Sistema com muitas falhas.")
            print("   ❌ Funcionalidade comprometida")
            print("   🛠️  CORREÇÕES URGENTES necessárias")
            return 2

def main():
    """Função principal"""
    def signal_handler(sig, frame):
        print("\n\n🛑 Teste interrompido")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    testador = TestadorFinalClienteServidor()
    exit_code = testador.executar_teste_final()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()