#!/usr/bin/env python3
"""
Teste que simula as importações exatas do main.py para identificar problemas
"""

print("🔍 TESTANDO IMPORTAÇÕES DO MAIN.PY")
print("=================================")

try:
    print("📋 1. Importando asyncio...")
    import asyncio
    print("✅ asyncio OK")
except Exception as e:
    print(f"❌ asyncio FALHOU: {e}")

try:
    print("📋 2. Importando logging...")
    import logging
    print("✅ logging OK")
except Exception as e:
    print(f"❌ logging FALHOU: {e}")

try:
    print("📋 3. Importando contextlib...")
    from contextlib import asynccontextmanager
    print("✅ contextlib OK")
except Exception as e:
    print(f"❌ contextlib FALHOU: {e}")

try:
    print("📋 4. Importando datetime...")
    from datetime import datetime
    print("✅ datetime OK")
except Exception as e:
    print(f"❌ datetime FALHOU: {e}")

try:
    print("📋 5. Importando uvicorn...")
    import uvicorn
    print("✅ uvicorn OK")
except Exception as e:
    print(f"❌ uvicorn FALHOU: {e}")

try:
    print("📋 6. Importando FastAPI...")
    from fastapi import FastAPI, HTTPException, Request
    print("✅ FastAPI OK")
except Exception as e:
    print(f"❌ FastAPI FALHOU: {e}")

try:
    print("📋 7. Importando CORSMiddleware...")
    from fastapi.middleware.cors import CORSMiddleware
    print("✅ CORSMiddleware OK")
except Exception as e:
    print(f"❌ CORSMiddleware FALHOU: {e}")

try:
    print("📋 8. Importando JSONResponse...")
    from fastapi.responses import JSONResponse, Response
    print("✅ JSONResponse OK")
except Exception as e:
    print(f"❌ JSONResponse FALHOU: {e}")

try:
    print("📋 9. Importando BaseHTTPMiddleware...")
    from starlette.middleware.base import BaseHTTPMiddleware
    print("✅ BaseHTTPMiddleware OK")
except Exception as e:
    print(f"❌ BaseHTTPMiddleware FALHOU: {e}")

try:
    print("📋 10. Importando app.config...")
    from app.config import settings
    print("✅ app.config OK")
except Exception as e:
    print(f"❌ app.config FALHOU: {e}")

try:
    print("📋 11. Importando app.config.config_factory...")
    from app.config.config_factory import is_development
    print("✅ app.config.config_factory OK")
except Exception as e:
    print(f"❌ app.config.config_factory FALHOU: {e}")

try:
    print("📋 12. Importando app.database...")
    from app.database import init_db
    print("✅ app.database OK")
except Exception as e:
    print(f"❌ app.database FALHOU: {e}")

try:
    print("📋 13. Importando app.middleware.request_logging...")
    from app.middleware.request_logging import add_request_logging_middleware
    print("✅ app.middleware.request_logging OK")
except Exception as e:
    print(f"❌ app.middleware.request_logging FALHOU: {e}")

try:
    print("📋 14. Importando app.routes.webhook...")
    from app.routes.webhook import router as webhook_router
    print("✅ app.routes.webhook OK")
except Exception as e:
    print(f"❌ app.routes.webhook FALHOU: {e}")

print("")
print("🎯 TESTE DE IMPORTAÇÕES CONCLUÍDO")
print("===============================")
print("Se alguma importação falhou, isso pode explicar por que o Railway não funciona!")
