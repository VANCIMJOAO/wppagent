#!/usr/bin/env python3
"""
🧪 Suite Completa de Testes E2E - WhatsApp Agent
Testando o ambiente Railway de produção
URL: https://wppagent-production-app-production.up.railway.app
"""

import requests
import json
import time
from datetime import datetime
import sys
import os
from urllib.parse import urljoin

# Configuração do Ambiente Railway de Produção
BASE_URL = "https://wppagent-production-app-production.up.railway.app"

class TestesWhatsAppAgent:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = 15
        self.resultados = []
        
    def log_resultado(self, teste, sucesso, detalhes=""):
        """Registra o resultado de um teste"""
        self.resultados.append({
            "teste": teste,
            "sucesso": sucesso,
            "detalhes": detalhes,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        status = "✅ SUCESSO" if sucesso else "❌ FALHA"
        print(f"{status} - {teste}")
        if detalhes:
            print(f"    Detalhes: {detalhes}")
    
    def teste_conectividade_basica(self):
        """Testa conectividade básica com o servidor"""
        print("\n🔗 TESTANDO CONECTIVIDADE BÁSICA")
        print("-" * 50)
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                tempo_resposta = response.elapsed.total_seconds()
                
                self.log_resultado(
                    "Conectividade básica",
                    True,
                    f"Status: {data['status']}, Tempo: {tempo_resposta:.3f}s"
                )
                return True
            else:
                self.log_resultado(
                    "Conectividade básica",
                    False,
                    f"Status HTTP: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_resultado("Conectividade básica", False, str(e))
            return False
    
    def teste_endpoints_publicos(self):
        """Testa endpoints públicos da API"""
        print("\n📡 TESTANDO ENDPOINTS PÚBLICOS")
        print("-" * 50)
        
        endpoints_publicos = [
            ("/health", "GET", "Endpoint de saúde"),
            ("/docs", "GET", "Documentação da API"),
            ("/openapi.json", "GET", "Schema OpenAPI"),
            ("/", "OPTIONS", "Preflight CORS")
        ]
        
        todos_ok = True
        
        for endpoint, method, descricao in endpoints_publicos:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                elif method == "OPTIONS":
                    response = self.session.options(f"{self.base_url}{endpoint}")
                
                sucesso = response.status_code in [200, 405]  # 405 é OK para alguns endpoints
                detalhes = f"Status: {response.status_code}"
                
                if endpoint == "/openapi.json" and sucesso:
                    try:
                        schema = response.json()
                        num_endpoints = len(schema.get('paths', {}))
                        detalhes += f", Endpoints: {num_endpoints}"
                    except:
                        pass
                
                self.log_resultado(descricao, sucesso, detalhes)
                if not sucesso:
                    todos_ok = False
                    
            except Exception as e:
                self.log_resultado(descricao, False, str(e))
                todos_ok = False
        
        return todos_ok
    
    def teste_headers_seguranca(self):
        """Testa headers de segurança"""
        print("\n🔒 TESTANDO HEADERS DE SEGURANÇA")
        print("-" * 50)
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            headers = response.headers
            
            headers_obrigatorios = {
                "content-security-policy": "Política de Segurança de Conteúdo",
                "x-content-type-options": "Proteção contra MIME sniffing",
                "x-frame-options": "Proteção contra clickjacking",
                "strict-transport-security": "HTTPS obrigatório",
                "x-xss-protection": "Proteção XSS",
                "referrer-policy": "Política de referência"
            }
            
            todos_ok = True
            
            for header, descricao in headers_obrigatorios.items():
                presente = header.lower() in [h.lower() for h in headers.keys()]
                self.log_resultado(descricao, presente, f"Header: {header}")
                if not presente:
                    todos_ok = False
            
            return todos_ok
            
        except Exception as e:
            self.log_resultado("Headers de segurança", False, str(e))
            return False
    
    def teste_rate_limiting(self):
        """Testa limitação de taxa de requisições"""
        print("\n⚡ TESTANDO RATE LIMITING")
        print("-" * 50)
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            headers = response.headers
            
            # Verifica headers de rate limiting
            rate_headers = [
                "x-ratelimit-limit",
                "x-ratelimit-remaining", 
                "x-ratelimit-window"
            ]
            
            headers_presentes = []
            for header in rate_headers:
                if header in headers:
                    headers_presentes.append(f"{header}: {headers[header]}")
            
            sucesso = len(headers_presentes) >= 2
            detalhes = ", ".join(headers_presentes) if headers_presentes else "Nenhum header encontrado"
            
            self.log_resultado("Rate limiting configurado", sucesso, detalhes)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Rate limiting", False, str(e))
            return False
    
    def teste_endpoints_autenticados(self):
        """Testa endpoints que requerem autenticação"""
        print("\n🔐 TESTANDO ENDPOINTS AUTENTICADOS")
        print("-" * 50)
        
        endpoints_auth = [
            "/admin/dashboard",
            "/api/whatsapp/send",
            "/api/contacts",
            "/api/messages"
        ]
        
        todos_ok = True
        
        for endpoint in endpoints_auth:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                
                # Endpoints autenticados devem retornar 401 ou 403
                sucesso = response.status_code in [401, 403]
                detalhes = f"Status: {response.status_code}"
                
                if response.status_code == 401:
                    detalhes += " (Não autorizado - correto)"
                elif response.status_code == 403:
                    detalhes += " (Proibido - correto)"
                else:
                    detalhes += " (Deveria ser 401/403)"
                
                self.log_resultado(f"Autenticação {endpoint}", sucesso, detalhes)
                if not sucesso:
                    todos_ok = False
                    
            except Exception as e:
                self.log_resultado(f"Endpoint {endpoint}", False, str(e))
                todos_ok = False
        
        return todos_ok
    
    def teste_performance(self):
        """Testa performance básica"""
        print("\n⚡ TESTANDO PERFORMANCE")
        print("-" * 50)
        
        tempos = []
        num_requests = 5
        
        try:
            for i in range(num_requests):
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/health")
                end_time = time.time()
                
                if response.status_code == 200:
                    tempo = end_time - start_time
                    tempos.append(tempo)
                    print(f"    Request {i+1}: {tempo:.3f}s")
            
            if tempos:
                tempo_medio = sum(tempos) / len(tempos)
                tempo_max = max(tempos)
                
                # Performance aceitável: < 2s média, < 5s máximo
                sucesso = tempo_medio < 2.0 and tempo_max < 5.0
                detalhes = f"Média: {tempo_medio:.3f}s, Máximo: {tempo_max:.3f}s"
                
                self.log_resultado("Performance básica", sucesso, detalhes)
                return sucesso
            else:
                self.log_resultado("Performance básica", False, "Nenhuma resposta válida")
                return False
                
        except Exception as e:
            self.log_resultado("Performance básica", False, str(e))
            return False
    
    def teste_disponibilidade_servicos(self):
        """Testa disponibilidade de serviços externos"""
        print("\n🌐 TESTANDO DISPONIBILIDADE DE SERVIÇOS")
        print("-" * 50)
        
        # Testa se a aplicação consegue se conectar com serviços externos
        # (através de endpoints que fazem verificações internas)
        
        try:
            # Endpoint que verifica conexões internas
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                
                # Se o health check passa, os serviços básicos estão OK
                sucesso = data.get("status") == "healthy"
                detalhes = f"Status dos serviços: {data.get('status', 'desconhecido')}"
                
                self.log_resultado("Disponibilidade de serviços", sucesso, detalhes)
                return sucesso
            else:
                self.log_resultado("Disponibilidade de serviços", False, f"Health check falhou: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_resultado("Disponibilidade de serviços", False, str(e))
            return False
    
    def executar_todos_testes(self):
        """Executa toda a suíte de testes"""
        print("🚀 INICIANDO SUITE COMPLETA DE TESTES E2E")
        print(f"🎯 Ambiente: {self.base_url}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)
        
        # Lista de todos os testes
        testes = [
            self.teste_conectividade_basica,
            self.teste_endpoints_publicos,
            self.teste_headers_seguranca,
            self.teste_rate_limiting,
            self.teste_endpoints_autenticados,
            self.teste_performance,
            self.teste_disponibilidade_servicos
        ]
        
        # Executa todos os testes
        for teste in testes:
            try:
                teste()
            except Exception as e:
                print(f"❌ ERRO CRÍTICO no teste {teste.__name__}: {e}")
        
        # Gera relatório final
        self.gerar_relatorio_final()
    
    def gerar_relatorio_final(self):
        """Gera relatório final dos testes"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("=" * 70)
        
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        print(f"📈 Resultados Gerais: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print()
        
        # Agrupa resultados por categoria
        print("📋 Detalhamento por Teste:")
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            print(f"{i:2d}. {status} {resultado['teste']}")
            if resultado["detalhes"]:
                print(f"      {resultado['detalhes']}")
        
        print()
        
        # Status final
        if percentual >= 90:
            print("🎉 EXCELENTE! O ambiente está funcionando perfeitamente!")
            status_final = 0
        elif percentual >= 75:
            print("✅ BOM! O ambiente está funcionando com pequenos problemas.")
            status_final = 0
        elif percentual >= 50:
            print("⚠️ ATENÇÃO! O ambiente tem problemas significativos.")
            status_final = 1
        else:
            print("❌ CRÍTICO! O ambiente tem falhas graves.")
            status_final = 1
        
        print(f"🕐 Finalizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        return status_final

def main():
    """Função principal"""
    tester = TestesWhatsAppAgent()
    exit_code = tester.executar_todos_testes()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()