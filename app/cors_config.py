"""
🔧 CONFIGURAÇÃO AVANÇADA DE CORS
Arquivo dedicado para resolver problemas de CORS no Railway e outras plataformas
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def setup_cors_middleware(app: FastAPI, debug: bool = False) -> None:
    """
    Configura middleware CORS com configurações específicas para Railway
    
    Args:
        app: Instância da aplicação FastAPI
        debug: Se True, permite origins mais amplos para desenvolvimento
    """
    
    # 🎯 Origens permitidas com base no ambiente
    if debug:
        # Desenvolvimento - permitir localhost e mais origins
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "https://localhost:3000",
            "http://localhost:8501",  # Streamlit
            "*"  # Temporário para desenvolvimento
        ]
        logger.info("🛠️ CORS configurado para DESENVOLVIMENTO")
    else:
        # Produção - mais restritivo
        allowed_origins = [
            "https://wppagent-production.up.railway.app",
            "http://localhost:3000",  # Para dashboard local ainda funcionar
            "https://localhost:3000",
            "*"  # Ainda permitindo tudo temporariamente para debug
        ]
        logger.info("🔒 CORS configurado para PRODUÇÃO")
    
    # 🔧 Headers permitidos (mais específicos)
    allowed_headers = [
        "Accept",
        "Accept-Language", 
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Cache-Control",
        "Pragma",
        "X-CSRF-Token",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Credentials",
        "User-Agent",
        "Referer"
    ]
    
    # 🔧 Métodos permitidos
    allowed_methods = [
        "GET",
        "POST", 
        "PUT",
        "DELETE",
        "OPTIONS",
        "HEAD",
        "PATCH"
    ]
    
    # 🔧 Headers expostos
    exposed_headers = [
        "Access-Control-Allow-Origin",
        "Content-Type",
        "Authorization",
        "Content-Length",
        "X-Requested-With"
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        expose_headers=exposed_headers,
        max_age=3600,  # Cache preflight por 1 hora
    )
    
    logger.info(f"✅ CORS Middleware configurado")
    logger.info(f"📋 Origins permitidas: {len(allowed_origins)} origins")
    logger.info(f"🔧 Métodos permitidos: {allowed_methods}")


def add_cors_test_endpoint(app: FastAPI) -> None:
    """
    Adiciona endpoint específico para testar CORS
    """
    
    @app.options("/{path:path}")
    async def cors_preflight_handler(path: str):
        """
        Handler específico para requests OPTIONS (preflight)
        """
        logger.info(f"🔍 CORS Preflight request para: /{path}")
        
        return JSONResponse(
            content={"message": "CORS preflight OK"},
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "3600",
            }
        )
    
    @app.get("/cors/test")
    async def cors_test():
        """
        Endpoint específico para testar CORS
        """
        return JSONResponse(
            content={
                "status": "success",
                "message": "CORS está funcionando!",
                "timestamp": "2025-09-05T12:00:00Z",
                "cors_headers_included": True
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    
    @app.post("/cors/test")
    async def cors_test_post():
        """
        Endpoint POST para testar CORS
        """
        return JSONResponse(
            content={
                "status": "success",
                "message": "CORS POST está funcionando!",
                "method": "POST"
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    
    logger.info("🧪 Endpoints de teste CORS adicionados: /cors/test")


def get_cors_debug_info() -> Dict:
    """
    Retorna informações de debug sobre configuração CORS
    """
    return {
        "cors_enabled": True,
        "middleware": "CORSMiddleware",
        "debug_endpoints": ["/cors/test"],
        "preflight_handler": "Ativo",
        "recommended_test": "curl -X OPTIONS https://wppagent-production.up.railway.app/cors/test -v"
    }
