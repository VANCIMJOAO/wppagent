"""
🔍 CSP Security Scanner & Tester
===============================

Sistema completo para testar e validar políticas CSP:
- Scanner de vulnerabilidades
- Testes automatizados
- Validação de headers
- Report de violações

Implementação do S001 - CSP Testing
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel
from app.utils.logger import get_logger

logger = get_logger(__name__)

class CSPTestResult(BaseModel):
    """Resultado de teste CSP"""
    directive: str
    test_name: str
    passed: bool
    details: str
    risk_level: str  # low, medium, high, critical

class CSPScanReport(BaseModel):
    """Relatório completo de scan CSP"""
    timestamp: float
    target_url: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    vulnerabilities: List[CSPTestResult]
    security_score: int  # 0-100
    recommendations: List[str]

class CSPSecurityScanner:
    """
    Scanner avançado de segurança CSP
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or "https://wppagent-production.up.railway.app"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def scan_csp_headers(self, endpoint: str = "/health") -> Dict[str, str]:
        """Scan CSP headers de um endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = await self.client.head(url)
            
            security_headers = {}
            for header_name in response.headers:
                if any(keyword in header_name.lower() for keyword in [
                    'content-security-policy', 'x-frame-options', 'x-content-type',
                    'strict-transport-security', 'permissions-policy', 'referrer-policy'
                ]):
                    security_headers[header_name] = response.headers[header_name]
            
            return security_headers
            
        except Exception as e:
            logger.error(f"Erro ao escanear headers CSP: {e}")
            return {}
    
    def parse_csp_policy(self, csp_header: str) -> Dict[str, List[str]]:
        """Parse política CSP em estrutura organizada"""
        directives = {}
        
        for directive in csp_header.split(';'):
            directive = directive.strip()
            if directive:
                parts = directive.split(' ', 1)
                directive_name = parts[0].strip()
                directive_values = parts[1].split() if len(parts) > 1 else []
                directives[directive_name] = directive_values
        
        return directives
    
    def test_directive_security(self, directive: str, values: List[str]) -> List[CSPTestResult]:
        """Testar segurança de uma diretiva específica"""
        results = []
        
        # Teste 1: Verificar uso de 'unsafe-inline'
        if "'unsafe-inline'" in values:
            results.append(CSPTestResult(
                directive=directive,
                test_name="unsafe-inline check",
                passed=False,
                details=f"Diretiva {directive} permite 'unsafe-inline' - risco XSS",
                risk_level="high"
            ))
        else:
            results.append(CSPTestResult(
                directive=directive,
                test_name="unsafe-inline check", 
                passed=True,
                details=f"Diretiva {directive} não usa 'unsafe-inline'",
                risk_level="low"
            ))
        
        # Teste 2: Verificar uso de 'unsafe-eval'
        if "'unsafe-eval'" in values:
            results.append(CSPTestResult(
                directive=directive,
                test_name="unsafe-eval check",
                passed=False,
                details=f"Diretiva {directive} permite 'unsafe-eval' - risco code injection",
                risk_level="high"
            ))
        else:
            results.append(CSPTestResult(
                directive=directive,
                test_name="unsafe-eval check",
                passed=True,
                details=f"Diretiva {directive} não usa 'unsafe-eval'",
                risk_level="low"
            ))
        
        # Teste 3: Verificar wildcard '*'
        if "*" in values:
            results.append(CSPTestResult(
                directive=directive,
                test_name="wildcard check",
                passed=False,
                details=f"Diretiva {directive} usa wildcard '*' - muito permissiva",
                risk_level="medium"
            ))
        else:
            results.append(CSPTestResult(
                directive=directive,
                test_name="wildcard check",
                passed=True,
                details=f"Diretiva {directive} não usa wildcard",
                risk_level="low"
            ))
        
        # Teste 4: Verificar uso de nonce
        has_nonce = any("'nonce-" in value for value in values)
        if directive == "script-src" and not has_nonce and "'self'" in values:
            results.append(CSPTestResult(
                directive=directive,
                test_name="nonce implementation",
                passed=False,
                details="script-src deveria usar nonces para segurança extra",
                risk_level="medium"
            ))
        elif has_nonce:
            results.append(CSPTestResult(
                directive=directive,
                test_name="nonce implementation",
                passed=True,
                details="Usa nonces para scripts inline - boa prática",
                risk_level="low"
            ))
        
        return results
    
    def test_critical_directives(self, csp_directives: Dict[str, List[str]]) -> List[CSPTestResult]:
        """Testar diretivas críticas de segurança"""
        results = []
        
        critical_directives = {
            "default-src": "Política padrão de fallback",
            "script-src": "Controle de execução de scripts",
            "object-src": "Controle de plugins/objetos",
            "frame-ancestors": "Proteção contra clickjacking"
        }
        
        for directive, description in critical_directives.items():
            if directive not in csp_directives:
                results.append(CSPTestResult(
                    directive=directive,
                    test_name="directive presence",
                    passed=False,
                    details=f"Diretiva crítica {directive} não encontrada - {description}",
                    risk_level="high"
                ))
            else:
                results.append(CSPTestResult(
                    directive=directive,
                    test_name="directive presence",
                    passed=True,
                    details=f"Diretiva {directive} presente",
                    risk_level="low"
                ))
        
        # Teste específico: object-src deve ser 'none'
        if "object-src" in csp_directives:
            if "'none'" not in csp_directives["object-src"]:
                results.append(CSPTestResult(
                    directive="object-src",
                    test_name="object-src restriction",
                    passed=False,
                    details="object-src deveria ser 'none' para máxima segurança",
                    risk_level="medium"
                ))
            else:
                results.append(CSPTestResult(
                    directive="object-src",
                    test_name="object-src restriction",
                    passed=True,
                    details="object-src corretamente configurado como 'none'",
                    risk_level="low"
                ))
        
        return results
    
    def calculate_security_score(self, results: List[CSPTestResult]) -> int:
        """Calcular score de segurança (0-100)"""
        if not results:
            return 0
        
        total_weight = 0
        passed_weight = 0
        
        weights = {
            "critical": 10,
            "high": 7,
            "medium": 4,
            "low": 1
        }
        
        for result in results:
            weight = weights.get(result.risk_level, 1)
            total_weight += weight
            
            if result.passed:
                passed_weight += weight
        
        return int((passed_weight / total_weight) * 100) if total_weight > 0 else 0
    
    def generate_recommendations(self, vulnerabilities: List[CSPTestResult]) -> List[str]:
        """Gerar recomendações baseadas nas vulnerabilidades"""
        recommendations = []
        
        # Análise de padrões
        has_unsafe_inline = any("unsafe-inline" in v.details for v in vulnerabilities if not v.passed)
        has_unsafe_eval = any("unsafe-eval" in v.details for v in vulnerabilities if not v.passed)
        has_wildcard = any("wildcard" in v.details for v in vulnerabilities if not v.passed)
        
        if has_unsafe_inline:
            recommendations.append(
                "🔒 Remover 'unsafe-inline' e implementar nonces para scripts/styles inline"
            )
        
        if has_unsafe_eval:
            recommendations.append(
                "🚫 Remover 'unsafe-eval' e refatorar código que depende de eval()"
            )
        
        if has_wildcard:
            recommendations.append(
                "🎯 Substituir wildcards '*' por domínios específicos whitelistados"
            )
        
        missing_directives = [v.directive for v in vulnerabilities 
                            if not v.passed and "não encontrada" in v.details]
        
        if missing_directives:
            recommendations.append(
                f"📋 Adicionar diretivas críticas: {', '.join(set(missing_directives))}"
            )
        
        # Recomendações gerais
        recommendations.extend([
            "🔍 Implementar monitoramento contínuo de violações CSP",
            "📊 Configurar alertas para violações críticas",
            "🧪 Testar política CSP em ambiente de staging antes da produção",
            "📚 Treinar equipe de desenvolvimento em práticas seguras de CSP"
        ])
        
        return recommendations
    
    async def comprehensive_scan(self, endpoints: List[str] = None) -> CSPScanReport:
        """Executar scan completo de segurança CSP"""
        endpoints = endpoints or ["/health", "/docs", "/"]
        
        logger.info(f"🔍 Iniciando scan CSP completo em {len(endpoints)} endpoints")
        
        all_vulnerabilities = []
        all_headers = {}
        
        # Coletar headers de todos endpoints
        for endpoint in endpoints:
            headers = await self.scan_csp_headers(endpoint)
            all_headers[endpoint] = headers
        
        # Analisar política CSP principal
        csp_header = None
        for headers in all_headers.values():
            if 'content-security-policy' in headers:
                csp_header = headers['content-security-policy']
                break
        
        if not csp_header:
            all_vulnerabilities.append(CSPTestResult(
                directive="global",
                test_name="csp presence",
                passed=False,
                details="Nenhum header Content-Security-Policy encontrado",
                risk_level="critical"
            ))
            
            return CSPScanReport(
                timestamp=time.time(),
                target_url=self.base_url,
                total_tests=1,
                passed_tests=0,
                failed_tests=1,
                vulnerabilities=all_vulnerabilities,
                security_score=0,
                recommendations=["🚨 CRÍTICO: Implementar Content-Security-Policy imediatamente"]
            )
        
        # Parse e teste da política CSP
        csp_directives = self.parse_csp_policy(csp_header)
        
        # Testar cada diretiva
        for directive, values in csp_directives.items():
            directive_results = self.test_directive_security(directive, values)
            all_vulnerabilities.extend(directive_results)
        
        # Testar diretivas críticas
        critical_results = self.test_critical_directives(csp_directives)
        all_vulnerabilities.extend(critical_results)
        
        # Calcular métricas
        total_tests = len(all_vulnerabilities)
        passed_tests = len([v for v in all_vulnerabilities if v.passed])
        failed_tests = total_tests - passed_tests
        
        security_score = self.calculate_security_score(all_vulnerabilities)
        vulnerabilities_only = [v for v in all_vulnerabilities if not v.passed]
        recommendations = self.generate_recommendations(vulnerabilities_only)
        
        report = CSPScanReport(
            timestamp=time.time(),
            target_url=self.base_url,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            vulnerabilities=vulnerabilities_only,
            security_score=security_score,
            recommendations=recommendations
        )
        
        logger.info(f"✅ Scan CSP completo: {security_score}/100 pontos, {failed_tests} vulnerabilidades")
        
        return report
    
    async def close(self):
        """Fechar cliente HTTP"""
        await self.client.aclose()


# Funções utilitárias
async def run_csp_security_scan(base_url: str = None) -> CSPScanReport:
    """Executar scan de segurança CSP completo"""
    scanner = CSPSecurityScanner(base_url)
    try:
        report = await scanner.comprehensive_scan()
        return report
    finally:
        await scanner.close()

def format_csp_report(report: CSPScanReport) -> str:
    """Formatar relatório CSP para exibição"""
    lines = [
        f"🔍 CSP Security Scan Report",
        f"===========================",
        f"🎯 Target: {report.target_url}",
        f"📊 Score: {report.security_score}/100",
        f"✅ Passed: {report.passed_tests}/{report.total_tests}",
        f"❌ Failed: {report.failed_tests}/{report.total_tests}",
        f""
    ]
    
    if report.vulnerabilities:
        lines.append("🚨 Vulnerabilidades encontradas:")
        for vuln in report.vulnerabilities:
            risk_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(vuln.risk_level, "⚪")
            lines.append(f"  {risk_emoji} [{vuln.risk_level.upper()}] {vuln.directive}: {vuln.details}")
    
    if report.recommendations:
        lines.append("\n💡 Recomendações:")
        for rec in report.recommendations:
            lines.append(f"  {rec}")
    
    return "\n".join(lines)
