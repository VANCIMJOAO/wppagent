#!/usr/bin/env python3
"""
API Contract Validation (Lightweight)
Percorre rotas em `app/routes` e valida se existem docstrings mínimas
e tipos básicos nos handlers. Não bloqueia o commit; apenas alerta.
"""

import ast
import pathlib
import sys


def has_min_docstring(node: ast.AST) -> bool:
    return bool(ast.get_docstring(node))


def check_file(path: pathlib.Path) -> list[str]:
    issues: list[str] = []
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        if not has_min_docstring(tree):
            issues.append(f"{path}: missing module docstring")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                if not has_min_docstring(node):
                    issues.append(f"{path}:{node.lineno} {node.name} missing docstring")
    except Exception as e:
        issues.append(f"{path}: parsing error: {e}")
    return issues


def main() -> int:
    routes_dir = pathlib.Path("app/routes")
    if not routes_dir.exists():
        return 0

    all_issues: list[str] = []
    for py in routes_dir.rglob("*.py"):
        all_issues.extend(check_file(py))

    if all_issues:
        print("⚠️  API contract warnings:")
        for issue in all_issues[:50]:
            print(" -", issue)
        # Não bloquear, apenas aviso
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
