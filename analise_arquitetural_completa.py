#!/usr/bin/env python3
"""
ANÁLISE ARQUITETURAL COMPLETA - SISTEMA DE APIS
==============================================
Investigação profunda do problema de rotas bloqueadas
"""

import os
import re
import json
from datetime import datetime

def analyze_file(filepath, description=""):
    """Analisa um arquivo específico"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "file": filepath,
            "description": description,
            "size": len(content),
            "lines": len(content.split('\n')),
            "content_preview": content[:500] if content else "",
            "exists": True
        }
    except Exception as e:
        return {
            "file": filepath,
            "description": description,
            "error": str(e),
            "exists": False
        }

def search_in_file(filepath, patterns):
    """Procura padrões específicos em um arquivo"""
    results = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        for pattern_name, pattern in patterns.items():
            matches = []
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append({
                        "line_number": i,
                        "line_content": line.strip(),
                        "context": lines[max(0, i-2):min(len(lines), i+2)]
                    })
            results[pattern_name] = matches
    except Exception as e:
        results["error"] = str(e)
    
    return results

def main():
    print("🔍 ANÁLISE ARQUITETURAL COMPLETA DO SISTEMA DE APIS")
    print("=" * 80)
    
    # 1. MAPEAMENTO DE ARQUIVOS CRÍTICOS
    critical_files = {
        "app/main.py": "Arquivo principal da aplicação - configuração de routers e middleware",
        "app/auth/middleware.py": "Middleware de autenticação - lógica de endpoints públicos",
        "app/routes/meta_webhook.py": "Router específico do Meta webhook",
        "app/routes/webhook.py": "Router principal de webhooks",
        "app/routes/debug_middleware.py": "Router de debug do middleware (recém criado)",
        "app/config.py": "Configurações da aplicação",
        "railway.toml": "Configuração do Railway",
        "Dockerfile": "Configuração do container",
        "requirements.txt": "Dependências Python"
    }
    
    print("\n📁 ANÁLISE DE ARQUIVOS CRÍTICOS:")
    file_analysis = {}
    
    for filepath, description in critical_files.items():
        analysis = analyze_file(filepath, description)
        file_analysis[filepath] = analysis
        
        status = "✅ OK" if analysis["exists"] else "❌ ERRO"
        print(f"{status} {filepath}: {description}")
        if not analysis["exists"]:
            print(f"   ⚠️  {analysis.get('error', 'Arquivo não encontrado')}")
    
    # 2. ANÁLISE DO MIDDLEWARE
    print("\n🔒 ANÁLISE DETALHADA DO MIDDLEWARE:")
    
    middleware_patterns = {
        "public_endpoints_definition": r"public_endpoints\s*=",
        "meta_endpoint": r"['\"]\/meta['\"]",
        "middleware_class": r"class\s+AuthenticationMiddleware",
        "dispatch_method": r"async\s+def\s+dispatch",
        "is_public_endpoint": r"def\s+.*is_public_endpoint",
        "middleware_instantiation": r"AuthenticationMiddleware\(",
        "app_add_middleware": r"app\.add_middleware"
    }
    
    middleware_search = search_in_file("app/auth/middleware.py", middleware_patterns)
    
    for pattern_name, matches in middleware_search.items():
        print(f"\n🔍 {pattern_name}:")
        if matches:
            for match in matches[:3]:  # Mostrar apenas 3 primeiros
                print(f"   Linha {match['line_number']}: {match['line_content']}")
        else:
            print("   ❌ Não encontrado")
    
    # 3. ANÁLISE DO MAIN.PY
    print("\n🚀 ANÁLISE DO MAIN.PY:")
    
    main_patterns = {
        "middleware_import": r"from\s+app\.auth\.middleware\s+import",
        "middleware_add": r"app\.add_middleware",
        "router_includes": r"app\.include_router",
        "meta_router_import": r"from\s+app\.routes\.meta_webhook",
        "meta_router_include": r"include_router.*meta.*webhook",
        "debug_router_import": r"from\s+app\.routes\.debug_middleware",
        "fastapi_app_creation": r"app\s*=\s*FastAPI",
        "cors_middleware": r"CORSMiddleware"
    }
    
    main_search = search_in_file("app/main.py", main_patterns)
    
    for pattern_name, matches in main_search.items():
        print(f"\n🔍 {pattern_name}:")
        if matches:
            for match in matches[:2]:  # Mostrar apenas 2 primeiros
                print(f"   Linha {match['line_number']}: {match['line_content']}")
        else:
            print("   ❌ Não encontrado")
    
    # 4. ANÁLISE DOS ROUTERS META
    print("\n📡 ANÁLISE DOS ROUTERS META:")
    
    meta_patterns = {
        "router_creation": r"router\s*=\s*APIRouter",
        "webhook_verify_endpoint": r"@router\.(get|post).*webhook.*verify",
        "verify_function": r"def\s+.*verify.*webhook",
        "verify_token_check": r"verify_token",
        "challenge_handling": r"challenge"
    }
    
    for meta_file in ["app/routes/meta_webhook.py", "app/routes/webhook.py"]:
        if os.path.exists(meta_file):
            print(f"\n📄 {meta_file}:")
            meta_search = search_in_file(meta_file, meta_patterns)
            
            for pattern_name, matches in meta_search.items():
                if matches:
                    print(f"   ✅ {pattern_name}: {len(matches)} matches")
                else:
                    print(f"   ❌ {pattern_name}: não encontrado")
    
    # 5. VERIFICAÇÃO DE ORDEM DE MIDDLEWARE
    print("\n⚙️ VERIFICAÇÃO DE ORDEM DE MIDDLEWARE:")
    
    try:
        with open("app/main.py", 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        # Procurar ordem de add_middleware
        middleware_adds = []
        lines = main_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'add_middleware' in line:
                middleware_adds.append({
                    "line": i,
                    "content": line.strip(),
                    "context": lines[max(0, i-2):min(len(lines), i+2)]
                })
        
        print(f"   Encontrados {len(middleware_adds)} add_middleware:")
        for middleware in middleware_adds:
            print(f"   Linha {middleware['line']}: {middleware['content']}")
    
    except Exception as e:
        print(f"   ❌ Erro ao analisar ordem de middleware: {e}")
    
    # 6. ANÁLISE DE IMPORTAÇÕES
    print("\n📦 ANÁLISE DE IMPORTAÇÕES:")
    
    import_patterns = {
        "auth_middleware_import": r"from\s+app\.auth\.middleware",
        "secrets_manager_import": r"from\s+.*secrets.*manager",
        "fastapi_imports": r"from\s+fastapi\s+import",
        "router_imports": r"from\s+app\.routes\."
    }
    
    import_search = search_in_file("app/main.py", import_patterns)
    
    for pattern_name, matches in import_search.items():
        print(f"   {pattern_name}: {len(matches)} matches")
    
    # 7. VERIFICAÇÃO DE CONFIGURAÇÕES
    print("\n⚙️ VERIFICAÇÃO DE CONFIGURAÇÕES:")
    
    config_files = ["app/config.py", "railway.toml", ".env"]
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   ✅ {config_file} existe")
        else:
            print(f"   ❌ {config_file} não encontrado")
    
    # 8. SALVAR RELATÓRIO COMPLETO
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": "complete_architecture",
        "file_analysis": file_analysis,
        "middleware_search": middleware_search,
        "main_search": main_search,
        "middleware_order": middleware_adds if 'middleware_adds' in locals() else [],
        "import_analysis": import_search
    }
    
    report_file = f"temp_reports/analise_arquitetural_{timestamp}.json"
    os.makedirs("temp_reports", exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório completo salvo em: {report_file}")
    
    # 9. DIAGNÓSTICO PRELIMINAR
    print("\n🩺 DIAGNÓSTICO PRELIMINAR:")
    
    issues_found = []
    
    # Verificar se middleware está sendo aplicado
    if not main_search.get("middleware_add"):
        issues_found.append("❌ Middleware de autenticação pode não estar sendo aplicado")
    
    # Verificar se endpoints meta estão definidos
    if not middleware_search.get("meta_endpoint"):
        issues_found.append("❌ Endpoints /meta podem não estar definidos como públicos")
    
    # Verificar se routers estão sendo incluídos
    if not main_search.get("meta_router_include"):
        issues_found.append("❌ Router meta_webhook pode não estar sendo incluído")
    
    if issues_found:
        print("   🚨 PROBLEMAS IDENTIFICADOS:")
        for issue in issues_found:
            print(f"     {issue}")
    else:
        print("   ✅ Estrutura básica parece correta - problema pode ser mais sutil")
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISE ARQUITETURAL COMPLETA FINALIZADA")

if __name__ == "__main__":
    main()