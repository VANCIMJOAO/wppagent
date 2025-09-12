"""
🔧 CONFIGURAÇÃO AVANÇADA DE CORS - SEGURA
Arquivo dedicado para configuração segura de CORS sem wildcards
Versão corrigida: Validação dinâmica baseada em variáveis de ambiente
SEC-001: Implementa validação dinâmica baseada em variáveis de ambiente
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional
import logging
import re
import os

logger = logging.getLogger(__name__)

def get_environment() -> str:
    """Detecta o ambiente atual baseado em variáveis de ambiente"""
    return os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()

def get_allowed_origins() -> List[str]:
    """
    🛡️ SEC-001 FIX: Obtém origens permitidas baseadas no ambiente
    Validação dinâmica evita mistura de URLs dev/prod
    """
    environment = get_environment()
    
    # Origens específicas do ambiente via variável de ambiente
    env_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if env_origins:
        origins = [origin.strip() for origin in env_origins.split(",") if origin.strip()]
        logger.info(f"🔒 CORS: Usando origens do ambiente {environment}: {len(origins)} configuradas")
        return origins
    
    # Fallback baseado no ambiente detectado
    if environment == "production":
        origins = [
            "https://wppagent-production.up.railway.app",
            "https://wppagent-production-app-production.up.railway.app", 
            "https://nextjs-dashboard-production.up.railway.app",
        ]
        logger.info(f"🔒 CORS: Ambiente PRODUCTION - {len(origins)} origens permitidas")
    elif environment == "staging":
        origins = [
            "https://wppagent-staging.up.railway.app",
            "https://nextjs-dashboard-staging.up.railway.app",
        ]
        logger.info(f"🔒 CORS: Ambiente STAGING - {len(origins)} origens permitidas")
    else:  # development
        origins = [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "https://localhost:3000",
            "http://localhost:8501",  # Streamlit
            "http://localhost:8000",  # Backend local
            "http://127.0.0.1:8000"
        ]
        logger.info(f"🔒 CORS: Ambiente DEVELOPMENT - {len(origins)} origens permitidas")
    
    return origins

def validate_origin(origin: str) -> bool:
    """
    🛡️ SEC-001 FIX: Valida se uma origem está na lista de permitidas
    Agora usa validação dinâmica baseada no ambiente
    
    Args:
        origin: Origem a ser validada
        
    Returns:
        bool: True se a origem for válida
    """
    if not origin:
        return False
    
    allowed_origins = get_allowed_origins()
    
    # Verificação exata
    if origin in allowed_origins:
        logger.debug(f"✅ CORS: Origem validada: {origin}")
        return True
    
    # Para desenvolvimento, permitir variações localhost
    environment = get_environment()
    if environment == "development":
        localhost_pattern = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
        if re.match(localhost_pattern, origin):
            logger.debug(f"✅ CORS: Origem localhost validada: {origin}")
            return True
    
    logger.warning(f"❌ CORS: Origem rejeitada: {origin}")
    return False

def get_cors_headers(origin: str) -> Dict[str, str]:
    """
    🛡️ SEC-001 FIX: Gera headers CORS seguros baseados na origem
    Agora usa validação dinâmica do ambiente
    
    Args:
        origin: Origem do request
        
    Returns:
        Dict com headers CORS seguros ou vazio se origem inválida
    """
    if validate_origin(origin):
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
    🛡️ SEC-001 FIX: Configura middleware CORS com validação dinâmica
    
    Args:
        app: Instância da aplicação FastAPI
        debug: Parâmetro mantido para compatibilidade (agora usa variáveis de ambiente)
    """
    
    # 🎯 SEC-001 FIX: Origens baseadas no ambiente - SEM WILDCARDS
    allowed_origins = get_allowed_origins()
    environment = get_environment()
    
    logger.info(f"� CORS configurado para ambiente: {environment.upper()}")
    logger.info(f"🔍 Origens permitidas: {len(allowed_origins)} configuradas")
    if environment == "development":
        logger.info(f"�️ Origens de desenvolvimento: {allowed_origins}")
    else:
        logger.info(f"� Origens de produção configuradas")
    
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
        "Referer"
    ]
    
    # 🔧 Métodos permitidos (específicos)
    allowed_methods = [
        "GET",
        "POST", 
        "PUT",
        "DELETE",
        "OPTIONS",
        "HEAD",
        "PATCH"
    ]
    
    # 🔧 Headers expostos (específicos)
    exposed_headers = [
        "Content-Type",
        "Authorization",
        "Content-Length",
        "X-Requested-With"
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
        is_debug = getattr(app.state, 'debug', False)
        
        # Obter headers CORS seguros baseados na origem
        cors_headers = get_cors_headers(origin, is_debug)
        
        return JSONResponse(
            content={
                "message": "CORS preflight OK",
                "origin_validated": cors_headers["Access-Control-Allow-Origin"] != "null",
                "security_mode": "strict - no wildcards"
            },
            status_code=200,
            headers=cors_headers
        )
    
    @app.get("/cors/test")
    async def cors_test(request: Request):
        """
        Endpoint seguro para testar CORS
        """
        origin = request.headers.get("origin", "")
        is_debug = getattr(app.state, 'debug', False)
        cors_headers = get_cors_headers(origin)
        
        is_valid_origin = bool(cors_headers and cors_headers.get("Access-Control-Allow-Origin"))
        
        allowed_origins = get_allowed_origins()
        
        return JSONResponse(
            content={
                "status": "success" if is_valid_origin else "rejected",
                "message": "CORS teste realizado com segurança!",
                "origin": origin,
                "origin_valid": is_valid_origin,
                "timestamp": "2025-09-12T12:00:00Z",
                "security_note": "SEC-001 FIX: CORS com validação dinâmica baseada em ambiente",
                "allowed_origins_count": len(allowed_origins),
                "environment": get_environment()
            },
            headers=cors_headers if cors_headers else {}
        )
    
    @app.post("/cors/test")
    async def cors_test_post(request: Request):
        """
        Endpoint POST seguro para testar CORS
        """
        origin = request.headers.get("origin", "")
        is_debug = getattr(app.state, 'debug', False)
        cors_headers = get_cors_headers(origin, is_debug)
        
        is_valid_origin = cors_headers["Access-Control-Allow-Origin"] != "null"
        
        return JSONResponse(
            content={
                "status": "success" if is_valid_origin else "rejected",
                "message": "CORS POST teste - configuração segura!",
                "method": "POST",
                "origin": origin,
                "origin_valid": is_valid_origin,
                "security_note": "Sem wildcards - origem validada individualmente"
            },
            headers=cors_headers
        )
    
    logger.info("🧪 Endpoints de teste CORS seguros adicionados: /cors/test")


def get_cors_debug_info() -> Dict:
    """
    Retorna informações de debug sobre configuração CORS segura
    """
    return {
        "cors_enabled": True,
        "middleware": "CORSMiddleware",
        "security_level": "HIGH - SEC-001 FIX: Environment-based validation",
        "wildcard_usage": "DISABLED",
        "environment": get_environment(),
        "allowed_origins_count": len(get_allowed_origins()),
        "debug_endpoints": ["/cors/test"],
        "preflight_handler": "Dynamic validation enabled",
        "validation_method": "Environment-based origin validation",
        "recommended_test": "curl -X OPTIONS -H 'Origin: https://wppagent-production.up.railway.app' https://wppagent-production.up.railway.app/cors/test -v"
    }
