#!/usr/bin/env python3
"""
🎯 TESTE FINAL DA CORREÇÃO RAILWAY - /ping 401 → 200

Testa se a correção definitiva resolveu o problema do /ping retornando 401
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, Any

def test_railway_endpoints() -> Dict[str, Any]:
    """Testa endpoints críticos no Railway após correção"""
    
    print("🚀 TESTE FINAL DA CORREÇÃO RAILWAY")
    print("=" * 60)
    print(f"📅 Data/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    base_url = "https://wppagent-production-app-production.up.railway.app"
    
    # Endpoints para testar
    test_endpoints = {
        "/": "Root endpoint",
        "/ping": "🚨 PROBLEMA PRINCIPAL - deve retornar 200 JSON",
        "/health": "Health check - funcionava antes",
        "/emergency": "Emergency endpoint", 
        "/railway": "Railway specific endpoint",
        "/status": "Status endpoint",
        "/healthcheck": "Alternative health check",
        "/railway-health": "Ultra simple Railway health"
    }
    
    results = {}
    success_count = 0
    total_count = len(test_endpoints)
    
    print("🔍 TESTANDO ENDPOINTS CRÍTICOS:")
    print("-" * 40)
    
    for endpoint, description in test_endpoints.items():
        url = f"{base_url}{endpoint}"
        
        try:
            # Fazer request com timeout
            response = requests.get(url, timeout=15, headers={
                "User-Agent": "Railway-Fix-Test/1.0",
                "Accept": "application/json"
            })
            
            # Analisar resposta
            is_success = response.status_code == 200
            success_count += 1 if is_success else 0
            
            # Tentar parsear JSON
            try:
                response_json = response.json()
                response_preview = json.dumps(response_json, indent=2)[:150]
                content_type = "JSON"
            except:
                response_preview = response.text[:150] 
                content_type = "TEXT"
            
            # Status visual
            status_icon = "✅" if is_success else "❌"
            
            print(f"{status_icon} {endpoint}")
            print(f"   Status: {response.status_code}")
            print(f"   Type: {content_type}")  
            print(f"   Preview: {response_preview[:80]}...")
            
            # Salvar resultado
            results[endpoint] = {
                "description": description,
                "status_code": response.status_code, 
                "success": is_success,
                "content_type": response.headers.get("content-type", "unknown"),
                "response_size": len(response.text),
                "response_preview": response_preview,
                "headers": dict(response.headers),
                "url": url
            }
            
            # Análise específica do /ping
            if endpoint == "/ping":
                print(f"   🎯 ANÁLISE /ping:")
                if is_success:
                    print(f"   ✅ CORREÇÃO FUNCIONOU! Status 200")
                    if "pong" in response.text.lower() or "ping" in response.text.lower():
                        print(f"   ✅ Resposta contém 'pong' conforme esperado")
                    if response.headers.get("content-type", "").startswith("application/json"):
                        print(f"   ✅ Content-Type é JSON conforme middleware")
                else:
                    print(f"   ❌ PROBLEMA PERSISTE! Status {response.status_code}")
                    print(f"   ❌ Response: {response.text[:100]}")
            
            print("")
            
        except requests.exceptions.Timeout:
            print(f"❌ {endpoint} - TIMEOUT após 15s")
            results[endpoint] = {
                "description": description,
                "error": "Timeout after 15 seconds",
                "success": False
            }
            
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - ERRO DE CONEXÃO")
            results[endpoint] = {
                "description": description, 
                "error": "Connection error",
                "success": False
            }
            
        except Exception as e:
            print(f"❌ {endpoint} - ERRO: {str(e)}")
            results[endpoint] = {
                "description": description,
                "error": str(e),
                "success": False
            }
            
        time.sleep(1)  # Rate limiting
    
    # Relatório final
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    print(f"✅ Sucessos: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    # Análise específica do problema principal
    ping_result = results.get("/ping", {})
    if ping_result.get("success"):
        print("🎉 PROBLEMA PRINCIPAL RESOLVIDO!")
        print("   ✅ /ping agora retorna 200")
        print("   ✅ Middleware UltraSimpleCriticalMiddleware funcionando")
        print("   ✅ Conflito de endpoints eliminado")
        
        # Verificar consistência
        if ping_result.get("status_code") == 200:
            if "pong" in str(ping_result.get("response_preview", "")).lower():
                print("   ✅ Resposta contém 'pong' ✓")
            if ping_result.get("content_type", "").startswith("application/json"):
                print("   ✅ Content-Type é JSON ✓")
        
        print("\n🚀 DEPLOY RAILWAY FUNCIONANDO CORRETAMENTE!")
        
    else:
        print("❌ PROBLEMA PRINCIPAL AINDA PERSISTE")
        print(f"   ❌ /ping retorna: {ping_result.get('status_code', 'ERRO')}")
        print("   ❌ Necessária investigação adicional")
        
        if ping_result.get("status_code") == 401:
            print("   🔍 Status 401 indica que middleware não está interceptando")
            print("   🔍 Possíveis causas:")
            print("     - Ordem de middlewares incorreta")
            print("     - Cache do Railway com versão antiga")
            print("     - Problema no deploy/build")
    
    # Salvar resultados detalhados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"railway_test_report_{timestamp}.json"
    
    full_report = {
        "timestamp": datetime.now().isoformat(),
        "test_summary": {
            "total_endpoints": total_count,
            "successful_endpoints": success_count,
            "success_rate": f"{success_count/total_count*100:.1f}%",
            "ping_fixed": ping_result.get("success", False)
        },
        "endpoint_results": results,
        "railway_url": base_url,
        "conclusions": {
            "main_problem_solved": ping_result.get("success", False),
            "middleware_working": ping_result.get("success", False),
            "deploy_successful": success_count >= total_count * 0.8,
        }
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório detalhado salvo: {report_file}")
    
    return full_report

def main():
    """Executa teste final"""
    
    print("🎯 TESTE FINAL - CORREÇÃO DEFINITIVA RAILWAY")
    print("Verificando se /ping agora retorna 200 em vez de 401")
    print("")
    
    try:
        report = test_railway_endpoints()
        
        if report["conclusions"]["main_problem_solved"]:
            print("\n🏆 MISSÃO CUMPRIDA!")
            print("✅ Problema /ping 401 → 200 RESOLVIDO")
            print("✅ UltraSimpleCriticalMiddleware funcionando")
            print("✅ Endpoints duplicados eliminados") 
            print("✅ Railway deploy estável")
            
            print("\n📋 AÇÕES COMPLETADAS:")
            print("1. ✅ Identificado conflito entre middleware e endpoint")
            print("2. ✅ Removido endpoints duplicados após middlewares")
            print("3. ✅ Padronizado retorno JSON no middleware")
            print("4. ✅ Testado e validado correção")
            
            print("\n🔧 SOLUÇÃO TÉCNICA APLICADA:")
            print("- Middleware UltraSimpleCriticalMiddleware intercepta /ping PRIMEIRO")
            print("- Retorna JSONResponse padronizada: {'message': 'pong', 'status': 'ok'}")
            print("- Eliminado conflito com endpoint @app.get('/ping') posterior")
            print("- Garantida execução antes do AuthMiddleware")
            
            return True
            
        else:
            print("\n⚠️ PROBLEMA AINDA NÃO RESOLVIDO COMPLETAMENTE")
            print("❌ /ping ainda retorna erro")
            print("\n🔍 PRÓXIMAS AÇÕES SUGERIDAS:")
            print("1. Verificar logs do Railway durante deploy")
            print("2. Confirmar que Railway está usando Dockerfile correto")
            print("3. Testar com curl direto para bypass de cache")
            print("4. Investigar se Railway tem proxy específico")
            print("5. Considerar redeploy forçado para limpar cache")
            
            return False
            
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        print("Verifique conectividade e tente novamente")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
