#!/usr/bin/env python3
"""
Script Completo de Execução de Testes - WhatsApp Agent
Executa todos os tipos de testes e fornece análise detalhada
"""

import json
import os
import re
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


class TestSuiteRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration": 0,
            "categories": {},
        }
        self.failed_tests = []
        self.skipped_tests = []
        self.error_tests = []
        self.current_process = None
        self.output_buffer = []
        self.last_output_time = time.time()
        self.realtime_stats = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}

    def setup_signal_handlers(self):
        """Configura handlers para sinais de interrupção"""

        def signal_handler(signum, frame):
            print(f"\n🛑 Interrupção detectada (Signal {signum})")
            if self.current_process:
                print("🔪 Terminando processo atual...")
                self.current_process.terminate()
                time.sleep(2)
                if self.current_process.poll() is None:
                    print("💀 Forçando término do processo...")
                    self.current_process.kill()
            print("👋 Saindo...")
            exit(130)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def monitor_output_realtime(self, process):
        """Monitora saída em tempo real e detecta travamentos"""

        def read_output():
            for line in iter(process.stdout.readline, ""):
                if line:
                    self.last_output_time = time.time()
                    self.output_buffer.append(line)
                    self.process_test_line(line.strip())
                    print(line.rstrip())

        def check_timeout():
            while process.poll() is None:
                time.sleep(5)  # Verifica a cada 5 segundos
                if time.time() - self.last_output_time > 60:  # 60s sem saída
                    print(
                        f"\n⚠️  AVISO: Sem saída há {time.time() - self.last_output_time:.0f}s"
                    )
                    print("🔍 Possível travamento detectado...")

                    if time.time() - self.last_output_time > 120:  # 2 minutos
                        print("🚨 TIMEOUT: Processo travado há mais de 2 minutos!")
                        print("🔪 Terminando processo...")
                        process.terminate()
                        break

        # Iniciar threads para monitoramento
        output_thread = threading.Thread(target=read_output, daemon=True)
        timeout_thread = threading.Thread(target=check_timeout, daemon=True)

        output_thread.start()
        timeout_thread.start()

        return output_thread

    def process_test_line(self, line):
        """Processa linha de saída em tempo real para contabilizar testes"""

        # Detectar testes passando
        if "PASSED" in line:
            self.realtime_stats["passed"] += 1
            test_name = line.split("::")[0] if "::" in line else line.split()[0]
            print(f"   ✅ PASSOU: {test_name}")

        # Detectar testes falhando
        elif "FAILED" in line:
            self.realtime_stats["failed"] += 1
            test_name = line.split("::")[0] if "::" in line else line.split()[0]
            print(f"   ❌ FALHOU: {test_name}")

        # Detectar testes pulados
        elif "SKIPPED" in line:
            self.realtime_stats["skipped"] += 1
            test_name = line.split("::")[0] if "::" in line else line.split()[0]
            print(f"   ⏭️  PULADO: {test_name}")

        # Detectar erros
        elif "ERROR" in line:
            self.realtime_stats["errors"] += 1
            test_name = line.split("::")[0] if "::" in line else line.split()[0]
            print(f"   💥 ERRO: {test_name}")

        # Mostrar progresso periodicamente
        total = sum(self.realtime_stats.values())
        if total > 0 and total % 10 == 0:
            self.print_realtime_progress()

    def print_realtime_progress(self):
        """Mostra progresso em tempo real"""
        stats = self.realtime_stats
        total = sum(stats.values())

        print(
            f"\n📊 PROGRESSO: {total} testes | "
            f"✅ {stats['passed']} | "
            f"❌ {stats['failed']} | "
            f"⏭️  {stats['skipped']} | "
            f"💥 {stats['errors']}"
        )

    def print_header(self, title, symbol="="):
        """Imprime cabeçalho formatado"""
        width = 80
        print("\n" + symbol * width)
        print(f"{title:^{width}}")
        print(symbol * width)

    def print_section(self, title):
        """Imprime seção formatada"""
        print(f"\n🔍 {title}")
        print("-" * 60)

    def run_command(self, command, description, category):
        """Executa comando com monitoramento em tempo real"""
        print(f"\n🚀 {description}")
        print(f"   Comando: {command}")
        print(f"   ⏱️  Iniciando em {datetime.now().strftime('%H:%M:%S')}")
        print(f"   📊 Acompanhe o progresso abaixo:")
        print("-" * 60)

        # Reset stats for this category
        self.realtime_stats = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
        self.output_buffer = []
        self.last_output_time = time.time()

        start_time = time.time()

        try:
            # Executar processo com stdout em tempo real
            self.current_process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Monitorar saída em tempo real
            output_thread = self.monitor_output_realtime(self.current_process)

            # Aguardar conclusão
            return_code = self.current_process.wait()

            # Aguardar thread de output terminar
            output_thread.join(timeout=5)

            duration = time.time() - start_time

            # Consolidar saída
            full_output = "".join(self.output_buffer)

            # Analisar saída do pytest
            output_analysis = self.analyze_pytest_output(full_output, "")

            # Atualizar com stats em tempo real se mais precisos
            if sum(self.realtime_stats.values()) > 0:
                output_analysis.update(self.realtime_stats)
                output_analysis["total_tests"] = sum(self.realtime_stats.values())

            self.results["categories"][category] = {
                "command": command,
                "duration": duration,
                "exit_code": return_code,
                "success": return_code == 0,
                "stdout": full_output,
                "stderr": "",
                "analysis": output_analysis,
            }

            # Status visual final
            print("\n" + "-" * 60)
            status = "✅ SUCESSO" if return_code == 0 else "❌ FALHA"
            print(f"🏁 {status} em {duration:.1f}s")

            # Mostrar resumo da categoria
            stats = output_analysis
            total = stats.get("total_tests", 0)
            if total > 0:
                print(
                    f"📊 RESUMO: {total} testes | "
                    f"✅ {stats.get('passed', 0)} | "
                    f"❌ {stats.get('failed', 0)} | "
                    f"⏭️  {stats.get('skipped', 0)} | "
                    f"💥 {stats.get('errors', 0)}"
                )

            if return_code != 0:
                print(f"⚠️  Código de saída: {return_code}")

            self.current_process = None
            return return_code == 0, full_output, ""

        except KeyboardInterrupt:
            print(f"\n🛑 Interrupção pelo usuário")
            if self.current_process:
                self.current_process.terminate()
            raise

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n💥 ERRO: {str(e)}")
            self.results["categories"][category] = {
                "command": command,
                "duration": duration,
                "exit_code": -1,
                "success": False,
                "error": str(e),
            }
            self.current_process = None
            return False, "", str(e)

    def analyze_pytest_output(self, stdout, stderr):
        """Analisa saída do pytest para extrair informações"""
        analysis = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "warnings": 0,
            "failed_tests": [],
            "skipped_tests": [],
            "error_tests": [],
        }

        if not stdout:
            return analysis

        # Extrair resumo final do pytest
        summary_match = re.search(r"=+ (.+) in [\d.]+s =+", stdout)
        if summary_match:
            summary = summary_match.group(1)

            # Extrair números
            passed_match = re.search(r"(\d+) passed", summary)
            failed_match = re.search(r"(\d+) failed", summary)
            skipped_match = re.search(r"(\d+) skipped", summary)
            error_match = re.search(r"(\d+) error", summary)

            if passed_match:
                analysis["passed"] = int(passed_match.group(1))
            if failed_match:
                analysis["failed"] = int(failed_match.group(1))
            if skipped_match:
                analysis["skipped"] = int(skipped_match.group(1))
            if error_match:
                analysis["errors"] = int(error_match.group(1))

        analysis["total_tests"] = (
            analysis["passed"]
            + analysis["failed"]
            + analysis["skipped"]
            + analysis["errors"]
        )

        # Extrair testes falhados
        failed_pattern = r"FAILED (.+?) - (.+)"
        for match in re.finditer(failed_pattern, stdout):
            test_name = match.group(1)
            error_msg = match.group(2)
            analysis["failed_tests"].append({"test": test_name, "error": error_msg})
            self.failed_tests.append({"test": test_name, "error": error_msg})

        # Extrair testes pulados
        skipped_pattern = r"SKIPPED (.+?) - (.+)"
        for match in re.finditer(skipped_pattern, stdout):
            test_name = match.group(1)
            reason = match.group(2)
            analysis["skipped_tests"].append({"test": test_name, "reason": reason})
            self.skipped_tests.append({"test": test_name, "reason": reason})

        # Extrair erros
        error_pattern = r"ERROR (.+?) - (.+)"
        for match in re.finditer(error_pattern, stdout):
            test_name = match.group(1)
            error_msg = match.group(2)
            analysis["error_tests"].append({"test": test_name, "error": error_msg})
            self.error_tests.append({"test": test_name, "error": error_msg})

        return analysis

    def run_all_tests(self):
        """Executa todas as categorias de testes"""

        # Configurar handlers de sinal
        self.setup_signal_handlers()

        self.print_header("🧪 EXECUÇÃO COMPLETA DE TESTES - WHATSAPP AGENT")
        print(f"📅 Data/Hora: {self.results['timestamp']}")
        print(f"📂 Diretório: {os.getcwd()}")
        print(f"💡 Use Ctrl+C para interromper execução com segurança")

        start_total = time.time()

        # Configuração de testes
        test_categories = [
            {
                "name": "Unit Tests",
                "command": "python -m pytest tests/unit/ -v --tb=short --disable-warnings --no-header",
                "description": "Executando Testes Unitários",
                "category": "unit",
            },
            {
                "name": "Integration Tests",
                "command": "python -m pytest tests/integration/ -v --tb=short --disable-warnings --no-header",
                "description": "Executando Testes de Integração",
                "category": "integration",
            },
            {
                "name": "Performance Tests",
                "command": "python -m pytest tests/performance/ -v --tb=short --disable-warnings --no-header",
                "description": "Executando Testes de Performance",
                "category": "performance",
            },
            {
                "name": "E2E Tests",
                "command": "python -m pytest tests/e2e/ -v --tb=short --disable-warnings --no-header",
                "description": "Executando Testes End-to-End",
                "category": "e2e",
            },
        ]

        success_categories = 0
        total_categories = len(test_categories)

        # Executar cada categoria
        try:
            for i, test_config in enumerate(test_categories, 1):
                print(
                    f"\n🎯 CATEGORIA {i}/{total_categories}: {test_config['name'].upper()}"
                )

                success, stdout, stderr = self.run_command(
                    test_config["command"],
                    test_config["description"],
                    test_config["category"],
                )

                if success:
                    success_categories += 1

                print(f"✨ Categoria {i}/{total_categories} concluída")

                # Pausa entre categorias
                if i < total_categories:
                    print(f"⏳ Preparando próxima categoria...")
                    time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n🛑 Execução interrompida pelo usuário")
            print(f"✅ Categorias concluídas: {success_categories}/{total_categories}")
            self.results["interrupted"] = True

        self.results["total_duration"] = time.time() - start_total
        self.results["success_categories"] = success_categories
        self.results["total_categories"] = total_categories

        # Gerar relatório consolidado
        self.generate_consolidated_report()

        # Salvar resultados em arquivo
        self.save_results()

    def generate_consolidated_report(self):
        """Gera relatório consolidado de todos os testes"""

        self.print_header("📊 RELATÓRIO CONSOLIDADO DE TESTES", "=")

        # Resumo geral
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0
        total_success = True

        print(f"⏱️  Duração Total: {self.results['total_duration']:.1f}s")

        # Verificar se foi interrompido
        if self.results.get("interrupted"):
            print(
                f"⚠️  Execução INTERROMPIDA ({self.results.get('success_categories', 0)}/{self.results.get('total_categories', 0)} categorias)"
            )

        print()

        # Análise por categoria
        self.print_section("RESUMO POR CATEGORIA")

        for category, data in self.results["categories"].items():
            if "analysis" in data:
                analysis = data["analysis"]

                total_tests += analysis["total_tests"]
                total_passed += analysis["passed"]
                total_failed += analysis["failed"]
                total_skipped += analysis["skipped"]
                total_errors += analysis["errors"]

                if not data["success"]:
                    total_success = False

                # Status da categoria
                status = "✅" if data["success"] else "❌"
                print(
                    f"{status} {category.upper():<12} | "
                    f"Total: {analysis['total_tests']:>3d} | "
                    f"✅ {analysis['passed']:>3d} | "
                    f"❌ {analysis['failed']:>3d} | "
                    f"⏭️  {analysis['skipped']:>3d} | "
                    f"💥 {analysis['errors']:>3d} | "
                    f"⏱️  {data['duration']:>5.1f}s"
                )

        # Totais
        print("-" * 70)
        print(
            f"{'TOTAL':<15} | "
            f"Total: {total_tests:>3d} | "
            f"✅ {total_passed:>3d} | "
            f"❌ {total_failed:>3d} | "
            f"⏭️  {total_skipped:>3d} | "
            f"💥 {total_errors:>3d}"
        )

        # Status geral
        overall_status = (
            "🟢 TODOS OS TESTES PASSARAM" if total_success else "🔴 EXISTEM FALHAS"
        )
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        print(f"\n🎯 STATUS GERAL: {overall_status}")
        print(f"📈 Taxa de Sucesso: {success_rate:.1f}%")

        # Detalhes de falhas
        if self.failed_tests:
            self.print_section("❌ TESTES FALHADOS")
            for i, failed in enumerate(self.failed_tests, 1):
                print(f"{i:2d}. {failed['test']}")
                print(f"    💬 {failed['error']}")

        # Detalhes de testes pulados
        if self.skipped_tests:
            self.print_section("⏭️  TESTES PULADOS")

            # Agrupar por motivo
            skip_reasons = {}
            for skipped in self.skipped_tests:
                reason = skipped["reason"]
                if reason not in skip_reasons:
                    skip_reasons[reason] = []
                skip_reasons[reason].append(skipped["test"])

            for reason, tests in skip_reasons.items():
                print(f"\n💭 Motivo: {reason}")
                for test in tests:
                    print(f"   • {test}")

        # Detalhes de erros
        if self.error_tests:
            self.print_section("💥 TESTES COM ERRO")
            for i, error in enumerate(self.error_tests, 1):
                print(f"{i:2d}. {error['test']}")
                print(f"    💬 {error['error']}")

        # Recomendações
        self.print_section("💡 RECOMENDAÇÕES")

        if total_failed > 0:
            print("🔧 Corrigir testes falhados:")
            print(
                "   • Executar testes individuais: pytest tests/path/to/test.py::test_name -v"
            )
            print("   • Verificar dependências e configurações")
            print("   • Analisar logs detalhados dos erros")

        if total_skipped > 5:
            print("📝 Revisar testes pulados:")
            print("   • Verificar se as condições de skip ainda são válidas")
            print("   • Considerar implementar funcionalidades pendentes")
            print("   • Atualizar configurações de ambiente")

        if total_errors > 0:
            print("🚨 Resolver erros de configuração:")
            print("   • Verificar setup de fixtures")
            print("   • Confirmar dependências instaladas")
            print("   • Checar configurações de banco/Redis")

        print("\n🔧 Comandos úteis:")
        print("   • Executar categoria específica: pytest tests/unit/ -v")
        print("   • Executar com cobertura: pytest --cov=app --cov-report=html")
        print("   • Modo verbose: pytest -v --tb=long")
        print("   • Só falhas: pytest --lf")

    def save_results(self):
        """Salva resultados em arquivo JSON"""

        # Criar diretório de relatórios se não existir
        reports_dir = Path("temp_reports")
        reports_dir.mkdir(exist_ok=True)

        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = reports_dir / f"test_run_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Resultados salvos em: {filename}")
            print(f"📊 Tamanho do arquivo: {filename.stat().st_size:,} bytes")

        except Exception as e:
            print(f"❌ Erro salvando resultados: {str(e)}")


def main():
    """Função principal"""

    # Verificar se estamos no diretório correto
    if not os.path.exists("pytest.ini"):
        print("❌ ERRO: pytest.ini não encontrado")
        print("   Execute este script a partir do diretório raiz do projeto")
        return 1

    # Verificar se pasta de testes existe
    if not os.path.exists("tests"):
        print("❌ ERRO: Diretório 'tests' não encontrado")
        return 1

    print("🧪 WhatsApp Agent - Test Suite Runner")
    print("🔄 Preparando execução de todos os testes...")

    # Executar todos os testes
    runner = TestSuiteRunner()
    runner.run_all_tests()

    # Verificar se houve falhas críticas
    has_failures = any(
        not result["success"] for result in runner.results["categories"].values()
    )

    return 1 if has_failures else 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
