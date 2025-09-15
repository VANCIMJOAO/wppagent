"""
Load Testing Melhorado para TRILHA 2 FASE 2.2
=============================================

Versão otimizada para trabalhar com servidor independente.
Inclui verificações de conectividade e relatórios detalhados.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime

import requests


class SmartLoadTestRunner:
    """Load Test Runner inteligente que verifica servidor antes de executar"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_file = "tests/load/test_load_whatsapp.py"
        self.results_dir = "tests/load/results"
        os.makedirs(self.results_dir, exist_ok=True)

    def check_server_health(self, timeout=10):
        """Verifica se servidor está saudável e respondendo"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=timeout)
            if response.status_code == 200:
                print(f"✅ Servidor saudável: {response.status_code}")
                return True
            else:
                print(f"⚠️  Servidor respondeu com status: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Erro de conexão com {self.base_url}")
            return False
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout conectando com {self.base_url}")
            return False
        except Exception as e:
            print(f"💥 Erro inesperado: {e}")
            return False

    def wait_for_server(self, max_wait=60):
        """Aguarda servidor ficar disponível"""
        print(f"⏳ Aguardando servidor em {self.base_url}...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.check_server_health(timeout=5):
                print(f"🎉 Servidor disponível após {time.time() - start_time:.1f}s")
                return True

            print("   ⏳ Tentando novamente em 3s...")
            time.sleep(3)

        print(f"❌ Servidor não ficou disponível em {max_wait}s")
        return False

    def pre_flight_check(self):
        """Verificações antes de executar testes"""
        print(f"\n🔍 PRÉ-VERIFICAÇÕES")
        print(f"=" * 40)

        # 1. Verificar arquivo de teste
        if not os.path.exists(self.test_file):
            print(f"❌ Arquivo de teste não encontrado: {self.test_file}")
            return False
        print(f"✅ Arquivo de teste: {self.test_file}")

        # 2. Verificar locust
        try:
            result = subprocess.run(
                ["locust", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Locust disponível: {result.stdout.strip()}")
            else:
                print(f"❌ Erro com locust: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Locust não encontrado: {e}")
            return False

        # 3. Verificar servidor
        if not self.check_server_health():
            print(f"⚠️  Servidor não está respondendo")
            print(f"💡 Sugestão: Execute './tests/load/server_manager.sh start'")
            return False

        print(f"✅ Todas as verificações passaram!")
        return True

    def run_targeted_test(self, scenario_name, users=10, spawn_rate=2, duration="1m"):
        """Executa um teste específico com parâmetros customizados"""

        print(f"\n🎯 EXECUTANDO: {scenario_name}")
        print(f"👥 Usuários: {users}")
        print(f"⚡ Spawn Rate: {spawn_rate}/s")
        print(f"⏱️  Duração: {duration}")
        print("-" * 50)

        # Comando locust
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_prefix = f"{self.results_dir}/{scenario_name}_{timestamp}"

        cmd = [
            "locust",
            "-f",
            self.test_file,
            "--host",
            self.base_url,
            "--users",
            str(users),
            "--spawn-rate",
            str(spawn_rate),
            "-t",
            duration,
            "--headless",
            "--csv",
            csv_prefix,
            "--html",
            f"{csv_prefix}_report.html",
        ]

        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            end_time = time.time()

            duration_actual = end_time - start_time

            if result.returncode == 0:
                print(f"✅ {scenario_name} completado em {duration_actual:.1f}s")

                # Analisar resultados
                self.analyze_results(csv_prefix, scenario_name)
                return True
            else:
                print(f"❌ {scenario_name} falhou:")
                print(f"STDOUT: {result.stdout}")
                print(f"STDERR: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"⏰ {scenario_name} timeout após 5 minutos")
            return False
        except Exception as e:
            print(f"💥 Erro executando {scenario_name}: {e}")
            return False

    def analyze_results(self, csv_prefix, scenario_name):
        """Análise detalhada dos resultados"""
        stats_file = f"{csv_prefix}_stats.csv"

        if not os.path.exists(stats_file):
            print("⚠️  Arquivo de estatísticas não encontrado")
            return

        try:
            with open(stats_file, "r") as f:
                lines = f.readlines()

            if len(lines) < 2:
                print("📊 Dados insuficientes para análise")
                return

            # Parse dos dados
            headers = [h.strip('"') for h in lines[0].strip().split(",")]
            data = [d.strip('"') for d in lines[1].strip().split(",")]
            stats = dict(zip(headers, data))

            # Extrair métricas principais
            total_requests = int(stats.get("Request Count", 0))
            failures = int(stats.get("Failure Count", 0))
            avg_time = float(stats.get("Average Response Time", 0))
            min_time = float(stats.get("Min Response Time", 0))
            max_time = float(stats.get("Max Response Time", 0))
            rps = float(stats.get("Requests/s", 0))
            failure_rate = (
                (failures / total_requests * 100) if total_requests > 0 else 0
            )

            # Relatório detalhado
            print(f"\n📈 RELATÓRIO DETALHADO - {scenario_name}")
            print(f"=" * 60)
            print(f"📊 Requisições Totais: {total_requests:,}")
            print(f"❌ Falhas: {failures:,} ({failure_rate:.2f}%)")
            print(f"⚡ RPS Médio: {rps:.2f}")
            print(f"⏱️  Tempo de Resposta:")
            print(f"   • Médio: {avg_time:.0f}ms")
            print(f"   • Mínimo: {min_time:.0f}ms")
            print(f"   • Máximo: {max_time:.0f}ms")

            # Análise de qualidade
            print(f"\n🎯 ANÁLISE DE QUALIDADE:")

            # Performance
            if avg_time < 100:
                print(
                    f"🚀 EXCELENTE: Tempo de resposta muito rápido ({avg_time:.0f}ms)"
                )
            elif avg_time < 300:
                print(f"✅ BOM: Tempo de resposta adequado ({avg_time:.0f}ms)")
            elif avg_time < 1000:
                print(f"⚠️  ATENÇÃO: Tempo de resposta elevado ({avg_time:.0f}ms)")
            else:
                print(f"❌ CRÍTICO: Tempo de resposta muito alto ({avg_time:.0f}ms)")

            # Confiabilidade
            if failure_rate == 0:
                print(f"🎯 PERFEITO: Zero falhas detectadas")
            elif failure_rate < 1:
                print(f"✅ EXCELENTE: Taxa de falhas muito baixa ({failure_rate:.2f}%)")
            elif failure_rate < 5:
                print(f"⚠️  ATENÇÃO: Taxa de falhas moderada ({failure_rate:.2f}%)")
            else:
                print(f"❌ CRÍTICO: Taxa de falhas alta ({failure_rate:.2f}%)")

            # Throughput
            if rps > 50:
                print(f"🚀 EXCELENTE: Alto throughput ({rps:.1f} RPS)")
            elif rps > 20:
                print(f"✅ BOM: Throughput adequado ({rps:.1f} RPS)")
            elif rps > 5:
                print(f"⚠️  BÁSICO: Throughput baixo ({rps:.1f} RPS)")
            else:
                print(f"❌ CRÍTICO: Throughput muito baixo ({rps:.1f} RPS)")

            print(f"\n📁 Relatório HTML: {csv_prefix}_report.html")

        except Exception as e:
            print(f"💥 Erro analisando resultados: {e}")

    def run_smart_suite(self):
        """Executa suite inteligente de testes progressivos"""

        print(f"🎯 TRILHA 2 FASE 2.2 - Smart Load Testing Suite")
        print(f"📍 Target: {self.base_url}")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Pré-verificações
        if not self.pre_flight_check():
            return False

        # Suite de testes progressivos
        test_scenarios = [
            {
                "name": "warmup",
                "description": "Aquecimento do sistema",
                "users": 3,
                "spawn_rate": 1,
                "duration": "30s",
            },
            {
                "name": "light_load",
                "description": "Carga leve - uso normal",
                "users": 8,
                "spawn_rate": 2,
                "duration": "1m",
            },
            {
                "name": "moderate_load",
                "description": "Carga moderada - pico diário",
                "users": 20,
                "spawn_rate": 4,
                "duration": "90s",
            },
            {
                "name": "stress_test",
                "description": "Teste de stress - limite",
                "users": 40,
                "spawn_rate": 8,
                "duration": "2m",
            },
        ]

        results = {}
        successful_tests = 0

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n🎬 CENÁRIO {i}/{len(test_scenarios)}: {scenario['description']}")

            success = self.run_targeted_test(
                scenario["name"],
                scenario["users"],
                scenario["spawn_rate"],
                scenario["duration"],
            )

            results[scenario["name"]] = success
            if success:
                successful_tests += 1
                print(f"✅ {scenario['name']}: SUCESSO")
            else:
                print(f"❌ {scenario['name']}: FALHA")

            # Pausa entre testes (exceto último)
            if i < len(test_scenarios):
                print(f"⏸️  Pausa de 15s antes do próximo teste...")
                time.sleep(15)

        # Relatório final
        print(f"\n" + "=" * 60)
        print(f"📋 RELATÓRIO FINAL - SMART LOAD TESTING")
        print(f"=" * 60)
        print(f"🎯 Cenários Executados: {len(test_scenarios)}")
        print(f"✅ Sucessos: {successful_tests}")
        print(f"❌ Falhas: {len(test_scenarios) - successful_tests}")
        print(f"📊 Taxa de Sucesso: {(successful_tests/len(test_scenarios))*100:.1f}%")

        if successful_tests == len(test_scenarios):
            print(f"\n🎉 EXCELENTE: Todos os testes de carga passaram!")
            print(f"🏆 Sistema demonstra excelente capacidade de resposta")
        elif successful_tests >= len(test_scenarios) * 0.75:
            print(f"\n✅ BOM: Maioria dos testes passou")
            print(f"🔧 Algumas otimizações podem ser necessárias")
        else:
            print(f"\n⚠️  ATENÇÃO: Muitos testes falharam")
            print(f"🔍 Investigação detalhada necessária")

        # Verificar servidor ainda está ativo
        print(f"\n🔍 VERIFICAÇÃO PÓS-TESTE:")
        if self.check_server_health():
            print(f"✅ Servidor ainda está saudável após os testes")
        else:
            print(f"⚠️  Servidor pode ter sido afetado pelos testes")

        return successful_tests == len(test_scenarios)


def main():
    """Função principal optimizada"""

    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    runner = SmartLoadTestRunner(base_url)
    success = runner.run_smart_suite()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
