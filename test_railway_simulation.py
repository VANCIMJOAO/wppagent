#!/usr/bin/env python3
"""
Teste que simula exatamente o que está no main.py do Railway
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Simular UltraSimpleCriticalMiddleware exatamente como no main.py
class UltraSimpleCriticalMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔒 UltraSimpleCriticalMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        print(f"🟡 UltraSimple processando: {method} {path}")
        
        # BYPASS DIRETO para /ping
        if path == "/ping":
            print(f"🔒 BYPASS ULTRA SIMPLES: {path} - RETORNANDO 200")
            return JSONResponse(
                content={"message": "pong", "status": "ok", "service": "whatsapp-agent", "railway": True, "middleware": "UltraSimpleCritical"},
                status_code=200,
                headers={"Content-Type": "application/json", "X-Bypass": "UltraSimpleCritical"}
            )
        
        # BYPASS DIRETO para outros endpoints críticos
        critical_paths = ["/health", "/emergency", "/railway-health", "/healthcheck", "/status", "/railway"]
        if path in critical_paths:
            print(f"🔒 BYPASS ULTRA SIMPLES: {path} - RETORNANDO 200")
            return JSONResponse(
                content={"status": "ok", "service": "whatsapp-agent", "middleware": "UltraSimpleCritical"},
                status_code=200,
                headers={"Content-Type": "application/json", "X-Bypass": "UltraSimpleCritical"}
            )
        
        print(f"🟡 UltraSimple passando adiante: {path}")
        response = await call_next(request)
        print(f"🟡 UltraSimple resposta final: {response.status_code}")
        return response

# Simular AuthMiddleware exatamente como no main.py
class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔐 AuthMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method
        
        print(f"🔍 AuthMiddleware processando: {method} {path}")
        
        # Verificar se endpoint é público
        if self._is_public_endpoint(path):
            print(f"✅ ENDPOINT PÚBLICO AuthMiddleware: {path}")
            return await call_next(request)
        
        # Verificar autenticação
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            print(f"❌ ENDPOINT PRIVADO SEM TOKEN: {path}")
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication failed", "message": "Missing or invalid authorization header"}
            )
        
        print(f"✅ TOKEN VÁLIDO: {path}")
        return await call_next(request)
    
    def _is_public_endpoint(self, path: str) -> bool:
        """Verifica se endpoint é público - CORREÇÃO DEFINITIVA"""
        # BYPASS DIRETO para endpoints críticos
        critical_endpoints = {"/ping", "/health", "/emergency", "/railway-health", "/healthcheck", "/status", "/railway"}
        if path in critical_endpoints:
            print(f"🚨 BYPASS CRÍTICO AuthMiddleware: {path}")
            return True
        
        # Outros endpoints públicos
        public_endpoints = {"/docs", "/openapi.json", "/webhook", "/metrics"}
        if path in public_endpoints:
            print(f"✅ ENDPOINT PÚBLICO (SET) AuthMiddleware: {path}")
            return True
        
        print(f"❌ ENDPOINT PRIVADO AuthMiddleware: {path}")
        return False

# Criar app
app = FastAPI(title="Teste Railway Simulation")

# Adicionar middlewares na MESMA ORDEM do main.py
app.add_middleware(AuthMiddleware)  # Linha 648 - será executado PRIMEIRO
app.add_middleware(UltraSimpleCriticalMiddleware)  # Linha 725 - será executado SEGUNDO

@app.get("/ping")
async def ping():
    print("🎯 ENDPOINT /ping executado - NUNCA DEVERIA CHEGAR AQUI!")
    return {"message": "pong", "endpoint": "ping"}

@app.get("/health")
async def health():
    print("🎯 ENDPOINT /health executado - NUNCA DEVERIA CHEGAR AQUI!")
    return {"status": "ok", "endpoint": "health"}

if __name__ == "__main__":
    print("🚀 Iniciando teste Railway Simulation...")
    print("📋 Ordem de adição (mesma do main.py):")
    print("1. AuthMiddleware (linha 648) - será executado PRIMEIRO")
    print("2. UltraSimpleCriticalMiddleware (linha 725) - será executado SEGUNDO")
    print("")
    print("🎯 Teste: /ping deve retornar 401 (bloqueado pelo Auth PRIMEIRO)")
    print("🎯 Teste: /health deve retornar 200 (bypass do Auth)")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
