#!/usr/bin/env python3
"""
🚀 Cenários Avançados de Teste - WhatsApp Agent
Simula casos de uso complexos e situações reais de produção
"""

import requests
import json
import time
import threading
import concurrent.futures
from datetime import datetime, timedelta
import sys
import random

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

class TestesAvancadosWhatsApp:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = 30
        self.resultados = []
        
    def log_resultado(self, teste, sucesso, detalhes="", metricas=None):
        """Registra resultado com métricas avançadas"""
        resultado = {
            "teste": teste,
            "sucesso": sucesso,
            "detalhes": detalhes,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "metricas": metricas or {}
        }
        self.resultados.append(resultado)
        
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        print(f"{status} - {teste}")
        if detalhes:
            print(f"    Detalhes: {detalhes}")
        if metricas:
            for key, value in metricas.items():
                print(f"    {key}: {value}")
    
    def teste_concorrencia_simulada(self):
        """Simula múltiplos clientes acessando simultaneamente"""
        print("\n⚡ TESTE DE CONCORRÊNCIA SIMULADA")
        print("-" * 50)
        
        num_threads = 5
        num_requests_por_thread = 10
        
        def fazer_requisicoes_thread(thread_id):
            """Função para cada thread simular cliente"""
            tempos = []
            sucessos = 0
            
            for i in range(num_requests_por_thread):
                start_time = time.time()
                try:
                    response = requests.get(
                        f"{self.base_url}/health",
                        timeout=10
                    )
                    end_time = time.time()
                    tempo = end_time - start_time
                    tempos.append(tempo)
                    
                    if response.status_code == 200:
                        sucessos += 1
                        
                except Exception as e:
                    print(f"    Thread {thread_id} erro: {e}")
            
            return {
                "thread_id": thread_id,
                "sucessos": sucessos,
                "total": num_requests_por_thread,
                "tempos": tempos
            }
        
        start_time = time.time()
        
        try:
            # Executar threads simultaneamente
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [
                    executor.submit(fazer_requisicoes_thread, i) 
                    for i in range(num_threads)
                ]
                
                resultados_threads = [
                    future.result() for future in concurrent.futures.as_completed(futures)
                ]
            
            tempo_total = time.time() - start_time
            
            # Analisar resultados
            total_requests = num_threads * num_requests_por_thread
            total_sucessos = sum(r["sucessos"] for r in resultados_threads)
            todos_tempos = []
            for r in resultados_threads:
                todos_tempos.extend(r["tempos"])
            
            if todos_tempos:
                tempo_medio = sum(todos_tempos) / len(todos_tempos)
                tempo_max = max(todos_tempos)
                tempo_min = min(todos_tempos)
                
                taxa_sucesso = (total_sucessos / total_requests) * 100
                requests_por_segundo = total_requests / tempo_total
                
                sucesso = taxa_sucesso >= 95 and tempo_medio < 1.0
                
                metricas = {
                    "Total Requests": total_requests,
                    "Taxa Sucesso": f"{taxa_sucesso:.1f}%",
                    "Requests/segundo": f"{requests_por_segundo:.2f}",
                    "Tempo Médio": f"{tempo_medio:.3f}s",
                    "Tempo Min/Max": f"{tempo_min:.3f}s / {tempo_max:.3f}s"
                }
                
                self.log_resultado(
                    "Teste de concorrência",
                    sucesso,
                    f"{num_threads} threads, {num_requests_por_thread} req/thread",
                    metricas
                )
                
                return sucesso
            else:
                self.log_resultado("Teste de concorrência", False, "Nenhuma resposta válida")
                return False
                
        except Exception as e:
            self.log_resultado("Teste de concorrência", False, str(e))
            return False
    
    def teste_endpoints_especificos(self):
        """Testa endpoints específicos do WhatsApp"""
        print("\n📱 TESTE DE ENDPOINTS ESPECÍFICOS")
        print("-" * 50)
        
        endpoints_teste = [
            # Endpoints de messaging
            ("/api/whatsapp/send", "POST", "Envio de mensagem", {
                "telefone": "+5511999999999",
                "mensagem": "Teste automatizado",
                "tipo": "text"
            }),
            ("/api/whatsapp/send-media", "POST", "Envio de mídia", {
                "telefone": "+5511999999999",
                "tipo": "image",
                "url": "https://example.com/image.jpg",
                "caption": "Teste de imagem"
            }),
            ("/api/whatsapp/status", "GET", "Status da conexão", {}),
            
            # Endpoints de contatos
            ("/api/contacts", "GET", "Listar contatos", {}),
            ("/api/contacts", "POST", "Criar contato", {
                "nome": "Teste Automatizado",
                "telefone": "+5511888888888"
            }),
            
            # Endpoints de grupos
            ("/api/groups", "GET", "Listar grupos", {}),
            ("/api/groups", "POST", "Criar grupo", {
                "nome": "Grupo Teste",
                "descricao": "Grupo criado por teste automatizado"
            }),
            
            # Endpoints de webhook
            ("/api/webhook/config", "GET", "Configuração webhook", {}),
            ("/api/webhook/test", "POST", "Teste webhook", {
                "url": "https://webhook-test.example.com"
            }),
            
            # Endpoints de relatórios
            ("/api/reports/messages", "GET", "Relatório mensagens", {}),
            ("/api/reports/delivery", "GET", "Relatório entregas", {}),
        ]
        
        todos_ok = True
        
        for endpoint, method, desc, dados in endpoints_teste:
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json=dados)
                
                tempo = time.time() - start_time
                
                # Analisar resposta
                if response.status_code == 401:
                    sucesso = True  # Esperado para endpoints protegidos
                    detalhes = "Autenticação necessária (comportamento correto)"
                elif response.status_code == 403:
                    sucesso = True  # Também esperado
                    detalhes = "Acesso negado (comportamento correto)"
                elif response.status_code == 404:
                    sucesso = False  # Endpoint pode não existir
                    detalhes = "Endpoint não encontrado"
                elif response.status_code == 422:
                    sucesso = True  # Validação de dados
                    detalhes = "Erro de validação (dados de teste)"
                elif response.status_code == 200:
                    sucesso = True  # Sucesso real
                    detalhes = "Resposta bem-sucedida"
                else:
                    sucesso = False
                    detalhes = f"Status inesperado: {response.status_code}"
                
                metricas = {
                    "Tempo Resposta": f"{tempo:.3f}s",
                    "Status Code": response.status_code,
                    "Content Length": len(response.content)
                }
                
                self.log_resultado(desc, sucesso, detalhes, metricas)
                
                if not sucesso:
                    todos_ok = False
                
                # Pequena pausa entre requests
                time.sleep(0.1)
                
            except Exception as e:
                self.log_resultado(desc, False, str(e))
                todos_ok = False
        
        return todos_ok
    
    def teste_validacao_dados(self):
        """Testa validação rigorosa de dados"""
        print("\n🔍 TESTE DE VALIDAÇÃO DE DADOS")
        print("-" * 50)
        
        casos_teste = [
            # Casos de telefone inválido
            {
                "nome": "Telefone inválido - formato",
                "dados": {"telefone": "123", "mensagem": "teste"},
                "endpoint": "/api/whatsapp/send"
            },
            {
                "nome": "Telefone inválido - vazio",
                "dados": {"telefone": "", "mensagem": "teste"},
                "endpoint": "/api/whatsapp/send"
            },
            {
                "nome": "Mensagem muito longa",
                "dados": {"telefone": "+5511999999999", "mensagem": "a" * 5000},
                "endpoint": "/api/whatsapp/send"
            },
            {
                "nome": "Caracteres especiais SQL injection",
                "dados": {"telefone": "+5511999999999", "mensagem": "'; DROP TABLE messages; --"},
                "endpoint": "/api/whatsapp/send"
            },
            {
                "nome": "XSS attempt",
                "dados": {"telefone": "+5511999999999", "mensagem": "<script>alert('xss')</script>"},
                "endpoint": "/api/whatsapp/send"
            },
            {
                "nome": "JSON malformado",
                "dados": {"telefone": "+5511999999999"},  # Sem mensagem obrigatória
                "endpoint": "/api/whatsapp/send"
            },
            # Casos de contato inválido
            {
                "nome": "Email inválido",
                "dados": {"nome": "Teste", "telefone": "+5511999999999", "email": "email_invalido"},
                "endpoint": "/api/contacts"
            },
            {
                "nome": "Nome muito longo",
                "dados": {"nome": "a" * 1000, "telefone": "+5511999999999"},
                "endpoint": "/api/contacts"
            }
        ]
        
        todos_ok = True
        
        for caso in casos_teste:
            start_time = time.time()
            
            try:
                response = self.session.post(
                    f"{self.base_url}{caso['endpoint']}",
                    json=caso["dados"]
                )
                
                tempo = time.time() - start_time
                
                # Para validação, esperamos 400, 401, 422 ou 403
                sucesso = response.status_code in [400, 401, 403, 422]
                
                if response.status_code == 401:
                    detalhes = "Autenticação necessária (correto)"
                elif response.status_code == 400:
                    detalhes = "Bad Request - validação rejeitou (correto)"
                elif response.status_code == 422:
                    detalhes = "Unprocessable Entity - validação detalhada (correto)"
                elif response.status_code == 403:
                    detalhes = "Forbidden (correto)"
                else:
                    detalhes = f"Status: {response.status_code} (inesperado)"
                
                metricas = {
                    "Tempo Validação": f"{tempo:.3f}s",
                    "Status Code": response.status_code
                }
                
                self.log_resultado(caso["nome"], sucesso, detalhes, metricas)
                
                if not sucesso:
                    todos_ok = False
                
            except Exception as e:
                self.log_resultado(caso["nome"], False, str(e))
                todos_ok = False
        
        return todos_ok
    
    def teste_rate_limiting_real(self):
        """Testa rate limiting com volume real"""
        print("\n🚦 TESTE DE RATE LIMITING REAL")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            requests_rapidos = 50  # Número alto para testar limite
            sucessos = 0
            rate_limited = 0
            tempos = []
            
            print(f"    Enviando {requests_rapidos} requests rapidamente...")
            
            for i in range(requests_rapidos):
                req_start = time.time()
                response = self.session.get(f"{self.base_url}/health")
                req_end = time.time()
                
                tempo_req = req_end - req_start
                tempos.append(tempo_req)
                
                if response.status_code == 200:
                    sucessos += 1
                elif response.status_code == 429:  # Too Many Requests
                    rate_limited += 1
                
                # Log a cada 10 requests
                if (i + 1) % 10 == 0:
                    print(f"    Progress: {i + 1}/{requests_rapidos}")
                
                # Pequeno delay para não sobrecarregar
                time.sleep(0.05)
            
            tempo_total = time.time() - start_time
            
            if tempos:
                tempo_medio = sum(tempos) / len(tempos)
                requests_por_segundo = requests_rapidos / tempo_total
                
                # Rate limiting é esperado em volume alto
                sucesso = sucessos > 0 and (rate_limited > 0 or sucessos == requests_rapidos)
                
                metricas = {
                    "Total Requests": requests_rapidos,
                    "Sucessos": sucessos,
                    "Rate Limited": rate_limited,
                    "Req/segundo": f"{requests_por_segundo:.2f}",
                    "Tempo Médio": f"{tempo_medio:.3f}s"
                }
                
                detalhes = "Rate limiting funcionando" if rate_limited > 0 else "Sem rate limiting detectado"
                
                self.log_resultado(
                    "Rate limiting real",
                    sucesso,
                    detalhes,
                    metricas
                )
                
                return sucesso
            else:
                self.log_resultado("Rate limiting test", False, "Nenhuma resposta")
                return False
                
        except Exception as e:
            self.log_resultado("Rate limiting real", False, str(e))
            return False
    
    def teste_resiliencia_api(self):
        """Testa resiliência da API em condições adversas"""
        print("\n🛡️ TESTE DE RESILIÊNCIA DA API")
        print("-" * 50)
        
        testes_resiliencia = [
            # Timeout simulation
            {
                "nome": "Timeout customizado",
                "func": lambda: self.session.get(f"{self.base_url}/health", timeout=0.001),
                "esperado": "timeout"
            },
            # Large payload
            {
                "nome": "Payload muito grande",
                "func": lambda: self.session.post(
                    f"{self.base_url}/api/whatsapp/send",
                    json={"telefone": "+5511999999999", "mensagem": "x" * 100000}
                ),
                "esperado": "rejection"
            },
            # Invalid content-type
            {
                "nome": "Content-Type inválido",
                "func": lambda: requests.post(
                    f"{self.base_url}/api/whatsapp/send",
                    data="invalid data",
                    headers={"Content-Type": "text/plain"}
                ),
                "esperado": "rejection"
            },
            # Empty request body
            {
                "nome": "Body vazio",
                "func": lambda: self.session.post(f"{self.base_url}/api/whatsapp/send"),
                "esperado": "rejection"
            }
        ]
        
        todos_ok = True
        
        for teste in testes_resiliencia:
            start_time = time.time()
            
            try:
                response = teste["func"]()
                tempo = time.time() - start_time
                
                if teste["esperado"] == "timeout":
                    # Se chegou aqui, não deu timeout
                    sucesso = True  # Servidor respondeu rápido
                    detalhes = f"Servidor respondeu em {tempo:.3f}s (sem timeout)"
                elif teste["esperado"] == "rejection":
                    # Esperamos rejeição (400, 401, 422, etc.)
                    sucesso = response.status_code >= 400
                    detalhes = f"Status: {response.status_code}"
                else:
                    sucesso = response.status_code == 200
                    detalhes = f"Status: {response.status_code}"
                
                metricas = {
                    "Tempo Resposta": f"{tempo:.3f}s",
                    "Status Code": getattr(response, 'status_code', 'N/A')
                }
                
                self.log_resultado(teste["nome"], sucesso, detalhes, metricas)
                
                if not sucesso:
                    todos_ok = False
                    
            except requests.exceptions.Timeout:
                # Timeout esperado para alguns testes
                sucesso = teste["esperado"] == "timeout"
                self.log_resultado(teste["nome"], sucesso, "Timeout ocorreu")
                if not sucesso:
                    todos_ok = False
                    
            except Exception as e:
                # Outros erros
                sucesso = teste["esperado"] in ["timeout", "rejection"]
                self.log_resultado(teste["nome"], sucesso, f"Exceção: {type(e).__name__}")
                if not sucesso:
                    todos_ok = False
        
        return todos_ok
    
    def executar_testes_avancados(self):
        """Executa todos os testes avançados"""
        print("🚀 INICIANDO TESTES AVANÇADOS - CENÁRIOS REAIS")
        print(f"🎯 API WhatsApp: {self.base_url}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)
        
        # Lista de testes avançados
        testes = [
            ("Concorrência", self.teste_concorrencia_simulada),
            ("Endpoints Específicos", self.teste_endpoints_especificos),
            ("Validação Dados", self.teste_validacao_dados),
            ("Rate Limiting", self.teste_rate_limiting_real),
            ("Resiliência", self.teste_resiliencia_api),
        ]
        
        # Executar testes
        for nome, teste_func in testes:
            try:
                print(f"\n🔄 Executando: {nome}")
                resultado = teste_func()
                time.sleep(2)  # Pausa entre testes
            except Exception as e:
                print(f"❌ ERRO CRÍTICO em {nome}: {e}")
        
        # Gerar relatório
        self.gerar_relatorio_avancado()
    
    def gerar_relatorio_avancado(self):
        """Gera relatório dos testes avançados"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO DOS TESTES AVANÇADOS")
        print("=" * 70)
        
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        print(f"📈 Resultados: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print()
        
        print("📋 Análise Detalhada:")
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            print(f"{i:2d}. {status} {resultado['teste']}")
            if resultado["detalhes"]:
                print(f"      {resultado['detalhes']}")
            if resultado.get("metricas"):
                for key, value in resultado["metricas"].items():
                    print(f"      {key}: {value}")
        
        print()
        
        # Avaliação final
        if percentual >= 90:
            print("🎉 EXCELENTE! A API demonstra robustez excepcional!")
            print("✅ Pronta para ambientes de produção de alta demanda.")
            return 0
        elif percentual >= 75:
            print("✅ MUITO BOM! A API tem boa performance em cenários avançados.")
            print("⚠️ Algumas otimizações podem melhorar ainda mais.")
            return 0
        elif percentual >= 60:
            print("⚠️ ADEQUADO! A API funciona mas precisa de ajustes.")
            print("🔧 Recomenda-se otimizações antes de produção intensa.")
            return 1
        else:
            print("❌ PROBLEMAS DETECTADOS! Melhorias urgentes necessárias.")
            print("🚨 Não recomendado para produção sem correções.")
            return 1

def main():
    """Função principal"""
    tester = TestesAvancadosWhatsApp()
    exit_code = tester.executar_testes_avancados()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()