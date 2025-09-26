"""
🚀 Autenticação Rápida com Pool Persistente
===========================================

Endpoint otimizado para login com pool de conexões persistente
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import text

from app.services.connection_pool_manager import get_pool_engine
from app.utils.logger import get_logger
from app.auth.jwt_manager import SimpleJWTManager

logger = get_logger(__name__)

router = APIRouter(prefix="/fast-auth", tags=["Fast Authentication"])

# Inicializar JWT Manager
jwt_manager = SimpleJWTManager()


class FastLoginRequest(BaseModel):
    username: str
    password: str


class FastLoginResponse(BaseModel):
    success: bool
    token: str
    expires_in: int
    user_info: dict


@router.post("/login", response_model=FastLoginResponse)
async def fast_login(request: FastLoginRequest, http_request: Request, response: Response):
    """Login otimizado com pool de conexões persistente"""
    
    start_time = datetime.now()
    
    try:
        # Obter engine do pool persistente
        engine = get_pool_engine()
        if not engine:
            raise HTTPException(status_code=500, detail="Pool de conexões não disponível")
        
        # Query otimizada com pool persistente
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, username, password_hash, full_name, is_active 
                    FROM admin_users 
                    WHERE username = :username AND is_active = true
                """),
                {"username": request.username}
            )
            user_data = result.fetchone()
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Verificar senha (usando bcrypt)
        import bcrypt
        if not bcrypt.checkpw(request.password.encode('utf-8'), user_data.password_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        
        # Gerar token JWT
        user_info = {
            "user_id": str(user_data.id),
            "username": user_data.username,
            "role": "admin",
            "full_name": user_data.full_name
        }
        
        # Criar token com expiração de 2 horas
        token = jwt_manager.create_access_token(
            user_id=str(user_data.id),
            role="admin",
            permissions=["read", "write", "delete", "admin", "user_management", "api_access"]
        )
        
        # Definir cookie seguro
        response.set_cookie(
            key="access_token",
            value=token,
            max_age=7200,  # 2 horas
            httponly=True,
            secure=os.getenv("NODE_ENV") == "production",
            samesite="strict"
        )
        
        # Calcular tempo de resposta
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"✅ Login rápido concluído em {response_time:.2f}ms para {request.username}")
        
        return FastLoginResponse(
            success=True,
            token=token,
            expires_in=7200,
            user_info=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro no login rápido: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/status")
async def auth_status():
    """Verificar status do pool de conexões"""
    try:
        engine = get_pool_engine()
        if not engine:
            return {"status": "error", "message": "Pool não inicializado"}
        
        # Teste rápido de conexão
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.scalar()
        
        return {
            "status": "healthy",
            "message": "Pool de conexões funcionando",
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "invalid": engine.pool.invalid()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Pool com problemas: {str(e)}"
        }
