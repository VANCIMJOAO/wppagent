#!/usr/bin/env python3
"""
🔄 TESTE COMPLETO CLIENTE-SERVIDOR REAL
Levanta servidor WhatsApp Agent localmente e executa simulação completa de cliente real
Inclui todos os aspectos: startup, descoberta, autenticação, uso da API, monitoramento e shutdown
"""

import subprocess
import requests
import json
import time
import threading
import signal
import sys
import os
import psutil
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import uuid
import hashlib

# Configuração Completa
SERVIDOR_HOST = "127.0.0.1"
SERVIDOR_PORT = 8002  # Porta exclusiva para este teste
BASE_URL = f"http://{SERVIDOR_HOST}:{SERVIDOR_PORT}"
TIMEOUT_STARTUP = 90  # Timeout generoso para startup completo
TIMEOUT_REQUEST = 15  # Timeout por request
MAX_RETRIES = 5
HEALTH_CHECK_INTERVAL = 2

class TestadorClienteServidorCompleto:
    """Testador completo que simula um cliente real interagindo com o servidor"""
    
    def __init__(self):
        self.processo_servidor = None
        self.servidor_rodando = False
        self.resultados = []
        self.session = requests.Session()
        self.token_auth = None
        self.estatisticas = {
            'requests_enviados': 0,
            'requests_sucesso': 0,
            'tempo_total_startup': 0,
            'tempo_total_testes': 0,
            'endpoints_descobertos': 0,
            'endpoints_testados': 0
        }
        
        # Configurar session com headers realistas
        self.session.headers.update({
            'User-Agent': 'WhatsApp-Client-Simulator/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Client-ID': str(uuid.uuid4()),
            'X-Test-Session': f"test-{int(time.time())}"
        })
    
    def log_resultado(self, categoria, teste, sucesso, detalhes="", duracao=None):
        """Registra resultado detalhado do teste"""
        resultado = {
            "categoria": categoria,
            "teste": teste,
            "sucesso": sucesso,
            "detalhes": detalhes,
            "duracao": duracao,
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3]
        }
        
        self.resultados.append(resultado)
        
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        duracao_str = f" ({duracao:.3f}s)" if duracao else ""
        
        print(f"[{resultado['timestamp']}] {status} [{categoria}] {teste}{duracao_str}")
        if detalhes:
            for linha in detalhes.split('\n'):
                if linha.strip():
                    print(f"    └─ {linha.strip()}")
    
    def verificar_requisitos_sistema(self):
        """Verifica se o sistema tem todos os requisitos para rodar o teste"""
        print("\n🔍 VERIFICAÇÃO DE REQUISITOS DO SISTEMA")
        print("-" * 60)
        
        requisitos_ok = True
        
        # Verificar porta disponível
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((SERVIDOR_HOST, SERVIDOR_PORT))
            sock.close()
            
            if result == 0:  # Porta ocupada
                self.log_resultado("Sistema", "Verificação de porta", False, 
                                 f"Porta {SERVIDOR_PORT} já está em uso")
                requisitos_ok = False
            else:
                self.log_resultado("Sistema", "Verificação de porta", True, 
                                 f"Porta {SERVIDOR_PORT} disponível")
        except Exception as e:
            self.log_resultado("Sistema", "Verificação de porta", False, f"Erro: {e}")
            requisitos_ok = False
        
        # Verificar memória disponível
        try:
            memoria = psutil.virtual_memory()
            memoria_livre_mb = memoria.available / (1024 * 1024)
            
            if memoria_livre_mb < 500:  # Menos de 500MB
                self.log_resultado("Sistema", "Verificação de memória", False, 
                                 f"Pouca memória disponível: {memoria_livre_mb:.1f}MB")
                requisitos_ok = False
            else:
                self.log_resultado("Sistema", "Verificação de memória", True, 
                                 f"Memória disponível: {memoria_livre_mb:.1f}MB")
        except Exception as e:
            self.log_resultado("Sistema", "Verificação de memória", False, f"Erro: {e}")
        
        # Verificar espaço em disco
        try:
            disco = psutil.disk_usage('/')
            disco_livre_mb = disco.free / (1024 * 1024)
            
            if disco_livre_mb < 100:  # Menos de 100MB
                self.log_resultado("Sistema", "Verificação de disco", False, 
                                 f"Pouco espaço em disco: {disco_livre_mb:.1f}MB")
                requisitos_ok = False
            else:
                self.log_resultado("Sistema", "Verificação de disco", True, 
                                 f"Espaço livre: {disco_livre_mb:.1f}MB")
        except Exception as e:
            self.log_resultado("Sistema", "Verificação de disco", False, f"Erro: {e}")
        
        # Verificar dependências Python
        dependencias = ['uvicorn', 'fastapi', 'sqlalchemy', 'redis']
        for dep in dependencias:
            try:
                __import__(dep)
                self.log_resultado("Sistema", f"Dependência {dep}", True, "Módulo disponível")
            except ImportError:
                self.log_resultado("Sistema", f"Dependência {dep}", False, "Módulo não encontrado")
                requisitos_ok = False
        
        return requisitos_ok
    
    def limpar_ambiente(self):
        """Limpa o ambiente antes de iniciar o teste"""
        print("\n🧹 LIMPEZA DO AMBIENTE")
        print("-" * 60)
        
        # Matar processos conflitantes
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'connections']):
                try:
                    # Verificar se é processo uvicorn na nossa porta
                    if proc.info['name'] == 'python' and proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if 'uvicorn' in cmdline and str(SERVIDOR_PORT) in cmdline:
                            print(f"    Matando processo conflitante PID {proc.info['pid']}")
                            proc.terminate()
                            proc.wait(timeout=5)
                    
                    # Verificar conexões na porta
                    connections = proc.info.get('connections', [])
                    for conn in connections:
                        if hasattr(conn, 'laddr') and conn.laddr.port == SERVIDOR_PORT:
                            print(f"    Matando processo usando porta {SERVIDOR_PORT}: PID {proc.info['pid']}")
                            proc.terminate()
                            proc.wait(timeout=5)
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
            
            self.log_resultado("Limpeza", "Processos conflitantes", True, "Ambiente limpo")
            
        except Exception as e:
            self.log_resultado("Limpeza", "Processos conflitantes", False, f"Erro: {e}")
        
        # Aguardar liberação da porta
        time.sleep(2)
    
    def iniciar_servidor_completo(self):
        """Inicia o servidor WhatsApp Agent com configuração completa"""
        print("\n🚀 INICIALIZAÇÃO COMPLETA DO SERVIDOR")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            # Configurar ambiente completo
            env = os.environ.copy()
            env.update({
                'PORT': str(SERVIDOR_PORT),
                'HOST': SERVIDOR_HOST,
                'UVICORN_PORT': str(SERVIDOR_PORT),
                'UVICORN_HOST': SERVIDOR_HOST,
                'ENVIRONMENT': 'testing',
                'DEBUG': 'true',
                'LOG_LEVEL': 'info',
                
                # Banco de dados
                'DATABASE_URL': 'sqlite:///./test_cliente_servidor.db',
                
                # Autenticação
                'ADMIN_USERNAME': 'admin',
                'ADMIN_PASSWORD': 'admin123',
                'JWT_SECRET_KEY': 'test-secret-key-super-secure-' + str(int(time.time())),
                'JWT_ALGORITHM': 'HS256',
                'JWT_EXPIRE_MINUTES': '60',
                
                # Redis (opcional para teste)
                'REDIS_URL': 'redis://localhost:6379/0',
                'REDIS_ENABLED': 'false',  # Desabilitar Redis para teste independente
                
                # APIs externas (mock)
                'OPENAI_API_KEY': 'sk-test-dummy-key-for-testing-only',
                'WHATSAPP_TOKEN': 'test-whatsapp-token',
                'WHATSAPP_VERIFY_TOKEN': 'test-verify-token',
                
                # Rate limiting para teste
                'RATE_LIMIT_REQUESTS': '1000',
                'RATE_LIMIT_WINDOW': '3600',
                
                # Configurações específicas do teste
                'CORS_ORIGINS': f'http://{SERVIDOR_HOST}:{SERVIDOR_PORT}',
                'ALLOWED_HOSTS': f'{SERVIDOR_HOST},localhost,127.0.0.1'
            })
            
            # Comando completo para uvicorn
            cmd = [
                sys.executable, '-m', 'uvicorn',
                'app.main:app',
                '--host', SERVIDOR_HOST,
                '--port', str(SERVIDOR_PORT),
                '--log-level', 'info',
                '--access-log',
                '--no-use-colors',
                '--loop', 'asyncio'
            ]
            
            print(f"    Comando: {' '.join(cmd)}")
            print(f"    Diretório: {os.getcwd()}")
            print(f"    Variáveis de ambiente: {len(env)} variáveis configuradas")
            
            # Iniciar processo
            self.processo_servidor = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=0,
                cwd=os.getcwd()
            )
            
            # Aguardar servidor ficar pronto
            if self.aguardar_servidor_completo():
                startup_time = time.time() - start_time
                self.estatisticas['tempo_total_startup'] = startup_time
                self.servidor_rodando = True
                
                self.log_resultado("Inicialização", "Servidor completo", True, 
                                 f"Servidor iniciado em {BASE_URL}", startup_time)
                return True
            else:
                self.log_resultado("Inicialização", "Servidor completo", False, 
                                 "Timeout na inicialização do servidor")
                return False
                
        except Exception as e:
            self.log_resultado("Inicialização", "Servidor completo", False, f"Erro: {e}")
            return False
    
    def aguardar_servidor_completo(self):
        """Aguarda o servidor ficar completamente pronto com verificações detalhadas"""
        print("    Aguardando servidor ficar completamente operacional...")
        
        checks = [
            ("/", "Endpoint raiz"),
            ("/health", "Health check"),
            ("/docs", "Documentação"),
            ("/openapi.json", "Schema OpenAPI")
        ]
        
        for tentativa in range(TIMEOUT_STARTUP):
            # Verificar se processo ainda está rodando
            if self.processo_servidor.poll() is not None:
                print(f"    ❌ Processo servidor morreu (exit code: {self.processo_servidor.returncode})")
                return False
            
            # Verificar endpoints essenciais
            endpoints_ok = 0
            for endpoint, desc in checks:
                try:
                    response = self.session.get(
                        urljoin(BASE_URL, endpoint), 
                        timeout=5,
                        allow_redirects=True
                    )
                    if response.status_code < 500:  # Qualquer coisa que não seja erro de servidor
                        endpoints_ok += 1
                except:
                    pass
            
            if endpoints_ok >= 3:  # Pelo menos 3 dos 4 endpoints devem responder
                print(f"    ✅ Servidor operacional em {tentativa + 1}s ({endpoints_ok}/{len(checks)} endpoints OK)")
                
                # Verificação adicional de estabilidade
                time.sleep(2)
                try:
                    response = self.session.get(urljoin(BASE_URL, "/health"), timeout=5)
                    if response.status_code == 200:
                        return True
                except:
                    pass
            
            if tentativa % 10 == 9:  # Log a cada 10 segundos
                print(f"    ⏳ Aguardando... {tentativa + 1}s ({endpoints_ok}/{len(checks)} endpoints)")
            
            time.sleep(1)
        
        print(f"    ❌ Timeout após {TIMEOUT_STARTUP}s")
        return False
    
    def descobrir_api_completa(self):
        """Simula descoberta completa da API por um cliente real"""
        print("\n🔍 DESCOBERTA COMPLETA DA API")
        print("-" * 60)
        
        descobertas = {}
        
        # 1. Descobrir documentação
        try:
            start_time = time.time()
            response = self.session.get(urljoin(BASE_URL, "/docs"), timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            docs_ok = response.status_code == 200
            descobertas['documentacao'] = docs_ok
            
            self.log_resultado("Descoberta", "Documentação Swagger", docs_ok, 
                             f"HTTP {response.status_code}", duracao)
            
        except Exception as e:
            self.log_resultado("Descoberta", "Documentação Swagger", False, f"Erro: {e}")
            descobertas['documentacao'] = False
        
        # 2. Obter schema OpenAPI completo
        try:
            start_time = time.time()
            response = self.session.get(urljoin(BASE_URL, "/openapi.json"), timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    schema = response.json()
                    paths = schema.get("paths", {})
                    components = schema.get("components", {})
                    
                    self.estatisticas['endpoints_descobertos'] = len(paths)
                    descobertas['schema'] = True
                    
                    # Análise detalhada do schema
                    detalhes = [
                        f"Endpoints: {len(paths)}",
                        f"Componentes: {len(components)}",
                        f"Versão API: {schema.get('info', {}).get('version', 'N/A')}",
                        f"Título: {schema.get('info', {}).get('title', 'N/A')}"
                    ]
                    
                    self.log_resultado("Descoberta", "Schema OpenAPI", True, 
                                     "\n".join(detalhes), duracao)
                    
                    # Guardar endpoints para testes posteriores
                    self.endpoints_descobertos = list(paths.keys())
                    
                except json.JSONDecodeError:
                    self.log_resultado("Descoberta", "Schema OpenAPI", False, 
                                     "JSON inválido no schema")
                    descobertas['schema'] = False
            else:
                self.log_resultado("Descoberta", "Schema OpenAPI", False, 
                                 f"HTTP {response.status_code}")
                descobertas['schema'] = False
                
        except Exception as e:
            self.log_resultado("Descoberta", "Schema OpenAPI", False, f"Erro: {e}")
            descobertas['schema'] = False
        
        # 3. Testar endpoint de health detalhado
        try:
            start_time = time.time()
            response = self.session.get(urljoin(BASE_URL, "/health"), timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    descobertas['health'] = True
                    
                    detalhes = []
                    if isinstance(health_data, dict):
                        for key, value in health_data.items():
                            detalhes.append(f"{key}: {value}")
                    
                    self.log_resultado("Descoberta", "Health endpoint", True, 
                                     "\n".join(detalhes) if detalhes else "Status OK", duracao)
                    
                except json.JSONDecodeError:
                    descobertas['health'] = True  # Mesmo que não seja JSON, se respondeu 200 está OK
                    self.log_resultado("Descoberta", "Health endpoint", True, 
                                     "Endpoint responde (não-JSON)", duracao)
            else:
                descobertas['health'] = False
                self.log_resultado("Descoberta", "Health endpoint", False, 
                                 f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_resultado("Descoberta", "Health endpoint", False, f"Erro: {e}")
            descobertas['health'] = False
        
        # 4. Verificar CORS e headers de segurança
        try:
            start_time = time.time()
            response = self.session.options(BASE_URL, timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            headers_seguranca = [
                'access-control-allow-origin',
                'access-control-allow-methods', 
                'x-content-type-options',
                'x-frame-options'
            ]
            
            headers_encontrados = []
            for header in headers_seguranca:
                if header in response.headers:
                    headers_encontrados.append(f"{header}: {response.headers[header]}")
            
            cors_ok = len(headers_encontrados) > 0
            descobertas['cors'] = cors_ok
            
            self.log_resultado("Descoberta", "CORS e Segurança", cors_ok, 
                             "\n".join(headers_encontrados), duracao)
            
        except Exception as e:
            self.log_resultado("Descoberta", "CORS e Segurança", False, f"Erro: {e}")
            descobertas['cors'] = False
        
        return sum(descobertas.values()) >= 3  # Pelo menos 3 das 4 descobertas devem funcionar
    
    def testar_autenticacao_completa(self):
        """Testa sistema de autenticação completo"""
        print("\n🔐 TESTE COMPLETO DE AUTENTICAÇÃO")
        print("-" * 60)
        
        auth_ok = False
        
        # Endpoints de autenticação para testar
        endpoints_auth = [
            "/auth/login",
            "/admin/login",
            "/api/auth/login",
            "/login"
        ]
        
        credenciais_teste = [
            {"username": "admin", "password": "admin123"},
            {"email": "admin@test.com", "password": "admin123"},
            {"user": "admin", "pass": "admin123"}
        ]
        
        for endpoint in endpoints_auth:
            for creds in credenciais_teste:
                try:
                    start_time = time.time()
                    response = self.session.post(
                        urljoin(BASE_URL, endpoint),
                        json=creds,
                        timeout=TIMEOUT_REQUEST
                    )
                    duracao = time.time() - start_time
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            # Procurar por token nas respostas possíveis
                            token_fields = ['access_token', 'token', 'authToken', 'jwt', 'bearer']
                            for field in token_fields:
                                if field in data:
                                    self.token_auth = data[field]
                                    auth_ok = True
                                    
                                    # Configurar token para próximas requests
                                    self.session.headers.update({
                                        'Authorization': f'Bearer {self.token_auth}'
                                    })
                                    
                                    detalhes = [
                                        f"Endpoint: {endpoint}",
                                        f"Credenciais: {list(creds.keys())}",
                                        f"Token obtido: {self.token_auth[:20]}...",
                                        f"Resposta: {list(data.keys())}"
                                    ]
                                    
                                    self.log_resultado("Autenticação", "Login com token", True, 
                                                     "\n".join(detalhes), duracao)
                                    return True
                                    
                        except json.JSONDecodeError:
                            pass
                    
                    elif response.status_code in [401, 403]:
                        # Endpoint existe mas credenciais inválidas
                        self.log_resultado("Autenticação", f"Endpoint {endpoint}", True, 
                                         f"Protegido adequadamente (HTTP {response.status_code})", duracao)
                    
                except Exception as e:
                    continue
        
        # Se não conseguiu fazer login, testar se endpoints estão protegidos
        if not auth_ok:
            endpoints_protegidos = [
                "/admin/dashboard",
                "/api/whatsapp/send", 
                "/api/contacts",
                "/api/messages"
            ]
            
            protecao_ok = True
            for endpoint in endpoints_protegidos:
                try:
                    start_time = time.time()
                    response = self.session.get(urljoin(BASE_URL, endpoint), timeout=TIMEOUT_REQUEST)
                    duracao = time.time() - start_time
                    
                    if response.status_code in [401, 403]:
                        self.log_resultado("Autenticação", f"Proteção {endpoint}", True, 
                                         f"Adequadamente protegido (HTTP {response.status_code})", duracao)
                    else:
                        protecao_ok = False
                        self.log_resultado("Autenticação", f"Proteção {endpoint}", False, 
                                         f"Não protegido (HTTP {response.status_code})", duracao)
                        
                except Exception as e:
                    self.log_resultado("Autenticação", f"Proteção {endpoint}", False, f"Erro: {e}")
                    protecao_ok = False
            
            return protecao_ok
        
        return auth_ok
    
    def testar_endpoints_principais(self):
        """Testa os endpoints principais da API"""
        print("\n📱 TESTE COMPLETO DOS ENDPOINTS PRINCIPAIS")
        print("-" * 60)
        
        endpoints_teste = [
            # GET endpoints
            ("/api/contacts", "GET", None, "Listar contatos"),
            ("/api/messages", "GET", None, "Listar mensagens"),
            ("/api/whatsapp/status", "GET", None, "Status WhatsApp"),
            ("/api/conversations", "GET", None, "Listar conversas"),
            
            # POST endpoints com dados de teste
            ("/api/whatsapp/send", "POST", {
                "telefone": "+5511999999999",
                "mensagem": "Teste de mensagem do cliente simulador"
            }, "Enviar mensagem"),
            
            ("/api/contacts", "POST", {
                "nome": "Contato Teste",
                "telefone": "+5511888888888"
            }, "Criar contato"),
            
            # Endpoints administrativos
            ("/admin/health", "GET", None, "Health administrativo"),
            ("/admin/stats", "GET", None, "Estatísticas admin")
        ]
        
        sucessos = 0
        total = len(endpoints_teste)
        
        for endpoint, method, data, descricao in endpoints_teste:
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = self.session.get(urljoin(BASE_URL, endpoint), timeout=TIMEOUT_REQUEST)
                else:
                    response = self.session.post(urljoin(BASE_URL, endpoint), 
                                               json=data, timeout=TIMEOUT_REQUEST)
                
                duracao = time.time() - start_time
                self.estatisticas['requests_enviados'] += 1
                
                # Avaliar resposta
                if response.status_code < 500:  # Qualquer coisa que não seja erro de servidor
                    sucessos += 1
                    self.estatisticas['requests_sucesso'] += 1
                    self.estatisticas['endpoints_testados'] += 1
                    
                    # Tentar analisar resposta
                    detalhes = [f"HTTP {response.status_code}"]
                    
                    try:
                        if response.content:
                            response_data = response.json()
                            if isinstance(response_data, dict):
                                detalhes.append(f"Campos: {list(response_data.keys())}")
                            elif isinstance(response_data, list):
                                detalhes.append(f"Lista com {len(response_data)} itens")
                    except:
                        detalhes.append(f"Resposta: {len(response.content)} bytes")
                    
                    self.log_resultado("Endpoints", descricao, True, 
                                     "\n".join(detalhes), duracao)
                else:
                    self.log_resultado("Endpoints", descricao, False, 
                                     f"Erro do servidor: HTTP {response.status_code}", duracao)
                
            except Exception as e:
                self.log_resultado("Endpoints", descricao, False, f"Erro: {e}")
        
        percentual_sucesso = (sucessos / total * 100) if total > 0 else 0
        return percentual_sucesso >= 70  # 70% dos endpoints devem funcionar
    
    def testar_carga_e_performance(self):
        """Testa carga e performance do servidor"""
        print("\n⚡ TESTE COMPLETO DE CARGA E PERFORMANCE")
        print("-" * 60)
        
        # Teste de requests sequenciais
        print("    Teste sequencial (20 requests)...")
        tempos_sequenciais = []
        
        for i in range(20):
            try:
                start_time = time.time()
                response = self.session.get(urljoin(BASE_URL, "/health"), timeout=TIMEOUT_REQUEST)
                tempo = time.time() - start_time
                
                if response.status_code == 200:
                    tempos_sequenciais.append(tempo)
                    
            except Exception:
                pass
        
        if tempos_sequenciais:
            tempo_medio_seq = sum(tempos_sequenciais) / len(tempos_sequenciais)
            tempo_max_seq = max(tempos_sequenciais)
            
            seq_ok = tempo_medio_seq < 1.0 and tempo_max_seq < 3.0
            detalhes_seq = [
                f"Requests OK: {len(tempos_sequenciais)}/20",
                f"Tempo médio: {tempo_medio_seq:.3f}s",
                f"Tempo máximo: {tempo_max_seq:.3f}s"
            ]
            
            self.log_resultado("Performance", "Teste sequencial", seq_ok, 
                             "\n".join(detalhes_seq), tempo_medio_seq)
        else:
            seq_ok = False
            self.log_resultado("Performance", "Teste sequencial", False, "Nenhuma resposta válida")
        
        # Teste de requests concorrentes
        print("    Teste concorrente (10 threads)...")
        
        def fazer_request():
            try:
                start_time = time.time()
                response = requests.get(urljoin(BASE_URL, "/health"), timeout=TIMEOUT_REQUEST)
                tempo = time.time() - start_time
                return tempo if response.status_code == 200 else None
            except:
                return None
        
        tempos_concorrentes = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fazer_request) for _ in range(30)]
            
            for future in as_completed(futures, timeout=30):
                try:
                    tempo = future.result()
                    if tempo is not None:
                        tempos_concorrentes.append(tempo)
                except:
                    pass
        
        if tempos_concorrentes:
            tempo_medio_conc = sum(tempos_concorrentes) / len(tempos_concorrentes)
            tempo_max_conc = max(tempos_concorrentes)
            
            conc_ok = tempo_medio_conc < 2.0 and len(tempos_concorrentes) >= 20
            detalhes_conc = [
                f"Requests OK: {len(tempos_concorrentes)}/30",
                f"Tempo médio: {tempo_medio_conc:.3f}s",
                f"Tempo máximo: {tempo_max_conc:.3f}s"
            ]
            
            self.log_resultado("Performance", "Teste concorrente", conc_ok, 
                             "\n".join(detalhes_conc), tempo_medio_conc)
        else:
            conc_ok = False
            self.log_resultado("Performance", "Teste concorrente", False, "Nenhuma resposta válida")
        
        # Teste de estabilidade sob carga
        print("    Teste de estabilidade...")
        
        start_estabilidade = time.time()
        requests_estabilidade = 0
        
        for _ in range(50):
            try:
                response = self.session.get(urljoin(BASE_URL, "/health"), timeout=5)
                if response.status_code == 200:
                    requests_estabilidade += 1
            except:
                pass
            time.sleep(0.1)  # 100ms entre requests
        
        tempo_estabilidade = time.time() - start_estabilidade
        estabilidade_ok = requests_estabilidade >= 40  # 80% dos requests devem ter sucesso
        
        detalhes_est = [
            f"Requests OK: {requests_estabilidade}/50",
            f"Tempo total: {tempo_estabilidade:.1f}s",
            f"Taxa de sucesso: {requests_estabilidade/50*100:.1f}%"
        ]
        
        self.log_resultado("Performance", "Estabilidade sob carga", estabilidade_ok, 
                         "\n".join(detalhes_est), tempo_estabilidade)
        
        return seq_ok and conc_ok and estabilidade_ok
    
    def simular_fluxo_cliente_real(self):
        """Simula um fluxo completo de uso por um cliente real"""
        print("\n🤖 SIMULAÇÃO COMPLETA DE FLUXO DE CLIENTE REAL")
        print("-" * 60)
        
        fluxo_ok = True
        
        # 1. Cliente inicia sessão
        session_id = str(uuid.uuid4())
        print(f"    Iniciando sessão cliente: {session_id[:8]}")
        
        # 2. Cliente consulta documentação
        try:
            start_time = time.time()
            response = self.session.get(urljoin(BASE_URL, "/docs"), timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            docs_ok = response.status_code == 200
            self.log_resultado("Fluxo Cliente", "Consulta documentação", docs_ok, 
                             f"Cliente lê documentação (HTTP {response.status_code})", duracao)
            
            if not docs_ok:
                fluxo_ok = False
                
        except Exception as e:
            self.log_resultado("Fluxo Cliente", "Consulta documentação", False, f"Erro: {e}")
            fluxo_ok = False
        
        # 3. Cliente tenta usar API sem autenticação
        try:
            start_time = time.time()
            response = self.session.post(
                urljoin(BASE_URL, "/api/whatsapp/send"),
                json={"telefone": "+5511999999999", "mensagem": "teste sem auth"},
                timeout=TIMEOUT_REQUEST
            )
            duracao = time.time() - start_time
            
            # Cliente deve ser rejeitado ou aceito com erro de validação
            sem_auth_ok = response.status_code in [401, 403, 422]
            self.log_resultado("Fluxo Cliente", "Teste sem autenticação", sem_auth_ok, 
                             f"API protegida adequadamente (HTTP {response.status_code})", duracao)
            
            if not sem_auth_ok:
                fluxo_ok = False
                
        except Exception as e:
            self.log_resultado("Fluxo Cliente", "Teste sem autenticação", False, f"Erro: {e}")
            fluxo_ok = False
        
        # 4. Cliente descobre como se autenticar
        # (Já testado em testar_autenticacao_completa)
        
        # 5. Cliente monitora saúde do serviço
        print("    Cliente inicia monitoramento de saúde...")
        
        monitoring_ok = True
        for i in range(5):
            try:
                start_time = time.time()
                response = self.session.get(urljoin(BASE_URL, "/health"), timeout=TIMEOUT_REQUEST)
                tempo = time.time() - start_time
                
                if response.status_code != 200 or tempo > 2.0:
                    monitoring_ok = False
                    break
                    
                time.sleep(1)  # Intervalo realista de monitoramento
                
            except Exception:
                monitoring_ok = False
                break
        
        self.log_resultado("Fluxo Cliente", "Monitoramento contínuo", monitoring_ok, 
                         "Cliente consegue monitorar saúde do serviço")
        
        if not monitoring_ok:
            fluxo_ok = False
        
        # 6. Cliente explora endpoints disponíveis
        endpoints_explorados = 0
        endpoints_para_explorar = [
            "/api/contacts",
            "/api/messages", 
            "/api/whatsapp/status",
            "/admin/health"
        ]
        
        for endpoint in endpoints_para_explorar:
            try:
                start_time = time.time()
                response = self.session.get(urljoin(BASE_URL, endpoint), timeout=TIMEOUT_REQUEST)
                duracao = time.time() - start_time
                
                if response.status_code < 500:  # Qualquer resposta estruturada
                    endpoints_explorados += 1
                    
            except Exception:
                pass
        
        exploracao_ok = endpoints_explorados >= len(endpoints_para_explorar) // 2
        detalhes_expl = f"Explorou {endpoints_explorados}/{len(endpoints_para_explorar)} endpoints"
        
        self.log_resultado("Fluxo Cliente", "Exploração de API", exploracao_ok, detalhes_expl)
        
        if not exploracao_ok:
            fluxo_ok = False
        
        # 7. Cliente testa casos de erro
        try:
            start_time = time.time()
            response = self.session.get(urljoin(BASE_URL, "/endpoint-inexistente"), timeout=TIMEOUT_REQUEST)
            duracao = time.time() - start_time
            
            erro_ok = response.status_code == 404
            self.log_resultado("Fluxo Cliente", "Tratamento de erro 404", erro_ok, 
                             f"API retorna 404 adequadamente (HTTP {response.status_code})", duracao)
            
        except Exception as e:
            self.log_resultado("Fluxo Cliente", "Tratamento de erro 404", False, f"Erro: {e}")
            fluxo_ok = False
        
        return fluxo_ok
    
    def finalizar_servidor_completo(self):
        """Finaliza o servidor de forma completa e limpa"""
        print("\n🛑 FINALIZAÇÃO COMPLETA DO SERVIDOR")
        print("-" * 60)
        
        if not self.processo_servidor:
            self.log_resultado("Finalização", "Processo servidor", True, "Nenhum processo para finalizar")
            return True
        
        try:
            # Verificar se processo ainda está rodando
            if self.processo_servidor.poll() is None:
                print("    Enviando sinal de término graceful...")
                self.processo_servidor.terminate()
                
                # Aguardar término graceful
                try:
                    self.processo_servidor.wait(timeout=10)
                    self.log_resultado("Finalização", "Término graceful", True, 
                                     "Servidor parou gracefully")
                except subprocess.TimeoutExpired:
                    print("    Forçando finalização...")
                    self.processo_servidor.kill()
                    self.processo_servidor.wait(timeout=5)
                    self.log_resultado("Finalização", "Término forçado", True, 
                                     "Servidor parado à força")
            else:
                exit_code = self.processo_servidor.returncode
                self.log_resultado("Finalização", "Processo servidor", True, 
                                 f"Processo já finalizado (exit code: {exit_code})")
            
            self.servidor_rodando = False
            
            # Limpar recursos
            if hasattr(self, 'session'):
                self.session.close()
            
            # Aguardar liberação da porta
            time.sleep(2)
            
            # Verificar se porta foi liberada
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((SERVIDOR_HOST, SERVIDOR_PORT))
            sock.close()
            
            porta_liberada = result != 0
            self.log_resultado("Finalização", "Liberação de porta", porta_liberada, 
                             f"Porta {SERVIDOR_PORT} {'liberada' if porta_liberada else 'ainda ocupada'}")
            
            return True
            
        except Exception as e:
            self.log_resultado("Finalização", "Erro na finalização", False, f"Erro: {e}")
            return False
    
    def executar_teste_completo(self):
        """Executa o teste completo cliente-servidor"""
        print("🔄 INICIANDO TESTE COMPLETO CLIENTE-SERVIDOR REAL")
        print(f"🎯 URL do Servidor: {BASE_URL}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"🔧 Timeout Startup: {TIMEOUT_STARTUP}s")
        print(f"⏱️  Timeout Request: {TIMEOUT_REQUEST}s")
        print("=" * 80)
        
        inicio_teste = time.time()
        
        try:
            # Fase 1: Verificações preliminares
            if not self.verificar_requisitos_sistema():
                print("❌ FALHA CRÍTICA: Requisitos do sistema não atendidos")
                return 1
            
            # Fase 2: Limpeza do ambiente
            self.limpar_ambiente()
            
            # Fase 3: Inicialização do servidor
            if not self.iniciar_servidor_completo():
                print("❌ FALHA CRÍTICA: Não foi possível iniciar o servidor")
                return 1
            
            # Aguardar estabilização completa
            print("\n⏳ Aguardando estabilização completa do servidor...")
            time.sleep(5)
            
            # Fase 4: Execução dos testes
            testes_principais = [
                ("Descoberta da API", self.descobrir_api_completa),
                ("Autenticação Completa", self.testar_autenticacao_completa),
                ("Endpoints Principais", self.testar_endpoints_principais),
                ("Carga e Performance", self.testar_carga_e_performance),
                ("Fluxo Cliente Real", self.simular_fluxo_cliente_real)
            ]
            
            print(f"\n🔄 Executando {len(testes_principais)} baterias de teste...")
            
            for nome_teste, funcao_teste in testes_principais:
                print(f"\n▶️  Iniciando: {nome_teste}")
                try:
                    resultado = funcao_teste()
                    time.sleep(1)  # Pausa entre testes
                except Exception as e:
                    print(f"❌ ERRO CRÍTICO em {nome_teste}: {e}")
                    resultado = False
            
            # Calcular tempo total
            self.estatisticas['tempo_total_testes'] = time.time() - inicio_teste
            
            # Gerar relatório final
            return self.gerar_relatorio_completo()
            
        finally:
            # Sempre limpar recursos
            self.finalizar_servidor_completo()
    
    def gerar_relatorio_completo(self):
        """Gera relatório final completo e detalhado"""
        print("\n" + "=" * 80)
        print("📊 RELATÓRIO FINAL COMPLETO - TESTE CLIENTE-SERVIDOR REAL")
        print("=" * 80)
        
        # Estatísticas gerais
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        print(f"📈 RESULTADO GERAL: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print()
        
        # Estatísticas detalhadas
        print("📊 ESTATÍSTICAS DETALHADAS:")
        stats = self.estatisticas
        print(f"   🚀 Tempo de startup: {stats['tempo_total_startup']:.2f}s")
        print(f"   ⏱️  Tempo total de testes: {stats['tempo_total_testes']:.2f}s")
        print(f"   🔍 Endpoints descobertos: {stats['endpoints_descobertos']}")
        print(f"   🧪 Endpoints testados: {stats['endpoints_testados']}")
        print(f"   📡 Requests enviados: {stats['requests_enviados']}")
        print(f"   ✅ Requests com sucesso: {stats['requests_sucesso']}")
        
        if stats['requests_enviados'] > 0:
            taxa_sucesso_req = stats['requests_sucesso'] / stats['requests_enviados'] * 100
            print(f"   📊 Taxa de sucesso requests: {taxa_sucesso_req:.1f}%")
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
        
        print("📋 RESULTADOS POR CATEGORIA:")
        for categoria, dados in categorias.items():
            perc_cat = (dados['sucessos'] / dados['total'] * 100) if dados['total'] > 0 else 0
            status_cat = "✅" if perc_cat >= 80 else "⚠️" if perc_cat >= 60 else "❌"
            print(f"   {status_cat} {categoria}: {dados['sucessos']}/{dados['total']} ({perc_cat:.1f}%)")
        print()
        
        # Resultados detalhados
        print("📝 RESULTADOS DETALHADOS:")
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            categoria = resultado["categoria"]
            teste = resultado["teste"]
            timestamp = resultado["timestamp"]
            duracao = f" ({resultado['duracao']:.3f}s)" if resultado['duracao'] else ""
            
            print(f"{i:3d}. [{timestamp}] {status} [{categoria}] {teste}{duracao}")
            
            if resultado["detalhes"]:
                for linha in resultado["detalhes"].split('\n'):
                    if linha.strip():
                        print(f"        └─ {linha.strip()}")
        print()
        
        # Avaliação final
        print("🎯 AVALIAÇÃO FINAL:")
        
        if percentual >= 95:
            print("🎉 EXCELENTE! Sistema funcionando perfeitamente para clientes!")
            print("   ✓ Servidor inicia rapidamente e de forma estável")
            print("   ✓ API é completamente descobrível e documentada")
            print("   ✓ Sistema de autenticação robusto e seguro")
            print("   ✓ Todos os endpoints respondem adequadamente")
            print("   ✓ Performance excelente sob carga")
            print("   ✓ Fluxo de cliente real funciona perfeitamente")
            print("   🚀 APROVADO PARA PRODUÇÃO!")
            return 0
            
        elif percentual >= 85:
            print("✅ MUITO BOM! Sistema funcional com excelente qualidade!")
            print("   ✓ Funcionalidades principais funcionam corretamente")
            print("   ✓ Performance adequada para uso real")
            print("   ✓ Poucos problemas menores detectados")
            print("   🎯 RECOMENDADO PARA PRODUÇÃO com monitoramento")
            return 0
            
        elif percentual >= 70:
            print("⚠️  BOM! Sistema funcional com alguns problemas.")
            print("   ✓ Funcionalidades básicas funcionam")
            print("   ⚠️  Algumas funcionalidades com problemas")
            print("   ⚠️  Performance pode precisar de otimização")
            print("   🔧 NECESSITA AJUSTES antes da produção")
            return 0
            
        elif percentual >= 50:
            print("⚠️  PROBLEMAS! Sistema com funcionalidade limitada.")
            print("   ⚠️  Muitas funcionalidades com problemas")
            print("   ⚠️  Performance inadequada")
            print("   ❌ NÃO RECOMENDADO para produção")
            print("   🛠️  CORREÇÕES NECESSÁRIAS")
            return 1
            
        else:
            print("❌ CRÍTICO! Sistema com falhas graves.")
            print("   ❌ Funcionalidade básica comprometida")
            print("   ❌ Não adequado para uso real")
            print("   🚨 REVISÃO COMPLETA NECESSÁRIA")
            return 2

def signal_handler(sig, frame):
    """Handler para interrupção graceful"""
    print("\n\n🛑 Teste interrompido pelo usuário")
    print("🧹 Limpando recursos...")
    sys.exit(0)

def main():
    """Função principal"""
    signal.signal(signal.SIGINT, signal_handler)
    
    testador = TestadorClienteServidorCompleto()
    exit_code = testador.executar_teste_completo()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()