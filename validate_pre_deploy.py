#!/usr/bin/env python3
"""
🔍 VALIDADOR COMPLETO PRÉ-DEPLOY
================================

Script para validar TODOS os aspectos da aplicação antes do push:
- Imports e dependências
- Modelos SQLAlchemy e compatibilidade com PostgreSQL
- Configurações Redis e variáveis de ambiente
- Sintaxe e erros básicos de Python
- Compatibilidade de tipos enum com banco de dados

Evita multiple pushes com pequenos erros!
"""

import os
import sys
import ast
import importlib.util
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configurar logging para este script
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class ValidationResult:
    def __init__(self, category: str):
        self.category = category
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        
    def add_error(self, msg: str):
        self.errors.append(msg)
        
    def add_warning(self, msg: str):
        self.warnings.append(msg)
        
    def add_info(self, msg: str):
        self.info.append(msg)
        
    def is_valid(self) -> bool:
        return len(self.errors) == 0
        
    def print_results(self):
        print(f"\n📋 {self.category}")
        print("=" * 50)
        
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
                
        if self.warnings:
            print("⚠️ WARNINGS:")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        if self.info:
            print("ℹ️ INFO:")
            for info in self.info:
                print(f"  - {info}")
                
        if not self.errors and not self.warnings:
            print("✅ ALL GOOD!")

class PreDeployValidator:
    """Validador completo pré-deploy"""
    
    def __init__(self, project_root: str = "/home/vancim/whats_agent"):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"
        
    def validate_python_syntax(self) -> ValidationResult:
        """Valida sintaxe Python de todos os arquivos"""
        result = ValidationResult("PYTHON SYNTAX")
        
        python_files = list(self.app_dir.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                    
                ast.parse(source_code)
                result.add_info(f"✓ {py_file.relative_to(self.project_root)}")
                
            except SyntaxError as e:
                result.add_error(f"Syntax error in {py_file.relative_to(self.project_root)}: {e}")
            except Exception as e:
                result.add_warning(f"Could not parse {py_file.relative_to(self.project_root)}: {e}")
                
        return result
    
    def validate_imports(self) -> ValidationResult:
        """Valida todos os imports problemáticos conhecidos"""
        result = ValidationResult("IMPORT VALIDATION")
        
        # Problemas conhecidos de imports
        problematic_imports = [
            ("app.utils.logger", "get_logger", "Use logging.getLogger(__name__) instead"),
            ("from app.utils.logger import get_logger", None, "Should use standard logging"),
        ]
        
        python_files = list(self.app_dir.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Verificar imports problemáticos
                for import_pattern, specific_import, message in problematic_imports:
                    if import_pattern in content:
                        if specific_import and specific_import in content:
                            result.add_error(f"{py_file.relative_to(self.project_root)}: {message}")
                        elif not specific_import:
                            result.add_error(f"{py_file.relative_to(self.project_root)}: {message}")
                
                # Verificar imports necessários que podem estar faltando
                if "from typing import" in content:
                    if "List[" in content and "List" not in content.split("from typing import")[1].split("\n")[0]:
                        result.add_warning(f"{py_file.relative_to(self.project_root)}: Uses List[] but doesn't import List")
                    if "Dict[" in content and "Dict" not in content.split("from typing import")[1].split("\n")[0]:
                        result.add_warning(f"{py_file.relative_to(self.project_root)}: Uses Dict[] but doesn't import Dict")
                        
            except Exception as e:
                result.add_warning(f"Could not check imports in {py_file}: {e}")
                
        return result
    
    def validate_redis_configuration(self) -> ValidationResult:
        """Valida configuração Redis"""
        result = ValidationResult("REDIS CONFIGURATION")
        
        # Verificar se REDIS_URL está nas variáveis de ambiente
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            result.add_info(f"REDIS_URL found: {redis_url}")
            if "localhost" in redis_url:
                result.add_warning("REDIS_URL points to localhost - may not work in production")
        else:
            result.add_warning("REDIS_URL not found in environment variables")
        
        # Verificar arquivos que usam Redis
        redis_files = [
            "app/middleware/user_rate_limit.py",
            "app/services/response_control.py", 
            "app/services/state_manager.py",
            "app/config/redis_config.py"
        ]
        
        for redis_file in redis_files:
            file_path = self.project_root / redis_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        
                    if "localhost:6379" in content:
                        result.add_error(f"{redis_file}: Still contains hardcoded localhost:6379")
                    elif "config.redis_url" in content or "redis_config.url" in content:
                        result.add_info(f"{redis_file}: ✓ Uses configuration-based Redis URL")
                        
                except Exception as e:
                    result.add_warning(f"Could not check {redis_file}: {e}")
            else:
                result.add_warning(f"Redis file not found: {redis_file}")
                
        return result
        
    async def validate_database_enums(self) -> ValidationResult:
        """Valida compatibilidade de enums com PostgreSQL"""
        result = ValidationResult("DATABASE ENUM VALIDATION")
        
        try:
            # Tentar importar configuração de database
            sys.path.insert(0, str(self.project_root))
            
            from app.database import AsyncSessionLocal
            from sqlalchemy import text
            
            # Verificar enums no PostgreSQL
            async with AsyncSessionLocal() as session:
                # Verificar permissioncategory enum
                try:
                    perm_result = await session.execute(text("""
                        SELECT unnest(enum_range(NULL::permissioncategory)) as category;
                    """))
                    categories = [r.category for r in perm_result.fetchall()]
                    result.add_info(f"PostgreSQL permissioncategory values: {categories}")
                    
                    # Verificar se Python enum corresponde
                    from app.models.rbac import PermissionCategory
                    python_categories = [cat.value for cat in PermissionCategory]
                    
                    missing_in_db = set(python_categories) - set(categories)
                    missing_in_python = set(categories) - set(python_categories)
                    
                    if missing_in_db:
                        result.add_error(f"PermissionCategory values missing in DB: {missing_in_db}")
                    if missing_in_python:
                        result.add_error(f"DB categories missing in Python enum: {missing_in_python}")
                    if not missing_in_db and not missing_in_python:
                        result.add_info("✓ PermissionCategory enum matches DB")
                        
                except Exception as e:
                    result.add_error(f"Could not validate permissioncategory enum: {e}")
                
                # Verificar risklevel enum
                try:
                    risk_result = await session.execute(text("""
                        SELECT unnest(enum_range(NULL::risklevel)) as risk_level;
                    """))
                    risk_levels = [r.risk_level for r in risk_result.fetchall()]
                    result.add_info(f"PostgreSQL risklevel values: {risk_levels}")
                    
                    from app.models.rbac import RiskLevel
                    python_risks = [risk.value for risk in RiskLevel]
                    
                    missing_in_db = set(python_risks) - set(risk_levels)
                    missing_in_python = set(risk_levels) - set(python_risks)
                    
                    if missing_in_db:
                        result.add_error(f"RiskLevel values missing in DB: {missing_in_db}")
                    if missing_in_python:
                        result.add_error(f"DB risk levels missing in Python enum: {missing_in_python}")
                    if not missing_in_db and not missing_in_python:
                        result.add_info("✓ RiskLevel enum matches DB")
                        
                except Exception as e:
                    result.add_error(f"Could not validate risklevel enum: {e}")
                    
                # Testar inserção de sample permission (dry run)
                try:
                    test_query = text("""
                        SELECT 1 FROM rbac_permissions 
                        WHERE permission_type = :ptype 
                        LIMIT 1;
                    """)
                    
                    await session.execute(test_query, {"ptype": "dashboard:view"})
                    result.add_info("✓ Database query structure is valid")
                    
                except Exception as e:
                    result.add_error(f"Database query test failed: {e}")
                    
        except Exception as e:
            result.add_error(f"Could not connect to database for enum validation: {e}")
            
        return result
    
    def validate_environment_vars(self) -> ValidationResult:
        """Valida variáveis de ambiente essenciais"""
        result = ValidationResult("ENVIRONMENT VARIABLES")
        
        essential_vars = [
            "DATABASE_URL",
            "REDIS_URL", 
            "META_ACCESS_TOKEN",
            "WEBHOOK_VERIFY_TOKEN"
        ]
        
        for var in essential_vars:
            value = os.getenv(var)
            if value:
                # Mascarar valores sensíveis no log
                if "password" in var.lower() or "token" in var.lower() or "key" in var.lower():
                    display_value = f"{value[:10]}***{value[-4:]}" if len(value) > 14 else "***"
                else:
                    display_value = value
                result.add_info(f"{var}: {display_value}")
            else:
                result.add_error(f"Missing environment variable: {var}")
                
        return result
    
    def validate_requirements(self) -> ValidationResult:
        """Valida requirements.txt"""
        result = ValidationResult("REQUIREMENTS.TXT")
        
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            result.add_error("requirements.txt not found")
            return result
            
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.read()
                
            # Verificar dependências conhecidas que causaram problemas
            critical_deps = [
                "pywebpush",
                "http-ece", 
                "cryptography",
                "reportlab",
                "fastapi",
                "sqlalchemy",
                "asyncpg"
            ]
            
            for dep in critical_deps:
                if dep in requirements:
                    result.add_info(f"✓ {dep} found in requirements")
                else:
                    result.add_warning(f"{dep} not found in requirements")
                    
        except Exception as e:
            result.add_error(f"Could not read requirements.txt: {e}")
            
        return result
        
    async def run_full_validation(self) -> Dict[str, ValidationResult]:
        """Executa validação completa"""
        print("🔍 INICIANDO VALIDAÇÃO COMPLETA PRÉ-DEPLOY")
        print("=" * 60)
        
        results = {}
        
        # Validações síncronas
        print("🔄 Validando sintaxe Python...")
        results["syntax"] = self.validate_python_syntax()
        
        print("🔄 Validando imports...")  
        results["imports"] = self.validate_imports()
        
        print("🔄 Validando configuração Redis...")
        results["redis"] = self.validate_redis_configuration()
        
        print("🔄 Validando variáveis de ambiente...")
        results["env_vars"] = self.validate_environment_vars()
        
        print("🔄 Validando requirements.txt...")
        results["requirements"] = self.validate_requirements()
        
        # Validações assíncronas
        print("🔄 Validando enums do banco de dados...")
        try:
            results["db_enums"] = await self.validate_database_enums()
        except Exception as e:
            db_result = ValidationResult("DATABASE ENUM VALIDATION")
            db_result.add_error(f"Failed to validate database enums: {e}")
            results["db_enums"] = db_result
        
        return results
    
    def print_summary(self, results: Dict[str, ValidationResult]):
        """Imprime resumo final"""
        print("\n" + "=" * 60)
        print("📊 RESUMO FINAL DA VALIDAÇÃO")
        print("=" * 60)
        
        total_errors = 0
        total_warnings = 0
        
        for category, result in results.items():
            result.print_results()
            total_errors += len(result.errors)
            total_warnings += len(result.warnings)
            
        print("\n" + "=" * 60)
        
        if total_errors == 0:
            print("🎉 VALIDAÇÃO PASSOU! ✅")
            print("🚀 Seguro para fazer push e deploy!")
            if total_warnings > 0:
                print(f"⚠️ {total_warnings} warnings encontrados (não bloqueantes)")
        else:
            print(f"❌ VALIDAÇÃO FALHOU! {total_errors} erros encontrados")
            print("🛑 CORRIJA OS ERROS ANTES DO PUSH!")
            if total_warnings > 0:
                print(f"⚠️ {total_warnings} warnings adicionais encontrados")
                
        return total_errors == 0

async def main():
    """Função principal"""
    validator = PreDeployValidator()
    results = await validator.run_full_validation()
    success = validator.print_summary(results)
    
    if success:
        print("\n✨ Pronto para deploy!")
        return 0
    else:
        print("\n🔧 Corrija os problemas e execute novamente")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Validação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erro inesperado na validação: {e}")
        sys.exit(1)
