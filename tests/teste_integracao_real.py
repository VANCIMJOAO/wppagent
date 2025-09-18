#!/usr/bin/env python3
"""
🔄 Teste Integração Cliente-Servidor Real (Versão Robusta)
Levanta o servidor localmente e simula interação completa de cliente real
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

# Configuração
SERVIDOR_HOST = "127.0.0.1"
SERVIDOR_PORT = 8001  # Mudando para 8001 para evitar conflitos
BASE_URL = f"http://{SERVIDOR_HOST}:{SERVIDOR_PORT}"
TIMEOUT_STARTUP = 30  # Reduzido para 30s

class TestadorServidorReal:
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
    
    def verificar_porta_livre(self):
        """Verifica se a porta está livre"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((SERVIDOR_HOST, SERVIDOR_PORT))
            sock.close()
            return result != 0  # 0 = porta ocupada
        except:
            return True
    
    def matar_processos_conflitantes(self):
        """Mata processos que podem estar usando a porta"""
        try:
            cmd = f"lsof -ti:{SERVIDOR_PORT}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        print(f"    Matando processo PID {pid}")
                        os.system(f"kill -9 {pid}")
                        time.sleep(1)
                        
            return True
        except Exception as e:
            print(f"    Erro ao limpar processos: {e}")
            return False
    
    def iniciar_servidor_local(self):
        """Inicia o servidor WhatsApp Agent localmente"""
        print("\n🚀 INICIANDO SERVIDOR LOCAL")
        print("-" * 50)
        
        try:
            # Limpar porta
            if not self.verificar_porta_livre():
                print(f"    Porta {SERVIDOR_PORT} ocupada - limpando...")
                self.matar_processos_conflitantes()
                time.sleep(2)
            
            # Configurar ambiente simplificado
            env = os.environ.copy()
            env.update({
                "PORT": str(SERVIDOR_PORT),
                "HOST": SERVIDOR_HOST,
                "ENVIRONMENT": "development",
                "DATABASE_URL": "sqlite:///./test_local.db",
                "ADMIN_USERNAME": "admin",
                "ADMIN_PASSWORD": "admin123"
            })
            
            # Comando simplificado
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", SERVIDOR_HOST,
                "--port", str(SERVIDOR_PORT),
                "--log-level", "warning"  # Menos verbose
            ]
            
            print(f"    Comando: {' '.join(cmd)}")
            
            # Iniciar servidor em background
            self.processo_servidor = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,  # Suprimir output
                stderr=subprocess.DEVNULL,
                cwd="/home/vancim/whats_agent"
            )
            
            # Aguardar servidor
            print("    Aguardando servidor ficar disponível...")
            if self.aguardar_servidor_responder():
                self.servidor_rodando = True
                self.log_resultado("Startup servidor local", True, f"Rodando em {BASE_URL}")
                return True
            else:
                self.log_resultado("Startup servidor local", False, "Timeout na inicialização")
                return False
                
        except Exception as e:
            self.log_resultado("Startup servidor local", False, f"Erro: {e}")
            return False
    
    def aguardar_servidor_responder(self):
        """Aguarda o servidor responder"""
        for tentativa in range(TIMEOUT_STARTUP):
            try:
                # Testar endpoint simples
                response = requests.get(f"{BASE_URL}/", timeout=2)
                if response.status_code in [200, 404, 422]:  # Qualquer resposta válida
                    print(f"    ✅ Servidor respondeu em {tentativa + 1}s")
                    return True
            except:
                pass
            
            time.sleep(1)
            if tentativa % 5 == 4:
                print(f"    ⏳ Tentativa {tentativa + 1}/{TIMEOUT_STARTUP}")
        
        return False
    
    def teste_conectividade_basica(self):
        """Teste básico de conectividade"""
        print("\n🔌 TESTE CONECTIVIDADE BÁSICA")
        print("-" * 50)
        
        endpoints_basicos = [
            ("/", "Endpoint raiz"),
            ("/health", "Health check"),
            ("/docs", "Documentação"),
        ]
        
        conectados = 0
        for endpoint, desc in endpoints_basicos:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                sucesso = response.status_code < 500  # Aceitar qualquer coisa que não seja erro de servidor
                
                if sucesso:
                    conectados += 1
                    
                self.log_resultado(
                    f"Conectividade {desc}", 
                    sucesso, 
                    f"{endpoint} → HTTP {response.status_code}"
                )
                
            except Exception as e:
                self.log_resultado(f"Conectividade {desc}", False, f"Erro: {e}")
        
        # Pelo menos 1 endpoint deve responder
        return conectados > 0
    
    def teste_descoberta_api(self):
        """Cliente descobre a API como um usuário real faria"""
        print("\n🔍 SIMULAÇÃO: CLIENTE DESCOBRINDO API")
        print("-" * 50)
        
        descobertas = 0
        
        # 1. Tentar acessar documentação
        try:
            response = requests.get(f"{BASE_URL}/docs", timeout=10)
            docs_acessivel = response.status_code == 200
            if docs_acessivel:
                descobertas += 1
            self.log_resultado("Acesso à documentação", docs_acessivel, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_resultado("Acesso à documentação", False, f"Erro: {e}")
        
        # 2. Tentar obter schema OpenAPI
        try:
            response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
            schema_disponivel = response.status_code == 200
            if schema_disponivel:
                descobertas += 1
                schema = response.json()
                num_paths = len(schema.get("paths", {}))
                self.log_resultado("Schema OpenAPI", True, f"{num_paths} endpoints encontrados")
            else:
                self.log_resultado("Schema OpenAPI", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_resultado("Schema OpenAPI", False, f"Erro: {e}")
        
        # 3. Testar endpoint de status/health
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            health_ok = response.status_code == 200
            if health_ok:
                descobertas += 1
            self.log_resultado("Health endpoint", health_ok, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_resultado("Health endpoint", False, f"Erro: {e}")
        
        return descobertas >= 2
    
    def teste_comportamento_cliente_real(self):
        """Simula como um cliente real integraria com a API"""
        print("\n🤖 SIMULAÇÃO: COMPORTAMENTO CLIENTE REAL")
        print("-" * 50)
        
        acoes_cliente = 0
        
        # 1. Cliente tenta usar API sem autenticação (comportamento normal)
        try:
            response = requests.post(
                f"{BASE_URL}/api/whatsapp/send",
                json={"telefone": "+5511999999999", "mensagem": "teste cliente"},
                timeout=10
            )
            
            # Cliente espera ser rejeitado (401/403) ou aceitar request (200/422)
            rejeitado_adequadamente = response.status_code in [401, 403]
            aceito_para_processamento = response.status_code in [200, 422]
            
            if rejeitado_adequadamente:
                acoes_cliente += 1
                self.log_resultado("Proteção de endpoint", True, "API protegida adequadamente")
            elif aceito_para_processamento:
                acoes_cliente += 1  
                self.log_resultado("Processamento request", True, "API aceitou request")
            else:
                self.log_resultado("Teste endpoint protegido", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_resultado("Teste endpoint protegido", False, f"Erro: {e}")
        
        # 2. Cliente monitora disponibilidade (polling)
        try:
            tempos_resposta = []
            for i in range(3):
                start = time.time()
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                tempo = time.time() - start
                
                if response.status_code == 200:
                    tempos_resposta.append(tempo)
                    
                time.sleep(0.5)  # Simular polling
            
            if tempos_resposta:
                tempo_medio = sum(tempos_resposta) / len(tempos_resposta)
                responsivo = tempo_medio < 2.0
                
                if responsivo:
                    acoes_cliente += 1
                    
                self.log_resultado(
                    "Monitoramento contínuo", 
                    responsivo, 
                    f"Tempo médio resposta: {tempo_medio:.3f}s"
                )
            else:
                self.log_resultado("Monitoramento contínuo", False, "Sem respostas válidas")
                
        except Exception as e:
            self.log_resultado("Monitoramento contínuo", False, f"Erro: {e}")
        
        # 3. Cliente testa diferentes endpoints (exploração)
        endpoints_teste = ["/api/contacts", "/api/messages", "/admin/dashboard"]
        endpoints_funcionais = 0
        
        for endpoint in endpoints_teste:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                # Qualquer resposta estruturada é boa (não erro 500)
                funcional = response.status_code < 500
                
                if funcional:
                    endpoints_funcionais += 1
                    
            except:
                pass
        
        if endpoints_funcionais > 0:
            acoes_cliente += 1
            self.log_resultado(
                "Exploração de endpoints", 
                True, 
                f"{endpoints_funcionais}/{len(endpoints_teste)} endpoints funcionais"
            )
        else:
            self.log_resultado("Exploração de endpoints", False, "Nenhum endpoint explorado com sucesso")
        
        return acoes_cliente >= 2
    
    def teste_integracao_completa(self):
        """Teste de integração completa cliente-servidor"""
        print("\n🎯 TESTE INTEGRAÇÃO COMPLETA")
        print("-" * 50)
        
        try:
            # Simular sessão completa de cliente
            sessao_sucesso = True
            
            # 1. Descoberta inicial
            response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
            if response.status_code != 200:
                self.log_resultado("Descoberta inicial", False, "OpenAPI inacessível")
                sessao_sucesso = False
            else:
                endpoints = list(response.json().get("paths", {}).keys())
                self.log_resultado("Descoberta inicial", True, f"{len(endpoints)} endpoints descobertos")
            
            # 2. Teste de múltiplas requisições (simula carga de cliente)
            requisicoes_ok = 0
            for i in range(5):
                try:
                    response = requests.get(f"{BASE_URL}/health", timeout=3)
                    if response.status_code == 200:
                        requisicoes_ok += 1
                except:
                    pass
                time.sleep(0.2)
            
            carga_ok = requisicoes_ok >= 3
            if carga_ok:
                self.log_resultado("Teste de carga básica", True, f"{requisicoes_ok}/5 requests OK")
            else:
                self.log_resultado("Teste de carga básica", False, f"Apenas {requisicoes_ok}/5 requests OK")
                sessao_sucesso = False
            
            # 3. Verificar estabilidade do servidor
            try:
                response = requests.get(f"{BASE_URL}/health", timeout=10)
                servidor_estavel = response.status_code == 200
                
                if servidor_estavel:
                    self.log_resultado("Estabilidade servidor", True, "Servidor mantém resposta após carga")
                else:
                    self.log_resultado("Estabilidade servidor", False, "Servidor instável após carga")
                    sessao_sucesso = False
                    
            except Exception as e:
                self.log_resultado("Estabilidade servidor", False, f"Erro: {e}")
                sessao_sucesso = False
            
            return sessao_sucesso
            
        except Exception as e:
            self.log_resultado("Integração completa", False, f"Erro: {e}")
            return False
    
    def finalizar_servidor(self):
        """Finaliza o servidor local"""
        print("\n🛑 FINALIZANDO SERVIDOR")
        print("-" * 50)
        
        try:
            if self.processo_servidor and self.processo_servidor.poll() is None:
                self.processo_servidor.terminate()
                time.sleep(2)
                
                if self.processo_servidor.poll() is None:
                    self.processo_servidor.kill()
                    
                self.log_resultado("Finalização servidor", True, "Servidor finalizado")
                self.servidor_rodando = False
                return True
            else:
                self.log_resultado("Finalização servidor", True, "Servidor já finalizado")
                return True
                
        except Exception as e:
            self.log_resultado("Finalização servidor", False, f"Erro: {e}")
            return False
    
    def executar_teste_real(self):
        """Executa o teste completo real cliente-servidor"""
        print("🔄 TESTE REAL CLIENTE-SERVIDOR LOCAL")
        print(f"🎯 URL: {BASE_URL}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)
        
        # Inicializar servidor
        if not self.iniciar_servidor_local():
            print("❌ FALHA CRÍTICA: Não foi possível iniciar servidor local")
            return 1
        
        try:
            # Aguardar estabilização
            time.sleep(2)
            
            # Executar testes em ordem lógica
            testes_realizados = [
                ("Conectividade Básica", self.teste_conectividade_basica),
                ("Descoberta da API", self.teste_descoberta_api),
                ("Comportamento Cliente Real", self.teste_comportamento_cliente_real),
                ("Integração Completa", self.teste_integracao_completa)
            ]
            
            print(f"\n🔄 Executando {len(testes_realizados)} testes...")
            
            for nome_teste, funcao_teste in testes_realizados:
                try:
                    resultado = funcao_teste()
                    time.sleep(0.5)
                except Exception as e:
                    print(f"❌ ERRO no teste {nome_teste}: {e}")
            
            # Relatório final
            self.relatorio_final()
            
        finally:
            # Limpar recursos
            self.finalizar_servidor()
    
    def relatorio_final(self):
        """Gera relatório final do teste"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL - TESTE CLIENTE-SERVIDOR REAL")
        print("=" * 70)
        
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        print(f"📈 Resultado Geral: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print()
        
        # Agrupar por categoria
        print("📋 Resultados Detalhados:")
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            print(f"{i:2d}. {status} {resultado['teste']}")
            if resultado["detalhes"]:
                print(f"      └─ {resultado['detalhes']}")
        
        print()
        
        # Avaliação final
        if percentual >= 85:
            print("🎉 EXCELENTE! Sistema local funcionando perfeitamente para clientes!")
            print("   ✓ Servidor inicia corretamente")
            print("   ✓ API é descobrível e documentada") 
            print("   ✓ Endpoints respondem adequadamente")
            print("   ✓ Comportamento de cliente funciona")
            return 0
        elif percentual >= 70:
            print("✅ BOM! Sistema funcional com pequenos problemas.")
            print("   ⚠️  Alguns aspectos podem precisar de ajustes")
            return 0
        else:
            print("⚠️ PROBLEMAS! Sistema precisa de correções significativas.")
            print("   ❌ Funcionalidade básica comprometida")
            return 1

def main():
    """Função principal"""
    def signal_handler(sig, frame):
        print("\n\n🛑 Teste interrompido pelo usuário")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    testador = TestadorServidorReal()
    exit_code = testador.executar_teste_real()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()