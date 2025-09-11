"""
🔧 CSP Testing Routes
====================

Endpoints para executar testes de segurança CSP
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
from app.security.csp_scanner import run_csp_security_scan, format_csp_report
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Router para testes CSP
csp_testing_router = APIRouter(prefix="/api/security/csp", tags=["CSP Testing"])

@csp_testing_router.get("/scan")
async def scan_csp_security(target_url: Optional[str] = None):
    """
    🔍 Executar scan completo de segurança CSP
    
    - Analisa headers CSP
    - Identifica vulnerabilidades
    - Calcula score de segurança
    - Fornece recomendações
    """
    try:
        logger.info(f"🔍 Iniciando scan CSP para: {target_url or 'produção'}")
        
        report = await run_csp_security_scan(target_url)
        
        return {
            "status": "success",
            "data": {
                "report": report.dict(),
                "summary": {
                    "security_score": report.security_score,
                    "risk_level": "high" if report.security_score < 70 else "medium" if report.security_score < 90 else "low",
                    "vulnerabilities_count": len(report.vulnerabilities),
                    "recommendations_count": len(report.recommendations)
                }
            },
            "message": f"Scan completo - Score: {report.security_score}/100"
        }
        
    except Exception as e:
        logger.error(f"Erro durante scan CSP: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no scan CSP: {str(e)}")

@csp_testing_router.get("/scan/formatted")
async def scan_csp_formatted(target_url: Optional[str] = None):
    """
    📊 Scan CSP com relatório formatado para leitura
    """
    try:
        report = await run_csp_security_scan(target_url)
        formatted_report = format_csp_report(report)
        
        return {
            "status": "success",
            "data": {
                "formatted_report": formatted_report,
                "security_score": report.security_score,
                "json_report": report.dict()
            }
        }
        
    except Exception as e:
        logger.error(f"Erro durante scan CSP formatado: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no scan CSP: {str(e)}")

@csp_testing_router.get("/headers")
async def check_csp_headers(target_url: Optional[str] = None):
    """
    🔍 Verificar apenas headers CSP de um endpoint
    """
    try:
        from app.security.csp_scanner import CSPSecurityScanner
        
        scanner = CSPSecurityScanner(target_url)
        try:
            headers = await scanner.scan_csp_headers()
            return {
                "status": "success",
                "data": {
                    "headers": headers,
                    "has_csp": "content-security-policy" in headers,
                    "has_csp_report_only": "content-security-policy-report-only" in headers
                }
            }
        finally:
            await scanner.close()
            
    except Exception as e:
        logger.error(f"Erro ao verificar headers CSP: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar headers: {str(e)}")

@csp_testing_router.post("/test")
async def test_csp_policy(csp_policy: str):
    """
    🧪 Testar uma política CSP específica
    """
    try:
        from app.security.csp_scanner import CSPSecurityScanner
        
        scanner = CSPSecurityScanner()
        csp_directives = scanner.parse_csp_policy(csp_policy)
        
        all_results = []
        
        # Testar cada diretiva
        for directive, values in csp_directives.items():
            directive_results = scanner.test_directive_security(directive, values)
            all_results.extend(directive_results)
        
        # Testar diretivas críticas
        critical_results = scanner.test_critical_directives(csp_directives)
        all_results.extend(critical_results)
        
        vulnerabilities = [r for r in all_results if not r.passed]
        security_score = scanner.calculate_security_score(all_results)
        
        return {
            "status": "success",
            "data": {
                "parsed_policy": csp_directives,
                "total_tests": len(all_results),
                "passed_tests": len(all_results) - len(vulnerabilities),
                "vulnerabilities": [v.dict() for v in vulnerabilities],
                "security_score": security_score,
                "recommendations": scanner.generate_recommendations(vulnerabilities)
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao testar política CSP: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no teste: {str(e)}")
