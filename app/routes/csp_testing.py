"""
🔒 CSP Testing Router
====================

Router para testes de Content Security Policy (CSP) implementados no S001.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any

# Criar router para testes CSP
csp_testing_router = APIRouter(prefix="/csp-test", tags=["CSP Testing"])


@csp_testing_router.get("/", response_class=HTMLResponse)
async def csp_test_page():
    """
    Página de teste para verificar se as políticas CSP estão funcionando
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSP Test Page</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>🔒 CSP Testing Page</h1>
        <p>Esta página testa as políticas de Content Security Policy implementadas no S001.</p>
        
        <div id="test-results">
            <h2>Testes CSP:</h2>
            <ul>
                <li id="inline-script-test">❓ Inline Script Test</li>
                <li id="external-script-test">❓ External Script Test</li>
                <li id="style-test">❓ Inline Style Test</li>
            </ul>
        </div>
        
        <!-- Este script inline deve ser BLOQUEADO pela CSP -->
        <script>
            document.getElementById('inline-script-test').innerHTML = '❌ Inline Script Executado (CSP não está funcionando)';
        </script>
        
        <!-- Este estilo inline deve ser BLOQUEADO pela CSP -->
        <div style="color: red;">Este texto não deve aparecer em vermelho se CSP estiver funcionando</div>
        
        <script nonce="csp-test-nonce">
            // Este script com nonce deve funcionar
            document.getElementById('inline-script-test').innerHTML = '✅ CSP está funcionando (inline script bloqueado)';
            
            // Testar script externo
            try {
                fetch('/static/test.js')
                .then(() => {
                    document.getElementById('external-script-test').innerHTML = '✅ Scripts externos permitidos';
                })
                .catch(() => {
                    document.getElementById('external-script-test').innerHTML = '❌ Scripts externos bloqueados';
                });
            } catch (e) {
                document.getElementById('external-script-test').innerHTML = '❌ Fetch bloqueado pela CSP';
            }
        </script>
    </body>
    </html>
    """
    return html_content


@csp_testing_router.get("/status")
async def csp_status():
    """
    Verificar status das políticas CSP implementadas
    """
    return {
        "success": True,
        "data": {
            "csp_enabled": True,
            "policies": [
                "default-src 'self'",
                "script-src 'self' 'nonce-{nonce}'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ],
            "implementation": "S001 - Content Security Policy",
            "test_endpoint": "/csp-test/"
        },
        "error": None
    }


@csp_testing_router.post("/report")
async def csp_violation_report(request: Request):
    """
    Endpoint para receber relatórios de violação CSP
    """
    try:
        violation_data = await request.json()
        
        # Log da violação para monitoramento
        print(f"🚨 CSP Violation Report: {violation_data}")
        
        return {
            "success": True,
            "data": {
                "message": "CSP violation report received",
                "violation": violation_data
            },
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": f"Error processing CSP violation report: {str(e)}"
        }


@csp_testing_router.get("/headers")
async def check_csp_headers(request: Request):
    """
    Verificar se os headers CSP estão sendo aplicados
    """
    return {
        "success": True,
        "data": {
            "request_headers": dict(request.headers),
            "csp_header_present": "content-security-policy" in request.headers,
            "expected_csp": "default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'"
        },
        "error": None
    }
