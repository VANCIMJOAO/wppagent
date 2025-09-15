#!/usr/bin/env python3
"""
Script para gerar relatórios de cobertura de testes
Gera relatórios HTML, JSON e Terminal com análise detalhada
"""

import datetime
import json
import os
import subprocess
from pathlib import Path


def run_command(command, description):
    """Executa comando e retorna resultado"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} concluído")
            return True, result.stdout
        else:
            print(f"❌ Erro em {description}: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ Erro executando {description}: {str(e)}")
        return False, str(e)


def generate_coverage_reports():
    """Gera relatórios de cobertura completos"""
    print("📊 Iniciando Geração de Relatórios de Cobertura")
    print("=" * 60)

    # Limpar relatórios anteriores
    if os.path.exists("htmlcov"):
        run_command("rm -rf htmlcov", "Limpando relatórios anteriores")

    # Executar testes com cobertura
    coverage_commands = [
        (
            "python -m pytest tests/unit/ --cov=app --cov-append",
            "Executando testes unitários",
        ),
        (
            "python -m pytest tests/integration/ --cov=app --cov-append",
            "Executando testes de integração",
        ),
        (
            "python -m pytest tests/performance/ --cov=app --cov-append",
            "Executando testes de performance",
        ),
    ]

    total_success = True
    for command, description in coverage_commands:
        success, output = run_command(command, description)
        if not success:
            print(f"⚠️  Aviso: {description} falhou, continuando...")
            print(output[:500])  # Primeiros 500 caracteres do erro

    # Gerar relatórios finais
    print("\n📋 Gerando Relatórios Finais...")

    # Relatório HTML
    run_command("python -m coverage html", "Gerando relatório HTML")

    # Relatório JSON
    run_command("python -m coverage json", "Gerando relatório JSON")

    # Relatório Terminal
    success, terminal_report = run_command(
        "python -m coverage report", "Gerando relatório terminal"
    )

    # Análise de cobertura por módulo
    analyze_coverage()

    # Resumo final
    print_summary()


def analyze_coverage():
    """Analisa cobertura por módulo"""
    print("\n📈 Análise de Cobertura por Módulo")
    print("-" * 50)

    try:
        if os.path.exists("coverage.json"):
            with open("coverage.json", "r") as f:
                data = json.load(f)

            files = data.get("files", {})

            # Agrupar por módulo
            modules = {}
            for file_path, file_data in files.items():
                if file_path.startswith("app/"):
                    module = file_path.split("/")[1] if "/" in file_path else "root"
                    if module not in modules:
                        modules[module] = {
                            "files": 0,
                            "total_lines": 0,
                            "covered_lines": 0,
                        }

                    modules[module]["files"] += 1
                    summary = file_data.get("summary", {})
                    modules[module]["total_lines"] += summary.get("num_statements", 0)
                    modules[module]["covered_lines"] += summary.get("covered_lines", 0)

            # Imprimir análise
            for module, stats in sorted(modules.items()):
                if stats["total_lines"] > 0:
                    coverage = (stats["covered_lines"] / stats["total_lines"]) * 100
                    print(
                        f"{module:20s} | {coverage:6.1f}% | {stats['files']:3d} arquivos | {stats['total_lines']:4d} linhas"
                    )

            # Cobertura geral
            total_coverage = data.get("totals", {}).get("percent_covered", 0)
            print(f"\n📊 Cobertura Total: {total_coverage:.1f}%")

    except Exception as e:
        print(f"❌ Erro analisando cobertura: {str(e)}")


def print_summary():
    """Imprime resumo final"""
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS RELATÓRIOS DE COBERTURA")
    print("=" * 60)

    # Verificar arquivos gerados
    reports = [
        ("htmlcov/index.html", "📄 Relatório HTML"),
        ("coverage.json", "📊 Relatório JSON"),
        (".coverage", "🗃️  Dados de cobertura"),
    ]

    for file_path, description in reports:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {description}: {file_path} ({size:,} bytes)")
        else:
            print(f"❌ {description}: Não encontrado")

    # Instruções
    print("\n📖 Para visualizar relatórios:")
    print("   • HTML: Abra htmlcov/index.html no navegador")
    print("   • Terminal: python -m coverage report")
    print("   • Detalhado: python -m coverage report --show-missing")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n⏰ Relatório gerado em: {timestamp}")


if __name__ == "__main__":
    generate_coverage_reports()
