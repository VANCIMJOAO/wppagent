#!/usr/bin/env python3
"""
🔍 S001 Validation Script - CSP Security Testing
===============================================

Script completo para validar implementação do S001:
- CSP headers em todas responses ✅
- Inline scripts removidos ✅  
- Externa resources whitelistadas ✅
- Browser console sem warnings ✅
- CSP scanner = 0 vulnerabilidades ✅
"""

import asyncio
import sys
import os
import time
from typing import List, Dict
import httpx

# Adicionar path para importar módulos da app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.security.csp_scanner import run_csp_security_scan, format_csp_report

class S001Validator:
    """Validador completo para S001 - CSP Implementation"""
    
    def __init__(self, base_url: str = "https://wppagent-production.up.railway.app"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def test_csp_headers_presence(self) -> bool:
        """Teste 1: CSP headers em todas responses"""
        print("🔍 Teste 1: Verificando presença de headers CSP...")
        
        endpoints = ["/health", "/docs", "/api/v1/users/me", "/"]
        all_have_csp = True
        
        for endpoint in endpoints:
            try:
                response = await self.client.head(f"{self.base_url}{endpoint}")
                has_csp = 'content-security-policy' in response.headers
                
                status = "✅" if has_csp else "❌"
                print(f"  {status} {endpoint}: CSP = {has_csp}")
                
                if not has_csp:
                    all_have_csp = False
                    
            except Exception as e:
                print(f"  ❌ {endpoint}: Erro - {e}")
                all_have_csp = False
        
        return all_have_csp
    
    async def test_inline_scripts_removal(self) -> bool:
        """Teste 2: Inline scripts removidos"""
        print("\n🔍 Teste 2: Verificando remoção de inline scripts...")
        
        # Verificar se CSP bloqueia unsafe-inline
        try:
            headers = await self.get_csp_headers()
            csp = headers.get('content-security-policy', '')
            
            has_unsafe_inline = "'unsafe-inline'" in csp
            
            if has_unsafe_inline:
                print("  ❌ CSP ainda permite 'unsafe-inline' em scripts")
                return False
            else:
                print("  ✅ CSP não permite 'unsafe-inline' - inline scripts bloqueados")
                return True
                
        except Exception as e:
            print(f"  ❌ Erro ao verificar inline scripts: {e}")
            return False
    
    async def test_external_resources_whitelist(self) -> bool:
        """Teste 3: External resources whitelistadas"""
        print("\n🔍 Teste 3: Verificando whitelist de recursos externos...")
        
        try:
            headers = await self.get_csp_headers()
            csp = headers.get('content-security-policy', '')
            
            # Verificar domínios críticos whitelistados
            required_domains = [
                "https://cdnjs.cloudflare.com",  # CDN scripts
                "https://fonts.googleapis.com",   # Google Fonts
                "https://api.whatsapp.com",      # WhatsApp API
                "wss://wppagent-production.up.railway.app"  # WebSocket
            ]
            
            all_domains_present = True
            for domain in required_domains:
                if domain in csp:
                    print(f"  ✅ {domain} - Whitelistado")
                else:
                    print(f"  ❌ {domain} - Não encontrado no CSP")
                    all_domains_present = False
            
            return all_domains_present
            
        except Exception as e:
            print(f"  ❌ Erro ao verificar whitelist: {e}")
            return False
    
    async def test_browser_console_warnings(self) -> bool:
        """Teste 4: Browser console sem warnings (simulado)"""
        print("\n🔍 Teste 4: Verificando configuração para evitar warnings...")
        
        try:
            headers = await self.get_csp_headers()
            
            # Verificar configurações que previnem warnings comuns
            checks = {
                "CSP presente": 'content-security-policy' in headers,
                "X-Frame-Options": 'x-frame-options' in headers,
                "X-Content-Type-Options": 'x-content-type-options' in headers,
                "Referrer-Policy": 'referrer-policy' in headers
            }
            
            all_ok = True
            for check, result in checks.items():
                status = "✅" if result else "❌"
                print(f"  {status} {check}: {result}")
                if not result:
                    all_ok = False
            
            return all_ok
            
        except Exception as e:
            print(f"  ❌ Erro ao verificar headers: {e}")
            return False
    
    async def test_csp_scanner_vulnerabilities(self) -> bool:
        """Teste 5: CSP scanner = 0 vulnerabilidades críticas"""
        print("\n🔍 Teste 5: Executando scan completo de vulnerabilidades CSP...")
        
        try:
            report = await run_csp_security_scan(self.base_url)
            
            # Contar vulnerabilidades críticas e altas
            critical_vulns = [v for v in report.vulnerabilities if v.risk_level in ['critical', 'high']]
            
            print(f"  📊 Score de segurança: {report.security_score}/100")
            print(f"  🔍 Total de testes: {report.total_tests}")
            print(f"  ✅ Testes passados: {report.passed_tests}")
            print(f"  ❌ Vulnerabilidades: {len(report.vulnerabilities)}")
            print(f"  🚨 Vulnerabilidades críticas/altas: {len(critical_vulns)}")
            
            if critical_vulns:
                print("\n  🚨 Vulnerabilidades críticas encontradas:")
                for vuln in critical_vulns:
                    print(f"    - [{vuln.risk_level.upper()}] {vuln.directive}: {vuln.details}")
            
            # Critério: 0 vulnerabilidades críticas/altas
            return len(critical_vulns) == 0
            
        except Exception as e:
            print(f"  ❌ Erro durante scan de vulnerabilidades: {e}")
            return False
    
    async def get_csp_headers(self) -> Dict[str, str]:
        """Obter headers CSP do endpoint principal"""
        response = await self.client.head(f"{self.base_url}/health")
        return {k.lower(): v for k, v in response.headers.items()}
    
    async def run_full_validation(self) -> bool:
        """Executar validação completa S001"""
        print("🔒 S001 - Content Security Policy Validation")
        print("=" * 50)
        
        tests = [
            ("CSP headers em todas responses", self.test_csp_headers_presence),
            ("Inline scripts removidos", self.test_inline_scripts_removal),
            ("External resources whitelistadas", self.test_external_resources_whitelist),
            ("Headers para evitar warnings", self.test_browser_console_warnings),
            ("Scanner: 0 vulnerabilidades críticas", self.test_csp_scanner_vulnerabilities)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append(result)
            except Exception as e:
                print(f"❌ Erro no teste '{test_name}': {e}")
                results.append(False)
        
        # Resumo final
        print("\n" + "=" * 50)
        print("📊 RESUMO S001 VALIDATION")
        print("=" * 50)
        
        passed = sum(results)
        total = len(results)
        
        for i, (test_name, _) in enumerate(tests):
            status = "✅ PASS" if results[i] else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        success_rate = (passed / total) * 100
        overall_pass = passed == total
        
        print(f"\n📈 Taxa de sucesso: {passed}/{total} ({success_rate:.1f}%)")
        
        if overall_pass:
            print("🎉 S001 - CSP Implementation: COMPLETO ✅")
            print("\n✅ Todos os critérios de pronto atendidos:")
            print("  ✅ CSP headers em todas responses")
            print("  ✅ Inline scripts removidos") 
            print("  ✅ External resources whitelistadas")
            print("  ✅ Headers configurados para evitar warnings")
            print("  ✅ CSP scanner = 0 vulnerabilidades críticas")
        else:
            print("❌ S001 - CSP Implementation: FALHOU")
            print(f"\n❌ {total - passed} critério(s) não atendido(s)")
        
        return overall_pass
    
    async def close(self):
        """Fechar cliente HTTP"""
        await self.client.aclose()


async def main():
    """Função principal para executar validação S001"""
    validator = S001Validator()
    
    try:
        success = await validator.run_full_validation()
        
        # Código de saída para CI/CD
        exit_code = 0 if success else 1
        sys.exit(exit_code)
        
    finally:
        await validator.close()


if __name__ == "__main__":
    asyncio.run(main())
