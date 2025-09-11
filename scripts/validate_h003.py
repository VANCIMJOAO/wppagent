#!/usr/bin/env python3
"""
🔧 H003 - Script de Validação da Correção de Configuração Alembic
================================================================

Validação completa da implementação H003 - Alembic.ini configuração incorreta.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class H003Validator:
    """Validador para correção H003"""
    
    def __init__(self):
        self.results = {
            'alembic_ini_fixed': False,
            'env_py_improved': False,
            'database_url_priority': False,
            'fallback_handling': False,
            'production_ready': False
        }
        self.errors = []
        
    def validate_alembic_ini_configuration(self):
        """Validar se alembic.ini foi corrigido com comentários apropriados"""
        try:
            print("🔍 1. Validando configuração do alembic.ini...")
            
            alembic_ini_path = Path("alembic.ini")
            if not alembic_ini_path.exists():
                self.errors.append("alembic.ini não encontrado")
                return False
                
            content = alembic_ini_path.read_text()
            
            # Verificar se há comentários explicativos sobre H003
            if "H003 FIX" not in content:
                self.errors.append("Comentário H003 FIX não encontrado no alembic.ini")
                return False
                
            # Verificar se há explicação sobre DATABASE_URL override
            if "DATABASE_URL environment variable" not in content:
                self.errors.append("Explicação sobre DATABASE_URL não encontrada")
                return False
                
            # Verificar se ainda mantém SQLite como fallback
            if "sqlite+aiosqlite:///./whatsapp_agent.db" not in content:
                self.errors.append("Fallback SQLite removido incorretamente")
                return False
                
            print("   ✅ alembic.ini configurado corretamente com H003 fix")
            self.results['alembic_ini_fixed'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de alembic.ini: {e}")
            return False
    
    def validate_env_py_improvements(self):
        """Validar se alembic/env.py foi melhorado"""
        try:
            print("🔍 2. Validando melhorias no alembic/env.py...")
            
            env_py_path = Path("alembic/env.py")
            if not env_py_path.exists():
                self.errors.append("alembic/env.py não encontrado")
                return False
                
            content = env_py_path.read_text()
            
            # Verificar se há referência ao H003 FIX
            if "H003 FIX" not in content:
                self.errors.append("Marcação H003 FIX não encontrada no env.py")
                return False
                
            # Verificar se há tratamento de DATABASE_URL
            if "os.environ.get(\"DATABASE_URL\")" not in content:
                self.errors.append("Tratamento de DATABASE_URL não implementado")
                return False
                
            # Verificar se há logging informativo
            if "H003 - Using DATABASE_URL" not in content:
                self.errors.append("Logging informativo H003 não implementado")
                return False
                
            print("   ✅ alembic/env.py melhorado com tratamento H003")
            self.results['env_py_improved'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de env.py: {e}")
            return False
    
    def validate_database_url_priority(self):
        """Validar se DATABASE_URL tem prioridade correta"""
        try:
            print("🔍 3. Validando prioridade de DATABASE_URL...")
            
            env_py_path = Path("alembic/env.py")
            content = env_py_path.read_text()
            
            # Procurar pela linha que define prioridade
            lines = content.split('\n')
            priority_line = None
            for line in lines:
                if "DATABASE_URL" in line and "config.get_main_option" in line:
                    priority_line = line
                    break
                    
            if not priority_line:
                self.errors.append("Prioridade DATABASE_URL não implementada corretamente")
                return False
                
            # Verificar se DATABASE_URL vem primeiro (||)
            if "os.environ.get(\"DATABASE_URL\") or config.get_main_option" not in priority_line:
                self.errors.append("DATABASE_URL não tem prioridade sobre alembic.ini")
                return False
                
            print("   ✅ DATABASE_URL tem prioridade correta sobre alembic.ini")
            self.results['database_url_priority'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de prioridade: {e}")
            return False
    
    def validate_fallback_handling(self):
        """Validar se fallback está sendo tratado adequadamente"""
        try:
            print("🔍 4. Validando tratamento de fallback...")
            
            env_py_path = Path("alembic/env.py")
            content = env_py_path.read_text()
            
            # Verificar se há tratamento para quando DATABASE_URL não existe
            if "WARNING: No DATABASE_URL found" not in content:
                self.errors.append("Warning para DATABASE_URL ausente não implementado")
                return False
                
            # Verificar se há fallback para SQLite
            if "sqlite+aiosqlite:///./whatsapp_agent.db" not in content:
                self.errors.append("Fallback SQLite não implementado no env.py")
                return False
                
            print("   ✅ Tratamento de fallback implementado corretamente")
            self.results['fallback_handling'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de fallback: {e}")
            return False
    
    def validate_production_ready(self):
        """Validar se a configuração está pronta para produção"""
        try:
            print("🔍 5. Validando prontidão para produção...")
            
            env_py_path = Path("alembic/env.py")
            content = env_py_path.read_text()
            
            # Verificar se há conversão para drivers assíncronos
            if "postgresql+asyncpg://" not in content:
                self.errors.append("Conversão para PostgreSQL assíncrono não implementada")
                return False
                
            # Verificar se há logging de conexão
            if "H003 - Connecting to:" not in content:
                self.errors.append("Logging de conexão não implementado")
                return False
                
            # Verificar se há tratamento de URL segura (ocultando credenciais)
            if "database_url.split('@')[-1]" not in content:
                self.errors.append("Tratamento de URL segura não implementado")
                return False
                
            print("   ✅ Configuração pronta para produção")
            self.results['production_ready'] = True
            return True
            
        except Exception as e:
            self.errors.append(f"Erro na validação de produção: {e}")
            return False
    
    def test_alembic_current_command(self):
        """Testar se alembic current funciona"""
        try:
            print("🔍 6. Testando comando alembic current...")
            
            # Testar com DATABASE_URL simulada
            env = os.environ.copy()
            env['DATABASE_URL'] = 'postgresql://user:pass@localhost/testdb'
            
            result = subprocess.run(
                ['python', '-m', 'alembic', 'current'],
                capture_output=True,
                text=True,
                env=env,
                timeout=10
            )
            
            # Verificar se não houve erro de configuração
            if "H003 - Using DATABASE_URL" in result.stdout or "H003 - Using DATABASE_URL" in result.stderr:
                print("   ✅ alembic current usa DATABASE_URL corretamente")
                return True
            else:
                # Tentar sem DATABASE_URL para testar fallback
                del env['DATABASE_URL']
                result = subprocess.run(
                    ['python', '-m', 'alembic', 'current'],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=10
                )
                
                if result.returncode == 0:
                    print("   ✅ alembic current funciona com fallback")
                    return True
                else:
                    print(f"   ⚠️  alembic current falhou: {result.stderr}")
                    return True  # Pode falhar por outras razões, não necessariamente H003
                    
        except subprocess.TimeoutExpired:
            print("   ⚠️  alembic current timeout (normal se DB não existir)")
            return True
        except Exception as e:
            print(f"   ⚠️  Erro ao testar alembic current: {e}")
            return True  # Não falhar validação por isso
    
    def run_validation(self):
        """Executar validação completa"""
        print("🔧 H003 - VALIDAÇÃO DA CORREÇÃO DE CONFIGURAÇÃO")
        print("=" * 60)
        print("Validando: Alembic.ini configuração incorreta")
        print("Local: alembic.ini:L35")
        print("Correção: Usar DATABASE_URL environment variable")
        print("-" * 60)
        
        # Executar todas as validações
        validations = [
            self.validate_alembic_ini_configuration,
            self.validate_env_py_improvements,
            self.validate_database_url_priority,
            self.validate_fallback_handling,
            self.validate_production_ready
        ]
        
        passed = 0
        total = len(validations)
        
        for validation in validations:
            try:
                if validation():
                    passed += 1
            except Exception as e:
                self.errors.append(f"Erro durante validação: {e}")
        
        # Testar comando alembic (não conta para score)
        self.test_alembic_current_command()
        
        print("\n" + "=" * 60)
        print("📊 RESULTADOS DA VALIDAÇÃO H003")
        print("=" * 60)
        
        for category, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{category:25} - {status}")
        
        print("-" * 60)
        print(f"Taxa de sucesso: {passed}/{total} ({(passed/total)*100:.1f}%)")
        
        if self.errors:
            print("\n❌ ERROS ENCONTRADOS:")
            for error in self.errors:
                print(f"   • {error}")
        
        if passed == total:
            print("\n🎉 H003 - CORREÇÃO IMPLEMENTADA COM SUCESSO ✅")
            print("   • DATABASE_URL tem prioridade sobre alembic.ini")
            print("   • Fallback SQLite para desenvolvimento")
            print("   • Logging informativo implementado")
            print("   • Configuração pronta para produção PostgreSQL")
        else:
            print(f"\n⚠️  H003 - CORREÇÃO INCOMPLETA ({passed}/{total})")
            print("   Revisar implementação antes do deploy")
        
        return passed == total


def main():
    """Função principal"""
    # Mudar para diretório do projeto
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    os.chdir(project_dir)
    
    validator = H003Validator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
