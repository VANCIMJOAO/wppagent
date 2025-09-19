#!/usr/bin/env python3
"""
🚨 CORREÇÃO DEFINITIVA DO PROBLEMA RAILWAY - /ping retorna 401

PROBLEMA IDENTIFICADO:
- Conflito entre UltraSimpleCriticalMiddleware e endpoint /ping
- Middleware retorna JSONResponse, endpoint retorna string
- Railway processa de forma inconsistente

SOLUÇÃO:
1. Remover endpoints duplicados APÓS os middlewares
2. Deixar apenas o middleware fazer o bypass
3. Padronizar todos os retornos para JSON
4. Testar consistência

"""

import os
import sys

# Adicionar o path do projeto
sys.path.insert(0, '/home/vancim/whats_agent')

def fix_main_py():
    """Corrige o main.py removendo endpoints duplicados"""
    
    print("🔧 INICIANDO CORREÇÃO DEFINITIVA DO PROBLEMA RAILWAY")
    print("=" * 60)
    
    main_py_path = "/home/vancim/whats_agent/app/main.py"
    
    # Ler arquivo atual
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("📖 Arquivo main.py lido com sucesso")
    
    # Encontrar e remover endpoints duplicados após os middlewares
    lines = content.split('\n')
    new_lines = []
    skip_next_lines = 0
    found_duplicates = 0
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detectar início dos endpoints duplicados (após os middlewares)
        if ('# Endpoints duplicados removidos - agora estão antes dos middlewares' in line or 
            '# 🚀 Railway Health Check - Simplified for reliable deployment' in line):
            
            # Pular até encontrar o próximo bloco importante
            print(f"🗑️  Removendo seção duplicada na linha {i+1}: {line[:50]}...")
            
            while i < len(lines):
                current_line = lines[i].strip()
                
                # Parar quando encontrar endpoints que devem ser mantidos
                if (current_line.startswith('@app.get("/health", response_model=HealthCheckResponse)') or
                    current_line.startswith('@app.get("/health/v2")') or
                    current_line.startswith('if __name__ == "__main__"')):
                    break
                    
                # Se for definição de endpoint duplicado, contar
                if current_line.startswith('@app.get("/ping")') or current_line.startswith('@app.get("/ready")') or current_line.startswith('@app.get("/alive")'):
                    found_duplicates += 1
                    print(f"    🚨 Endpoint duplicado removido: {current_line}")
                
                i += 1
            
            continue
        
        new_lines.append(lines[i])
        i += 1
    
    print(f"✅ Endpoints duplicados removidos: {found_duplicates}")
    
    # Reconstruir conteúdo
    new_content = '\n'.join(new_lines)
    
    # Backup do arquivo original
    backup_path = "/home/vancim/whats_agent/app/main.py.backup.railway_fix"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 Backup criado: {backup_path}")
    
    # Salvar arquivo corrigido
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Arquivo main.py corrigido com sucesso!")
    
    return True

def fix_middleware_consistency():
    """Garante que o middleware seja consistente"""
    
    print("\n🔧 CORRIGINDO CONSISTÊNCIA DO MIDDLEWARE")
    print("-" * 40)
    
    main_py_path = "/home/vancim/whats_agent/app/main.py"
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Localizar e corrigir UltraSimpleCriticalMiddleware
    # Garantir que /ping retorna JSON consistente
    old_middleware = '''        # BYPASS DIRETO para /ping
        if path == "/ping":
            debug_logger.info(f"🔒 BYPASS ULTRA SIMPLES: {path} - RETORNANDO 200")
            debug_logger.info(f"🔒 BYPASS ULTRA SIMPLES: Headers de resposta: {{'Content-Type': 'application/json'}}")
            return JSONResponse(
                content={"status": "ok", "service": "whatsapp-agent", "railway": True},
                status_code=200
            )'''
    
    new_middleware = '''        # BYPASS DIRETO para /ping - PADRONIZADO JSON
        if path == "/ping":
            debug_logger.info(f"🔒 BYPASS ULTRA SIMPLES: {path} - RETORNANDO JSON 200")
            debug_logger.info(f"🔒 BYPASS RAILWAY: Middleware processando /ping diretamente")
            return JSONResponse(
                content={"message": "pong", "status": "ok", "service": "whatsapp-agent", "railway": True},
                status_code=200,
                headers={"Content-Type": "application/json"}
            )'''
    
    if old_middleware in content:
        content = content.replace(old_middleware, new_middleware)
        print("✅ UltraSimpleCriticalMiddleware corrigido para consistência JSON")
    else:
        print("⚠️  UltraSimpleCriticalMiddleware não encontrado com padrão esperado")
    
    # Salvar
    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Consistência do middleware garantida!")

def test_consistency():
    """Testa se a correção foi aplicada corretamente"""
    
    print("\n🧪 TESTANDO CORREÇÃO APLICADA")
    print("-" * 40)
    
    main_py_path = "/home/vancim/whats_agent/app/main.py"
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se não há endpoints duplicados
    ping_count = content.count('@app.get("/ping")')
    ready_count = content.count('@app.get("/ready")')
    alive_count = content.count('@app.get("/alive")')
    
    print(f"📊 Contagem de endpoints:")
    print(f"  @app.get('/ping'): {ping_count}")
    print(f"  @app.get('/ready'): {ready_count}")
    print(f"  @app.get('/alive'): {alive_count}")
    
    # Verificar se middleware tem o bypass correto
    has_ping_bypass = '"message": "pong"' in content and 'BYPASS ULTRA SIMPLES' in content
    
    print(f"\n🔍 Verificações:")
    print(f"  ✅ Middleware tem bypass /ping: {has_ping_bypass}")
    print(f"  ✅ Endpoints não duplicados: {ping_count <= 1 and ready_count <= 1 and alive_count <= 1}")
    
    if ping_count <= 1 and has_ping_bypass:
        print("\n🎯 CORREÇÃO APLICADA COM SUCESSO!")
        print("   - Endpoints duplicados removidos")
        print("   - Middleware com bypass consistente")
        print("   - /ping agora retornará JSON via middleware")
        return True
    else:
        print("\n❌ CORREÇÃO PRECISA DE AJUSTES")
        return False

def main():
    """Executa correção completa"""
    
    print("🚨 CORREÇÃO DEFINITIVA DO PROBLEMA RAILWAY")
    print("Problema: /ping retorna 401 devido a conflitos de endpoints")
    print("")
    
    try:
        # 1. Corrigir main.py
        success1 = fix_main_py()
        
        # 2. Corrigir consistência do middleware  
        fix_middleware_consistency()
        
        # 3. Testar correção
        success2 = test_consistency()
        
        if success1 and success2:
            print("\n🎉 CORREÇÃO DEFINITIVA APLICADA COM SUCESSO!")
            print("=" * 60)
            print("✅ PRÓXIMOS PASSOS:")
            print("1. Fazer commit das alterações")
            print("2. Deploy no Railway")
            print("3. Testar https://wppagent-production-app-production.up.railway.app/ping")
            print("4. Verificar logs do Railway para confirmação")
            print("")
            print("🚀 EXPECTATIVA: /ping agora deve retornar 200 JSON via middleware!")
        else:
            print("\n❌ CORREÇÃO NÃO APLICADA COMPLETAMENTE")
            print("Verificar logs acima e aplicar correções manuais se necessário")
            
    except Exception as e:
        print(f"\n❌ ERRO DURANTE CORREÇÃO: {e}")
        print("Restaurar backup se necessário:")
        print("cp /home/vancim/whats_agent/app/main.py.backup.railway_fix /home/vancim/whats_agent/app/main.py")

if __name__ == "__main__":
    main()
