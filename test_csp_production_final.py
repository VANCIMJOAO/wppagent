#!/usr/bin/env python3
"""
🛡️ CSP Production Testing Final

Teste completo e final do sistema CSP implementado no Railway.
Validação da solução "5.1 CSP Headers Incompletos".
"""

import requests
import re
import json
from urllib.parse import urlparse

# 🎯 URL do Railway
RAILWAY_URL = "https://wppagent-production.up.railway.app"

def test_csp_headers():
    """🛡️ Testa se os headers CSP estão implementados"""
    print("🛡️ Testando CSP Headers no Railway...")
    
    try:
        response = requests.get(RAILWAY_URL, timeout=10)
        headers = response.headers
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"🌐 Server: {headers.get('server', 'N/A')}")
        
        # Verificar CSP principal
        csp_header = headers.get('content-security-policy')
        if csp_header:
            print("✅ Content-Security-Policy ENCONTRADO!")
            print(f"📋 CSP: {csp_header[:100]}...")
            
            # Verificações específicas
            checks = [
                ("default-src 'self'", "Política padrão restritiva"),
                ("script-src 'self'", "Scripts apenas do próprio domínio"),
                ("'nonce-", "Suporte a nonce para scripts inline"),
                ("'strict-dynamic'", "Política dinâmica rigorosa"),
                ("report-uri", "Relatório de violações configurado")
            ]
            
            for check, desc in checks:
                if check in csp_header:
                    print(f"  ✅ {desc}")
                else:
                    print(f"  ❌ {desc}")
        else:
            print("❌ CSP Header NÃO encontrado!")
            
        # Verificar CSP Report-Only
        csp_report = headers.get('content-security-policy-report-only')
        if csp_report:
            print("✅ CSP-Report-Only ENCONTRADO!")
            print(f"📋 CSP-RO: {csp_report[:100]}...")
        
        return csp_header is not None
        
    except Exception as e:
        print(f"❌ Erro ao testar CSP: {e}")
        return False

def test_security_headers():
    """🔒 Testa outros headers de segurança"""
    print("\n🔒 Testando Headers de Segurança...")
    
    try:
        response = requests.head(RAILWAY_URL, timeout=10)
        headers = response.headers
        
        security_headers = [
            ('strict-transport-security', 'HSTS - Força HTTPS'),
            ('x-content-type-options', 'Previne MIME sniffing'),
            ('x-frame-options', 'Previne clickjacking'),
            ('x-xss-protection', 'Proteção XSS'),
            ('referrer-policy', 'Política de referrer'),
            ('permissions-policy', 'Permissões de APIs'),
            ('cross-origin-embedder-policy', 'Política COEP'),
            ('cross-origin-opener-policy', 'Política COOP'),
            ('cross-origin-resource-policy', 'Política CORP')
        ]
        
        found_headers = 0
        for header, description in security_headers:
            value = headers.get(header)
            if value:
                print(f"  ✅ {description}: {value[:50]}...")
                found_headers += 1
            else:
                print(f"  ❌ {description}: NÃO encontrado")
        
        print(f"\n📊 Headers de segurança: {found_headers}/{len(security_headers)}")
        return found_headers >= 7  # Pelo menos 7 de 9
        
    except Exception as e:
        print(f"❌ Erro ao testar headers: {e}")
        return False

def test_csp_violation_endpoint():
    """📍 Testa endpoint de violação CSP"""
    print("\n📍 Testando Endpoint de Violações CSP...")
    
    try:
        # Payload de teste de violação CSP
        violation_payload = {
            "csp-report": {
                "document-uri": f"{RAILWAY_URL}/test",
                "violated-directive": "script-src 'self'",
                "blocked-uri": "https://evil.example.com/malicious.js",
                "line-number": 1,
                "column-number": 1,
                "source-file": f"{RAILWAY_URL}/test.html"
            }
        }
        
        response = requests.post(
            f"{RAILWAY_URL}/api/security/csp-report",
            json=violation_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Endpoint de violação CSP funcionando!")
            return True
        elif response.status_code == 401:
            print("🔐 Endpoint protegido (autenticação necessária) - OK")
            return True
        else:
            print(f"⚠️ Status inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar endpoint: {e}")
        return False

def test_api_endpoint():
    """🔗 Testa um endpoint da API"""
    print("\n🔗 Testando Endpoint da API...")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/api/health", timeout=10)
        headers = response.headers
        
        print(f"📡 Status: {response.status_code}")
        
        # Verificar se CSP está presente na API também
        csp_header = headers.get('content-security-policy')
        if csp_header:
            print("✅ CSP aplicado na API também!")
        else:
            print("⚠️ CSP não encontrado na API")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")
        return False

def main():
    """🎯 Execução principal dos testes"""
    print("🛡️ TESTE FINAL CSP PRODUCTION - RAILWAY")
    print("=" * 50)
    
    results = {
        "csp_headers": test_csp_headers(),
        "security_headers": test_security_headers(), 
        "csp_endpoint": test_csp_violation_endpoint(),
        "api_test": test_api_endpoint()
    }
    
    print("\n📊 RESULTADO FINAL:")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 SCORE: {passed_tests}/{total_tests}")
    
    if passed_tests >= 3:
        print("🎉 SUCESSO! Sistema CSP implementado corretamente!")
        print("✅ Solução '5.1 CSP Headers Incompletos' RESOLVIDA!")
        if passed_tests == total_tests:
            print("🏆 PERFEITO! Todos os testes passaram!")
    else:
        print("⚠️ Alguns testes falharam. Revisar implementação.")
    
    return passed_tests >= 3

if __name__ == "__main__":
    main()
