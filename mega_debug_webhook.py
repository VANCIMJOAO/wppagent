#!/usr/bin/env python3
"""
MEGA DEBUG PROFUNDO - WEBHOOK META
==================================
Análise completa do problema de validação do webhook Meta
"""

import requests
import json
import time
from datetime import datetime

def print_separator(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def test_endpoint(url, headers=None, description=""):
    """Testa um endpoint e retorna informações detalhadas"""
    print(f"\n🔍 {description}")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers or {}, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text[:500]}...")
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "success": response.status_code == 200
        }
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return {
            "status_code": None,
            "error": str(e),
            "success": False
        }

def main():
    print_separator("MEGA DEBUG WEBHOOK META - INÍCIO")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    base_url = "https://wppagent-production-app-production.up.railway.app"
    
    # Configurações de teste
    test_configs = [
        {
            "name": "1. Health Check",
            "url": f"{base_url}/health",
            "headers": None,
            "description": "Verificar se servidor está funcionando"
        },
        {
            "name": "2. Ping Railway",
            "url": f"{base_url}/ping",
            "headers": None,
            "description": "Endpoint de healthcheck Railway"
        },
        {
            "name": "3. Root Endpoint",
            "url": f"{base_url}/",
            "headers": None,
            "description": "Endpoint raiz da aplicação"
        },
        {
            "name": "4. Docs (público)",
            "url": f"{base_url}/docs",
            "headers": None,
            "description": "Documentação da API (deve ser público)"
        },
        {
            "name": "5. Meta Webhook - Curl Normal",
            "url": f"{base_url}/meta/webhook/verify?hub.mode=subscribe&hub.challenge=12345&hub.verify_token=whatsapp_webhook_verify_token",
            "headers": None,
            "description": "Teste com curl normal - sem User-Agent especial"
        },
        {
            "name": "6. Meta Webhook - Facebook User-Agent",
            "url": f"{base_url}/meta/webhook/verify?hub.mode=subscribe&hub.challenge=12345&hub.verify_token=whatsapp_webhook_verify_token",
            "headers": {"User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"},
            "description": "Teste com Facebook User-Agent"
        },
        {
            "name": "7. Meta Webhook - Challenge String",
            "url": f"{base_url}/meta/webhook/verify?hub.mode=subscribe&hub.challenge=CHALLENGE_VERIF_TOKEN&hub.verify_token=whatsapp_webhook_verify_token",
            "headers": {"User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"},
            "description": "Teste com challenge string (como Meta envia)"
        },
        {
            "name": "8. Webhook Principal",
            "url": f"{base_url}/webhook/verify?hub.mode=subscribe&hub.challenge=12345&hub.verify_token=whatsapp_webhook_verify_token",
            "headers": None,
            "description": "Teste webhook principal"
        },
        {
            "name": "9. Meta Base Path",
            "url": f"{base_url}/meta",
            "headers": None,
            "description": "Teste path base /meta"
        },
        {
            "name": "10. Meta Webhook Sem Verify",
            "url": f"{base_url}/meta/webhook",
            "headers": None,
            "description": "Teste path /meta/webhook sem /verify"
        }
    ]
    
    results = []
    
    for config in test_configs:
        print_separator(config["name"])
        result = test_endpoint(
            config["url"], 
            config.get("headers"), 
            config["description"]
        )
        result["name"] = config["name"]
        result["url"] = config["url"]
        results.append(result)
        
        # Pausa entre requests
        time.sleep(1)
    
    # Análise de resultados
    print_separator("ANÁLISE DE RESULTADOS")
    
    public_endpoints = []
    auth_failed = []
    errors = []
    successful = []
    
    for result in results:
        if result["success"]:
            successful.append(result)
        elif result.get("status_code") == 200:
            public_endpoints.append(result)
        elif "Authentication failed" in result.get("body", ""):
            auth_failed.append(result)
        else:
            errors.append(result)
    
    print(f"\n✅ SUCESSOS ({len(successful)}):")
    for r in successful:
        print(f"  - {r['name']}: {r['status_code']}")
    
    print(f"\n🔐 FALHAS DE AUTENTICAÇÃO ({len(auth_failed)}):")
    for r in auth_failed:
        print(f"  - {r['name']}: {r['status_code']} - {r['body'][:100]}")
    
    print(f"\n❌ OUTROS ERROS ({len(errors)}):")
    for r in errors:
        print(f"  - {r['name']}: {r.get('status_code', 'N/A')} - {r.get('body', r.get('error', ''))[:100]}")
    
    # Diagnóstico específico
    print_separator("DIAGNÓSTICO ESPECÍFICO")
    
    meta_tests = [r for r in results if "/meta" in r["url"]]
    print(f"\nTestes específicos do Meta ({len(meta_tests)}):")
    
    for test in meta_tests:
        print(f"\n📋 {test['name']}:")
        print(f"   Status: {test.get('status_code', 'ERRO')}")
        print(f"   Body: {test.get('body', test.get('error', ''))[:200]}")
        
        if "Authentication failed" in test.get("body", ""):
            print("   🚨 PROBLEMA: Middleware está bloqueando endpoint Meta!")
            print("   💡 SOLUÇÃO: Verificar configuração de endpoints públicos")
    
    # Salvar relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"temp_reports/mega_debug_webhook_{timestamp}.json"
    
    with open(report_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "results": results,
            "summary": {
                "successful": len(successful),
                "auth_failed": len(auth_failed),
                "errors": len(errors),
                "total_tests": len(results)
            }
        }, f, indent=2)
    
    print(f"\n💾 Relatório salvo: {report_file}")
    
    print_separator("CONCLUSÕES")
    
    if auth_failed:
        print("🚨 PROBLEMA IDENTIFICADO:")
        print("   - Endpoints /meta/webhook estão sendo bloqueados pelo middleware")
        print("   - Middleware não está reconhecendo /meta/webhook como público")
        print("   - Necessário verificar lógica de verificação de endpoints públicos")
        
        print("\n🔧 PRÓXIMOS PASSOS:")
        print("   1. Verificar se deploy foi aplicado corretamente")
        print("   2. Examinar logs do Railway para ver middleware em ação")
        print("   3. Testar com endpoint público conhecido (ex: /health)")
        print("   4. Verificar se existe cache ou delay no deploy")
    
    if successful:
        print("✅ ENDPOINTS FUNCIONANDO:")
        for s in successful:
            print(f"   - {s['name']}")

if __name__ == "__main__":
    main()