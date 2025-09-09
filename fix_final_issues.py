#!/usr/bin/env python3
"""
Script final para corrigir os últimos problemas da validação
"""

import os
import re
from pathlib import Path

def fix_validation_script():
    """Corrige o próprio script de validação"""
    validation_file = "/home/vancim/whats_agent/validate_pre_deploy.py"
    
    try:
        with open(validation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Adiciona import logging se não existir
        if 'import logging' not in content:
            # Encontra a posição após os imports existentes
            lines = content.split('\n')
            import_pos = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')) and not line.strip().startswith('#'):
                    import_pos = i + 1
            
            lines.insert(import_pos, 'import logging')
            content = '\n'.join(lines)
        
        with open(validation_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed validation script logging import")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing validation script: {e}")
        return False

def create_env_file():
    """Cria arquivo .env com variáveis necessárias"""
    env_file = "/home/vancim/whats_agent/.env"
    
    env_content = """# Database Configuration
DATABASE_URL=postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway

# Redis Configuration
REDIS_URL=redis://default:SvSHiMNuuQEtmIUgGIEGqPpXsdZeInDG@yamanote.proxy.rlwy.net:14106

# Environment
ENVIRONMENT=PRODUCTION

# WhatsApp Meta Configuration
META_ACCESS_TOKEN=your_meta_access_token_here
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token_here

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# Features
DEBUG=False
TESTING=False
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ Created .env file with all required variables")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def fix_logger_patterns():
    """Corrige padrões específicos de logger que foram perdidos"""
    files_to_fix = [
        "/home/vancim/whats_agent/app/config.py",
        "/home/vancim/whats_agent/app/database.py", 
        "/home/vancim/whats_agent/app/main.py",
        "/home/vancim/whats_agent/app/prompts.py"
    ]
    
    success_count = 0
    
    for file_path in files_to_fix:
        try:
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Remove imports antigos de logger
            content = re.sub(r'from app\.utils\.logger import.*\n', '', content)
            content = re.sub(r'from app\.services\.production_logger import.*\n', '', content)
            
            # Adiciona import logging se necessário
            if 'logger.' in content and 'import logging' not in content:
                # Encontra posição após imports
                lines = content.split('\n')
                insert_pos = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')) or line.strip().startswith('#'):
                        insert_pos = i + 1
                
                lines.insert(insert_pos, '')
                lines.insert(insert_pos + 1, 'import logging')
                lines.insert(insert_pos + 2, 'logger = logging.getLogger(__name__)')
                content = '\n'.join(lines)
            
            # Remove definições antigas de logger
            content = re.sub(r'logger\s*=\s*get_logger\([^)]*\)\s*\n', '', content)
            content = re.sub(r'logger\s*=\s*Logger\([^)]*\)\s*\n', '', content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Fixed logger patterns in {file_path}")
                success_count += 1
        
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
    
    return success_count > 0

def main():
    """Executa as correções finais"""
    print("🔧 EXECUTANDO CORREÇÕES FINAIS")
    print("=" * 50)
    
    fixes = []
    
    # 1. Corrigir script de validação
    print("1. Corrigindo script de validação...")
    if fix_validation_script():
        fixes.append("Validation script")
    
    # 2. Criar arquivo .env
    print("2. Criando arquivo .env...")
    if create_env_file():
        fixes.append(".env file")
    
    # 3. Corrigir padrões de logger específicos
    print("3. Corrigindo padrões de logger...")
    if fix_logger_patterns():
        fixes.append("Logger patterns")
    
    print("\n" + "=" * 50)
    if fixes:
        print(f"✅ Correções aplicadas: {', '.join(fixes)}")
        print("🚀 Execute 'python validate_pre_deploy.py' novamente")
    else:
        print("⚠️ Nenhuma correção foi necessária")
    
    return len(fixes) > 0

if __name__ == "__main__":
    main()
