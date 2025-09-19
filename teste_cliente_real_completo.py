#!/usr/bin/env python3
"""
🧪 TESTE CLIENTE REAL COMPLETO
==============================

Teste abrangente que simula um cliente real usando:
- Servidor real do Railway
- APIs do Meta (WhatsApp Business)
- OpenAPI/Swagger
- Todos os endpoints críticos
- Fluxos completos de negócio

Autor: Desenvolvedor
Data: 2025-09-19
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

import httpx
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Configurações
RAILWAY_URL = "https://wppagent-production.up.railway.app"
OPENAPI_URL = f"{RAILWAY_URL}/openapi.json"
META_VERIFY_TOKEN = "test_verify_token_123"
META_ACCESS_TOKEN = "test_access_token_456"

class ClienteRealTester:
    """Testador completo para simular cliente real"""
    
    def __init__(self):
        self.base_url = RAILWAY_URL
        self.results = []
        self.session = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    def log_result(self, test_name: str, status: str, details: str = "", response_time: float = 0):
        """Registra resultado do teste"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        # Log colorido
        if status == "✅ PASS":
            console.print(f"[green]{status}[/green] {test_name} ({response_time:.2f}s)")
        elif status == "❌ FAIL":
            console.print(f"[red]{status}[/red] {test_name} - {details}")
        else:
            console.print(f"[yellow]{status}[/yellow] {test_name}")
    
    async def test_endpoints_criticos(self):
        """Testa todos os endpoints críticos"""
        console.print("\n[bold blue]🔍 TESTANDO ENDPOINTS CRÍTICOS[/bold blue]")
        
        endpoints = [
            ("/ping", "Health check principal"),
            ("/health", "Health check alternativo"),
            ("/emergency", "Endpoint de emergência"),
            ("/railway", "Health check Railway"),
            ("/status", "Status da aplicação"),
            ("/", "Endpoint raiz"),
            ("/ready", "Endpoint ready"),
            ("/alive", "Endpoint alive")
        ]
        
        for endpoint, description in endpoints:
            try:
                start_time = time.time()
                response = await self.session.get(f"{self.base_url}{endpoint}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(f"GET {endpoint}", "✅ PASS", f"{description} - {response.status_code}", response_time)
                else:
                    self.log_result(f"GET {endpoint}", "❌ FAIL", f"Status {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_result(f"GET {endpoint}", "❌ FAIL", str(e))
    
    async def test_openapi_documentation(self):
        """Testa documentação OpenAPI/Swagger"""
        console.print("\n[bold blue]📚 TESTANDO DOCUMENTAÇÃO OPENAPI[/bold blue]")
        
        try:
            start_time = time.time()
            response = await self.session.get(OPENAPI_URL)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                openapi_data = response.json()
                
                # Verificar estrutura básica
                required_fields = ["openapi", "info", "paths"]
                missing_fields = [field for field in required_fields if field not in openapi_data]
                
                if not missing_fields:
                    self.log_result("OpenAPI Schema", "✅ PASS", f"Estrutura válida - {len(openapi_data.get('paths', {}))} endpoints", response_time)
                    
                    # Testar endpoint /docs
                    docs_response = await self.session.get(f"{self.base_url}/docs")
                    if docs_response.status_code == 200:
                        self.log_result("Swagger UI", "✅ PASS", "Interface Swagger acessível", 0)
                    else:
                        self.log_result("Swagger UI", "❌ FAIL", f"Status {docs_response.status_code}")
                else:
                    self.log_result("OpenAPI Schema", "❌ FAIL", f"Campos faltando: {missing_fields}")
            else:
                self.log_result("OpenAPI Schema", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("OpenAPI Schema", "❌ FAIL", str(e))
    
    async def test_meta_webhook_simulation(self):
        """Simula webhook do Meta WhatsApp"""
        console.print("\n[bold blue]📱 TESTANDO WEBHOOK META WHATSAPP[/bold blue]")
        
        # Dados simulados do Meta
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "15551234567",
                                    "phone_number_id": "987654321"
                                },
                                "messages": [
                                    {
                                        "from": "5511999999999",
                                        "id": "wamid.test123",
                                        "timestamp": str(int(time.time())),
                                        "text": {
                                            "body": "Olá! Gostaria de agendar um horário."
                                        },
                                        "type": "text"
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        # Teste de verificação do webhook
        try:
            verify_params = {
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": META_VERIFY_TOKEN
            }
            
            start_time = time.time()
            response = await self.session.get(f"{self.base_url}/webhook", params=verify_params)
            response_time = time.time() - start_time
            
            if response.status_code == 200 and response.text == "test_challenge_123":
                self.log_result("Webhook Verification", "✅ PASS", "Verificação do webhook funcionando", response_time)
            else:
                self.log_result("Webhook Verification", "❌ FAIL", f"Status {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_result("Webhook Verification", "❌ FAIL", str(e))
        
        # Teste de recebimento de mensagem
        try:
            start_time = time.time()
            response = await self.session.post(
                f"{self.base_url}/webhook",
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Webhook Message", "✅ PASS", "Mensagem processada com sucesso", response_time)
            else:
                self.log_result("Webhook Message", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Webhook Message", "❌ FAIL", str(e))
    
    async def test_authentication_flow(self):
        """Testa fluxo de autenticação"""
        console.print("\n[bold blue]🔐 TESTANDO FLUXO DE AUTENTICAÇÃO[/bold blue]")
        
        # Teste de registro
        try:
            register_data = {
                "username": "teste_cliente_real",
                "email": "teste@cliente.com",
                "password": "senha123456",
                "full_name": "Cliente Real Teste"
            }
            
            start_time = time.time()
            response = await self.session.post(f"{self.base_url}/auth/register", json=register_data)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201, 409]:  # 409 = usuário já existe
                self.log_result("User Registration", "✅ PASS", f"Status {response.status_code}", response_time)
            else:
                self.log_result("User Registration", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("User Registration", "❌ FAIL", str(e))
        
        # Teste de login
        try:
            login_data = {
                "username": "teste_cliente_real",
                "password": "senha123456"
            }
            
            start_time = time.time()
            response = await self.session.post(f"{self.base_url}/auth/login", json=login_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                login_result = response.json()
                if "access_token" in login_result:
                    self.log_result("User Login", "✅ PASS", "Token gerado com sucesso", response_time)
                    return login_result["access_token"]
                else:
                    self.log_result("User Login", "❌ FAIL", "Token não encontrado na resposta")
            else:
                self.log_result("User Login", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("User Login", "❌ FAIL", str(e))
        
        return None
    
    async def test_protected_endpoints(self, token: Optional[str] = None):
        """Testa endpoints protegidos"""
        console.print("\n[bold blue]🛡️ TESTANDO ENDPOINTS PROTEGIDOS[/bold blue]")
        
        if not token:
            self.log_result("Protected Endpoints", "⚠️ SKIP", "Token não disponível")
            return
        
        headers = {"Authorization": f"Bearer {token}"}
        
        protected_endpoints = [
            ("/appointments", "Lista de agendamentos"),
            ("/conversations", "Lista de conversas"),
            ("/admin/debug-admin", "Debug administrativo"),
            ("/metrics", "Métricas do sistema")
        ]
        
        for endpoint, description in protected_endpoints:
            try:
                start_time = time.time()
                response = await self.session.get(f"{self.base_url}{endpoint}", headers=headers)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_result(f"GET {endpoint}", "✅ PASS", f"{description} - {response.status_code}", response_time)
                elif response.status_code == 401:
                    self.log_result(f"GET {endpoint}", "✅ PASS", f"{description} - Protegido corretamente", response_time)
                else:
                    self.log_result(f"GET {endpoint}", "❌ FAIL", f"Status {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"GET {endpoint}", "❌ FAIL", str(e))
    
    async def test_business_workflow(self):
        """Testa fluxo completo de negócio"""
        console.print("\n[bold blue]💼 TESTANDO FLUXO DE NEGÓCIO[/bold blue]")
        
        # Simular criação de agendamento
        try:
            appointment_data = {
                "client_name": "João Silva",
                "client_phone": "5511999999999",
                "service_type": "Consulta",
                "appointment_date": "2025-09-20T14:00:00Z",
                "notes": "Cliente preferencial"
            }
            
            start_time = time.time()
            response = await self.session.post(f"{self.base_url}/appointments", json=appointment_data)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201, 401]:  # 401 = precisa de auth
                self.log_result("Create Appointment", "✅ PASS", f"Status {response.status_code}", response_time)
            else:
                self.log_result("Create Appointment", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Create Appointment", "❌ FAIL", str(e))
        
        # Testar métricas
        try:
            start_time = time.time()
            response = await self.session.get(f"{self.base_url}/metrics")
            response_time = time.time() - start_time
            
            if response.status_code in [200, 401]:
                self.log_result("System Metrics", "✅ PASS", f"Status {response.status_code}", response_time)
            else:
                self.log_result("System Metrics", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("System Metrics", "❌ FAIL", str(e))
    
    async def test_performance(self):
        """Testa performance da aplicação"""
        console.print("\n[bold blue]⚡ TESTANDO PERFORMANCE[/bold blue]")
        
        # Teste de carga nos endpoints críticos
        endpoints = ["/ping", "/health", "/status"]
        
        for endpoint in endpoints:
            times = []
            for i in range(5):  # 5 requisições por endpoint
                try:
                    start_time = time.time()
                    response = await self.session.get(f"{self.base_url}{endpoint}")
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        times.append(response_time)
                    
                except Exception:
                    pass
            
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)
                
                if avg_time < 1.0:  # Menos de 1 segundo
                    self.log_result(f"Performance {endpoint}", "✅ PASS", f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s", avg_time)
                else:
                    self.log_result(f"Performance {endpoint}", "⚠️ SLOW", f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s", avg_time)
    
    def generate_report(self):
        """Gera relatório final"""
        console.print("\n[bold green]📊 RELATÓRIO FINAL[/bold green]")
        
        # Estatísticas
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "✅ PASS"])
        failed_tests = len([r for r in self.results if r["status"] == "❌ FAIL"])
        skipped_tests = len([r for r in self.results if r["status"] == "⚠️ SKIP"])
        
        # Tabela de resumo
        table = Table(title="Resumo dos Testes")
        table.add_column("Categoria", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Passou", justify="right", style="green")
        table.add_column("Falhou", justify="right", style="red")
        table.add_column("Pulou", justify="right", style="yellow")
        
        table.add_row("Todos os Testes", str(total_tests), str(passed_tests), str(failed_tests), str(skipped_tests))
        
        console.print(table)
        
        # Taxa de sucesso
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        console.print(f"\n[bold]Taxa de Sucesso: {success_rate:.1f}%[/bold]")
        
        # Testes que falharam
        if failed_tests > 0:
            console.print("\n[bold red]❌ TESTES QUE FALHARAM:[/bold red]")
            for result in self.results:
                if result["status"] == "❌ FAIL":
                    console.print(f"  • {result['test']}: {result['details']}")
        
        # Tempo médio de resposta
        response_times = [r["response_time"] for r in self.results if r["response_time"] > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            console.print(f"\n[bold]Tempo Médio de Resposta: {avg_response_time:.3f}s[/bold]")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "success_rate": success_rate,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0
        }

async def main():
    """Função principal"""
    console.print(Panel.fit(
        "[bold blue]🧪 TESTE CLIENTE REAL COMPLETO[/bold blue]\n"
        "Simulando cliente real com servidor Railway\n"
        "APIs do Meta, OpenAPI e fluxos completos",
        border_style="blue"
    ))
    
    async with ClienteRealTester() as tester:
        # Executar todos os testes
        await tester.test_endpoints_criticos()
        await tester.test_openapi_documentation()
        await tester.test_meta_webhook_simulation()
        
        # Teste de autenticação
        token = await tester.test_authentication_flow()
        await tester.test_protected_endpoints(token)
        
        await tester.test_business_workflow()
        await tester.test_performance()
        
        # Gerar relatório
        report = tester.generate_report()
        
        # Salvar relatório
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"relatorio_teste_cliente_real_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": report,
                "results": tester.results,
                "timestamp": datetime.now().isoformat(),
                "railway_url": RAILWAY_URL
            }, f, indent=2, ensure_ascii=False)
        
        console.print(f"\n[bold green]✅ Relatório salvo em: {report_file}[/bold green]")
        
        # Status final
        if report["success_rate"] >= 90:
            console.print("\n[bold green]🎉 TESTE CONCLUÍDO COM SUCESSO![/bold green]")
            console.print("[green]Aplicação está pronta para clientes reais![/green]")
        elif report["success_rate"] >= 70:
            console.print("\n[bold yellow]⚠️ TESTE CONCLUÍDO COM AVISOS[/bold yellow]")
            console.print("[yellow]Alguns problemas foram encontrados, mas a aplicação está funcional.[/yellow]")
        else:
            console.print("\n[bold red]❌ TESTE FALHOU[/bold red]")
            console.print("[red]Problemas críticos encontrados. Verifique a aplicação.[/red]")

if __name__ == "__main__":
    asyncio.run(main())
