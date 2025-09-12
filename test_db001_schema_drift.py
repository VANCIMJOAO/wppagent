#!/usr/bin/env python3
"""
🔧 DB-001: Schema Drift - Teste e Correção

Verifica e corrige a discrepância entre HEAD arquivo vs DB atual
Migração remove_duplicate_admin_2025 não implementada ou não aplicada

Evidência: "HEAD aponta para remove_duplicate_admin_2025 mas DB está em pd002_schema_cleanup"
Risco: Schema drift - inconsistência entre estado do código e banco de dados
"""

import asyncio
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao Python path
sys.path.insert(0, str(Path(__file__).parent))

class DB001SchemaDriftValidator:
    """Validador para problema DB-001: Schema Drift"""
    
    def __init__(self):
        self.workspace_root = Path(__file__).parent
        self.results = {
            "test_id": "DB-001", 
            "description": "Schema Drift - HEAD vs DB atual",
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
    
    def run_alembic_command(self, command):
        """Executa comando Alembic e retorna resultado"""
        try:
            result = subprocess.run(
                f"cd {self.workspace_root} && alembic {command}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Timeout executando comando Alembic",
                "returncode": -1
            }
    
    def test_alembic_current_status(self):
        """Teste 1: Verificar estado atual do Alembic"""
        print("🔍 Teste 1: Verificando estado atual do Alembic...")
        
        result = self.run_alembic_command("current")
        
        test_result = {
            "test_name": "alembic_current_status",
            "description": "Verifica qual migração está aplicada no DB",
            "success": result["success"],
            "details": {
                "command": "alembic current",
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "current_migration": "unknown"
            }
        }
        
        if result["success"]:
            # Extrair migração atual do output
            output_lines = result["stdout"].split('\\n')
            for line in output_lines:
                if line.strip() and not line.startswith("INFO") and not line.startswith("H003"):
                    test_result["details"]["current_migration"] = line.strip()
                    break
            
            print(f"✅ Estado atual: {test_result['details']['current_migration']}")
        else:
            print(f"❌ Erro ao verificar estado: {result['stderr']}")
        
        self.results["tests"].append(test_result)
        return test_result["success"]
    
    def test_alembic_heads(self):
        """Teste 2: Verificar HEADs disponíveis"""
        print("🔍 Teste 2: Verificando HEADs disponíveis...")
        
        result = self.run_alembic_command("heads")
        
        test_result = {
            "test_name": "alembic_heads", 
            "description": "Lista todos os HEADs disponíveis",
            "success": result["success"],
            "details": {
                "command": "alembic heads",
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "heads": []
            }
        }
        
        if result["success"]:
            # Extrair HEADs do output
            output_lines = result["stdout"].split('\\n')
            for line in output_lines:
                if line.strip() and not line.startswith("INFO") and not line.startswith("/"):
                    test_result["details"]["heads"].append(line.strip())
            
            print(f"✅ HEADs encontrados: {test_result['details']['heads']}")
        else:
            print(f"❌ Erro ao verificar HEADs: {result['stderr']}")
        
        self.results["tests"].append(test_result)
        return test_result["success"]
    
    def test_migration_files_consistency(self):
        """Teste 3: Verificar consistência dos arquivos de migração"""
        print("🔍 Teste 3: Verificando consistência dos arquivos de migração...")
        
        versions_dir = self.workspace_root / "alembic" / "versions"
        migration_files = list(versions_dir.glob("*.py"))
        
        test_result = {
            "test_name": "migration_files_consistency",
            "description": "Verifica arquivos de migração duplicados ou vazios",
            "success": True,
            "details": {
                "total_files": len(migration_files),
                "files": [],
                "duplicates": [],
                "empty_migrations": []
            }
        }
        
        revision_ids = {}
        
        for file_path in migration_files:
            if file_path.name.startswith("__"):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extrair revision ID
                revision_line = [line for line in content.split('\\n') if 'revision =' in line or 'revision:' in line]
                if revision_line:
                    revision_id = revision_line[0].split('=')[1].strip().strip("'\"")
                    
                    if revision_id in revision_ids:
                        test_result["details"]["duplicates"].append({
                            "revision_id": revision_id,
                            "files": [str(revision_ids[revision_id]), str(file_path)]
                        })
                        test_result["success"] = False
                    else:
                        revision_ids[revision_id] = file_path
                
                # Verificar se upgrade/downgrade estão implementados
                if 'def upgrade() -> None:' in content and 'pass' in content:
                    if content.count('pass') >= 2:  # upgrade e downgrade vazios
                        test_result["details"]["empty_migrations"].append(str(file_path))
                        test_result["success"] = False
                
                test_result["details"]["files"].append({
                    "path": str(file_path),
                    "size": len(content),
                    "has_implementation": 'pass' not in content or content.count('pass') < 2
                })
                
            except Exception as e:
                test_result["details"]["files"].append({
                    "path": str(file_path),
                    "error": str(e)
                })
                test_result["success"] = False
        
        if test_result["success"]:
            print(f"✅ {len(migration_files)} arquivos de migração verificados, sem problemas")
        else:
            print(f"❌ Problemas encontrados:")
            if test_result["details"]["duplicates"]:
                print(f"   • {len(test_result['details']['duplicates'])} duplicatas")
            if test_result["details"]["empty_migrations"]:
                print(f"   • {len(test_result['details']['empty_migrations'])} migrações vazias")
        
        self.results["tests"].append(test_result)
        return test_result["success"]
    
    def test_schema_drift_resolution(self):
        """Teste 4: Tentar resolver schema drift aplicando migrações"""
        print("🔍 Teste 4: Tentando resolver schema drift...")
        
        # Primeiro, tentar aplicar migrações pendentes
        result = self.run_alembic_command("upgrade head")
        
        test_result = {
            "test_name": "schema_drift_resolution",
            "description": "Aplica migrações pendentes para resolver schema drift",
            "success": result["success"],
            "details": {
                "command": "alembic upgrade head",
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "resolution_attempt": "upgrade_head"
            }
        }
        
        if result["success"]:
            print("✅ Migrações aplicadas com sucesso")
            
            # Verificar estado após upgrade
            current_result = self.run_alembic_command("current")
            test_result["details"]["final_state"] = current_result["stdout"]
            
        else:
            print(f"❌ Erro ao aplicar migrações: {result['stderr']}")
            
            # Se falhou, pode ser problema de compatibilidade SQLite
            if "unknown function: now()" in result["stderr"]:
                test_result["details"]["sqlite_compatibility_issue"] = True
                test_result["details"]["resolution_suggestion"] = "Usar CURRENT_TIMESTAMP ao invés de now() para SQLite"
        
        self.results["tests"].append(test_result)
        return test_result["success"]
    
    def generate_fix_proposal(self):
        """Gera proposta de correção baseada nos testes"""
        print("\\n🔧 Gerando proposta de correção...")
        
        success_count = sum(1 for test in self.results["tests"] if test["success"])
        total_tests = len(self.results["tests"])
        
        proposal = {
            "test_summary": {
                "total_tests": total_tests,
                "passed": success_count,
                "failed": total_tests - success_count,
                "success_rate": f"{(success_count/total_tests)*100:.1f}%"
            },
            "db001_status": "REQUIRES_ATTENTION" if success_count < total_tests else "RESOLVED",
            "actions_required": []
        }
        
        # Analisar resultados e gerar ações
        for test in self.results["tests"]:
            if not test["success"]:
                if test["test_name"] == "migration_files_consistency":
                    if test["details"]["duplicates"]:
                        proposal["actions_required"].append({
                            "action": "remove_duplicate_migration_files",
                            "description": "Remover arquivos de migração duplicados",
                            "files_to_remove": [dup["files"][0] for dup in test["details"]["duplicates"]]
                        })
                    
                    if test["details"]["empty_migrations"]:
                        proposal["actions_required"].append({
                            "action": "implement_or_remove_empty_migrations", 
                            "description": "Implementar ou remover migrações vazias",
                            "empty_files": test["details"]["empty_migrations"]
                        })
                
                elif test["test_name"] == "schema_drift_resolution":
                    if test["details"].get("sqlite_compatibility_issue"):
                        proposal["actions_required"].append({
                            "action": "fix_sqlite_compatibility",
                            "description": "Corrigir problemas de compatibilidade com SQLite",
                            "issue": "Função now() não existe no SQLite, usar CURRENT_TIMESTAMP"
                        })
        
        self.results["fix_proposal"] = proposal
        
        print(f"📊 Resumo: {success_count}/{total_tests} testes passaram")
        print(f"🎯 Status DB-001: {proposal['db001_status']}")
        
        if proposal["actions_required"]:
            print("🔧 Ações necessárias:")
            for i, action in enumerate(proposal["actions_required"], 1):
                print(f"   {i}. {action['description']}")
        
        return proposal
    
    def save_results(self):
        """Salva resultados em arquivo JSON"""
        output_file = self.workspace_root / "db001_validation_report.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\\n📄 Relatório salvo em: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {e}")
            return False
    
    async def run_all_tests(self):
        """Executa todos os testes de validação DB-001"""
        print("🚀 Iniciando validação DB-001: Schema Drift")
        print("=" * 60)
        
        # Executar testes sequencialmente
        tests = [
            self.test_alembic_current_status,
            self.test_alembic_heads,
            self.test_migration_files_consistency,
            self.test_schema_drift_resolution
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Erro no teste {test.__name__}: {e}")
                results.append(False)
        
        # Gerar proposta de correção
        proposal = self.generate_fix_proposal()
        
        # Salvar resultados
        self.save_results()
        
        print("\\n" + "=" * 60)
        print("🏁 Validação DB-001 concluída!")
        
        return proposal

async def main():
    """Função principal"""
    validator = DB001SchemaDriftValidator()
    proposal = await validator.run_all_tests()
    
    # Retornar código de saída baseado no resultado
    if proposal["db001_status"] == "RESOLVED":
        print("\\n✅ DB-001 RESOLVIDO!")
        sys.exit(0)
    else:
        print("\\n⚠️  DB-001 REQUER ATENÇÃO!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
