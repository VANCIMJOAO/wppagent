#!/usr/bin/env python3
"""
Security Headers Check (Non-blocking)
Verifica se o projeto define cabeçalhos de segurança comuns em algum middleware/config.
Não bloqueia o commit; apenas avisa se não encontrar referências esperadas.
"""

import sys
from pathlib import Path

EXPECTED_KEYWORDS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
]


def search_keywords() -> list[str]:
    root = Path("app")
    findings: list[str] = []
    if not root.exists():
        return findings

    for py in root.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
            for kw in EXPECTED_KEYWORDS:
                if kw in text:
                    findings.append(f"{py}: {kw}")
        except Exception:
            continue
    return findings


def main() -> int:
    results = search_keywords()
    if not results:
        print("⚠️  Não foram encontradas referências a headers de segurança esperados.")
        print("   Verifique `app/security/csp_manager.py` ou middlewares de segurança.")
        return 0
    print("✅ Referências a headers de segurança encontradas (amostragem):")
    for r in results[:10]:
        print(" -", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
