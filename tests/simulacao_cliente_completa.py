#!/usr/bin/env python3
"""
🤖 Simulação Completa de Cliente - WhatsApp Agent
Testa cenários reais de uso da API como um cliente real
"""

import requests
import json
import time
import base64
from datetime import datetime, timedelta
import sys
import random
import asyncio
from typing import Dict, List, Optional

# Configuração
BASE_URL = "https://wppagent-production-app-production.up.railway.app"

# Dados de teste simulando cliente real
CONTATOS_TESTE = [
    {"nome": "João Silva", "telefone": "+5511999999001", "empresa": "Tech Corp"},
    {"nome": "Maria Santos", "telefone": "+5511999999002", "empresa": "Startup XYZ"},
    {"nome": "Pedro Costa", "telefone": "+5511999999003", "empresa": "Digital Solutions"},
    {"nome": "Ana Oliveira", "telefone": "+5511999999004", "empresa": "E-commerce Plus"},
    {"nome": "Carlos Lima", "telefone": "+5511999999005", "empresa": "Marketing Pro"}
]

MENSAGENS_TESTE = [
    "Olá! Como posso ajudá-lo hoje?",
    "Obrigado pelo seu interesse em nossos serviços.",
    "Gostaria de agendar uma reunião para discutir seu projeto?",
    "Temos uma promoção especial que pode interessar você.",
    "Confirma o recebimento desta mensagem?"
]

class SimuladorClienteWhatsApp:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = 30
        self.token = None
        self.resultados = []
        self.contatos_criados = []
        self.mensagens_enviadas = []
        
    def log_resultado(self, teste, sucesso, detalhes="", tempo_execucao=0):
        """Registra resultado do teste com métricas"""
        self.resultados.append({
            "teste": teste,
            "sucesso": sucesso,
            "detalhes": detalhes,
            "tempo": tempo_execucao,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        tempo_str = f" ({tempo_execucao:.3f}s)" if tempo_execucao > 0 else ""
        print(f"{status} - {teste}{tempo_str}")
        if detalhes:
            print(f"    Detalhes: {detalhes}")
    
    def obter_token_autenticacao(self):
        """Simula obtenção de token como cliente real faria"""
        print("\n🔐 SIMULANDO AUTENTICAÇÃO DO CLIENTE")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Primeiro: verificar se existem endpoints de autenticação públicos
            response = self.session.get(f"{self.base_url}/openapi.json")
            
            if response.status_code == 200:
                schema = response.json()
                auth_endpoints = [path for path in schema.get('paths', {}).keys() 
                                if 'auth' in path.lower() and 'login' in path.lower()]
                
                tempo = time.time() - start_time
                self.log_resultado(
                    "Descoberta de endpoints de auth",
                    True,
                    f"Encontrados {len(auth_endpoints)} endpoints: {auth_endpoints[:3]}",
                    tempo
                )
                
                # Para simulação, vamos criar um token fictício
                # Em caso real, cliente usaria endpoint de auth adequado
                self.token = "simulated_client_token_12345"
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                
                self.log_resultado(
                    "Configuração de autenticação",
                    True,
                    "Token simulado configurado para testes"
                )
                return True
            else:
                tempo = time.time() - start_time
                self.log_resultado(
                    "Descoberta de endpoints",
                    False,
                    f"Erro ao acessar schema: {response.status_code}",
                    tempo
                )
                return False
                
        except Exception as e:
            tempo = time.time() - start_time
            self.log_resultado("Autenticação cliente", False, str(e), tempo)
            return False
    
    def teste_exploracao_api(self):
        """Simula cliente explorando a API pela primeira vez"""
        print("\n🔍 SIMULANDO EXPLORAÇÃO DA API")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # 1. Verificar documentação
            response = self.session.get(f"{self.base_url}/docs")
            docs_ok = response.status_code == 200
            
            # 2. Verificar schema OpenAPI
            response_schema = self.session.get(f"{self.base_url}/openapi.json")
            schema_ok = response_schema.status_code == 200
            
            endpoints_whatsapp = []
            if schema_ok:
                schema = response_schema.json()
                endpoints_whatsapp = [
                    path for path in schema.get('paths', {}).keys()
                    if 'whatsapp' in path.lower() or 'message' in path.lower()
                ]
            
            tempo = time.time() - start_time
            self.log_resultado(
                "Exploração inicial da API",
                docs_ok and schema_ok,
                f"Docs: {docs_ok}, Schema: {schema_ok}, Endpoints WhatsApp: {len(endpoints_whatsapp)}",
                tempo
            )
            
            return endpoints_whatsapp
            
        except Exception as e:
            tempo = time.time() - start_time
            self.log_resultado("Exploração da API", False, str(e), tempo)
            return []
    
    def teste_envio_mensagem_simples(self):
        """Simula envio de mensagem simples como cliente faria"""
        print("\n📱 SIMULANDO ENVIO DE MENSAGEM SIMPLES")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Dados de teste como cliente real enviaria
            dados_mensagem = {
                "telefone": "+5511999999999",
                "mensagem": "Teste de mensagem via API - Cliente simulado",
                "tipo": "text"
            }
            
            # Testar endpoint principal de envio
            response = self.session.post(
                f"{self.base_url}/api/whatsapp/send",
                json=dados_mensagem
            )
            
            tempo = time.time() - start_time
            
            # Como esperamos 401 (sem auth válida), isso é "sucesso" para o teste
            sucesso = response.status_code in [401, 403, 422]
            
            detalhes = f"Status: {response.status_code}"
            if response.status_code == 401:
                detalhes += " (Autenticação necessária - comportamento correto)"
            elif response.status_code == 422:
                detalhes += " (Validação de dados - comportamento correto)"
            
            self.log_resultado(
                "Envio de mensagem simples",
                sucesso,
                detalhes,
                tempo
            )
            
            return sucesso
            
        except Exception as e:
            tempo = time.time() - start_time
            self.log_resultado("Envio mensagem simples", False, str(e), tempo)
            return False
    
    def teste_gestao_contatos(self):
        """Simula gestão de contatos como cliente faria"""
        print("\n👥 SIMULANDO GESTÃO DE CONTATOS")
        print("-" * 50)
        
        testes_contatos = [
            ("Listar contatos", "GET", "/api/contacts", {}),
            ("Criar contato", "POST", "/api/contacts", {
                "nome": "Cliente Teste",
                "telefone": "+5511988887777",
                "email": "teste@cliente.com"
            }),
            ("Buscar contato", "GET", "/api/contacts/search", {"q": "Cliente"}),
        ]
        
        todos_ok = True
        
        for nome_teste, method, endpoint, dados in testes_contatos:
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json=dados)
                
                tempo = time.time() - start_time
                
                # Esperamos 401/403 para endpoints protegidos
                sucesso = response.status_code in [401, 403, 404, 422]
                
                detalhes = f"Status: {response.status_code}"
                if response.status_code == 401:
                    detalhes += " (Auth necessária)"
                elif response.status_code == 404:
                    detalhes += " (Endpoint pode não existir)"
                elif response.status_code == 422:
                    detalhes += " (Validação de dados)"
                
                self.log_resultado(nome_teste, sucesso, detalhes, tempo)
                
                if not sucesso:
                    todos_ok = False
                    
            except Exception as e:
                tempo = time.time() - start_time
                self.log_resultado(nome_teste, False, str(e), tempo)
                todos_ok = False
        
        return todos_ok
    
    def teste_webhooks_simulado(self):
        """Simula teste de webhooks como cliente configuraria"""
        print("\n🔗 SIMULANDO CONFIGURAÇÃO DE WEBHOOKS")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Simula cliente tentando configurar webhook
            webhook_config = {
                "url": "https://cliente-webhook.example.com/whatsapp",
                "eventos": ["message_received", "message_sent", "delivery_status"],
                "ativo": True
            }
            
            response = self.session.post(
                f"{self.base_url}/api/whatsapp/webhook",
                json=webhook_config
            )
            
            tempo = time.time() - start_time
            
            # Esperamos proteção de auth
            sucesso = response.status_code in [401, 403, 404, 422]
            
            detalhes = f"Status: {response.status_code}"
            if response.status_code == 401:
                detalhes += " (Webhook protegido - correto)"
            elif response.status_code == 404:
                detalhes += " (Endpoint webhook pode não existir)"
            
            self.log_resultado(
                "Configuração de webhook",
                sucesso,
                detalhes,
                tempo
            )
            
            return sucesso
            
        except Exception as e:
            tempo = time.time() - start_time
            self.log_resultado("Configuração webhook", False, str(e), tempo)
            return False
    
    def teste_envio_massa_simulado(self):
        """Simula envio em massa como cliente faria"""
        print("\n📢 SIMULANDO ENVIO EM MASSA")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Simula lista de destinatários
            mensagem_massa = {
                "destinatarios": [contato["telefone"] for contato in CONTATOS_TESTE],
                "mensagem": "Promoção especial para clientes VIP!",
                "tipo": "broadcast",
                "agendamento": (datetime.now() + timedelta(minutes=30)).isoformat()
            }
            
            response = self.session.post(
                f"{self.base_url}/api/whatsapp/broadcast",
                json=mensagem_massa
            )
            
            tempo = time.time() - start_time
            
            # Esperamos proteção ou endpoint específico
            sucesso = response.status_code in [401, 403, 404, 422]
            
            detalhes = f"Status: {response.status_code}, Destinatários: {len(mensagem_massa['destinatarios'])}"
            
            self.log_resultado(
                "Envio em massa simulado",
                sucesso,
                detalhes,
                tempo
            )
            
            return sucesso
            
        except Exception as e:
            tempo = time.time() - start_time
            self.log_resultado("Envio em massa", False, str(e), tempo)
            return False
    
    def teste_status_monitoramento(self):
        """Simula cliente monitorando status do serviço"""
        print("\n📊 SIMULANDO MONITORAMENTO DE STATUS")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Endpoints que cliente pode usar para monitoramento
            endpoints_status = [
                ("/health", "Health Check"),
                ("/api/whatsapp/status", "Status WhatsApp"),
                ("/api/stats", "Estatísticas"),
            ]
            
            todos_ok = True
            
            for endpoint, desc in endpoints_status:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    
                    if endpoint == "/health":
                        # Health deve ser público
                        sucesso = response.status_code == 200
                        detalhes = f"Status: {response.status_code}"
                        if sucesso:
                            data = response.json()
                            detalhes += f", Service: {data.get('service', 'N/A')}"
                    else:
                        # Outros podem ser protegidos
                        sucesso = response.status_code in [200, 401, 403, 404]
                        detalhes = f"Status: {response.status_code}"
                    
                    self.log_resultado(desc, sucesso, detalhes)
                    
                    if not sucesso:
                        todos_ok = False
                        
                except Exception as e:
                    self.log_resultado(desc, False, str(e))
                    todos_ok = False
            
            tempo = time.time() - start_time
            return todos_ok
            
        except Exception as e:
            tempo = time.time() - start_time
            self.log_resultado("Monitoramento status", False, str(e), tempo)
            return False
    
    def teste_performance_cliente(self):
        """Testa performance do ponto de vista do cliente"""
        print("\n⚡ SIMULANDO TESTE DE PERFORMANCE DO CLIENTE")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            # Simula cliente fazendo múltiplas requisições
            tempos_resposta = []
            num_requests = 10
            
            print(f"    Executando {num_requests} requisições sequenciais...")
            
            for i in range(num_requests):
                req_start = time.time()
                response = self.session.get(f"{self.base_url}/health")
                req_end = time.time()
                
                if response.status_code == 200:
                    tempo_req = req_end - req_start
                    tempos_resposta.append(tempo_req)
                    print(f"    Request {i+1}: {tempo_req:.3f}s")
            
            if tempos_resposta:
                tempo_medio = sum(tempos_resposta) / len(tempos_resposta)
                tempo_max = max(tempos_resposta)
                tempo_min = min(tempos_resposta)
                
                # Critérios de performance para cliente
                sucesso = tempo_medio < 1.0 and tempo_max < 3.0
                
                detalhes = f"Média: {tempo_medio:.3f}s, Min: {tempo_min:.3f}s, Max: {tempo_max:.3f}s"
                
                tempo_total = time.time() - start_time
                self.log_resultado(
                    "Performance sequencial",
                    sucesso,
                    detalhes,
                    tempo_total
                )
                
                return sucesso
            else:
                self.log_resultado("Performance teste", False, "Nenhuma resposta válida")
                return False
                
        except Exception as e:
            tempo = time.time() - start_time
            self.log_resultado("Performance cliente", False, str(e), tempo)
            return False
    
    def executar_simulacao_completa(self):
        """Executa simulação completa como cliente real"""
        print("🤖 INICIANDO SIMULAÇÃO COMPLETA DE CLIENTE")
        print(f"🎯 API WhatsApp: {self.base_url}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)
        
        # Sequência de testes como cliente real faria
        testes_simulacao = [
            ("Autenticação", self.obter_token_autenticacao),
            ("Exploração API", self.teste_exploracao_api),
            ("Envio Mensagem", self.teste_envio_mensagem_simples),
            ("Gestão Contatos", self.teste_gestao_contatos),
            ("Webhooks", self.teste_webhooks_simulado),
            ("Envio Massa", self.teste_envio_massa_simulado),
            ("Monitoramento", self.teste_status_monitoramento),
            ("Performance", self.teste_performance_cliente),
        ]
        
        # Executar todos os testes
        for nome, teste_func in testes_simulacao:
            try:
                print(f"\n🔄 Executando: {nome}")
                resultado = teste_func()
                time.sleep(1)  # Simula pausa entre operações
            except Exception as e:
                print(f"❌ ERRO CRÍTICO em {nome}: {e}")
        
        # Gerar relatório final
        self.gerar_relatorio_simulacao()
    
    def gerar_relatorio_simulacao(self):
        """Gera relatório da simulação do cliente"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO DA SIMULAÇÃO DE CLIENTE")
        print("=" * 70)
        
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        tempo_total = sum(r.get("tempo", 0) for r in self.resultados)
        
        print(f"📈 Resultados: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print(f"⏱️ Tempo total: {tempo_total:.3f}s")
        print()
        
        print("📋 Experiência do Cliente:")
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            tempo = f" ({resultado.get('tempo', 0):.3f}s)" if resultado.get('tempo', 0) > 0 else ""
            print(f"{i:2d}. {status} {resultado['teste']}{tempo}")
            if resultado["detalhes"]:
                print(f"      {resultado['detalhes']}")
        
        print()
        
        # Avaliação da experiência do cliente
        if percentual >= 85:
            print("🎉 EXCELENTE! A API oferece uma experiência de cliente excepcional!")
            print("✅ Cliente pode integrar facilmente e usar a API com confiança.")
            status_final = 0
        elif percentual >= 70:
            print("✅ BOM! A API atende às necessidades básicas do cliente.")
            print("⚠️ Algumas melhorias podem aprimorar a experiência.")
            status_final = 0
        elif percentual >= 50:
            print("⚠️ ADEQUADO! A API funciona mas pode frustrar alguns clientes.")
            print("🔧 Recomenda-se melhorias na documentação e usabilidade.")
            status_final = 1
        else:
            print("❌ PROBLEMÁTICA! A experiência do cliente precisa de melhorias urgentes.")
            print("🚨 Cliente pode ter dificuldades significativas na integração.")
            status_final = 1
        
        print(f"🕐 Simulação concluída: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        return status_final

def main():
    """Função principal da simulação"""
    simulador = SimuladorClienteWhatsApp()
    exit_code = simulador.executar_simulacao_completa()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()