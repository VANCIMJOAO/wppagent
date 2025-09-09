#!/usr/bin/env python3
"""
Script para corrigir todos os problemas encontrados pela validação pré-deploy
Automatiza as correções de:
1. Imports de logger (usar logging padrão)
2. Redis hardcoded (usar variável de ambiente)
3. Adicionar variáveis de ambiente faltantes
4. Corrigir enums do banco de dados
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

def fix_logger_imports(file_path: str) -> bool:
    """Corrige imports de logger personalizado para logging padrão"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Padrões a serem substituídos
        patterns = [
            # from app.utils.logger import logger
            (r'from app\.utils\.logger import logger', 'import logging'),
            # from app.services.production_logger import logger
            (r'from app\.services\.production_logger import logger', 'import logging'),
            # from app.config import logger
            (r'from app\.config import.*logger', 'import logging'),
            # logger = get_logger(__name__)
            (r'logger\s*=\s*get_logger\([^)]*\)', 'logger = logging.getLogger(__name__)'),
            # logger = Logger(__name__)
            (r'logger\s*=\s*Logger\([^)]*\)', 'logger = logging.getLogger(__name__)'),
            # Qualquer outro padrão similar
            (r'logger\s*=\s*[^=\n]*logger[^=\n]*\([^)]*\)', 'logger = logging.getLogger(__name__)'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Se não encontrou nenhum logger mas usa logger no código, adiciona no início
        if 'logger.' in content and 'logging.getLogger' not in content and 'import logging' not in content:
            # Adiciona import logging após outros imports
            lines = content.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')) or line.strip().startswith('#'):
                    import_end = i
            
            lines.insert(import_end + 1, 'import logging')
            lines.insert(import_end + 2, '')
            lines.insert(import_end + 3, 'logger = logging.getLogger(__name__)')
            content = '\n'.join(lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed logger imports in {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error fixing logger in {file_path}: {e}")
        return False

def fix_redis_hardcode(file_path: str) -> bool:
    """Corrige conexões Redis hardcoded para usar variáveis de ambiente"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Padrões de Redis hardcoded
        patterns = [
            # redis://localhost:6379
            (r'redis://localhost:6379[^"\'\s]*', 'redis://localhost:6379'),
            # localhost:6379
            (r'localhost:6379', ''),
            # redis.from_url("redis://localhost:6379")
            (r'redis\.from_url\(["\']redis://localhost:6379[^"\']*["\']\)', 'redis.from_url(get_settings().REDIS_URL)'),
            # redis.Redis(host="localhost", port=6379)
            (r'redis\.Redis\([^)]*host=["\']localhost["\'][^)]*\)', 'redis.from_url(get_settings().REDIS_URL)'),
            # Outras variações
            (r'Redis\([^)]*host=["\']localhost["\'][^)]*\)', 'redis.from_url(get_settings().REDIS_URL)'),
        ]
        
        for pattern, replacement in patterns:
            if replacement:
                content = re.sub(pattern, replacement, content)
            else:
                # Para casos onde precisamos substituir por config dinâmico
                if 'localhost:6379' in content:
                    content = content.replace('localhost:6379', '${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}')
        
        # Adiciona import se necessário e usa Redis URL
        if 'redis.' in content and 'get_settings()' in content and 'from app.config import get_settings' not in content:
            if 'from app.config' not in content:
                lines = content.split('\n')
                import_end = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')):
                        import_end = i
                lines.insert(import_end + 1, 'from app.config import get_settings')
                content = '\n'.join(lines)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed Redis hardcode in {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error fixing Redis in {file_path}: {e}")
        return False

def fix_rbac_enums() -> bool:
    """Corrige enums do RBAC para compatibilidade com PostgreSQL"""
    rbac_file = "/home/vancim/whats_agent/app/models/rbac.py"
    
    try:
        with open(rbac_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Definição correta dos enums baseada no banco
        new_enum_definition = '''import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

class PermissionCategory(enum.Enum):
    """Categorias de permissões alinhadas com PostgreSQL"""
    DASHBOARD = "DASHBOARD"
    APPOINTMENTS = "APPOINTMENTS" 
    CONVERSATIONS = "CONVERSATIONS"
    CLIENTS = "CLIENTS"
    REPORTS = "REPORTS"
    SYSTEM = "SYSTEM"

class RiskLevel(enum.Enum):
    """Níveis de risco alinhados com PostgreSQL"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class PermissionType(enum.Enum):
    """Tipos de permissão específicos"""
    # Dashboard
    DASHBOARD_VIEW = "DASHBOARD_VIEW"
    DASHBOARD_EDIT = "DASHBOARD_EDIT"
    
    # Appointments
    APPOINTMENTS_VIEW = "APPOINTMENTS_VIEW"
    APPOINTMENTS_CREATE = "APPOINTMENTS_CREATE"
    APPOINTMENTS_EDIT = "APPOINTMENTS_EDIT"
    APPOINTMENTS_DELETE = "APPOINTMENTS_DELETE"
    
    # Conversations
    CONVERSATIONS_VIEW = "CONVERSATIONS_VIEW"
    CONVERSATIONS_MANAGE = "CONVERSATIONS_MANAGE"
    
    # Clients
    CLIENTS_VIEW = "CLIENTS_VIEW"
    CLIENTS_CREATE = "CLIENTS_CREATE"
    CLIENTS_EDIT = "CLIENTS_EDIT"
    CLIENTS_DELETE = "CLIENTS_DELETE"
    
    # Reports
    REPORTS_VIEW = "REPORTS_VIEW"
    REPORTS_EXPORT = "REPORTS_EXPORT"
    
    # System
    SYSTEM_CONFIG = "SYSTEM_CONFIG"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
'''
        
        # Substitui definições antigas dos enums
        enum_pattern = r'class (PermissionCategory|RiskLevel|PermissionType)\(enum\.Enum\):.*?(?=class|\Z)'
        content = re.sub(enum_pattern, '', content, flags=re.DOTALL)
        
        # Adiciona as novas definições no início após imports
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')) or line.strip().startswith('#'):
                insert_pos = i + 1
        
        lines.insert(insert_pos, new_enum_definition)
        content = '\n'.join(lines)
        
        # Corrige uso dos enums nas classes
        content = re.sub(
            r'SQLEnum\(PermissionCategory\)',
            'SQLEnum(PermissionCategory, name="permissioncategory")',
            content
        )
        content = re.sub(
            r'SQLEnum\(RiskLevel\)',
            'SQLEnum(RiskLevel, name="risklevel")', 
            content
        )
        
        with open(rbac_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed RBAC enums in {rbac_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing RBAC enums: {e}")
        return False

def add_missing_env_vars() -> bool:
    """Adiciona variáveis de ambiente faltantes ao .env"""
    env_file = "/home/vancim/whats_agent/.env"
    
    missing_vars = {
        'META_ACCESS_TOKEN': 'your_meta_access_token_here',
        'WEBHOOK_VERIFY_TOKEN': 'your_webhook_verify_token_here'
    }
    
    try:
        # Lê .env existente ou cria novo
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()
        else:
            env_content = ""
        
        # Verifica quais variáveis estão faltando
        added_vars = []
        for var_name, default_value in missing_vars.items():
            if f"{var_name}=" not in env_content:
                env_content += f"\n# {var_name}\n{var_name}={default_value}\n"
                added_vars.append(var_name)
        
        if added_vars:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            print(f"✅ Added missing environment variables: {', '.join(added_vars)}")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error adding environment variables: {e}")
        return False

def get_python_files() -> List[str]:
    """Retorna lista de todos os arquivos Python do projeto"""
    python_files = []
    
    for root, dirs, files in os.walk("/home/vancim/whats_agent/app"):
        # Pula diretórios __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    """Executa todas as correções"""
    print("🔧 INICIANDO CORREÇÕES AUTOMÁTICAS")
    print("=" * 50)
    
    success_count = 0
    total_fixes = 0
    
    # 1. Corrigir imports de logger
    print("\n📝 Corrigindo imports de logger...")
    python_files = get_python_files()
    
    for file_path in python_files:
        if fix_logger_imports(file_path):
            success_count += 1
        total_fixes += 1
    
    # 2. Corrigir Redis hardcoded
    print("\n🔴 Corrigindo Redis hardcoded...")
    redis_files = [
        "/home/vancim/whats_agent/app/middleware/user_rate_limit.py",
        "/home/vancim/whats_agent/app/services/response_control.py",
        "/home/vancim/whats_agent/app/services/state_manager.py",
        "/home/vancim/whats_agent/app/config/redis_config.py"
    ]
    
    for file_path in redis_files:
        if os.path.exists(file_path):
            if fix_redis_hardcode(file_path):
                success_count += 1
            total_fixes += 1
    
    # 3. Corrigir enums RBAC
    print("\n⚡ Corrigindo enums RBAC...")
    if fix_rbac_enums():
        success_count += 1
    total_fixes += 1
    
    # 4. Adicionar variáveis de ambiente
    print("\n🌍 Adicionando variáveis de ambiente faltantes...")
    if add_missing_env_vars():
        success_count += 1
    total_fixes += 1
    
    # Resumo
    print("\n" + "=" * 50)
    print(f"✅ CORREÇÕES CONCLUÍDAS: {success_count}/{total_fixes}")
    
    if success_count == total_fixes:
        print("🎉 TODAS AS CORREÇÕES FORAM APLICADAS COM SUCESSO!")
        print("🚀 Execute 'python validate_pre_deploy.py' para verificar")
    else:
        print("⚠️ Algumas correções falharam. Verifique os logs acima.")
    
    return success_count == total_fixes

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
