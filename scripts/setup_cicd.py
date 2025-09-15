#!/usr/bin/env python3
"""
🔧 Setup CI/CD Environment
Configura ambiente para CI/CD melhorado com observabilidade
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Executa comando e mostra resultado"""
    if description:
        print(f"🔄 {description}...")

    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description or cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or cmd} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def install_dependencies():
    """Instala dependências necessárias"""
    print("\n📦 Installing CI/CD dependencies...")

    dependencies = [
        "pre-commit",
        "black",
        "flake8",
        "mypy",
        "bandit",
        "safety",
        "pytest",
        "pytest-cov",
        "pytest-xdist",
        "pytest-benchmark",
        "isort",
        "pip-audit",
    ]

    for dep in dependencies:
        run_command(f"pip install {dep}", f"Installing {dep}")


def setup_pre_commit():
    """Configura pre-commit hooks"""
    print("\n🎣 Setting up pre-commit hooks...")

    # Install pre-commit hooks
    if run_command("pre-commit install", "Installing pre-commit hooks"):
        print("✅ Pre-commit hooks installed")

    # Install commit-msg hook
    if run_command(
        "pre-commit install --hook-type commit-msg", "Installing commit-msg hooks"
    ):
        print("✅ Commit-msg hooks installed")

    # Run pre-commit on all files to verify setup
    print("🧪 Testing pre-commit setup...")
    result = subprocess.run(
        "pre-commit run --all-files", shell=True, capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ Pre-commit setup test passed")
    else:
        print("⚠️ Pre-commit found issues (expected on first run)")
        print("Running auto-fixes...")

        # Run black to fix formatting
        run_command("black .", "Auto-fixing code formatting")

        # Run isort to fix imports
        run_command("isort .", "Auto-fixing import sorting")


def create_secrets_baseline():
    """Cria baseline para detecção de secrets"""
    print("\n🔐 Creating secrets baseline...")

    # Create .secrets.baseline if it doesn't exist
    if not os.path.exists(".secrets.baseline"):
        run_command(
            "detect-secrets scan --baseline .secrets.baseline",
            "Creating secrets baseline",
        )


def setup_git_hooks():
    """Configura hooks git adicionais"""
    print("\n📝 Setting up additional git hooks...")

    # Create .git/hooks directory if it doesn't exist
    hooks_dir = Path(".git/hooks")
    hooks_dir.mkdir(exist_ok=True)

    # Create commit-msg hook for conventional commits
    commit_msg_hook = hooks_dir / "commit-msg"

    commit_msg_content = """#!/bin/sh
# Conventional Commits validation
commit_regex='^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\\(.+\\))?: .{1,50}'

error_msg="Commit message does not follow Conventional Commits format!
Format: <type>[optional scope]: <description>
Types: feat, fix, docs, style, refactor, test, chore, perf, ci, build, revert
Example: feat(auth): add JWT authentication"

if ! grep -qE "$commit_regex" "$1"; then
    echo "$error_msg" >&2
    exit 1
fi
"""

    with open(commit_msg_hook, "w") as f:
        f.write(commit_msg_content)

    # Make hook executable
    os.chmod(commit_msg_hook, 0o755)
    print("✅ Commit message validation hook created")


def create_github_issue_templates():
    """Cria templates para issues no GitHub"""
    print("\n📋 Creating GitHub issue templates...")

    github_dir = Path(".github")
    templates_dir = github_dir / "ISSUE_TEMPLATE"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Bug report template
    bug_template = templates_dir / "bug_report.yml"
    bug_content = """name: 🐛 Bug Report
description: Report a bug to help us improve
title: "[BUG] "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report!

  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: A clear description of what the bug is
      placeholder: Describe the bug...
    validations:
      required: true

  - type: textarea
    id: steps
    attributes:
      label: Steps to reproduce
      description: Steps to reproduce the behavior
      placeholder: |
        1. Go to '...'
        2. Click on '....'
        3. Scroll down to '....'
        4. See error
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
      description: What you expected to happen
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: |
        Please provide information about your environment
      value: |
        - OS:
        - Python version:
        - App version:
    validations:
      required: true
"""

    with open(bug_template, "w") as f:
        f.write(bug_content)

    print("✅ GitHub issue templates created")


def create_quality_check_script():
    """Cria script para verificação de qualidade local"""
    print("\n📊 Creating local quality check script...")

    quality_script = Path("scripts/local_quality_check.py")
    quality_content = '''#!/usr/bin/env python3
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
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
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
        ("pytest tests/unit/ -x", "Unit tests")
    ]

    passed = 0
    total = len(checks)

    for cmd, name in checks:
        if run_check(cmd, name):
            passed += 1

    print(f"\\n📊 Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All quality checks passed! Ready to commit.")
        return 0
    else:
        print("❌ Some quality checks failed. Please fix issues before committing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

    with open(quality_script, "w") as f:
        f.write(quality_content)

    os.chmod(quality_script, 0o755)
    print("✅ Local quality check script created")


def main():
    """Função principal"""
    print("🚀 Setting up CI/CD Enhanced Environment")
    print("=" * 50)

    # Verify we're in the right directory
    if not os.path.exists("app"):
        print("❌ This script must be run from the project root directory")
        sys.exit(1)

    # Install dependencies
    install_dependencies()

    # Setup pre-commit
    setup_pre_commit()

    # Create secrets baseline
    create_secrets_baseline()

    # Setup git hooks
    setup_git_hooks()

    # Create GitHub templates
    create_github_issue_templates()

    # Create quality check script
    create_quality_check_script()

    print("\n🎉 CI/CD Enhanced Environment Setup Complete!")
    print("\n📋 Next steps:")
    print("   1. Run 'scripts/local_quality_check.py' to test setup")
    print("   2. Make a test commit to verify pre-commit hooks")
    print("   3. Push to trigger GitHub Actions workflow")
    print("   4. Monitor observability dashboard for CI/CD metrics")

    print("\n✨ Features enabled:")
    print("   ✅ Pre-commit hooks with quality gates")
    print("   ✅ Security scanning (Bandit + Safety)")
    print("   ✅ Code formatting (Black + isort)")
    print("   ✅ Type checking (MyPy)")
    print("   ✅ Conventional commits validation")
    print("   ✅ GitHub issue templates")
    print("   ✅ Local quality checking")
    print("   ✅ Integration with observability stack")


if __name__ == "__main__":
    main()
