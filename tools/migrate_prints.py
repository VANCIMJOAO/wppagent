#!/usr/bin/env python3
"""
Script de migração automática de print statements
Executar com: python migrate_prints.py
"""

import re
import os
from pathlib import Path

def migrate_file(file_path: Path) -> bool:
    """Migrar um arquivo específico"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Adicionar import do logger se não existir
        if 'from app.utils.logger import get_logger' not in content:
            # Encontrar local apropriado para adicionar import
            lines = content.split('\n')
            import_added = False
            
            for i, line in enumerate(lines):
                if line.startswith('from app.') and not import_added:
                    lines.insert(i + 1, 'from app.utils.logger import get_logger')
                    import_added = True
                    break
            
            if not import_added:
                # Adicionar após último import
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('#') and not line.startswith('import') and not line.startswith('from'):
                        lines.insert(i, 'from app.utils.logger import get_logger')
                        lines.insert(i + 1, '')
                        break
            
            content = '\n'.join(lines)
        
        # Adicionar inicialização do logger se não existir
        if 'logger = get_logger(__name__)' not in content:
            lines = content.split('\n')
            
            # Encontrar local após imports
            for i, line in enumerate(lines):
                if 'from app.utils.logger import get_logger' in line:
                    lines.insert(i + 2, 'logger = get_logger(__name__)')
                    break
            
            content = '\n'.join(lines)
        
        # Substituir print statements
        # Padrões de substituição
        replacements = [
            (r'print\(f?"?([^"]*✅[^"]*)"?\)', r'logger.info("\1")'),
            (r'print\(f?"?([^"]*❌[^"]*)"?\)', r'logger.error("\1")'),
            (r'print\(f?"?([^"]*⚠️[^"]*)"?\)', r'logger.warning("\1")'),
            (r'print\(f?"?([^"]*🔍[^"]*)"?\)', r'logger.debug("\1")'),
            (r'print\(f?"?([^"]*ERROR[^"]*)"?\)', r'logger.error("\1")'),
            (r'print\(f?"?([^"]*WARNING[^"]*)"?\)', r'logger.warning("\1")'),
            (r'print\(f?"?([^"]*DEBUG[^"]*)"?\)', r'logger.debug("\1")'),
            (r'print\(([^)]*)\)', r'logger.info(\1)'),  # Fallback genérico
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Salvar se houve mudanças
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao migrar {file_path}: {e}")
        return False

def main():
    """Executar migração"""
    target_dirs = ["app"]
    total_files = 0
    migrated_files = 0
    
    print("🚀 Iniciando migração automática de print statements...")
    
    for target_dir in target_dirs:
        target_path = Path(target_dir)
        if not target_path.exists():
            continue
        
        for py_file in target_path.rglob("*.py"):
            total_files += 1
            if migrate_file(py_file):
                migrated_files += 1
                print(f"✅ Migrado: {py_file}")
    
    print(f"\n📊 Migração concluída!")
    print(f"   Arquivos processados: {total_files}")
    print(f"   Arquivos migrados: {migrated_files}")

if __name__ == "__main__":
    main()
