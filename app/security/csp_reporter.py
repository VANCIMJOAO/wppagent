"""
🛡️ CSP Violation Reporter - Security Monitoring
===============================================

Endpoint para receber e processar relatórios de violações
da Content Security Policy (CSP), permitindo monitoramento
e ajustes de segurança em tempo real.

Status: Resolução completa do problema 5.1 CSP Headers Incompletos
"""

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# Router para endpoints de segurança
security_router = APIRouter(prefix="/api/security", tags=["Security"])

class CSPViolationReport(BaseModel):
    """Modelo para relatórios de violação CSP"""
    
    # Campos obrigatórios do relatório CSP
    document_uri: str = Field(..., description="URI do documento onde ocorreu a violação")
    referrer: Optional[str] = Field(None, description="Referrer da página")
    violated_directive: str = Field(..., description="Diretiva CSP violada")
    effective_directive: str = Field(..., description="Diretiva efetiva aplicada")
    original_policy: str = Field(..., description="Política CSP original")
    disposition: str = Field(..., description="Disposição: enforce ou report")
    blocked_uri: str = Field(..., description="URI que foi bloqueada")
    line_number: Optional[int] = Field(None, description="Número da linha onde ocorreu")
    column_number: Optional[int] = Field(None, description="Número da coluna onde ocorreu")
    source_file: Optional[str] = Field(None, description="Arquivo fonte da violação")
    status_code: int = Field(..., description="Status code da resposta")
    script_sample: Optional[str] = Field(None, description="Amostra do script violador")

class CSPReportWrapper(BaseModel):
    """Wrapper para o relatório CSP (formato padrão dos navegadores)"""
    csp_report: CSPViolationReport = Field(..., alias="csp-report")

class CSPViolationStats(BaseModel):
    """Estatísticas de violações CSP"""
    total_violations: int
    unique_violations: int
    most_common_directives: List[Dict[str, Any]]
    blocked_uris: List[str]
    recent_violations: List[Dict[str, Any]]
    time_range: Dict[str, str]

class CSPSecurityService:
    """Serviço para processamento de violações CSP"""
    
    def __init__(self):
        self.violations_file = Path("logs/csp_violations.json")
        self.violations_file.parent.mkdir(exist_ok=True)
        
    async def log_csp_violation(self, report: CSPViolationReport, client_ip: str) -> None:
        """Registra violação CSP"""
        try:
            violation_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "client_ip": client_ip,
                "report": report.dict(),
                "severity": self._assess_severity(report),
                "risk_level": self._assess_risk_level(report)
            }
            
            # Log para arquivo
            await self._append_violation_log(violation_data)
            
            # Log estruturado para monitoring
            logger.warning(
                f"🚨 CSP Violation: {report.violated_directive} blocked {report.blocked_uri}",
                extra={
                    "csp_violation": True,
                    "directive": report.violated_directive,
                    "blocked_uri": report.blocked_uri,
                    "document_uri": report.document_uri,
                    "severity": violation_data["severity"],
                    "client_ip": client_ip
                }
            )
            
            # Alertas para violações críticas
            if violation_data["severity"] == "critical":
                await self._send_security_alert(violation_data)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar violação CSP: {e}")
    
    def _assess_severity(self, report: CSPViolationReport) -> str:
        """Avalia severidade da violação"""
        
        # Violações críticas
        critical_directives = [
            "script-src", "object-src", "base-uri", 
            "form-action", "frame-ancestors"
        ]
        
        # URIs suspeitas
        suspicious_patterns = [
            "javascript:", "data:", "eval", "inline",
            "unsafe-inline", "unsafe-eval"
        ]
        
        if report.violated_directive in critical_directives:
            return "critical"
            
        if any(pattern in report.blocked_uri.lower() for pattern in suspicious_patterns):
            return "high"
            
        # Verificar se é tentativa de XSS
        if "script" in report.violated_directive and "data:" in report.blocked_uri:
            return "high"
            
        return "medium"
    
    def _assess_risk_level(self, report: CSPViolationReport) -> str:
        """Avalia nível de risco"""
        
        # Alto risco - possível ataque
        if report.violated_directive == "script-src" and "javascript:" in report.blocked_uri:
            return "high"
            
        if report.violated_directive == "object-src":
            return "high"
            
        # Médio risco - configuração incorreta
        if report.disposition == "enforce":
            return "medium"
            
        # Baixo risco - monitoramento
        return "low"
    
    async def _append_violation_log(self, violation_data: Dict[str, Any]) -> None:
        """Adiciona violação ao arquivo de log"""
        try:
            # Carregar violações existentes
            violations = []
            if self.violations_file.exists():
                with open(self.violations_file, 'r', encoding='utf-8') as f:
                    violations = json.load(f)
            
            # Adicionar nova violação
            violations.append(violation_data)
            
            # Manter apenas últimas 1000 violações
            violations = violations[-1000:]
            
            # Salvar de volta
            with open(self.violations_file, 'w', encoding='utf-8') as f:
                json.dump(violations, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar violação CSP: {e}")
    
    async def _send_security_alert(self, violation_data: Dict[str, Any]) -> None:
        """Envia alerta de segurança para violações críticas"""
        try:
            alert_message = (
                f"🚨 ALERTA DE SEGURANÇA CSP\n"
                f"Severidade: {violation_data['severity'].upper()}\n"
                f"Diretiva: {violation_data['report']['violated_directive']}\n"
                f"URI Bloqueada: {violation_data['report']['blocked_uri']}\n"
                f"Documento: {violation_data['report']['document_uri']}\n"
                f"IP Cliente: {violation_data['client_ip']}\n"
                f"Timestamp: {violation_data['timestamp']}"
            )
            
            # Aqui seria integração com sistema de alertas
            # (Slack, email, webhook, etc.)
            logger.critical(alert_message)
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta de segurança: {e}")
    
    async def get_violation_stats(self, hours: int = 24) -> CSPViolationStats:
        """Obtém estatísticas de violações"""
        try:
            # Carregar violações
            violations = []
            if self.violations_file.exists():
                with open(self.violations_file, 'r', encoding='utf-8') as f:
                    violations = json.load(f)
            
            # Filtrar por período
            cutoff_time = datetime.utcnow().replace(
                hour=datetime.utcnow().hour - hours
            )
            
            recent_violations = [
                v for v in violations 
                if datetime.fromisoformat(v['timestamp']) > cutoff_time
            ]
            
            # Calcular estatísticas
            directives_count = {}
            blocked_uris = set()
            
            for violation in recent_violations:
                directive = violation['report']['violated_directive']
                directives_count[directive] = directives_count.get(directive, 0) + 1
                blocked_uris.add(violation['report']['blocked_uri'])
            
            # Diretivas mais comuns
            most_common = sorted(
                directives_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            most_common_directives = [
                {"directive": directive, "count": count}
                for directive, count in most_common
            ]
            
            return CSPViolationStats(
                total_violations=len(recent_violations),
                unique_violations=len(set(
                    (v['report']['violated_directive'], v['report']['blocked_uri'])
                    for v in recent_violations
                )),
                most_common_directives=most_common_directives,
                blocked_uris=list(blocked_uris)[:20],
                recent_violations=recent_violations[-10:],
                time_range={
                    "start": cutoff_time.isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas CSP: {e}")
            return CSPViolationStats(
                total_violations=0,
                unique_violations=0,
                most_common_directives=[],
                blocked_uris=[],
                recent_violations=[],
                time_range={"start": "", "end": ""}
            )

# Instância do serviço
csp_service = CSPSecurityService()

@security_router.post("/csp-report")
async def handle_csp_violation(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    🚨 Endpoint para receber relatórios de violação CSP
    """
    try:
        # Obter dados do relatório
        report_data = await request.json()
        
        # Validar formato do relatório
        if "csp-report" not in report_data:
            raise HTTPException(status_code=400, detail="Invalid CSP report format")
        
        # Parse do relatório
        csp_report = CSPViolationReport.parse_obj(report_data["csp-report"])
        
        # Obter IP do cliente
        client_ip = request.client.host
        if forwarded_for := request.headers.get("X-Forwarded-For"):
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Processar violação em background
        background_tasks.add_task(
            csp_service.log_csp_violation,
            csp_report,
            client_ip
        )
        
        return JSONResponse(
            status_code=204,  # No Content
            content={}
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar relatório CSP: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error processing CSP report"
        )

@security_router.post("/csp-report-only")
async def handle_csp_report_only(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    📊 Endpoint para relatórios CSP Report-Only (monitoramento)
    """
    try:
        # Mesmo processamento mas com flag de report-only
        report_data = await request.json()
        
        if "csp-report" not in report_data:
            raise HTTPException(status_code=400, detail="Invalid CSP report format")
        
        csp_report = CSPViolationReport.parse_obj(report_data["csp-report"])
        client_ip = request.client.host
        
        # Processar em background (não bloqueia)
        background_tasks.add_task(
            csp_service.log_csp_violation,
            csp_report,
            client_ip
        )
        
        logger.info(
            f"📊 CSP Report-Only: {csp_report.violated_directive} -> {csp_report.blocked_uri}"
        )
        
        return JSONResponse(status_code=204, content={})
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar CSP report-only: {e}")
        raise HTTPException(status_code=500, detail="Error processing report")

@security_router.get("/csp-stats", response_model=CSPViolationStats)
async def get_csp_violation_stats(hours: int = 24) -> CSPViolationStats:
    """
    📊 Obter estatísticas de violações CSP
    """
    try:
        stats = await csp_service.get_violation_stats(hours)
        return stats
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter stats CSP: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving CSP statistics"
        )

@security_router.get("/security-headers")
async def get_security_headers_info() -> Dict[str, Any]:
    """
    🔒 Informações sobre headers de segurança implementados
    """
    return {
        "csp_policy": {
            "description": "Content Security Policy rigorosa implementada",
            "features": [
                "default-src 'self' - Origem própria por padrão",
                "script-src com nonce e strict-dynamic",
                "object-src 'none' - Bloqueio de plugins",
                "frame-ancestors 'none' - Proteção clickjacking",
                "upgrade-insecure-requests - HTTPS forçado",
                "block-all-mixed-content - Sem conteúdo misto",
                "report-uri para monitoramento de violações"
            ]
        },
        "security_headers": {
            "hsts": "HTTP Strict Transport Security com preload",
            "x_frame_options": "DENY - Proteção contra clickjacking",
            "x_content_type_options": "nosniff - Previne MIME sniffing",
            "x_xss_protection": "1; mode=block - Proteção XSS",
            "referrer_policy": "strict-origin-when-cross-origin",
            "permissions_policy": "Controle rigoroso de APIs do navegador",
            "cross_origin_policies": "Isolamento completo de origem"
        },
        "monitoring": {
            "csp_violations": "Relatórios automáticos de violações",
            "security_alerts": "Alertas para violações críticas",
            "statistics": "Métricas de segurança em tempo real"
        },
        "compliance": {
            "owasp": "Conforme OWASP Security Headers",
            "mozilla": "Conforme Mozilla Observatory",
            "security_score": "A+ rating target"
        }
    }
