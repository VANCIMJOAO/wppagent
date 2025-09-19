#!/usr/bin/env python3
"""
🧪 TESTE CLIENTE REAL OTIMIZADO
===============================

Teste focado nos endpoints críticos sem sobrecarregar logs
"""

import asyncio
import json
import time
from datetime import datetime

import httpx
from rich.console import Console
from rich.table import Table

console = Console()

# Configurações
RAILWAY_URL = "https://wppagent-production.up.railway.app"

class ClienteRealOtimizado:
    """Testador otimizado para Railway"""
    
    def __init__(self):
        self.base_url = RAILWAY_URL
        self.results = []
        self.session = httpx.AsyncClient(timeout=10.0)
        
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
        """Testa endpoints críticos essenciais"""
        console.print("\n[bold blue]🔍 TESTANDO ENDPOINTS CRÍTICOS[/bold blue]")
        
        endpoints = [
            ("/ping", "Health check principal"),
            ("/health", "Health check alternativo"),
            ("/emergency", "Endpoint de emergência"),
            ("/railway", "Health check Railway"),
            ("/status", "Status da aplicação")
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
    
    async def test_openapi_basico(self):
        """Testa documentação OpenAPI básica"""
        console.print("\n[bold blue]📚 TESTANDO OPENAPI BÁSICO[/bold blue]")
        
        try:
            start_time = time.time()
            response = await self.session.get(f"{self.base_url}/openapi.json")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("OpenAPI Schema", "✅ PASS", f"Schema válido - {response.status_code}", response_time)
            else:
                self.log_result("OpenAPI Schema", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("OpenAPI Schema", "❌ FAIL", str(e))
    
    async def test_webhook_basico(self):
        """Testa webhook básico"""
        console.print("\n[bold blue]📱 TESTANDO WEBHOOK BÁSICO[/bold blue]")
        
        # Teste de verificação do webhook
        try:
            verify_params = {
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_123",
                "hub.verify_token": "test_verify_token_123"
            }
            
            start_time = time.time()
            response = await self.session.get(f"{self.base_url}/webhook", params=verify_params)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_result("Webhook Verification", "✅ PASS", "Verificação funcionando", response_time)
            else:
                self.log_result("Webhook Verification", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("Webhook Verification", "❌ FAIL", str(e))
    
    async def test_metrics(self):
        """Testa métricas do sistema"""
        console.print("\n[bold blue]📊 TESTANDO MÉTRICAS[/bold blue]")
        
        try:
            start_time = time.time()
            response = await self.session.get(f"{self.base_url}/metrics")
            response_time = time.time() - start_time
            
            if response.status_code in [200, 401]:  # 401 = precisa de auth
                self.log_result("System Metrics", "✅ PASS", f"Status {response.status_code}", response_time)
            else:
                self.log_result("System Metrics", "❌ FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_result("System Metrics", "❌ FAIL", str(e))
    
    def generate_report(self):
        """Gera relatório final"""
        console.print("\n[bold green]📊 RELATÓRIO FINAL[/bold green]")
        
        # Estatísticas
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "✅ PASS"])
        failed_tests = len([r for r in self.results if r["status"] == "❌ FAIL"])
        
        # Tabela de resumo
        table = Table(title="Resumo dos Testes")
        table.add_column("Categoria", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Passou", justify="right", style="green")
        table.add_column("Falhou", justify="right", style="red")
        
        table.add_row("Todos os Testes", str(total_tests), str(passed_tests), str(failed_tests))
        
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
            "success_rate": success_rate,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0
        }

async def main():
    """Função principal"""
    console.print("[bold blue]🧪 TESTE CLIENTE REAL OTIMIZADO[/bold blue]")
    console.print("Teste focado sem sobrecarregar logs do Railway")
    
    async with ClienteRealOtimizado() as tester:
        # Executar testes essenciais
        await tester.test_endpoints_criticos()
        await tester.test_openapi_basico()
        await tester.test_webhook_basico()
        await tester.test_metrics()
        
        # Gerar relatório
        report = tester.generate_report()
        
        # Salvar relatório
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"relatorio_teste_otimizado_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": report,
                "results": tester.results,
                "timestamp": datetime.now().isoformat(),
                "railway_url": RAILWAY_URL
            }, f, indent=2, ensure_ascii=False)
        
        console.print(f"\n[bold green]✅ Relatório salvo em: {report_file}[/bold green]")
        
        # Status final
        if report["success_rate"] >= 80:
            console.print("\n[bold green]🎉 TESTE CONCLUÍDO COM SUCESSO![/bold green]")
        elif report["success_rate"] >= 60:
            console.print("\n[bold yellow]⚠️ TESTE CONCLUÍDO COM AVISOS[/bold yellow]")
        else:
            console.print("\n[bold red]❌ TESTE FALHOU[/bold red]")

if __name__ == "__main__":
    asyncio.run(main())
