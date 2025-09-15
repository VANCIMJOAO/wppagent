#!/usr/bin/env python3
"""
📊 Local Quality Check
Executa verificações de qualidade localmente antes do commit
"""

import subprocess
import sys


def run_check(cmd, name):
    """Executa verificação individual"""
    print(f"🔍 Running {name}...")
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {name} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} failed:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def main():
    """Executa todas as verificações"""
    print("🎯 Running local quality checks...")

    checks = [
        ("black --check .", "Code formatting"),
        ("isort --check-only .", "Import sorting"),
        ("flake8 app/", "Linting"),
        ("mypy app/ --ignore-missing-imports", "Type checking"),
        ("bandit -r app/", "Security scan"),
        ("safety check", "Dependency vulnerabilities"),
        ("pytest tests/unit/ -x", "Unit tests"),
    ]

    passed = 0
    total = len(checks)

    for cmd, name in checks:
        if run_check(cmd, name):
            passed += 1

    print(f"\n📊 Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All quality checks passed! Ready to commit.")
        return 0
    else:
        print("❌ Some quality checks failed. Please fix issues before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
