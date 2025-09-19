#!/usr/bin/env python3
"""
🔍 ANÁLISE FORENSE COMPLETA - PROBLEMA DE AUTENTICAÇÃO RAILWAY

O problema persiste mesmo após correções de middleware. Isso indica:
1. Há outro sistema de autenticação interceptando
2. Pode ser um middleware oculto
3. Pode ser configuração do Railway
4. Pode ser proxy/load balancer

Vamos investigar TUDO.
"""

import os
import re
from pathlib import Path

def analyze_auth_system():
    """Analisa todo o sistema de autenticação"""
    
    print("🔍 ANÁLISE FORENSE COMPLETA - SISTEMA DE AUTENTICAÇÃO")
    print("=" * 70)
    
    project_root = "/home/vancim/whats_agent"
    
    # 1. Analisar TODOS os arquivos que mencionam autenticação
    print("\n📋 1. BUSCANDO TODOS OS ARQUIVOS COM 'AUTH' OU 'AUTHENTICATION'")
    print("-" * 50)
    
    auth_files = []
    
    for root, dirs, files in os.walk(project_root):
        # Pular diretórios não relevantes
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for file in files:
            if file.endswith(('.py', '.toml', '.yml', '.yaml', '.json', '.sh')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        if any(term in content for term in ['auth', 'token', 'jwt', 'bearer', 'authorization']):
                            auth_files.append(file_path)
                            print(f"   📁 {file_path}")
                except:
                    pass
    
    print(f"\n✅ Encontrados {len(auth_files)} arquivos relacionados à autenticação")
    
    # 2. Analisar middleware de autenticação específico
    print("\n📋 2. ANALISANDO AuthMiddleware DETALHADAMENTE")
    print("-" * 50)
    
    auth_middleware_path = os.path.join(project_root, "app/auth/middleware.py")
    if os.path.exists(auth_middleware_path):
        with open(auth_middleware_path, 'r', encoding='utf-8') as f:
            auth_content = f.read()
        
        # Procurar pela função _is_public_endpoint
        public_endpoint_match = re.search(r'def _is_public_endpoint\(.*?\):(.*?)(?=def|\Z)', auth_content, re.DOTALL)
        if public_endpoint_match:
            public_function = public_endpoint_match.group(0)
            print("📍 FUNÇÃO _is_public_endpoint ENCONTRADA:")
            print(public_function[:500] + "..." if len(public_function) > 500 else public_function)
        
        # Procurar public_endpoints set
        public_set_match = re.search(r'self\.public_endpoints\s*=\s*\{([^}]+)\}', auth_content, re.DOTALL)
        if public_set_match:
            public_set = public_set_match.group(1)
            print(f"\n📍 PUBLIC_ENDPOINTS SET ENCONTRADO:")
            endpoints = [ep.strip().strip('"').strip("'") for ep in public_set.split(',')]
            for ep in endpoints:
                if ep:
                    status = "✅" if "/ping" in ep else "❓"
                    print(f"   {status} {ep}")
    
    # 3. Verificar se há outros middlewares de autenticação
    print("\n📋 3. BUSCANDO OUTROS MIDDLEWARES DE AUTENTICAÇÃO")
    print("-" * 50)
    
    middleware_files = []
    for auth_file in auth_files:
        if 'middleware' in auth_file.lower():
            middleware_files.append(auth_file)
            print(f"   🔧 {auth_file}")
    
    # 4. Analisar main.py para middlewares ocultos
    print("\n📋 4. ANALISANDO MAIN.PY PARA MIDDLEWARES OCULTOS")
    print("-" * 50)
    
    main_py_path = os.path.join(project_root, "app/main.py")
    if os.path.exists(main_py_path):
        with open(main_py_path, 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        # Procurar todas as linhas com add_middleware
        middleware_lines = []
        for i, line in enumerate(main_content.split('\n'), 1):
            if 'add_middleware' in line and not line.strip().startswith('#'):
                middleware_lines.append((i, line.strip()))
        
        print("📍 TODOS OS MIDDLEWARES ENCONTRADOS NO MAIN.PY:")
        for line_num, line in middleware_lines:
            print(f"   Linha {line_num}: {line}")
        
        # Verificar se há FastAPI dependencies globais
        if 'Depends(' in main_content:
            print(f"\n⚠️  DEPENDENCIES GLOBAIS ENCONTRADAS - podem estar causando autenticação!")
            depends_lines = [line.strip() for line in main_content.split('\n') if 'Depends(' in line]
            for dep in depends_lines[:10]:  # Mostrar apenas 10 primeiras
                print(f"   📎 {dep}")
    
    # 5. Verificar configurações do Railway
    print("\n📋 5. VERIFICANDO CONFIGURAÇÕES RAILWAY")
    print("-" * 50)
    
    railway_toml = os.path.join(project_root, "railway.toml")
    if os.path.exists(railway_toml):
        with open(railway_toml, 'r', encoding='utf-8') as f:
            railway_content = f.read()
        print("📍 RAILWAY.TOML:")
        print(railway_content)
    
    # 6. Verificar variáveis de ambiente
    print("\n📋 6. VERIFICANDO ARQUIVOS DE AMBIENTE")
    print("-" * 50)
    
    env_files = ['.env', '.env.production', '.env.railway']
    for env_file in env_files:
        env_path = os.path.join(project_root, env_file)
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # Procurar por configurações de auth
            auth_vars = [line for line in env_content.split('\n') 
                        if any(term in line.upper() for term in ['AUTH', 'JWT', 'TOKEN', 'SECRET'])]
            if auth_vars:
                print(f"📍 {env_file}:")
                for var in auth_vars:
                    # Mascarar valores sensíveis
                    if '=' in var:
                        key, value = var.split('=', 1)
                        masked_value = value[:3] + "***" if len(value) > 3 else "***"
                        print(f"   {key}={masked_value}")
    
    # 7. Procurar por decorators de autenticação
    print("\n📋 7. BUSCANDO DECORATORS DE AUTENTICAÇÃO")
    print("-" * 50)
    
    decorator_patterns = ['@require_auth', '@auth_required', '@login_required', '@jwt_required']
    
    for auth_file in auth_files:
        if auth_file.endswith('.py'):
            try:
                with open(auth_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                found_decorators = []
                for pattern in decorator_patterns:
                    if pattern in file_content:
                        found_decorators.append(pattern)
                
                if found_decorators:
                    print(f"   📍 {auth_file}: {', '.join(found_decorators)}")
            except:
                pass
    
    return auth_files

def investigate_specific_endpoints():
    """Investiga especificamente os endpoints que falam"""
    
    print("\n📋 8. INVESTIGAÇÃO ESPECÍFICA DOS ENDPOINTS PROBLEMÁTICOS")
    print("-" * 50)
    
    project_root = "/home/vancim/whats_agent"
    
    # Buscar definições dos endpoints específicos
    endpoints_to_find = ['/ping', '/emergency', '/railway', '/status']
    
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for endpoint in endpoints_to_find:
                        if f'"{endpoint}"' in content or f"'{endpoint}'" in content:
                            print(f"   📍 {endpoint} encontrado em: {file_path}")
                            
                            # Mostrar contexto da definição
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if endpoint in line and ('@app.' in line or 'router.' in line):
                                    context_start = max(0, i-2)
                                    context_end = min(len(lines), i+5)
                                    print(f"      Contexto (linhas {context_start+1}-{context_end}):")
                                    for j in range(context_start, context_end):
                                        marker = "  ► " if j == i else "     "
                                        print(f"      {marker}{lines[j]}")
                                    print()
                except:
                    pass

def check_fastapi_global_dependencies():
    """Verifica se há dependencies globais no FastAPI"""
    
    print("\n📋 9. VERIFICANDO DEPENDENCIES GLOBAIS DO FASTAPI")
    print("-" * 50)
    
    main_py_path = "/home/vancim/whats_agent/app/main.py"
    
    if os.path.exists(main_py_path):
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Procurar por dependencies globais
        if 'dependencies=' in content:
            print("⚠️  DEPENDENCIES GLOBAIS ENCONTRADAS NO FASTAPI APP!")
            
            # Encontrar a definição do app FastAPI
            app_match = re.search(r'app\s*=\s*FastAPI\([^)]*dependencies\s*=\s*([^,\)]+)', content, re.DOTALL)
            if app_match:
                deps = app_match.group(1)
                print(f"   📎 Dependencies encontradas: {deps}")
                print("   🚨 ISSO PODE SER A CAUSA! Dependencies globais aplicam autenticação a TODOS os endpoints!")
        
        # Procurar por router includes com dependencies
        router_matches = re.findall(r'app\.include_router\([^)]*dependencies\s*=\s*([^,\)]+)', content)
        if router_matches:
            print("⚠️  ROUTER DEPENDENCIES ENCONTRADAS:")
            for i, dep in enumerate(router_matches, 1):
                print(f"   📎 Router {i}: dependencies={dep}")

def main():
    """Executa análise forense completa"""
    
    print("🚨 ANÁLISE FORENSE - PROBLEMA DE AUTENTICAÇÃO PERSISTENTE")
    print("O problema continua mesmo após correções de middleware.")
    print("Vamos investigar TODAS as possibilidades de interceptação de autenticação.")
    print()
    
    try:
        auth_files = analyze_auth_system()
        investigate_specific_endpoints()
        check_fastapi_global_dependencies()
        
        print("\n" + "=" * 70)
        print("📊 RESUMO DA ANÁLISE FORENSE")
        print("=" * 70)
        print(f"✅ Total de arquivos analisados: {len(auth_files)}")
        print("✅ Middlewares identificados")
        print("✅ Endpoints mapeados") 
        print("✅ Dependencies verificadas")
        print("✅ Configurações Railway analisadas")
        
        print("\n🎯 POSSÍVEIS CAUSAS IDENTIFICADAS:")
        print("1. 🔍 AuthMiddleware ainda executando primeiro (verificar ordem)")
        print("2. 🔍 Dependencies globais no FastAPI (força autenticação)")
        print("3. 🔍 Router dependencies aplicadas")  
        print("4. 🔍 Decorators ocultos nos endpoints")
        print("5. 🔍 Proxy/Load Balancer do Railway interceptando")
        print("6. 🔍 Configuração específica do Railway.app")
        
        print("\n🚀 PRÓXIMAS AÇÕES RECOMENDADAS:")
        print("1. Verificar se UltraSimpleCriticalMiddleware realmente executa primeiro")
        print("2. Procurar dependencies globais no FastAPI")
        print("3. Testar endpoint completamente sem middleware")
        print("4. Verificar logs do Railway para identificar interceptação")
        
    except Exception as e:
        print(f"\n❌ ERRO NA ANÁLISE: {e}")

if __name__ == "__main__":
    main()
