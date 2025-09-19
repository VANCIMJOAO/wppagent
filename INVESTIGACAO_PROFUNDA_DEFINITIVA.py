#!/usr/bin/env python3
"""
🔍 INVESTIGAÇÃO PROFUNDA E DEFINITIVA - ENCONTRAR SOLUÇÃO REAL
==============================================================

Este script faz uma investigação MEGA PROFUNDA para encontrar a solução
definitiva para o problema do /ping retornando 401.

INVESTIGAÇÕES INCLUÍDAS:
1. ✅ Análise completa do código local vs produção
2. ✅ Verificação de versões e commits
3. ✅ Análise de logs detalhados do Railway
4. ✅ Teste de diferentes abordagens de middleware
5. ✅ Verificação de configurações do Railway
6. ✅ Análise de cache e deploy
7. ✅ Teste de soluções alternativas
8. ✅ Verificação de problemas de importação
9. ✅ Análise de ordem de execução real
10. ✅ Teste de bypass completo
"""

import requests
import time
import json
import sys
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

# Adicionar path do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "https://wppagent-production-app-production.up.railway.app"

class InvestigadorProfundo:
    """Investigador Profundo - Análise definitiva e solução real"""
    
    def __init__(self):
        self.descobertas = []
        self.solucoes = []
        self.problemas = []
        self.evidencias = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def investigacao_1_analise_codigo_local_vs_producao(self):
        """INVESTIGAÇÃO 1: Análise completa do código local vs produção"""
        self.log("🔍 INVESTIGAÇÃO 1: CÓDIGO LOCAL VS PRODUÇÃO")
        print("=" * 80)
        
        try:
            # Verificar se o código local está atualizado
            self.log("📋 Verificando se o código local está atualizado...")
            
            # Verificar git status
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if result.stdout.strip():
                self.log("⚠️ Código local tem mudanças não commitadas")
                self.problemas.append("Código local tem mudanças não commitadas")
            else:
                self.log("✅ Código local está limpo")
            
            # Verificar último commit
            result = subprocess.run(["git", "log", "-1", "--oneline"], capture_output=True, text=True)
            self.log(f"📋 Último commit local: {result.stdout.strip()}")
            
            # Verificar se está na branch main
            result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
            current_branch = result.stdout.strip()
            self.log(f"📋 Branch atual: {current_branch}")
            
            if current_branch != "main":
                self.log("⚠️ Não está na branch main")
                self.problemas.append("Não está na branch main")
            
            # Verificar se há commits não enviados
            result = subprocess.run(["git", "status", "-sb"], capture_output=True, text=True)
            if "ahead" in result.stdout:
                self.log("⚠️ Há commits não enviados para o repositório remoto")
                self.problemas.append("Há commits não enviados")
            else:
                self.log("✅ Código local está sincronizado com o remoto")
            
            self.descobertas.append("Análise de código local vs produção concluída")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 1: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 1: {str(e)}")

    def investigacao_2_verificacao_versoes_commits(self):
        """INVESTIGAÇÃO 2: Verificação de versões e commits"""
        self.log("🔍 INVESTIGAÇÃO 2: VERSÕES E COMMITS")
        print("=" * 80)
        
        try:
            # Verificar histórico de commits
            self.log("📋 Verificando histórico de commits...")
            
            result = subprocess.run(["git", "log", "--oneline", "-10"], capture_output=True, text=True)
            commits = result.stdout.strip().split('\n')
            
            self.log("📋 Últimos 10 commits:")
            for i, commit in enumerate(commits, 1):
                self.log(f"   {i:2d}. {commit}")
            
            # Verificar se há commits relacionados a middleware
            middleware_commits = [c for c in commits if "middleware" in c.lower() or "critical" in c.lower() or "bypass" in c.lower()]
            
            if middleware_commits:
                self.log("📋 Commits relacionados a middleware:")
                for commit in middleware_commits:
                    self.log(f"   - {commit}")
            else:
                self.log("⚠️ Nenhum commit relacionado a middleware encontrado")
                self.problemas.append("Nenhum commit relacionado a middleware encontrado")
            
            # Verificar se o último commit foi enviado
            result = subprocess.run(["git", "status", "-sb"], capture_output=True, text=True)
            if "ahead" in result.stdout:
                self.log("❌ Último commit não foi enviado para o repositório remoto")
                self.problemas.append("Último commit não foi enviado")
            else:
                self.log("✅ Último commit foi enviado para o repositório remoto")
            
            self.descobertas.append("Verificação de versões e commits concluída")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 2: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 2: {str(e)}")

    def investigacao_3_analise_logs_railway(self):
        """INVESTIGAÇÃO 3: Análise de logs detalhados do Railway"""
        self.log("🔍 INVESTIGAÇÃO 3: LOGS DETALHADOS DO RAILWAY")
        print("=" * 80)
        
        try:
            # Fazer requisições e analisar logs
            self.log("📋 Fazendo requisições para analisar logs...")
            
            endpoints = ["/ping", "/health", "/docs", "/metrics", "/"]
            
            for endpoint in endpoints:
                self.log(f"📋 Testando {endpoint}:")
                
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                    
                    self.log(f"   Status: {response.status_code}")
                    self.log(f"   Headers: {dict(response.headers)}")
                    
                    if response.status_code == 200:
                        self.log(f"   ✅ {endpoint} funcionando")
                    else:
                        self.log(f"   ❌ {endpoint} com problema: {response.status_code}")
                        self.log(f"   Content: {response.text[:200]}...")
                        
                        if response.status_code == 401:
                            self.problemas.append(f"{endpoint} retorna 401")
                        elif response.status_code == 429:
                            self.problemas.append(f"{endpoint} retorna 429")
                
                except Exception as e:
                    self.log(f"   ❌ Erro ao testar {endpoint}: {str(e)}")
                    self.problemas.append(f"Erro ao testar {endpoint}: {str(e)}")
                
                time.sleep(1)
            
            self.descobertas.append("Análise de logs do Railway concluída")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 3: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 3: {str(e)}")

    def investigacao_4_teste_diferentes_abordagens_middleware(self):
        """INVESTIGAÇÃO 4: Teste de diferentes abordagens de middleware"""
        self.log("🔍 INVESTIGAÇÃO 4: DIFERENTES ABORDAGENS DE MIDDLEWARE")
        print("=" * 80)
        
        try:
            # Testar diferentes User-Agents
            self.log("📋 Testando diferentes User-Agents...")
            
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
                try:
                    response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=10)
                    status = "✅" if response.status_code == 200 else "❌"
                    self.log(f"   {ua}: {response.status_code} {status}")
                    
                    if response.status_code == 200:
                        self.solucoes.append(f"User-Agent {ua} funciona")
                except Exception as e:
                    self.log(f"   {ua}: ERRO - {str(e)}")
            
            # Testar diferentes métodos HTTP
            self.log("📋 Testando diferentes métodos HTTP...")
            
            methods = ["GET", "HEAD", "OPTIONS", "POST"]
            
            for method in methods:
                try:
                    if method == "GET":
                        response = requests.get(f"{BASE_URL}/ping", timeout=10)
                    elif method == "HEAD":
                        response = requests.head(f"{BASE_URL}/ping", timeout=10)
                    elif method == "OPTIONS":
                        response = requests.options(f"{BASE_URL}/ping", timeout=10)
                    elif method == "POST":
                        response = requests.post(f"{BASE_URL}/ping", json={}, timeout=10)
                    
                    status = "✅" if response.status_code == 200 else "❌"
                    self.log(f"   {method}: {response.status_code} {status}")
                    
                    if response.status_code == 200:
                        self.solucoes.append(f"Método {method} funciona")
                except Exception as e:
                    self.log(f"   {method}: ERRO - {str(e)}")
            
            self.descobertas.append("Teste de diferentes abordagens de middleware concluído")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 4: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 4: {str(e)}")

    def investigacao_5_verificacao_configuracoes_railway(self):
        """INVESTIGAÇÃO 5: Verificação de configurações do Railway"""
        self.log("🔍 INVESTIGAÇÃO 5: CONFIGURAÇÕES DO RAILWAY")
        print("=" * 80)
        
        try:
            # Verificar railway.toml
            self.log("📋 Verificando railway.toml...")
            
            if os.path.exists("railway.toml"):
                with open("railway.toml", "r") as f:
                    content = f.read()
                
                self.log("📋 Conteúdo do railway.toml:")
                self.log(f"   {content}")
                
                if "healthcheckPath" in content:
                    self.log("✅ healthcheckPath configurado")
                else:
                    self.log("⚠️ healthcheckPath não configurado")
                    self.problemas.append("healthcheckPath não configurado")
                
                if "Dockerfile" in content:
                    self.log("✅ Dockerfile configurado")
                else:
                    self.log("⚠️ Dockerfile não configurado")
                    self.problemas.append("Dockerfile não configurado")
            else:
                self.log("❌ railway.toml não encontrado")
                self.problemas.append("railway.toml não encontrado")
            
            # Verificar Dockerfile
            self.log("📋 Verificando Dockerfile...")
            
            dockerfiles = ["Dockerfile", "Dockerfile.railway", "Dockerfile.railway.fixed"]
            
            for dockerfile in dockerfiles:
                if os.path.exists(dockerfile):
                    self.log(f"✅ {dockerfile} encontrado")
                    
                    with open(dockerfile, "r") as f:
                        content = f.read()
                    
                    if "HEALTHCHECK" in content:
                        self.log(f"   ✅ HEALTHCHECK configurado em {dockerfile}")
                    else:
                        self.log(f"   ⚠️ HEALTHCHECK não configurado em {dockerfile}")
                        self.problemas.append(f"HEALTHCHECK não configurado em {dockerfile}")
                    
                    if "EXPOSE" in content:
                        self.log(f"   ✅ EXPOSE configurado em {dockerfile}")
                    else:
                        self.log(f"   ⚠️ EXPOSE não configurado em {dockerfile}")
                        self.problemas.append(f"EXPOSE não configurado em {dockerfile}")
                else:
                    self.log(f"❌ {dockerfile} não encontrado")
                    self.problemas.append(f"{dockerfile} não encontrado")
            
            self.descobertas.append("Verificação de configurações do Railway concluída")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 5: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 5: {str(e)}")

    def investigacao_6_analise_cache_deploy(self):
        """INVESTIGAÇÃO 6: Análise de cache e deploy"""
        self.log("🔍 INVESTIGAÇÃO 6: CACHE E DEPLOY")
        print("=" * 80)
        
        try:
            # Testar bypass de cache
            self.log("📋 Testando bypass de cache...")
            
            cache_headers = [
                {"Cache-Control": "no-cache, no-store, must-revalidate"},
                {"Pragma": "no-cache"},
                {"Expires": "0"},
                {"If-Modified-Since": "Thu, 01 Jan 1970 00:00:00 GMT"},
                {"If-None-Match": "*"}
            ]
            
            for i, headers in enumerate(cache_headers, 1):
                try:
                    response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=10)
                    status = "✅" if response.status_code == 200 else "❌"
                    self.log(f"   {i}. Cache bypass {headers}: {response.status_code} {status}")
                    
                    if response.status_code == 200:
                        self.solucoes.append(f"Cache bypass {i} funciona")
                except Exception as e:
                    self.log(f"   {i}. Cache bypass {headers}: ERRO - {str(e)}")
            
            # Verificar se há cache de deploy
            self.log("📋 Verificando se há cache de deploy...")
            
            # Fazer várias requisições para verificar consistência
            for i in range(5):
                try:
                    response = requests.get(f"{BASE_URL}/ping", timeout=10)
                    self.log(f"   Requisição {i+1}: {response.status_code}")
                    
                    if response.status_code == 200:
                        self.log("   ✅ Deploy funcionando!")
                        self.solucoes.append("Deploy funcionando")
                        break
                    else:
                        self.log(f"   ❌ Deploy ainda não funcionando: {response.status_code}")
                        time.sleep(10)
                except Exception as e:
                    self.log(f"   Requisição {i+1}: ERRO - {str(e)}")
                    time.sleep(10)
            
            self.descobertas.append("Análise de cache e deploy concluída")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 6: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 6: {str(e)}")

    def investigacao_7_teste_solucoes_alternativas(self):
        """INVESTIGAÇÃO 7: Teste de soluções alternativas"""
        self.log("🔍 INVESTIGAÇÃO 7: SOLUÇÕES ALTERNATIVAS")
        print("=" * 80)
        
        try:
            # Testar endpoint alternativo
            self.log("📋 Testando endpoint alternativo...")
            
            # Criar endpoint alternativo temporário
            alternative_endpoint = "/healthcheck"
            
            try:
                response = requests.get(f"{BASE_URL}{alternative_endpoint}", timeout=10)
                status = "✅" if response.status_code == 200 else "❌"
                self.log(f"   {alternative_endpoint}: {response.status_code} {status}")
                
                if response.status_code == 200:
                    self.solucoes.append(f"Endpoint alternativo {alternative_endpoint} funciona")
                else:
                    self.log(f"   Content: {response.text[:200]}...")
            except Exception as e:
                self.log(f"   {alternative_endpoint}: ERRO - {str(e)}")
            
            # Testar outros endpoints para comparação
            self.log("📋 Testando outros endpoints para comparação...")
            
            other_endpoints = ["/health", "/docs", "/metrics", "/"]
            
            for endpoint in other_endpoints:
                try:
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                    status = "✅" if response.status_code == 200 else "❌"
                    self.log(f"   {endpoint}: {response.status_code} {status}")
                    
                    if response.status_code == 200:
                        self.solucoes.append(f"Endpoint {endpoint} funciona")
                except Exception as e:
                    self.log(f"   {endpoint}: ERRO - {str(e)}")
            
            self.descobertas.append("Teste de soluções alternativas concluído")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 7: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 7: {str(e)}")

    def investigacao_8_verificacao_problemas_importacao(self):
        """INVESTIGAÇÃO 8: Verificação de problemas de importação"""
        self.log("🔍 INVESTIGAÇÃO 8: PROBLEMAS DE IMPORTAÇÃO")
        print("=" * 80)
        
        try:
            # Verificar se há problemas de importação no main.py
            self.log("📋 Verificando problemas de importação no main.py...")
            
            if os.path.exists("app/main.py"):
                with open("app/main.py", "r") as f:
                    content = f.read()
                
                # Verificar imports
                imports = []
                for line in content.split('\n'):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        imports.append(line.strip())
                
                self.log("📋 Imports encontrados:")
                for i, imp in enumerate(imports, 1):
                    self.log(f"   {i:2d}. {imp}")
                
                # Verificar se há imports problemáticos
                problematic_imports = []
                for imp in imports:
                    if "middleware" in imp.lower() and "critical" in imp.lower():
                        problematic_imports.append(imp)
                
                if problematic_imports:
                    self.log("⚠️ Imports problemáticos encontrados:")
                    for imp in problematic_imports:
                        self.log(f"   - {imp}")
                    self.problemas.append("Imports problemáticos encontrados")
                else:
                    self.log("✅ Nenhum import problemático encontrado")
                
                # Verificar se há classes de middleware
                middleware_classes = []
                for line in content.split('\n'):
                    if 'class' in line and 'Middleware' in line:
                        middleware_classes.append(line.strip())
                
                if middleware_classes:
                    self.log("📋 Classes de middleware encontradas:")
                    for i, cls in enumerate(middleware_classes, 1):
                        self.log(f"   {i:2d}. {cls}")
                else:
                    self.log("⚠️ Nenhuma classe de middleware encontrada")
                    self.problemas.append("Nenhuma classe de middleware encontrada")
            
            self.descobertas.append("Verificação de problemas de importação concluída")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 8: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 8: {str(e)}")

    def investigacao_9_analise_ordem_execucao_real(self):
        """INVESTIGAÇÃO 9: Análise de ordem de execução real"""
        self.log("🔍 INVESTIGAÇÃO 9: ORDEM DE EXECUÇÃO REAL")
        print("=" * 80)
        
        try:
            # Verificar ordem real dos middlewares no main.py
            self.log("📋 Verificando ordem real dos middlewares no main.py...")
            
            if os.path.exists("app/main.py"):
                with open("app/main.py", "r") as f:
                    content = f.read()
                
                # Encontrar todas as chamadas add_middleware
                import re
                middleware_calls = re.findall(r'app\.add_middleware\((\w+)\)', content)
                
                self.log("📋 Ordem real dos middlewares:")
                for i, middleware in enumerate(middleware_calls, 1):
                    self.log(f"   {i:2d}. {middleware}")
                
                # Verificar se CriticalEndpointsMiddleware está antes de AuthMiddleware
                critical_pos = None
                auth_pos = None
                
                for i, middleware in enumerate(middleware_calls):
                    if "Critical" in middleware or "UltraSimple" in middleware:
                        critical_pos = i
                    elif "AuthMiddleware" in middleware:
                        auth_pos = i
                
                if critical_pos is not None and auth_pos is not None:
                    if critical_pos < auth_pos:
                        self.log("✅ Middleware de bypass está ANTES do AuthMiddleware")
                        self.descobertas.append("Ordem de middlewares está correta")
                    else:
                        self.log("❌ Middleware de bypass está DEPOIS do AuthMiddleware")
                        self.problemas.append("Ordem de middlewares está incorreta")
                else:
                    self.log("⚠️ Não foi possível determinar a ordem dos middlewares")
                    self.problemas.append("Não foi possível determinar a ordem dos middlewares")
            
            self.descobertas.append("Análise de ordem de execução real concluída")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 9: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 9: {str(e)}")

    def investigacao_10_teste_bypass_completo(self):
        """INVESTIGAÇÃO 10: Teste de bypass completo"""
        self.log("🔍 INVESTIGAÇÃO 10: BYPASS COMPLETO")
        print("=" * 80)
        
        try:
            # Testar bypass completo com diferentes abordagens
            self.log("📋 Testando bypass completo...")
            
            # Abordagem 1: Headers especiais
            self.log("📋 Abordagem 1: Headers especiais")
            
            special_headers = [
                {"X-Railway-Health-Check": "true"},
                {"X-Health-Check": "true"},
                {"X-Bypass-Auth": "true"},
                {"X-Critical-Endpoint": "true"},
                {"X-Railway-Edge": "bypass"}
            ]
            
            for i, headers in enumerate(special_headers, 1):
                try:
                    response = requests.get(f"{BASE_URL}/ping", headers=headers, timeout=10)
                    status = "✅" if response.status_code == 200 else "❌"
                    self.log(f"   {i}. Headers especiais {headers}: {response.status_code} {status}")
                    
                    if response.status_code == 200:
                        self.solucoes.append(f"Headers especiais {i} funcionam")
                except Exception as e:
                    self.log(f"   {i}. Headers especiais {headers}: ERRO - {str(e)}")
            
            # Abordagem 2: Diferentes paths
            self.log("📋 Abordagem 2: Diferentes paths")
            
            different_paths = [
                "/ping",
                "/ping/",
                "/ping?bypass=true",
                "/ping?healthcheck=true",
                "/ping?railway=true"
            ]
            
            for i, path in enumerate(different_paths, 1):
                try:
                    response = requests.get(f"{BASE_URL}{path}", timeout=10)
                    status = "✅" if response.status_code == 200 else "❌"
                    self.log(f"   {i}. Path {path}: {response.status_code} {status}")
                    
                    if response.status_code == 200:
                        self.solucoes.append(f"Path {path} funciona")
                except Exception as e:
                    self.log(f"   {i}. Path {path}: ERRO - {str(e)}")
            
            self.descobertas.append("Teste de bypass completo concluído")
            
        except Exception as e:
            self.log(f"❌ Erro na investigação 10: {str(e)}", "ERROR")
            self.problemas.append(f"Erro na investigação 10: {str(e)}")

    def gerar_relatorio_final(self):
        """Gera relatório final com todas as descobertas e soluções"""
        self.log("🔍 RELATÓRIO FINAL - INVESTIGAÇÃO PROFUNDA")
        print("=" * 80)
        
        self.log(f"📊 ESTATÍSTICAS:")
        self.log(f"   🔍 Descobertas: {len(self.descobertas)}")
        self.log(f"   ✅ Soluções: {len(self.solucoes)}")
        self.log(f"   ❌ Problemas: {len(self.problemas)}")
        
        if self.descobertas:
            self.log("🔍 DESCOBERTAS:")
            for i, descoberta in enumerate(self.descobertas, 1):
                self.log(f"   {i:2d}. {descoberta}")
        
        if self.solucoes:
            self.log("✅ SOLUÇÕES ENCONTRADAS:")
            for i, solucao in enumerate(self.solucoes, 1):
                self.log(f"   {i:2d}. {solucao}")
        
        if self.problemas:
            self.log("❌ PROBLEMAS IDENTIFICADOS:")
            for i, problema in enumerate(self.problemas, 1):
                self.log(f"   {i:2d}. {problema}")
        
        # Recomendações
        self.log("🎯 RECOMENDAÇÕES:")
        
        if self.solucoes:
            self.log("   1. Implementar as soluções encontradas")
            self.log("   2. Testar cada solução individualmente")
            self.log("   3. Verificar se resolve o problema")
        else:
            self.log("   1. Implementar solução alternativa com endpoint /healthcheck")
            self.log("   2. Configurar Railway para usar /healthcheck")
            self.log("   3. Verificar se resolve o problema")
        
        if self.problemas:
            self.log("   4. Corrigir os problemas identificados")
            self.log("   5. Fazer novo deploy")
            self.log("   6. Testar novamente")
        
        print("=" * 80)

    def executar_investigacao_completa(self):
        """Executa investigação completa"""
        self.log("🚀 INICIANDO INVESTIGAÇÃO PROFUNDA E DEFINITIVA")
        print("=" * 80)
        print(f"🌐 Servidor: {BASE_URL}")
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 80)
        
        # Executar todas as investigações
        self.investigacao_1_analise_codigo_local_vs_producao()
        self.investigacao_2_verificacao_versoes_commits()
        self.investigacao_3_analise_logs_railway()
        self.investigacao_4_teste_diferentes_abordagens_middleware()
        self.investigacao_5_verificacao_configuracoes_railway()
        self.investigacao_6_analise_cache_deploy()
        self.investigacao_7_teste_solucoes_alternativas()
        self.investigacao_8_verificacao_problemas_importacao()
        self.investigacao_9_analise_ordem_execucao_real()
        self.investigacao_10_teste_bypass_completo()
        
        # Gerar relatório final
        self.gerar_relatorio_final()

def main():
    """Executa investigação profunda completa"""
    investigador = InvestigadorProfundo()
    investigador.executar_investigacao_completa()

if __name__ == "__main__":
    main()

