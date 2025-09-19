#!/usr/bin/env python3
"""
Teste local simples para verificar middleware
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Middleware de teste
class TestBypassMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔒 TestBypassMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"🔍 TestBypass processando: {path}")
        
        if path == "/ping":
            print(f"🚨 BYPASS TESTE: {path} - RETORNANDO 200")
            return JSONResponse(
                content={"message": "pong", "bypass": "TestBypassMiddleware"},
                status_code=200
            )
        
        print(f"🟡 TestBypass passando adiante: {path}")
        return await call_next(request)

class TestAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔐 TestAuthMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"🔍 TestAuth processando: {path}")
        
        if path == "/ping":
            print(f"❌ AUTH BLOQUEANDO: {path} - RETORNANDO 401")
            return JSONResponse(
                content={"error": "Authentication failed"},
                status_code=401
            )
        
        print(f"🟡 TestAuth passando adiante: {path}")
        return await call_next(request)

# Criar app
app = FastAPI(title="Teste Local")

# Adicionar middlewares na ordem INVERSA da execução
app.add_middleware(TestAuthMiddleware)  # Será executado PRIMEIRO
app.add_middleware(TestBypassMiddleware)  # Será executado SEGUNDO

@app.get("/ping")
async def ping():
    return {"message": "pong", "endpoint": "ping"}

@app.get("/health")
async def health():
    return {"status": "ok", "endpoint": "health"}

if __name__ == "__main__":
    print("🚀 Iniciando teste local...")
    print("📋 Ordem de adição:")
    print("1. TestAuthMiddleware (será executado PRIMEIRO)")
    print("2. TestBypassMiddleware (será executado SEGUNDO)")
    print("")
    print("🎯 Teste: /ping deve retornar 401 (bloqueado pelo Auth)")
    print("🎯 Teste: /health deve retornar 200 (passa pelo Auth)")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
