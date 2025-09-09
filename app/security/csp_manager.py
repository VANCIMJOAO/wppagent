"""
import logging
logger = logging.getLogger(__name__)

🔒 CSP Middleware Manager
========================

Middleware para Content Security Policy com:
- CSP headers rigorosos
- Nonce generation para scripts inline
- Environment-specific policies
- Report-Only mode para testing

Resolve o problema 5.1 CSP Headers Incompletos
"""

import os
import secrets
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class CSPMiddleware(BaseHTTPMiddleware):
    """
    Middleware para implementar Content Security Policy rigoroso
    """
    
    def __init__(self, app, report_only: bool = False):
        super().__init__(app)
        self.report_only = report_only
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # CSP Policies baseados no ambiente
        self.csp_policies = self._get_csp_policies()
        
        logger.info(f"🔒 CSP Middleware initialized (report_only={report_only}, env={self.environment})")
    
    def _get_csp_policies(self) -> Dict[str, str]:
        """Get CSP policies based on environment"""
        
        base_policy = {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline'",
            "style-src": "'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src": "'self' https://fonts.gstatic.com",
            "img-src": "'self' data: https: blob:",
            "connect-src": "'self'",
            "media-src": "'none'",
            "object-src": "'none'",
            "frame-src": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "upgrade-insecure-requests": ""
        }
        
        if self.environment == "production":
            # Produção - Política mais rigorosa
            base_policy.update({
                "script-src": "'self' https://cdnjs.cloudflare.com https://vercel.live",
                "connect-src": "'self' https://wppagent-production.up.railway.app wss://wppagent-production.up.railway.app",
                "report-uri": "/api/csp-report"
            })
        elif self.environment == "development":
            # Desenvolvimento - Mais permissivo para debugging
            base_policy.update({
                "script-src": "'self' 'unsafe-inline' 'unsafe-eval' http://localhost:*",
                "connect-src": "'self' http://localhost:* ws://localhost:* wss://localhost:*"
            })
        
        return base_policy
    
    def _generate_nonce(self) -> str:
        """Generate cryptographically secure nonce"""
        return secrets.token_urlsafe(16)
    
    def _build_csp_header(self, nonce: Optional[str] = None) -> str:
        """Build CSP header string"""
        policies = self.csp_policies.copy()
        
        # Add nonce to script-src if provided
        if nonce and 'script-src' in policies:
            policies['script-src'] += f" 'nonce-{nonce}'"
        
        # Build header string
        directives = []
        for directive, value in policies.items():
            if value:
                directives.append(f"{directive} {value}")
            else:
                directives.append(directive)
        
        return "; ".join(directives)
    
    def _add_security_headers(self, response: Response, nonce: Optional[str] = None):
        """Add comprehensive security headers"""
        
        # Content Security Policy
        csp_header = self._build_csp_header(nonce)
        if self.report_only:
            response.headers["Content-Security-Policy-Report-Only"] = csp_header
        else:
            response.headers["Content-Security-Policy"] = csp_header
        
        # Additional security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Permissions Policy (Feature Policy replacement)
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "fullscreen=(), "
            "payment=(), "
            "usb=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add CSP headers"""
        
        try:
            # Generate nonce for this request
            nonce = self._generate_nonce()
            
            # Store nonce in request state for use in templates
            request.state.csp_nonce = nonce
            
            # Process request
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add CSP and security headers
            self._add_security_headers(response, nonce)
            
            # Add performance headers
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            # Log CSP application
            if process_time > 0.1:  # Log slow requests
                logger.warning(f"Slow CSP request: {request.url.path} ({process_time:.3f}s)")
            
            return response
            
        except Exception as e:
            logger.error(f"CSP Middleware error: {e}")
            
            # Return error response with basic security headers
            error_response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
            
            # Basic security headers even on error
            error_response.headers["X-Frame-Options"] = "DENY"
            error_response.headers["X-Content-Type-Options"] = "nosniff"
            
            return error_response


def get_csp_nonce(request: Request) -> Optional[str]:
    """Get CSP nonce from request state"""
    return getattr(request.state, 'csp_nonce', None)


class CSPReportParser:
    """Parser for CSP violation reports"""
    
    @staticmethod
    def parse_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate CSP report"""
        
        if 'csp-report' not in report_data:
            return {"error": "Invalid CSP report format"}
        
        csp_report = report_data['csp-report']
        
        # Extract key information
        parsed = {
            "timestamp": time.time(),
            "document_uri": csp_report.get('document-uri', ''),
            "violated_directive": csp_report.get('violated-directive', ''),
            "effective_directive": csp_report.get('effective-directive', ''),
            "original_policy": csp_report.get('original-policy', ''),
            "blocked_uri": csp_report.get('blocked-uri', ''),
            "status_code": csp_report.get('status-code', 0),
            "disposition": csp_report.get('disposition', 'enforce')
        }
        
        # Classify violation type
        directive = parsed["violated_directive"]
        if "script-src" in directive:
            parsed["violation_type"] = "script_injection"
        elif "style-src" in directive:
            parsed["violation_type"] = "style_injection"
        elif "img-src" in directive:
            parsed["violation_type"] = "image_load"
        elif "connect-src" in directive:
            parsed["violation_type"] = "network_request"
        elif "frame-src" in directive:
            parsed["violation_type"] = "frame_load"
        else:
            parsed["violation_type"] = "other"
        
        return parsed


# Factory function for middleware creation
def create_csp_middleware(report_only: bool = None) -> CSPMiddleware:
    """Create CSP middleware with environment-based defaults"""
    
    if report_only is None:
        # Default to report-only in development
        environment = os.getenv("ENVIRONMENT", "development")
        report_only = environment != "production"
    
    return CSPMiddleware(None, report_only=report_only)
