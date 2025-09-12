#!/usr/bin/env python3
"""
H005: Script de teste automático do PWA
Testa a implementação programaticamente
"""

import requests
import json
import os
import time
from urllib.parse import urlparse

class H005PWATester:
    def __init__(self):
        self.base_url = "https://wppagent-production-app-production.up.railway.app"
        self.results = []
        
    def log_result(self, test, status, message):
        """Log de resultado do teste"""
        result = {
            "test": test,
            "status": status,
            "message": message,
            "timestamp": time.time()
        }
        self.results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test}: {message}")
        
    def test_pwa_manifest(self):
        """Teste 1: Verificar manifest.json"""
        try:
            response = requests.get(f"{self.base_url}/manifest.json", timeout=10)
            if response.status_code == 200:
                manifest = response.json()
                if "name" in manifest and "short_name" in manifest:
                    self.log_result("PWA Manifest", "PASS", "Manifest.json válido encontrado")
                else:
                    self.log_result("PWA Manifest", "FAIL", "Manifest.json sem campos obrigatórios")
            else:
                self.log_result("PWA Manifest", "FAIL", f"Manifest não encontrado: {response.status_code}")
        except Exception as e:
            self.log_result("PWA Manifest", "FAIL", f"Erro ao verificar manifest: {str(e)}")
            
    def test_service_worker(self):
        """Teste 2: Verificar Service Worker H005"""
        try:
            response = requests.get(f"{self.base_url}/sw-h005.js", timeout=10)
            if response.status_code == 200:
                sw_content = response.text
                if "H005" in sw_content and "AUTH_BYPASS_URLS" in sw_content:
                    self.log_result("Service Worker", "PASS", "sw-h005.js carregado com auth bypass")
                else:
                    self.log_result("Service Worker", "FAIL", "sw-h005.js sem implementação H005")
            else:
                self.log_result("Service Worker", "FAIL", f"sw-h005.js não encontrado: {response.status_code}")
        except Exception as e:
            self.log_result("Service Worker", "FAIL", f"Erro ao verificar SW: {str(e)}")
            
    def test_offline_page(self):
        """Teste 3: Verificar página offline"""
        try:
            response = requests.get(f"{self.base_url}/offline", timeout=10)
            if response.status_code == 200:
                content = response.text
                if "offline" in content.lower() and "login" in content.lower():
                    self.log_result("Página Offline", "PASS", "Página /offline configurada corretamente")
                else:
                    self.log_result("Página Offline", "WARN", "Página /offline existe mas conteúdo não verificado")
            else:
                self.log_result("Página Offline", "FAIL", f"Página /offline não acessível: {response.status_code}")
        except Exception as e:
            self.log_result("Página Offline", "FAIL", f"Erro ao verificar página offline: {str(e)}")
            
    def test_auth_endpoints(self):
        """Teste 4: Verificar endpoints de autenticação"""
        auth_urls = [
            "/api/auth/login",
            "/api/auth/logout", 
            "/api/auth/refresh",
            "/api/auth/verify"
        ]
        
        for url in auth_urls:
            try:
                response = requests.get(f"{self.base_url}{url}", timeout=5)
                # Esperamos 401/403 para endpoints protegidos
                if response.status_code in [401, 403, 405]:
                    self.log_result(f"Auth Endpoint {url}", "PASS", "Endpoint protegido corretamente")
                elif response.status_code == 200:
                    self.log_result(f"Auth Endpoint {url}", "WARN", "Endpoint acessível sem auth")
                else:
                    self.log_result(f"Auth Endpoint {url}", "FAIL", f"Endpoint com erro: {response.status_code}")
            except Exception as e:
                self.log_result(f"Auth Endpoint {url}", "FAIL", f"Erro: {str(e)}")
                
    def test_dashboard_pages(self):
        """Teste 5: Verificar páginas do dashboard"""
        dashboard_pages = [
            "/dashboard",
            "/agendamentos",
            "/conversas", 
            "/monitoring"
        ]
        
        for page in dashboard_pages:
            try:
                response = requests.get(f"{self.base_url}{page}", timeout=10)
                if response.status_code == 200:
                    self.log_result(f"Dashboard {page}", "PASS", "Página carregada")
                elif response.status_code == 302:
                    self.log_result(f"Dashboard {page}", "PASS", "Página redireciona (auth)")
                else:
                    self.log_result(f"Dashboard {page}", "FAIL", f"Página com erro: {response.status_code}")
            except Exception as e:
                self.log_result(f"Dashboard {page}", "FAIL", f"Erro: {str(e)}")
                
    def test_pwa_headers(self):
        """Teste 6: Verificar headers PWA"""
        try:
            response = requests.head(self.base_url, timeout=10)
            headers = response.headers
            
            # Verificar headers importantes para PWA
            pwa_headers = {
                "x-frame-options": "DENY",
                "x-content-type-options": "nosniff"
            }
            
            for header, expected in pwa_headers.items():
                if header.lower() in [h.lower() for h in headers.keys()]:
                    self.log_result(f"Header {header}", "PASS", f"Header de segurança presente")
                else:
                    self.log_result(f"Header {header}", "WARN", f"Header de segurança ausente")
                    
        except Exception as e:
            self.log_result("PWA Headers", "FAIL", f"Erro ao verificar headers: {str(e)}")
            
    def run_all_tests(self):
        """Executar todos os testes"""
        print("🚀 H005: Testando PWA com Auth Bypass")
        print("=" * 50)
        print()
        
        self.test_pwa_manifest()
        self.test_service_worker()
        self.test_offline_page()
        self.test_auth_endpoints()
        self.test_dashboard_pages()
        self.test_pwa_headers()
        
        print()
        print("📊 RESUMO DOS TESTES:")
        print("-" * 30)
        
        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        
        print(f"✅ Passou: {passed}/{total}")
        print(f"❌ Falhou: {failed}/{total}")
        print(f"⚠️  Avisos: {warnings}/{total}")
        
        if failed == 0:
            print("\n🎉 H005: PWA está funcionando corretamente!")
            return True
        else:
            print(f"\n❌ H005: {failed} testes falharam. Verifique a implementação.")
            return False
            
    def save_results(self):
        """Salvar resultados em arquivo JSON"""
        with open('/home/vancim/whats_agent/h005_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Resultados salvos em: h005_test_results.json")

if __name__ == "__main__":
    tester = H005PWATester()
    success = tester.run_all_tests()
    tester.save_results()
    
    if success:
        exit(0)
    else:
        exit(1)
