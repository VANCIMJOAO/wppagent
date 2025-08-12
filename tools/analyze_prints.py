#!/usr/bin/env python3
"""
Script para migração de print statements para logging estruturado
================================================================

Este script identifica e substitui automaticamente print statements
por chamadas de logging apropriadas no código da aplicação.
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Diretórios para processar
TARGET_DIRS = [
    "app",
    "tests"
]

# Padrões para identificar diferentes tipos de print
PRINT_PATTERNS = {
    'success': [r'✅', r'🎉', r'✓', r'SUCCESS', r'sucesso'],
    'error': [r'❌', r'💥', r'✗', r'ERROR', r'erro', r'Erro'],
    'warning': [r'⚠️', r'🚨', r'WARNING', r'warning', r'atenção'],
    'info': [r'📋', r'📊', r'ℹ️', r'INFO', r'info'],
    'debug': [r'🔍', r'🐛', r'DEBUG', r'debug']
}

def analyze_print_content(content: str) -> str:
    """Analisar conteúdo do print para determinar nível apropriado"""
    content_lower = content.lower()
    
    # Verificar padrões em ordem de prioridade
    for level, patterns in PRINT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return level
    
    # Padrão para testes ou código de exemplo
    if any(word in content_lower for word in ['test', 'exemplo', 'demo']):
        return 'debug'
    
    # Padrão para dados/status
    if any(word in content_lower for word in ['status', 'resultado', 'dados']):
        return 'info'
    
    # Padrão default
    return 'info'

def extract_prints_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """Extrair todos os print statements de um arquivo"""
    prints_found = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST para encontrar prints
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Name) and node.func.id == 'print'):
                    # Extrair argumentos do print
                    args = []
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            args.append(repr(arg.value))
                        elif isinstance(arg, ast.Constant):  # Python >= 3.8
                            args.append(repr(arg.value))
                        else:
                            # Para expressões complexas, usar representação básica
                            args.append(ast.get_source_segment(content, arg) or "...")
                    
                    print_content = ", ".join(args)
                    suggested_level = analyze_print_content(print_content)
                    
                    prints_found.append({
                        'line': node.lineno,
                        'content': print_content,
                        'suggested_level': suggested_level,
                        'full_call': ast.get_source_segment(content, node) or f"print({print_content})"
                    })
                    
    except Exception as e:
        print(f"❌ Erro ao analisar {file_path}: {e}")
    
    return prints_found

def suggest_logger_replacement(print_info: Dict[str, Any]) -> str:
    """Sugerir substituição para logging"""
    level = print_info['suggested_level']
    content = print_info['content']
    
    # Limpar e preparar conteúdo
    if content.startswith("'") and content.endswith("'"):
        content = content[1:-1]
    elif content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
    
    # Gerar sugestão de substituição
    if level == 'success':
        return f'logger.info("{content}")'
    elif level == 'error':
        return f'logger.error("{content}")'
    elif level == 'warning':
        return f'logger.warning("{content}")'
    elif level == 'info':
        return f'logger.info("{content}")'
    elif level == 'debug':
        return f'logger.debug("{content}")'
    else:
        return f'logger.info("{content}")'

def generate_migration_report() -> None:
    """Gerar relatório de migração de print statements"""
    print("🔍 Analisando print statements no código...")
    print("=" * 60)
    
    total_prints = 0
    files_with_prints = 0
    level_counts = {level: 0 for level in PRINT_PATTERNS.keys()}
    level_counts['info'] = 0  # Adicionar info que não está em PRINT_PATTERNS
    
    for target_dir in TARGET_DIRS:
        target_path = Path(target_dir)
        if not target_path.exists():
            continue
            
        print(f"\n📁 Processando diretório: {target_dir}")
        print("-" * 40)
        
        for py_file in target_path.rglob("*.py"):
            prints = extract_prints_from_file(py_file)
            
            if prints:
                files_with_prints += 1
                total_prints += len(prints)
                
                print(f"\n📄 {py_file}")
                print(f"   Prints encontrados: {len(prints)}")
                
                for print_info in prints:
                    level = print_info['suggested_level']
                    level_counts[level] += 1
                    
                    print(f"   Linha {print_info['line']:3d}: {level.upper():8s} - {print_info['content'][:50]}...")
                    print(f"   {'':10s} Sugestão: {suggest_logger_replacement(print_info)}")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE MIGRAÇÃO")
    print("=" * 60)
    print(f"📈 Total de prints encontrados: {total_prints}")
    print(f"📁 Arquivos com prints: {files_with_prints}")
    print("\n📋 Distribuição por nível:")
    
    for level, count in level_counts.items():
        if count > 0:
            percentage = (count / total_prints * 100) if total_prints > 0 else 0
            print(f"   {level.upper():8s}: {count:3d} ({percentage:5.1f}%)")
    
    # Recomendações
    print("\n💡 RECOMENDAÇÕES:")
    print("1. Adicionar 'from app.utils.logger import get_logger' no início dos arquivos")
    print("2. Adicionar 'logger = get_logger(__name__)' após os imports")
    print("3. Substituir print statements pelas chamadas de logger sugeridas")
    print("4. Remover print statements de código de produção")
    print("5. Usar logger.debug() para informações de desenvolvimento")

def create_migration_script() -> None:
    """Criar script automatizado de migração"""
    script_content = '''#!/usr/bin/env python3
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
            lines = content.split('\\n')
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
            
            content = '\\n'.join(lines)
        
        # Adicionar inicialização do logger se não existir
        if 'logger = get_logger(__name__)' not in content:
            lines = content.split('\\n')
            
            # Encontrar local após imports
            for i, line in enumerate(lines):
                if 'from app.utils.logger import get_logger' in line:
                    lines.insert(i + 2, 'logger = get_logger(__name__)')
                    break
            
            content = '\\n'.join(lines)
        
        # Substituir print statements
        # Padrões de substituição
        replacements = [
            (r'print\\(f?"?([^"]*✅[^"]*)"?\\)', r'logger.info("\\1")'),
            (r'print\\(f?"?([^"]*❌[^"]*)"?\\)', r'logger.error("\\1")'),
            (r'print\\(f?"?([^"]*⚠️[^"]*)"?\\)', r'logger.warning("\\1")'),
            (r'print\\(f?"?([^"]*🔍[^"]*)"?\\)', r'logger.debug("\\1")'),
            (r'print\\(f?"?([^"]*ERROR[^"]*)"?\\)', r'logger.error("\\1")'),
            (r'print\\(f?"?([^"]*WARNING[^"]*)"?\\)', r'logger.warning("\\1")'),
            (r'print\\(f?"?([^"]*DEBUG[^"]*)"?\\)', r'logger.debug("\\1")'),
            (r'print\\(([^)]*)\\)', r'logger.info(\\1)'),  # Fallback genérico
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
    
    print(f"\\n📊 Migração concluída!")
    print(f"   Arquivos processados: {total_files}")
    print(f"   Arquivos migrados: {migrated_files}")

if __name__ == "__main__":
    main()
'''
    
    with open("migrate_prints.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("📝 Script de migração criado: migrate_prints.py")
    print("   Execute com: python migrate_prints.py")

if __name__ == "__main__":
    print("🚀 Analisador de Print Statements - WhatsApp Agent")
    print("=" * 60)
    
    generate_migration_report()
    print("\n" + "=" * 60)
    create_migration_script()
    
    print("\n✅ Análise completa!")
    print("💡 Execute 'python migrate_prints.py' para migração automática")
