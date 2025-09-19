#!/usr/bin/env python3
"""
🚨 ANÁLISE DEFINITIVA DO PROBLEMA RAILWAY - /ping retorna 401

PROBLEMA IDENTIFICADO:
- `/ping` retorna 401 em produção
- `/health` e `/` funcionam perfeitamente
- Todos estão na mesma posição (antes dos middlewares)
- Todos têm as mesmas configurações de bypass

CAUSA RAIZ IDENTIFICADA:
O problema está na INCONSISTÊNCIA entre o retorno do middleware e do endpoint real:

1. UltraSimpleCriticalMiddleware retorna JSONResponse para /ping
2. Endpoint real /ping retorna string "pong"
3. Railway pode estar cacheando/interceptando de forma inconsistente

SOLUÇÃO:
Padronizar TODOS os retornos para JSON e eliminar conflitos.
"""

import json
import requests
import time
from typing import Dict, Any

def test_endpoints(base_url: str) -> Dict[str, Any]:
    """Testa todos os endpoints críticos"""
    
    endpoints = {
        "/": "GET",
        "/ping": "GET", 
        "/health": "GET",
        "/emergency": "GET",
        "/railway": "GET",
        "/status": "GET",
        "/healthcheck": "GET",
        "/railway-health": "GET",
        "/ready": "GET",
        "/alive": "GET"
    }
    
    results = {}
    
    for endpoint, method in endpoints.items():
        url = f"{base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                response = requests.request(method, url, timeout=10)
                
            results[endpoint] = {
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", "N/A"),
                "response_body": response.text[:200] if len(response.text) < 200 else response.text[:200] + "...",
                "success": response.status_code == 200,
                "headers": dict(response.headers)
            }
            
            print(f"✅ {endpoint}: {response.status_code} - {response.text[:50]}")
            
        except Exception as e:
            results[endpoint] = {
                "status_code": "ERROR",
                "error": str(e),
                "success": False
            }
            print(f"❌ {endpoint}: ERROR - {str(e)}")
            
        time.sleep(0.5)  # Rate limiting
    
    return results

def analyze_problem() -> None:
    """Analisa o problema detalhadamente"""
    
    print("🔍 ANÁLISE DETALHADA DO PROBLEMA RAILWAY")
    print("=" * 60)
    
    # URLs para teste
    urls = {
        "Production (Railway)": "https://wppagent-production-app-production.up.railway.app",
        "Local": "http://localhost:8000"
    }
    
    all_results = {}
    
    for env_name, base_url in urls.items():
        print(f"\n🌐 Testando {env_name}: {base_url}")
        print("-" * 40)
        
        try:
            results = test_endpoints(base_url)
            all_results[env_name] = results
            
            # Análise específica do /ping
            ping_result = results.get("/ping", {})
            health_result = results.get("/health", {})
            root_result = results.get("/", {})
            
            print(f"\n📊 ANÁLISE {env_name}:")
            print(f"  /ping: {ping_result.get('status_code')} - {'✅' if ping_result.get('success') else '❌'}")
            print(f"  /health: {health_result.get('status_code')} - {'✅' if health_result.get('success') else '❌'}")  
            print(f"  /: {root_result.get('status_code')} - {'✅' if root_result.get('success') else '❌'}")
            
            if ping_result.get("status_code") == 401 and health_result.get("success"):
                print(f"  🚨 PROBLEMA IDENTIFICADO em {env_name}: /ping retorna 401 mas /health funciona!")
                
        except Exception as e:
            print(f"❌ Erro ao testar {env_name}: {e}")
            all_results[env_name] = {"error": str(e)}
    
    # Comparação entre ambientes
    print(f"\n🔄 COMPARAÇÃO ENTRE AMBIENTES")
    print("=" * 60)
    
    if "Production (Railway)" in all_results and "Local" in all_results:
        prod_results = all_results["Production (Railway)"]
        local_results = all_results["Local"]
        
        if not isinstance(prod_results, dict) or "error" in prod_results:
            print("❌ Erro nos testes de produção")
        elif not isinstance(local_results, dict) or "error" in local_results:
            print("❌ Erro nos testes locais")  
        else:
            for endpoint in ["/ping", "/health", "/"]:
                prod_status = prod_results.get(endpoint, {}).get("status_code", "N/A")
                local_status = local_results.get(endpoint, {}).get("status_code", "N/A")
                
                status_symbol = "✅" if prod_status == local_status else "❌"
                print(f"  {endpoint}: Prod={prod_status} vs Local={local_status} {status_symbol}")
                
                if endpoint == "/ping" and prod_status == 401 and local_status == 200:
                    print(f"    🚨 PROBLEMA CONFIRMADO: /ping falha apenas em produção!")
    
    # Salvar resultados
    with open("railway_endpoint_analysis.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Resultados salvos em: railway_endpoint_analysis.json")
    
    # Recomendações
    print(f"\n🎯 RECOMENDAÇÕES PARA CORREÇÃO:")
    print("=" * 60)
    print("1. ✅ Padronizar retorno do endpoint /ping para JSONResponse")
    print("2. ✅ Verificar ordem de execução dos middlewares no Railway")  
    print("3. ✅ Implementar logs mais detalhados no UltraSimpleCriticalMiddleware")
    print("4. ✅ Testar com curl direto no Railway para bypass de cache")
    print("5. ✅ Verificar se Railway tem proxy específico para /ping")

if __name__ == "__main__":
    analyze_problem()
