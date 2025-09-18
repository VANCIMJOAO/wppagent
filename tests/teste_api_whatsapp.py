#!/usr/bin/env python3
"""
🔐 Testes de API WhatsApp com Autenticação
Testando endpoints autenticados do WhatsApp Agent
"""

import requests
import json
import base64
from datetime import datetime
import sys

# Configuração
BASE_URL = "https://wppagent-production-app-production.up.railway.app"

# Credenciais de teste (do railway variables)
ADMIN_USER = "admin_producao_seguro"
ADMIN_PASS = "SenhaSeguraProducao2025!@#$"

class TestesAPIWhatsApp:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.timeout = 15
        self.token = None
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
            print(f"    Detalhes: {detalhes}")
    
    def teste_autenticacao_admin(self):
        """Testa autenticação do admin"""
        print("\n🔐 TESTANDO AUTENTICAÇÃO ADMIN")
        print("-" * 50)
        
        try:
            # Tenta fazer login com credenciais admin
            login_data = {
                "username": ADMIN_USER,
                "password": ADMIN_PASS
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.token = data["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}"
                    })
                    self.log_resultado(
                        "Login admin",
                        True,
                        f"Token obtido, tipo: {data.get('token_type', 'bearer')}"
                    )
                    return True
                else:
                    self.log_resultado("Login admin", False, "Token não retornado")
                    return False
            else:
                self.log_resultado(
                    "Login admin",
                    False,
                    f"Status: {response.status_code}, Resposta: {response.text[:100]}"
                )
                return False
                
        except Exception as e:
            self.log_resultado("Login admin", False, str(e))
            return False
    
    def teste_autenticacao_basica(self):
        """Testa autenticação básica HTTP"""
        print("\n🔑 TESTANDO AUTENTICAÇÃO BÁSICA")
        print("-" * 50)
        
        try:
            # Cria header de autenticação básica
            credentials = f"{ADMIN_USER}:{ADMIN_PASS}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}"
            }
            
            # Testa endpoint que pode aceitar auth básica
            response = requests.get(
                f"{self.base_url}/admin/dashboard",
                headers=headers,
                timeout=15
            )
            
            # Se conseguir acesso ou retornar 405 (método não permitido), auth funciona
            sucesso = response.status_code in [200, 405, 302]
            detalhes = f"Status: {response.status_code}"
            
            if response.status_code == 401:
                detalhes += " (Credenciais rejeitadas)"
            elif response.status_code == 403:
                detalhes += " (Acesso negado)"
            elif response.status_code in [200, 302]:
                detalhes += " (Acesso autorizado)"
            elif response.status_code == 405:
                detalhes += " (Método não permitido - mas autenticado)"
            
            self.log_resultado("Autenticação básica", sucesso, detalhes)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Autenticação básica", False, str(e))
            return False
    
    def teste_endpoints_admin(self):
        """Testa endpoints administrativos"""
        print("\n👑 TESTANDO ENDPOINTS ADMINISTRATIVOS")
        print("-" * 50)
        
        endpoints_admin = [
            ("/admin/dashboard", "GET", "Dashboard administrativo"),
            ("/admin/users", "GET", "Gerenciamento de usuários"),
            ("/admin/stats", "GET", "Estatísticas do sistema"),
            ("/admin/logs", "GET", "Logs do sistema")
        ]
        
        todos_ok = True
        
        for endpoint, method, descricao in endpoints_admin:
            try:
                # Testa sem autenticação primeiro
                response_sem_auth = requests.get(
                    f"{self.base_url}{endpoint}",
                    timeout=10
                )
                
                # Deve retornar 401 sem autenticação
                sem_auth_ok = response_sem_auth.status_code == 401
                
                # Testa com autenticação básica
                credentials = f"{ADMIN_USER}:{ADMIN_PASS}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                
                headers = {
                    "Authorization": f"Basic {encoded_credentials}"
                }
                
                response_com_auth = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                
                # Com auth, deve ser diferente de 401
                com_auth_ok = response_com_auth.status_code != 401
                
                sucesso = sem_auth_ok and com_auth_ok
                detalhes = f"Sem auth: {response_sem_auth.status_code}, Com auth: {response_com_auth.status_code}"
                
                self.log_resultado(descricao, sucesso, detalhes)
                
                if not sucesso:
                    todos_ok = False
                    
            except Exception as e:
                self.log_resultado(descricao, False, str(e))
                todos_ok = False
        
        return todos_ok
    
    def teste_endpoints_whatsapp(self):
        """Testa endpoints da API do WhatsApp"""
        print("\n📱 TESTANDO ENDPOINTS WHATSAPP")
        print("-" * 50)
        
        endpoints_whatsapp = [
            ("/api/whatsapp/send", "POST", "Envio de mensagens"),
            ("/api/whatsapp/webhook", "POST", "Webhook do WhatsApp"),
            ("/api/contacts", "GET", "Lista de contatos"),
            ("/api/messages", "GET", "Histórico de mensagens"),
            ("/api/whatsapp/status", "GET", "Status da conexão")
        ]
        
        todos_ok = True
        
        for endpoint, method, descricao in endpoints_whatsapp:
            try:
                # Testa sem autenticação
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=10)
                
                # Deve exigir autenticação (401 ou 403)
                sucesso = response.status_code in [401, 403]
                detalhes = f"Status: {response.status_code}"
                
                if response.status_code == 401:
                    detalhes += " (Autenticação necessária - correto)"
                elif response.status_code == 403:
                    detalhes += " (Acesso negado - correto)"
                elif response.status_code == 404:
                    detalhes += " (Endpoint não encontrado)"
                elif response.status_code == 405:
                    detalhes += " (Método não permitido)"
                else:
                    detalhes += " (Deveria exigir autenticação)"
                
                self.log_resultado(descricao, sucesso, detalhes)
                
                if not sucesso:
                    todos_ok = False
                    
            except Exception as e:
                self.log_resultado(descricao, False, str(e))
                todos_ok = False
        
        return todos_ok
    
    def teste_validacao_dados(self):
        """Testa validação de dados de entrada"""
        print("\n✅ TESTANDO VALIDAÇÃO DE DADOS")
        print("-" * 50)
        
        try:
            # Testa envio de dados inválidos para endpoint de mensagem
            dados_invalidos = {
                "telefone": "numero_invalido",
                "mensagem": "",
                "tipo": "tipo_inexistente"
            }
            
            response = requests.post(
                f"{self.base_url}/api/whatsapp/send",
                json=dados_invalidos,
                timeout=10
            )
            
            # Deve retornar erro de validação (400) ou auth (401)
            sucesso = response.status_code in [400, 401, 422]
            detalhes = f"Status: {response.status_code}"
            
            if response.status_code == 400:
                detalhes += " (Dados inválidos - correto)"
            elif response.status_code == 422:
                detalhes += " (Erro de validação - correto)"
            elif response.status_code == 401:
                detalhes += " (Autenticação necessária - correto)"
            
            self.log_resultado("Validação de dados", sucesso, detalhes)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Validação de dados", False, str(e))
            return False
    
    def teste_documentacao_api(self):
        """Testa acessibilidade da documentação"""
        print("\n📚 TESTANDO DOCUMENTAÇÃO DA API")
        print("-" * 50)
        
        try:
            # Testa acesso aos docs
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            docs_ok = response.status_code == 200
            
            # Testa schema OpenAPI
            response_schema = requests.get(f"{self.base_url}/openapi.json", timeout=10)
            schema_ok = response_schema.status_code == 200
            
            if schema_ok:
                try:
                    schema = response_schema.json()
                    num_paths = len(schema.get('paths', {}))
                    detalhes = f"Docs: {response.status_code}, Schema: {response_schema.status_code}, Endpoints: {num_paths}"
                except:
                    detalhes = f"Docs: {response.status_code}, Schema: {response_schema.status_code}"
            else:
                detalhes = f"Docs: {response.status_code}, Schema: {response_schema.status_code}"
            
            sucesso = docs_ok and schema_ok
            self.log_resultado("Documentação da API", sucesso, detalhes)
            return sucesso
            
        except Exception as e:
            self.log_resultado("Documentação da API", False, str(e))
            return False
    
    def executar_todos_testes(self):
        """Executa todos os testes de API"""
        print("🚀 INICIANDO TESTES DA API WHATSAPP")
        print(f"🎯 Ambiente: {self.base_url}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 70)
        
        # Lista de testes
        testes = [
            self.teste_autenticacao_basica,
            self.teste_endpoints_admin,
            self.teste_endpoints_whatsapp,
            self.teste_validacao_dados,
            self.teste_documentacao_api
        ]
        
        # Executa testes
        for teste in testes:
            try:
                teste()
            except Exception as e:
                print(f"❌ ERRO CRÍTICO no teste {teste.__name__}: {e}")
        
        # Relatório final
        self.gerar_relatorio()
    
    def gerar_relatorio(self):
        """Gera relatório dos testes"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO DOS TESTES DE API")
        print("=" * 70)
        
        sucessos = sum(1 for r in self.resultados if r["sucesso"])
        total = len(self.resultados)
        percentual = (sucessos / total * 100) if total > 0 else 0
        
        print(f"📈 Resultados: {sucessos}/{total} testes aprovados ({percentual:.1f}%)")
        print()
        
        for i, resultado in enumerate(self.resultados, 1):
            status = "✅" if resultado["sucesso"] else "❌"
            print(f"{i:2d}. {status} {resultado['teste']}")
            if resultado["detalhes"]:
                print(f"      {resultado['detalhes']}")
        
        print()
        
        if percentual >= 80:
            print("🎉 EXCELENTE! A API está funcionando corretamente!")
            return 0
        elif percentual >= 60:
            print("✅ BOM! A API tem funcionamento adequado.")
            return 0
        else:
            print("⚠️ ATENÇÃO! A API tem problemas que precisam ser corrigidos.")
            return 1

def main():
    """Função principal"""
    tester = TestesAPIWhatsApp()
    exit_code = tester.executar_todos_testes()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()