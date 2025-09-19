#!/usr/bin/env python3
"""
🔍 MEGA DEBUG COMPLETO - ANÁLISE PROFUNDA E DEFINITIVA
========================================================

Este script faz uma análise MEGA PROFUNDA de todo o sistema para encontrar
o erro definitivo do /ping retornando 401.

ANÁLISES INCLUÍDAS:
1. ✅ Verificação de middlewares locais vs produção
2. ✅ Análise de ordem de execução dos middlewares
3. ✅ Teste de todos os endpoints críticos
4. ✅ Verificação de configurações de rate limiting
5. ✅ Análise de logs detalhados
6. ✅ Teste de diferentes User-Agents e headers
7. ✅ Verificação de cache e Redis
8. ✅ Análise de configurações de autenticação
9. ✅ Teste de bypass de middlewares
10. ✅ Verificação de deploy e versões
"""

import requests
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "https://wppagent-production-app-production.up.railway.app"
LOCAL_URL = "http://localhost:8000"

class MegaDebugger:
    """Mega Debugger - Análise profunda e definitiva"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.error_count = 0
        
    def log(self, message: str, level: str = "INFO"):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_endpoint(self, url: str, method: str = "GET", headers: Dict = None, 
                     data: Dict = None, timeout: int = 10) -> Dict:
        """Testa endpoint com análise completa"""
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            elif method == "HEAD":
                response = requests.head(url, headers=headers, timeout=timeout)
            elif method == "OPTIONS":
                response = requests.options(url, headers=headers, timeout=timeout)
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text[:500],
                "success": response.status_code == 200,
                "error": None
            }
        except Exception as e:
            return {
                "status_code": 0,
                "headers": {},
                "content": "",
                "success": False,
                "error": str(e)
            }

    def analise_1_verificacao_middlewares_locais(self):
        """ANÁLISE 1: Verificação de middlewares locais vs produção"""
        self.log("🔍 ANÁLISE 1: VERIFICAÇÃO DE MIDDLEWARES LOCAIS VS PRODUÇÃO")
        print("=" * 80)
        
        try:
            # Importar middlewares locais
            from app.middleware.critical_endpoints import CriticalEndpointsMiddleware
            from app.auth.middleware import AuthMiddleware
            
            # Testar CriticalEndpointsMiddleware local
            critical_middleware = CriticalEndpointsMiddleware(app=None)
            
            # Testar endpoints críticos localmente
            test_endpoints = ["/ping", "/health", "/meta/webhook/verify"]
            
            self.log("📋 Testando CriticalEndpointsMiddleware localmente:")
            for endpoint in test_endpoints:
                is_critical = critical_middleware._is_critical_endpoint(endpoint)
                status = "✅" if is_critical else "❌"
                self.log(f"   {status} {endpoint}: {'CRÍTICO' if is_critical else 'NÃO CRÍTICO'}")
            
            # Testar AuthMiddleware local
            auth_middleware = AuthMiddleware(app=None)
            
            self.log("📋 Testando AuthMiddleware localmente:")
            for endpoint in test_endpoints:
                is_public = auth_middleware._is_public_endpoint(endpoint)
                status = "✅" if is_public else "❌"
                self.log(f"   {status} {endpoint}: {'PÚBLICO' if is_public else 'PRIVADO'}")
            
            self.success_count += 1
            
        except Exception as e:
            self.log(f"❌ Erro na análise 1: {str(e)}", "ERROR")
            self.error_count += 1

    def analise_2_ordem_execucao_middlewares(self):
        """ANÁLISE 2: Análise de ordem de execução dos middlewares"""
        self.log("🔍 ANÁLISE 2: ORDEM DE EXECUÇÃO DOS MIDDLEWARES")
        print("=" * 80)
        
        try:
            # Ler main.py e analisar ordem
            with open("app/main.py", "r") as f:
                content = f.read()
            
            # Encontrar todas as chamadas add_middleware
            import re
            middleware_calls = re.findall(r'app\.add_middleware\((\w+)\)', content)
            
            self.log("📋 Ordem atual dos middlewares:")
            for i, middleware in enumerate(middleware_calls, 1):
                self.log(f"   {i:2d}. {middleware}")
            
            # Verificar se CriticalEndpointsMiddleware está antes de AuthMiddleware
            critical_pos = None
            auth_pos = None
            
            for i, middleware in enumerate(middleware_calls):
                if "CriticalEndpoints" in middleware:
                    critical_pos = i
                elif "AuthMiddleware" in middleware:
                    auth_pos = i
            
            if critical_pos is not None and auth_pos is not None:
                if critical_pos < auth_pos:
                    self.log("✅ CriticalEndpointsMiddleware está ANTES do AuthMiddleware")
                    self.success_count += 1
                else:
                    self.log("❌ CriticalEndpointsMiddleware está DEPOIS do AuthMiddleware")
                    self.error_count += 1
            else:
                self.log("⚠️ Não foi possível determinar a ordem dos middlewares")
                self.warnings.append("Ordem de middlewares não clara")
            
        except Exception as e:
            self.log(f"❌ Erro na análise 2: {str(e)}", "ERROR")
            self.error_count += 1

    def analise_3_testes_endpoints_criticos(self):
        """ANÁLISE 3: Teste de todos os endpoints críticos"""
        self.log("🔍 ANÁLISE 3: TESTE DE ENDPOINTS CRÍTICOS")
        print("=" * 80)
        
        critical_endpoints = [
            ("/ping", "GET"),
            ("/health", "GET"),
            ("/meta/webhook/verify", "POST"),
            ("/meta/webhook", "GET"),
            ("/webhook", "GET"),
            ("/webhook/test", "GET")
        ]
        
        for endpoint, method in critical_endpoints:
            self.log(f"📋 Testando {method} {endpoint}:")
            
            # Teste com headers diferentes
            test_headers = [
                {},
                {"User-Agent": "Railway-Health-Check/1.0"},
                {"User-Agent": "curl/7.68.0"},
                {"Cache-Control": "no-cache"},
                {"X-Forwarded-For": "127.0.0.1"}
            ]
            
            for i, headers in enumerate(test_headers, 1):
                result = self.test_endpoint(f"{BASE_URL}{endpoint}", method, headers)
                
                status = "✅" if result["success"] else "❌"
                self.log(f"   {i}. Headers {headers}: {result['status_code']} {status}")
                
                if not result["success"] and result["error"]:
                    self.log(f"      Erro: {result['error']}")
                elif not result["success"]:
                    self.log(f"      Content: {result['content'][:100]}...")
            
            print()

    def analise_4_configuracoes_rate_limiting(self):
        """ANÁLISE 4: Verificação de configurações de rate limiting"""
        self.log("🔍 ANÁLISE 4: CONFIGURAÇÕES DE RATE LIMITING")
        print("=" * 80)
        
        try:
            # Verificar rate_limit_config.py
            with open("app/config/rate_limit_config.py", "r") as f:
                content = f.read()
            
            # Verificar se /ping está nos EXEMPT_ENDPOINTS
            if "GET /ping" in content and "EXEMPT_ENDPOINTS" in content:
                self.log("✅ /ping está configurado nos EXEMPT_ENDPOINTS")
                self.success_count += 1
            else:
                self.log("❌ /ping NÃO está configurado nos EXEMPT_ENDPOINTS")
                self.error_count += 1
            
            # Verificar webhook_rate_limit.py
            with open("app/middleware/webhook_rate_limit.py", "r") as f:
                content = f.read()
            
            if "/ping" in content and "exempt_paths" in content:
                self.log("✅ /ping está configurado nos exempt_paths do WebhookRateLimitMiddleware")
                self.success_count += 1
            else:
                self.log("❌ /ping NÃO está configurado nos exempt_paths do WebhookRateLimitMiddleware")
                self.error_count += 1
            
        except Exception as e:
            self.log(f"❌ Erro na análise 4: {str(e)}", "ERROR")
            self.error_count += 1

    def analise_5_logs_detalhados(self):
        """ANÁLISE 5: Análise de logs detalhados"""
        self.log("🔍 ANÁLISE 5: LOGS DETALHADOS")
        print("=" * 80)
        
        # Fazer requisições e analisar logs
        for i in range(3):
            self.log(f"📋 Requisição {i+1} para /ping:")
            
            result = self.test_endpoint(f"{BASE_URL}/ping")
            
            self.log(f"   Status: {result['status_code']}")
            self.log(f"   Headers: {result['headers']}")
            self.log(f"   Content: {result['content'][:200]}...")
            
            if result["status_code"] == 401:
                self.log("   ❌ Ainda retornando 401 - CriticalEndpointsMiddleware não está funcionando")
                self.error_count += 1
            elif result["status_code"] == 200:
                self.log("   ✅ Funcionando! CriticalEndpointsMiddleware ativo!")
                self.success_count += 1
            
            time.sleep(2)

    def analise_6_user_agents_headers(self):
        """ANÁLISE 6: Teste de diferentes User-Agents e headers"""
        self.log("🔍 ANÁLISE 6: USER-AGENTS E HEADERS")
        print("=" * 80)
        
        user_agents = [
            "Railway-Health-Check/1.0",
            "curl/7.68.0",
            "Mozilla/5.0 (compatible; Railway/1.0)",
            "HealthCheck/1.0",
            "Python-requests/2.28.1",
            "Railway/1.0",
            "Health-Check/1.0"
        ]
        
        for ua in user_agents:
            headers = {"User-Agent": ua}
            result = self.test_endpoint(f"{BASE_URL}/ping", headers=headers)
            
            status = "✅" if result["success"] else "❌"
            self.log(f"   {ua}: {result['status_code']} {status}")

    def analise_7_cache_redis(self):
        """ANÁLISE 7: Verificação de cache e Redis"""
        self.log("🔍 ANÁLISE 7: CACHE E REDIS")
        print("=" * 80)
        
        # Teste com bypass de cache
        cache_headers = [
            {"Cache-Control": "no-cache, no-store, must-revalidate"},
            {"Pragma": "no-cache"},
            {"Expires": "0"},
            {"If-Modified-Since": "Thu, 01 Jan 1970 00:00:00 GMT"},
            {"If-None-Match": "*"}
        ]
        
        for i, headers in enumerate(cache_headers, 1):
            result = self.test_endpoint(f"{BASE_URL}/ping", headers=headers)
            
            status = "✅" if result["success"] else "❌"
            self.log(f"   {i}. Cache bypass {headers}: {result['status_code']} {status}")

    def analise_8_configuracoes_autenticacao(self):
        """ANÁLISE 8: Análise de configurações de autenticação"""
        self.log("🔍 ANÁLISE 8: CONFIGURAÇÕES DE AUTENTICAÇÃO")
        print("=" * 80)
        
        try:
            # Verificar AuthMiddleware
            with open("app/auth/middleware.py", "r") as f:
                content = f.read()
            
            # Verificar se /ping está nos public_endpoints
            if "/ping" in content and "public_endpoints" in content:
                self.log("✅ /ping está configurado nos public_endpoints do AuthMiddleware")
                self.success_count += 1
            else:
                self.log("❌ /ping NÃO está configurado nos public_endpoints do AuthMiddleware")
                self.error_count += 1
            
            # Verificar ApiResponseMiddleware
            with open("app/middleware/response_standardizer.py", "r") as f:
                content = f.read()
            
            if "/ping" in content and "excluded_paths" in content:
                self.log("✅ /ping está configurado nos excluded_paths do ApiResponseMiddleware")
                self.success_count += 1
            else:
                self.log("❌ /ping NÃO está configurado nos excluded_paths do ApiResponseMiddleware")
                self.error_count += 1
            
        except Exception as e:
            self.log(f"❌ Erro na análise 8: {str(e)}", "ERROR")
            self.error_count += 1

    def analise_9_teste_bypass_middlewares(self):
        """ANÁLISE 9: Teste de bypass de middlewares"""
        self.log("🔍 ANÁLISE 9: TESTE DE BYPASS DE MIDDLEWARES")
        print("=" * 80)
        
        # Testar diferentes métodos HTTP
        methods = ["GET", "HEAD", "OPTIONS", "POST"]
        
        for method in methods:
            result = self.test_endpoint(f"{BASE_URL}/ping", method=method)
            
            status = "✅" if result["success"] else "❌"
            self.log(f"   {method}: {result['status_code']} {status}")

    def analise_10_verificacao_deploy_versoes(self):
        """ANÁLISE 10: Verificação de deploy e versões"""
        self.log("🔍 ANÁLISE 10: DEPLOY E VERSÕES")
        print("=" * 80)
        
        # Verificar se o deploy foi concluído
        self.log("📋 Verificando se o deploy foi concluído...")
        
        # Fazer várias requisições para verificar consistência
        for i in range(5):
            result = self.test_endpoint(f"{BASE_URL}/ping")
            
            if result["status_code"] == 200:
                self.log(f"   ✅ Requisição {i+1}: FUNCIONANDO! Deploy concluído!")
                self.success_count += 1
                break
            else:
                self.log(f"   ❌ Requisição {i+1}: {result['status_code']} - Deploy ainda não concluído")
                time.sleep(10)
        
        # Verificar outros endpoints para comparar
        other_endpoints = ["/health", "/docs", "/metrics", "/"]
        
        self.log("📋 Verificando outros endpoints para comparação:")
        for endpoint in other_endpoints:
            result = self.test_endpoint(f"{BASE_URL}{endpoint}")
            
            status = "✅" if result["success"] else "❌"
            self.log(f"   {endpoint}: {result['status_code']} {status}")

    def gerar_relatorio_final(self):
        """Gera relatório final com todas as descobertas"""
        self.log("🔍 RELATÓRIO FINAL - ANÁLISE COMPLETA")
        print("=" * 80)
        
        self.log(f"📊 ESTATÍSTICAS:")
        self.log(f"   ✅ Sucessos: {self.success_count}")
        self.log(f"   ❌ Erros: {self.error_count}")
        self.log(f"   ⚠️ Avisos: {len(self.warnings)}")
        
        if self.error_count > 0:
            self.log("❌ PROBLEMAS IDENTIFICADOS:")
            for error in self.errors:
                self.log(f"   - {error}")
        
        if self.warnings:
            self.log("⚠️ AVISOS:")
            for warning in self.warnings:
                self.log(f"   - {warning}")
        
        if self.success_count > self.error_count:
            self.log("✅ SISTEMA FUNCIONANDO CORRETAMENTE!")
        else:
            self.log("❌ SISTEMA COM PROBLEMAS - ANÁLISE NECESSÁRIA!")
        
        print("=" * 80)

    def executar_analise_completa(self):
        """Executa análise completa"""
        self.log("🚀 INICIANDO MEGA ANÁLISE PROFUNDA E DEFINITIVA")
        print("=" * 80)
        print(f"🌐 Servidor: {BASE_URL}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        
        # Executar todas as análises
        self.analise_1_verificacao_middlewares_locais()
        self.analise_2_ordem_execucao_middlewares()
        self.analise_3_testes_endpoints_criticos()
        self.analise_4_configuracoes_rate_limiting()
        self.analise_5_logs_detalhados()
        self.analise_6_user_agents_headers()
        self.analise_7_cache_redis()
        self.analise_8_configuracoes_autenticacao()
        self.analise_9_teste_bypass_middlewares()
        self.analise_10_verificacao_deploy_versoes()
        
        # Gerar relatório final
        self.gerar_relatorio_final()

def main():
    """Executa mega análise completa"""
    debugger = MegaDebugger()
    debugger.executar_analise_completa()

if __name__ == "__main__":
    main()

