#!/usr/bin/env python3
"""
Execução Rápida de Testes - WhatsApp Agent
Script simplificado para verificação rápida de status
"""

import subprocess
import sys
import time
from datetime import datetime


def quick_test_check():
    """Execução rápida de testes com output mínimo"""

    print("🧪 VERIFICAÇÃO RÁPIDA DE TESTES")
    print("=" * 50)
    print(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
    print()

    categories = [
        ("Unit", "tests/unit/", "🔬"),
        ("Integration", "tests/integration/", "🔗"),
        ("Performance", "tests/performance/", "⚡"),
        ("E2E", "tests/e2e/", "🌐"),
    ]

    total_passed = 0
    total_failed = 0
    total_skipped = 0
    all_success = True

    for name, path, icon in categories:
        print(f"{icon} {name:<12}", end=" ")

        try:
            result = subprocess.run(
                f"python -m pytest {path} --tb=no -q",
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutos
            )

            # Extrair números do output
            output = result.stdout
            passed = output.count(" passed")
            failed = output.count(" failed")
            skipped = output.count(" skipped")

            if "passed" in output:
                # Capturar números reais
                import re

                numbers = re.findall(r"(\d+) (passed|failed|skipped)", output)
                for num, status in numbers:
                    if status == "passed":
                        passed = int(num)
                    elif status == "failed":
                        failed = int(num)
                    elif status == "skipped":
                        skipped = int(num)

            total_passed += passed
            total_failed += failed
            total_skipped += skipped

            if result.returncode == 0:
                print(f"✅ {passed}✅ {skipped}⏭️  {failed}❌")
            else:
                print(f"❌ {passed}✅ {skipped}⏭️  {failed}❌")
                all_success = False

        except subprocess.TimeoutExpired:
            print("⏰ TIMEOUT")
            all_success = False
        except Exception as e:
            print(f"💥 ERRO: {str(e)[:20]}")
            all_success = False

    print()
    print("-" * 50)
    print(f"📊 TOTAL: {total_passed + total_failed + total_skipped} testes")
    print(f"✅ Passou: {total_passed}")
    print(f"❌ Falhou: {total_failed}")
    print(f"⏭️  Pulou: {total_skipped}")

    status = "🟢 SUCESSO" if all_success else "🔴 FALHAS"
    print(f"🎯 Status: {status}")

    return 0 if all_success else 1


if __name__ == "__main__":
    exit(quick_test_check())
