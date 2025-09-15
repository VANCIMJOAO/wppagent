"""
🔧 CONFIGURAÇÃO AVANÇADA DE CORS - SEGURA
Arquivo dedicado para configuração segura de CORS sem wildcards
Versão corrigida: Remove todas as configurações inseguras com "*"
"""

import logging
import re
from typing import Dict, List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# 🛡️ Lista de origens permitidas por ambiente
ALLOWED_ORIGINS_PRODUCTION = [
    "https://wppagent-production.up.railway.app",
    "https://wppagent-production-app-production.up.railway.app",
    "https://nextjs-dashboard-production.up.railway.app",
    # Adicionar outras origens de produção conforme necessário
]

ALLOWED_ORIGINS_DEVELOPMENT = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "http://localhost:8501",  # Streamlit
    "http://localhost:8000",  # Backend local
    "http://127.0.0.1:8000",
]


def validate_origin(origin: str, allowed_origins: List[str]) -> bool:
    """
    Valida se uma origem está na lista de permitidas

    Args:
        origin: Origem a ser validada
        allowed_origins: Lista de origens permitidas

    Returns:
        bool: True se a origem for válida
    """
    if not origin:
        return False

    # Verificação exata
    if origin in allowed_origins:
        return True

    # Para desenvolvimento, permitir variações localhost
    if any("localhost" in allowed for allowed in allowed_origins):
        localhost_pattern = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
        if re.match(localhost_pattern, origin):
            return True

    return False


def get_cors_headers(origin: str, is_debug: bool = False) -> Dict[str, str]:
    """
    Gera headers CORS seguros baseados na origem

    Args:
        origin: Origem do request
        is_debug: Se está em modo debug

    Returns:
        Dict com headers CORS seguros
    """
    allowed_origins = (
        ALLOWED_ORIGINS_DEVELOPMENT if is_debug else ALLOWED_ORIGINS_PRODUCTION
    )

    if validate_origin(origin, allowed_origins):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH",
            "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Type, Authorization, X-Requested-With, Origin, Cache-Control, Pragma, X-CSRF-Token",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600",
        }
    else:
        # Retorna headers restritivos para origens não permitidas
        return {
            "Access-Control-Allow-Origin": "null",
            "Access-Control-Allow-Methods": "OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Credentials": "false",
        }


def setup_cors_middleware(app: FastAPI, debug: bool = False) -> None:
    """
    Configura middleware CORS com configurações seguras (sem wildcards)

    Args:
        app: Instância da aplicação FastAPI
        debug: Se True, permite origens de desenvolvimento
    """

    # 🎯 Origens permitidas baseadas no ambiente - SEM WILDCARDS
    if debug:
        allowed_origins = ALLOWED_ORIGINS_DEVELOPMENT.copy()
        logger.info("🛠️ CORS configurado para DESENVOLVIMENTO com origens específicas")
        logger.info(f"🔍 Origens permitidas: {allowed_origins}")
    else:
        allowed_origins = ALLOWED_ORIGINS_PRODUCTION.copy()
        logger.info("🔒 CORS configurado para PRODUÇÃO com origens restritas")
        logger.info(f"🔍 Origens permitidas: {allowed_origins}")

    # 🔧 Headers permitidos (específicos - sem wildcards)
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
        "User-Agent",
        "Referer",
    ]

    # 🔧 Métodos permitidos (específicos)
    allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"]

    # 🔧 Headers expostos (específicos)
    exposed_headers = [
        "Content-Type",
        "Authorization",
        "Content-Length",
        "X-Requested-With",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # SEM WILDCARDS
        allow_credentials=True,
        allow_methods=allowed_methods,  # SEM WILDCARDS
        allow_headers=allowed_headers,  # SEM WILDCARDS
        expose_headers=exposed_headers,
        max_age=3600,  # Cache preflight por 1 hora
    )

    logger.info(f"✅ CORS Middleware configurado SEGURAMENTE")
    logger.info(f"📋 Origins permitidas: {len(allowed_origins)} origins específicas")
    logger.info(f"🔧 Métodos permitidos: {allowed_methods}")
    logger.info(f"🚫 WILDCARDS REMOVIDOS - Configuração segura ativada")


def add_cors_test_endpoint(app: FastAPI) -> None:
    """
    Adiciona endpoints seguros para testar CORS
    """

    @app.options("/{path:path}")
    async def cors_preflight_handler(request: Request, path: str):
        """
        Handler seguro para requests OPTIONS (preflight)
        """
        origin = request.headers.get("origin", "")
        logger.info(f"🔍 CORS Preflight request de '{origin}' para: /{path}")

        # Determinar se está em modo debug
        is_debug = getattr(app.state, "debug", False)

        # Obter headers CORS seguros baseados na origem
        cors_headers = get_cors_headers(origin, is_debug)

        return JSONResponse(
            content={
                "message": "CORS preflight OK",
                "origin_validated": cors_headers["Access-Control-Allow-Origin"]
                != "null",
                "security_mode": "strict - no wildcards",
            },
            status_code=200,
            headers=cors_headers,
        )

    @app.get("/cors/test")
    async def cors_test(request: Request):
        """
        Endpoint seguro para testar CORS
        """
        origin = request.headers.get("origin", "")
        is_debug = getattr(app.state, "debug", False)
        cors_headers = get_cors_headers(origin, is_debug)

        is_valid_origin = cors_headers["Access-Control-Allow-Origin"] != "null"

        return JSONResponse(
            content={
                "status": "success" if is_valid_origin else "rejected",
                "message": "CORS teste realizado com segurança!",
                "origin": origin,
                "origin_valid": is_valid_origin,
                "timestamp": "2025-09-11T12:00:00Z",
                "security_note": "CORS configurado SEM wildcards - máxima segurança",
                "allowed_origins_count": len(
                    ALLOWED_ORIGINS_PRODUCTION
                    if not is_debug
                    else ALLOWED_ORIGINS_DEVELOPMENT
                ),
            },
            headers=cors_headers,
        )

    @app.post("/cors/test")
    async def cors_test_post(request: Request):
        """
        Endpoint POST seguro para testar CORS
        """
        origin = request.headers.get("origin", "")
        is_debug = getattr(app.state, "debug", False)
        cors_headers = get_cors_headers(origin, is_debug)

        is_valid_origin = cors_headers["Access-Control-Allow-Origin"] != "null"

        return JSONResponse(
            content={
                "status": "success" if is_valid_origin else "rejected",
                "message": "CORS POST teste - configuração segura!",
                "method": "POST",
                "origin": origin,
                "origin_valid": is_valid_origin,
                "security_note": "Sem wildcards - origem validada individualmente",
            },
            headers=cors_headers,
        )

    logger.info("🧪 Endpoints de teste CORS seguros adicionados: /cors/test")


def get_cors_debug_info() -> Dict:
    """
    Retorna informações de debug sobre configuração CORS segura
    """
    return {
        "cors_enabled": True,
        "middleware": "CORSMiddleware",
        "security_level": "HIGH - No wildcards",
        "wildcard_usage": "DISABLED",
        "allowed_origins_production": ALLOWED_ORIGINS_PRODUCTION,
        "allowed_origins_development": ALLOWED_ORIGINS_DEVELOPMENT,
        "debug_endpoints": ["/cors/test"],
        "preflight_handler": "Dynamic validation enabled",
        "validation_method": "Origin-specific headers",
        "recommended_test": "curl -X OPTIONS -H 'Origin: https://wppagent-production.up.railway.app' https://wppagent-production.up.railway.app/cors/test -v",
    }
