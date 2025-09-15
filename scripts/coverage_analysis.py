#!/usr/bin/env python3
"""
Relatório de Cobertura de Testes - WhatsApp Agent
Análise detalhada dos resultados de cobertura
"""

import json
import os
from datetime import datetime


def generate_coverage_summary():
    """Gera resumo detalhado da cobertura"""

    print("=" * 80)
    print("📊 RELATÓRIO DE COBERTURA DE TESTES - WHATSAPP AGENT")
    print("=" * 80)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()

    # Verificar se existe arquivo de cobertura JSON
    if not os.path.exists("coverage.json"):
        print("❌ Arquivo coverage.json não encontrado")
        return

    with open("coverage.json", "r") as f:
        data = json.load(f)

    # Cobertura geral
    totals = data.get("totals", {})
    total_coverage = totals.get("percent_covered", 0)
    total_lines = totals.get("num_statements", 0)
    covered_lines = totals.get("covered_lines", 0)
    missing_lines = total_lines - covered_lines

    print("🎯 MÉTRICAS GERAIS")
    print("-" * 40)
    print(f"Cobertura Total:     {total_coverage:.1f}%")
    print(f"Linhas Totais:       {total_lines:,}")
    print(f"Linhas Cobertas:     {covered_lines:,}")
    print(f"Linhas Não Cobertas: {missing_lines:,}")
    print()

    # Análise por módulo
    print("📁 COBERTURA POR MÓDULO")
    print("-" * 60)
    print(f"{'Módulo':<25} {'Cobertura':<12} {'Arquivos':<10} {'Linhas':<10}")
    print("-" * 60)

    modules = {}
    files = data.get("files", {})

    for file_path, file_data in files.items():
        if file_path.startswith("app/"):
            # Extrair módulo
            parts = file_path.split("/")
            if len(parts) > 1:
                module = parts[1]
            else:
                module = "root"

            if module not in modules:
                modules[module] = {
                    "files": 0,
                    "total_lines": 0,
                    "covered_lines": 0,
                    "coverage": 0,
                }

            summary = file_data.get("summary", {})
            modules[module]["files"] += 1
            modules[module]["total_lines"] += summary.get("num_statements", 0)
            modules[module]["covered_lines"] += summary.get("covered_lines", 0)

    # Calcular cobertura por módulo
    for module in modules:
        if modules[module]["total_lines"] > 0:
            modules[module]["coverage"] = (
                modules[module]["covered_lines"] / modules[module]["total_lines"]
            ) * 100

    # Ordenar por cobertura (maior para menor)
    sorted_modules = sorted(
        modules.items(), key=lambda x: x[1]["coverage"], reverse=True
    )

    for module, stats in sorted_modules:
        print(
            f"{module:<25} {stats['coverage']:>6.1f}%     {stats['files']:>3d}       {stats['total_lines']:>6,d}"
        )

    print()

    # Classificação de módulos
    print("🎯 CLASSIFICAÇÃO DE COBERTURA")
    print("-" * 40)

    excellent = []  # >= 90%
    good = []  # 70-89%
    fair = []  # 50-69%
    poor = []  # 30-49%
    critical = []  # < 30%

    for module, stats in modules.items():
        coverage = stats["coverage"]
        if coverage >= 90:
            excellent.append((module, coverage))
        elif coverage >= 70:
            good.append((module, coverage))
        elif coverage >= 50:
            fair.append((module, coverage))
        elif coverage >= 30:
            poor.append((module, coverage))
        else:
            critical.append((module, coverage))

    categories = [
        ("🟢 Excelente (≥90%)", excellent),
        ("🔵 Boa (70-89%)", good),
        ("🟡 Regular (50-69%)", fair),
        ("🟠 Baixa (30-49%)", poor),
        ("🔴 Crítica (<30%)", critical),
    ]

    for category_name, category_modules in categories:
        if category_modules:
            print(f"\n{category_name}:")
            for module, coverage in sorted(
                category_modules, key=lambda x: x[1], reverse=True
            ):
                print(f"  • {module}: {coverage:.1f}%")

    # Arquivos com maior necessidade de testes
    print("\n🎯 PRIORIDADES PARA MELHORIA")
    print("-" * 50)

    low_coverage_files = []
    for file_path, file_data in files.items():
        if file_path.startswith("app/"):
            summary = file_data.get("summary", {})
            coverage = summary.get("percent_covered", 0)
            lines = summary.get("num_statements", 0)

            # Focar em arquivos com muitas linhas e baixa cobertura
            if lines > 50 and coverage < 50:
                low_coverage_files.append((file_path, coverage, lines))

    # Ordenar por impacto (linhas * (100 - cobertura))
    low_coverage_files.sort(key=lambda x: x[2] * (100 - x[1]), reverse=True)

    print("Arquivos com maior impacto potencial:")
    for i, (file_path, coverage, lines) in enumerate(low_coverage_files[:10]):
        impact_score = lines * (100 - coverage) / 100
        print(
            f"{i+1:2d}. {file_path:<40} {coverage:>5.1f}% ({lines:>3d} linhas, impacto: {impact_score:.0f})"
        )

    # Recomendações
    print("\n💡 RECOMENDAÇÕES")
    print("-" * 40)

    if total_coverage < 30:
        status = "🔴 CRÍTICA"
        recommendations = [
            "Implementar testes unitários básicos para todos os módulos",
            "Focar em cobertura de modelos e schemas (alta prioridade)",
            "Criar testes de integração para endpoints principais",
        ]
    elif total_coverage < 50:
        status = "🟠 BAIXA"
        recommendations = [
            "Expandir testes para módulos de serviços e rotas",
            "Implementar testes de middleware e autenticação",
            "Adicionar testes de validação e tratamento de erros",
        ]
    elif total_coverage < 70:
        status = "🟡 REGULAR"
        recommendations = [
            "Melhorar cobertura de casos edge e tratamento de exceções",
            "Adicionar testes de performance e stress",
            "Implementar testes de segurança mais abrangentes",
        ]
    elif total_coverage < 90:
        status = "🔵 BOA"
        recommendations = [
            "Otimizar testes existentes para melhor cobertura",
            "Adicionar testes de regressão",
            "Focar em cenários complexos e integrações",
        ]
    else:
        status = "🟢 EXCELENTE"
        recommendations = [
            "Manter qualidade dos testes existentes",
            "Implementar testes de mutação",
            "Adicionar métricas de qualidade de código",
        ]

    print(f"Status Geral: {status} ({total_coverage:.1f}%)")
    print("\nAções Recomendadas:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")

    print("\n" + "=" * 80)
    print("📋 Para visualizar relatório detalhado: abra htmlcov/index.html")
    print("🔍 Para análise específica: python -m coverage report --show-missing")
    print("=" * 80)


if __name__ == "__main__":
    generate_coverage_summary()
