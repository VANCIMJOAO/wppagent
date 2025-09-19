#!/usr/bin/env python3
"""
Teste com TODOS os middlewares do main.py
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Simular todos os middlewares
class CSPMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔒 CSPMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"🔒 CSP processando: {path}")
        return await call_next(request)

class HTTPSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔒 HTTPSMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"🔒 HTTPS processando: {path}")
        return await call_next(request)

class ApiResponseMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("📊 ApiResponseMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"📊 ApiResponse processando: {path}")
        return await call_next(request)

class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("📈 MetricsMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"📈 Metrics processando: {path}")
        return await call_next(request)

class UserRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("⏱️ UserRateLimitMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"⏱️ UserRateLimit processando: {path}")
        return await call_next(request)

class WebhookRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("⏱️ WebhookRateLimitMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"⏱️ WebhookRateLimit processando: {path}")
        return await call_next(request)

class DatabasePerformanceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🗄️ DatabasePerformanceMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"🗄️ DatabasePerformance processando: {path}")
        return await call_next(request)

class APMMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("📊 APMMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"📊 APM processando: {path}")
        return await call_next(request)

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔐 AuthMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"🔐 Auth processando: {path}")
        
        if self._is_public_endpoint(path):
            print(f"✅ ENDPOINT PÚBLICO AuthMiddleware: {path}")
            return await call_next(request)
        
        print(f"❌ ENDPOINT PRIVADO AuthMiddleware: {path}")
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication failed", "message": "Missing or invalid authorization header"}
        )
    
    def _is_public_endpoint(self, path: str) -> bool:
        critical_endpoints = {"/ping", "/health", "/emergency", "/railway-health", "/healthcheck", "/status", "/railway"}
        return path in critical_endpoints

class SuperDebugMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔍 SuperDebugMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"🔍 SuperDebug processando: {path}")
        return await call_next(request)

class UltraSimpleCriticalMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        print("🔒 UltraSimpleCriticalMiddleware inicializado")
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        print(f"🟡 UltraSimple processando: {path}")
        
        if path == "/ping":
            print(f"🔒 BYPASS ULTRA SIMPLES: {path} - RETORNANDO 200")
            return JSONResponse(
                content={"message": "pong", "status": "ok", "service": "whatsapp-agent", "railway": True, "middleware": "UltraSimpleCritical"},
                status_code=200
            )
        
        critical_paths = ["/health", "/emergency", "/railway-health", "/healthcheck", "/status", "/railway"]
        if path in critical_paths:
            print(f"🔒 BYPASS ULTRA SIMPLES: {path} - RETORNANDO 200")
            return JSONResponse(
                content={"status": "ok", "service": "whatsapp-agent", "middleware": "UltraSimpleCritical"},
                status_code=200
            )
        
        print(f"🟡 UltraSimple passando adiante: {path}")
        return await call_next(request)

# Criar app
app = FastAPI(title="Teste Todos Middlewares")

# Adicionar middlewares na MESMA ORDEM do main.py (última para primeira)
app.add_middleware(CSPMiddleware)
app.add_middleware(HTTPSMiddleware)
app.add_middleware(ApiResponseMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(UserRateLimitMiddleware)
app.add_middleware(WebhookRateLimitMiddleware)
app.add_middleware(DatabasePerformanceMiddleware)
app.add_middleware(APMMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(SuperDebugMiddleware)
app.add_middleware(UltraSimpleCriticalMiddleware)  # ÚLTIMO ADICIONADO = PRIMEIRO EXECUTADO

@app.get("/ping")
async def ping():
    print("🎯 ENDPOINT /ping executado - NUNCA DEVERIA CHEGAR AQUI!")
    return {"message": "pong", "endpoint": "ping"}

@app.get("/health")
async def health():
    print("🎯 ENDPOINT /health executado - NUNCA DEVERIA CHEGAR AQUI!")
    return {"status": "ok", "endpoint": "health"}

if __name__ == "__main__":
    print("🚀 Iniciando teste com TODOS os middlewares...")
    print("📋 Ordem de execução (última adicionada = primeira executada):")
    print("1. UltraSimpleCriticalMiddleware (PRIMEIRO EXECUTADO)")
    print("2. SuperDebugMiddleware")
    print("3. AuthMiddleware")
    print("4. APMMiddleware")
    print("5. DatabasePerformanceMiddleware")
    print("6. WebhookRateLimitMiddleware")
    print("7. UserRateLimitMiddleware")
    print("8. MetricsMiddleware")
    print("9. ApiResponseMiddleware")
    print("10. HTTPSMiddleware")
    print("11. CSPMiddleware (ÚLTIMO EXECUTADO)")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8004, log_level="info")
