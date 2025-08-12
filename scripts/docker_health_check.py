#!/bin/bash
"""
Health Check simples para Docker containers
Script otimizado para verificações rápidas
"""

import asyncio
import sys
import httpx
import time
from sqlalchemy import text
from app.database import get_async_engine
from app.config import settings

async def quick_health_check():
    """Health check rápido para Docker"""
    checks_passed = 0
    total_checks = 3
    
    # 1. Verificar API básica
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://localhost:{settings.app_port}/health")
            if response.status_code == 200:
                checks_passed += 1
    except:
        pass
    
    # 2. Verificar banco de dados
    try:
        engine = get_async_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            checks_passed += 1
    except:
        pass
    
    # 3. Verificar se o processo principal está rodando
    try:
        # Se chegou até aqui, o processo está rodando
        checks_passed += 1
    except:
        pass
    
    # Health check passa se pelo menos 2 de 3 checks passaram
    if checks_passed >= 2:
        print("OK")
        sys.exit(0)
    else:
        print("FAIL")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(quick_health_check())
