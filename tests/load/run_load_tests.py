"""
Load Testing Executável para TRILHA 2 FASE 2.2
==============================================

Script executável para rodar diferentes cenários
de load testing com configurações otimizadas.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime


class LoadTestRunner:
    """Executa e gerencia testes de carga"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_file = "tests/load/test_load_whatsapp.py"
        self.results_dir = "tests/load/results"
        os.makedirs(self.results_dir, exist_ok=True)

    def check_server_availability(self):
        """Verifica se o servidor está rodando"""
        try:
            import requests

            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def run_scenario(self, scenario_name, config, headless=True):
        """Executa um cenário específico de load testing"""

        print(f"\n🚀 Executando: {scenario_name}")
        print(f"📋 {config['description']}")
        print(f"👥 Usuários: {config['users']}")
        print(f"⚡ Spawn Rate: {config['spawn_rate']}/s")
        print(f"⏱️  Duração: {config['run_time']}")
        print("-" * 50)

        # Comando locust
        cmd = [
            "locust",
            "-f",
            self.test_file,
            "--host",
            self.base_url,
            "--users",
            str(config["users"]),
            "--spawn-rate",
            str(config["spawn_rate"]),
            "-t",
            config["run_time"],
        ]

        if headless:
            cmd.append("--headless")

            # Arquivo de resultados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_prefix = f"{self.results_dir}/{scenario_name}_{timestamp}"
            cmd.extend(["--csv", csv_prefix, "--html", f"{csv_prefix}_report.html"])

        try:
            # Executar teste
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            end_time = time.time()

            duration = end_time - start_time

            # Analisar resultados
            if result.returncode == 0:
                print(f"✅ {scenario_name} completado em {duration:.1f}s")

                if headless:
                    self.analyze_results(csv_prefix)
                else:
                    print("📊 Interface web aberta no navegador")

            else:
                print(f"❌ {scenario_name} falhou:")
                print(result.stderr)

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print(f"⏰ {scenario_name} timeout após 10 minutos")
            return False
        except Exception as e:
            print(f"💥 Erro executando {scenario_name}: {e}")
            return False

    def analyze_results(self, csv_prefix):
        """Analisa resultados do CSV gerado pelo Locust"""
        stats_file = f"{csv_prefix}_stats.csv"

        if not os.path.exists(stats_file):
            print("⚠️  Arquivo de estatísticas não encontrado")
            return

        try:
            # Ler estatísticas principais
            with open(stats_file, "r") as f:
                lines = f.readlines()

            if len(lines) < 2:
                print("📊 Dados insuficientes para análise")
                return

            # Header da primeira linha, dados da segunda
            headers = lines[0].strip().split(",")
            data = lines[1].strip().split(",")

            # Criar dicionário com dados
            stats = dict(zip(headers, data))

            # Análise básica
            print("\n📈 RESULTADOS DO TESTE:")
            print(f"🔢 Total Requests: {stats.get('Request Count', 'N/A')}")
            print(f"❌ Falhas: {stats.get('Failure Count', 'N/A')}")
            print(f"📊 Taxa de Falhas: {stats.get('Failure Count %', 'N/A')}")
            print(f"⚡ Tempo Médio: {stats.get('Average Response Time', 'N/A')}ms")
            print(f"🏃 RPS Médio: {float(stats.get('Requests/s', 0)):.2f}")

            # Análise de performance
            avg_time = float(stats.get("Average Response Time", 0))
            failure_rate = float(stats.get("Failure Count %", 0))

            print(f"\n🎯 ANÁLISE DE PERFORMANCE:")

            if avg_time < 100:
                print(f"⚡ EXCELENTE: Tempo de resposta muito bom ({avg_time:.0f}ms)")
            elif avg_time < 500:
                print(f"✅ BOM: Tempo de resposta aceitável ({avg_time:.0f}ms)")
            elif avg_time < 1000:
                print(f"⚠️  ATENÇÃO: Tempo de resposta alto ({avg_time:.0f}ms)")
            else:
                print(f"❌ CRÍTICO: Tempo de resposta muito alto ({avg_time:.0f}ms)")

            if failure_rate == 0:
                print(f"✅ PERFEITO: Zero falhas no teste")
            elif failure_rate < 1:
                print(f"✅ BOM: Taxa de falhas baixa ({failure_rate:.2f}%)")
            elif failure_rate < 5:
                print(f"⚠️  ATENÇÃO: Taxa de falhas moderada ({failure_rate:.2f}%)")
            else:
                print(f"❌ CRÍTICO: Taxa de falhas alta ({failure_rate:.2f}%)")

        except Exception as e:
            print(f"💥 Erro analisando resultados: {e}")

    def run_all_scenarios(self):
        """Executa todos os cenários de teste"""

        scenarios = {
            "light_load": {
                "users": 10,
                "spawn_rate": 2,
                "run_time": "1m",
                "description": "Carga leve - uso normal",
            },
            "moderate_load": {
                "users": 25,
                "spawn_rate": 5,
                "run_time": "2m",
                "description": "Carga moderada - pico normal",
            },
            "heavy_load": {
                "users": 50,
                "spawn_rate": 10,
                "run_time": "2m",
                "description": "Carga pesada - stress test",
            },
        }

        print(f"🎯 TRILHA 2 FASE 2.2 - Load Testing")
        print(f"📍 Target: {self.base_url}")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Verificar servidor
        if not self.check_server_availability():
            print(f"❌ Servidor não disponível em {self.base_url}")
            print(f"💡 Certifique-se que o WhatsApp Agent está rodando")
            return False

        print(f"✅ Servidor disponível em {self.base_url}")

        # Executar cenários
        results = {}
        for name, config in scenarios.items():
            success = self.run_scenario(name, config)
            results[name] = success

            if success:
                print(f"✅ {name}: SUCESSO")
            else:
                print(f"❌ {name}: FALHA")

            # Pausa entre testes
            if name != list(scenarios.keys())[-1]:  # Não pausar no último
                print("⏸️  Pausa de 30s entre testes...")
                time.sleep(30)

        # Relatório final
        print("\n" + "=" * 60)
        print("📋 RELATÓRIO FINAL - LOAD TESTING")
        print("=" * 60)

        total_tests = len(scenarios)
        successful_tests = sum(results.values())

        print(f"🎯 Testes Executados: {total_tests}")
        print(f"✅ Sucessos: {successful_tests}")
        print(f"❌ Falhas: {total_tests - successful_tests}")
        print(f"📊 Taxa de Sucesso: {(successful_tests/total_tests)*100:.1f}%")

        if successful_tests == total_tests:
            print(f"\n🎉 EXCELENTE: Todos os testes de carga passaram!")
            print(f"🚀 Sistema demonstra boa capacidade de resposta sob carga")
        else:
            print(f"\n⚠️  ATENÇÃO: Alguns testes falharam")
            print(f"🔍 Verifique os logs para mais detalhes")

        return successful_tests == total_tests


def main():
    """Função principal para execução do load testing"""

    # Verificar dependências
    try:
        import locust
    except ImportError:
        print("❌ Locust não encontrado. Instale com: pip install locust")
        sys.exit(1)

    # Parâmetros da linha de comando
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    # Executar testes
    runner = LoadTestRunner(base_url)
    success = runner.run_all_scenarios()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
