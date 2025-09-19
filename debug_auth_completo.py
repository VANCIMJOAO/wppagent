#!/usr/bin/env python3
"""
🔍 DEBUG COMPLETO DA AUTENTICAÇÃO
================================
Script para depurar cada camada da autenticação no Railway
"""

import asyncio
import uvicorn
import httpx
import logging
import os
import sys
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class DebugAuthMiddleware(BaseHTTPMiddleware):
    """Middleware de debug para rastrear autenticação"""
    
    def __init__(self, app, name="DebugAuth"):
        super().__init__(app)
        self.name = name
        self.request_count = 0
    
    async def dispatch(self, request: Request, call_next):
        self.request_count += 1
        path = request.url.path
        method = request.method
        
        logger.info(f"🔍 [{self.name}] REQUEST #{self.request_count}: {method} {path}")
        logger.info(f"🔍 [{self.name}] Headers: {dict(request.headers)}")
        logger.info(f"🔍 [{self.name}] Query: {dict(request.query_params)}")
        logger.info(f"🔍 [{self.name}] Client IP: {request.client.host if request.client else 'unknown'}")
        logger.info(f"🔍 [{self.name}] User-Agent: {request.headers.get('user-agent', 'N/A')}")
        
        # Verificar se é endpoint crítico
        critical_endpoints = {"/ping", "/health", "/emergency", "/railway", "/ready", "/alive"}
        if path in critical_endpoints:
            logger.info(f"🚨 [{self.name}] ENDPOINT CRÍTICO DETECTADO: {path}")
            logger.info(f"🚨 [{self.name}] Deveria fazer bypass total!")
        
        # Processar request
        start_time = datetime.now()
        response = await call_next(request)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() * 1000
        
        logger.info(f"🔍 [{self.name}] Response: {response.status_code} in {duration:.2f}ms")
        logger.info(f"🔍 [{self.name}] Response headers: {dict(response.headers)}")
        
        return response

class MockAuthMiddleware(BaseHTTPMiddleware):
    """Mock do AuthMiddleware para teste"""
    
    def __init__(self, app):
        super().__init__(app)
        self.public_endpoints = {
            "/health", "/emergency", "/railway-health", "/healthcheck", 
            "/status", "/railway", "/ready", "/alive", "/ping"
        }
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        logger.info(f"🔒 [MockAuth] Processando: {method} {path}")
        
        # Verificar se é público
        is_public = self._is_public_endpoint(path)
        logger.info(f"🔒 [MockAuth] _is_public_endpoint({path}) = {is_public}")
        
        if is_public:
            logger.info(f"✅ [MockAuth] Endpoint público: {path}")
            response = await call_next(request)
            return response
        else:
            logger.warning(f"❌ [MockAuth] Endpoint privado: {path} - REQUER AUTENTICAÇÃO")
            return JSONResponse(
                content={"error": "Authentication failed", "message": "Missing or invalid authorization header"},
                status_code=401
            )
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Verifica se endpoint é público"""
        logger.info(f"🔍 [MockAuth] _is_public_endpoint chamado para: {path}")
        logger.info(f"🔍 [MockAuth] public_endpoints: {self.public_endpoints}")
        
        # Verificação direta
        if path in self.public_endpoints:
            logger.info(f"✅ [MockAuth] path in public_endpoints = True")
            return True
        
        # Verificação de prefixos
        for public_path in self.public_endpoints:
            if path.startswith(public_path + "/"):
                logger.info(f"✅ [MockAuth] path.startswith('{public_path}/') = True")
                return True
        
        logger.info(f"❌ [MockAuth] path not in public_endpoints = False")
        return False

class UltraSimpleCriticalMiddleware(BaseHTTPMiddleware):
    """Middleware ultra simples para bypass de endpoints críticos"""
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        logger.info(f"🟡 [UltraSimple] Processando: {method} {path}")
        
        # BYPASS DIRETO para /ping
        if path == "/ping":
            logger.info(f"🚨 [UltraSimple] BYPASS DIRETO: {path} - RETORNANDO 200")
            return JSONResponse(
                content={"status": "ok", "service": "whatsapp-agent", "railway": True, "middleware": "UltraSimple"},
                status_code=200
            )
        
        # BYPASS DIRETO para outros endpoints críticos
        critical_paths = ["/health", "/emergency", "/railway"]
        if path in critical_paths:
            logger.info(f"🚨 [UltraSimple] BYPASS DIRETO: {path} - RETORNANDO 200")
            return JSONResponse(
                content={"status": "ok", "service": "whatsapp-agent", "middleware": "UltraSimple"},
                status_code=200
            )
        
        logger.info(f"🟡 [UltraSimple] Passando adiante: {path}")
        response = await call_next(request)
        logger.info(f"🟡 [UltraSimple] Resposta: {response.status_code}")
        return response

# Criar app FastAPI
app = FastAPI(title="Debug Auth Completo")

# Adicionar middlewares em ordem específica para teste
app.add_middleware(DebugAuthMiddleware, name="Debug1")
app.add_middleware(UltraSimpleCriticalMiddleware)
app.add_middleware(MockAuthMiddleware)
app.add_middleware(DebugAuthMiddleware, name="Debug2")

# Endpoints de teste
@app.get("/ping")
async def ping():
    logger.info("🎯 [ENDPOINT] /ping chamado")
    return {"status": "ok", "endpoint": "ping", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health():
    logger.info("🎯 [ENDPOINT] /health chamado")
    return {"status": "ok", "endpoint": "health", "timestamp": datetime.now().isoformat()}

@app.get("/emergency")
async def emergency():
    logger.info("🎯 [ENDPOINT] /emergency chamado")
    return {"status": "ok", "endpoint": "emergency", "timestamp": datetime.now().isoformat()}

@app.get("/railway")
async def railway():
    logger.info("🎯 [ENDPOINT] /railway chamado")
    return {"status": "ok", "endpoint": "railway", "timestamp": datetime.now().isoformat()}

@app.get("/private")
async def private():
    logger.info("🎯 [ENDPOINT] /private chamado")
    return {"status": "ok", "endpoint": "private", "timestamp": datetime.now().isoformat()}

async def test_endpoints():
    """Testar todos os endpoints"""
    await asyncio.sleep(2)  # Aguardar servidor iniciar
    
    print("\n🧪 TESTE COMPLETO DE AUTENTICAÇÃO")
    print("=================================")
    
    async with httpx.AsyncClient() as client:
        endpoints = ["/ping", "/health", "/emergency", "/railway", "/private"]
        
        for endpoint in endpoints:
            print(f"\n📋 TESTE {endpoint}:")
            print("-" * 30)
            try:
                response = await client.get(f"http://localhost:8002{endpoint}")
                print(f"Status: {response.status_code}")
                print(f"Response: {response.json()}")
            except Exception as e:
                print(f"Erro: {e}")

async def run_server():
    """Executar servidor"""
    config = uvicorn.Config(app, host="0.0.0.0", port=8002, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    """Função principal"""
    print("🚀 INICIANDO DEBUG COMPLETO DA AUTENTICAÇÃO")
    print("==========================================")
    print("📋 Ordem dos middlewares:")
    print("   1. Debug1 (entrada)")
    print("   2. UltraSimpleCriticalMiddleware")
    print("   3. MockAuthMiddleware")
    print("   4. Debug2 (saída)")
    print("")
    
    # Executar servidor e testes em paralelo
    server_task = asyncio.create_task(run_server())
    test_task = asyncio.create_task(test_endpoints())
    
    await test_task
    server_task.cancel()
    print("\n🛑 Parando servidor de debug...")

if __name__ == "__main__":
    asyncio.run(main())
