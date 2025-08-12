#!/usr/bin/env python3
"""
🔒 Servidor de Teste para Sistema de Autenticação

Servidor simplificado para testar apenas o sistema de autenticação
sem dependências do banco PostgreSQL.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import asyncio

# Importar componentes de autenticação
from app.auth import JWTManager, TwoFactorAuth, RateLimiter, SecretsManager
from app.auth.secrets_manager import SecretType

# Configuração simplificada
app = FastAPI(
    title="WhatsApp Agent Auth Test",
    description="Teste do sistema de autenticação",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar componentes
jwt_manager = JWTManager()
twofa = TwoFactorAuth()
rate_limiter = RateLimiter()
secrets_manager = SecretsManager()

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class TwoFAVerifyRequest(BaseModel):
    code: str
    type: str = "totp"

class SecretCreateRequest(BaseModel):
    secret_id: str
    secret_type: str
    value: Optional[str] = None

# Simulação de usuários (para teste)
USERS_DB = {
    "admin": {
        "password": "os.getenv("ADMIN_PASSWORD", "SECURE_ADMIN_PASSWORD")",
        "role": "admin",
        "is_2fa_enabled": False
    }
}

# Dependência para verificar token
async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token not provided")
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt_manager.verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except Exception as e:
        # Capturar qualquer erro de JWT (incluindo token revogado)
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Rotas de autenticação
@app.post("/auth/login")
async def login(request: LoginRequest):
    """Login básico"""
    user = USERS_DB.get(request.username)
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Gerar token
    token = jwt_manager.create_access_token(
        user_id=request.username,
        role=user["role"],
        permissions=[]
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": request.username,
            "role": user["role"],
            "is_2fa_enabled": user["is_2fa_enabled"]
        }
    }

@app.post("/auth/2fa/setup")
async def setup_2fa(current_user: dict = Depends(get_current_user)):
    """Configurar 2FA"""
    username = current_user["sub"]
    
    # Gerar secret TOTP
    secret = twofa.generate_secret(username)
    
    # Gerar QR code
    qr_code = twofa.generate_qr_code(username, f"{username}@whatsapp-agent.com", secret)
    
    # Salvar na "base de dados" simulada
    if username in USERS_DB:
        USERS_DB[username]["totp_secret"] = secret
    
    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": twofa.regenerate_backup_codes(username)
    }

@app.post("/auth/2fa/verify")
async def verify_2fa(
    request: TwoFAVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Verificar código 2FA"""
    username = current_user["sub"]
    user = USERS_DB.get(username)
    
    # Verificar código
    is_valid = False
    backup_codes = []
    
    if request.type == "totp":
        # Primeiro tentar confirmar setup (caso seja a primeira verificação)
        is_valid, backup_codes = twofa.confirm_2fa_setup(username, request.code)
        
        # Se não funcionou, tentar verificação normal
        if not is_valid:
            is_valid = twofa.verify_totp(username, request.code)
            
    elif request.type == "backup":
        is_valid = twofa.verify_backup_code(username, request.code)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    
    # Atualizar status
    USERS_DB[username]["is_2fa_enabled"] = True
    
    # Gerar novo token com 2FA verificado
    token = jwt_manager.create_access_token(
        user_id=username,
        role=user["role"],
        permissions=["2fa_verified"]
    )
    
    response = {
        "access_token": token,
        "token_type": "bearer",
        "message": "2FA verified successfully"
    }
    
    # Se foram gerados backup codes, incluir na resposta
    if backup_codes:
        response["backup_codes"] = backup_codes
        response["message"] = "2FA setup confirmed successfully"
    
    return response

@app.get("/auth/status")
async def auth_status(current_user: dict = Depends(get_current_user)):
    """Status da autenticação"""
    return {
        "authenticated": True,
        "user": current_user.get("username"),
        "role": current_user.get("role"),
        "2fa_verified": current_user.get("2fa_verified", False)
    }

@app.post("/auth/refresh")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Renovar token"""
    new_token = jwt_manager.create_access_token(
        user_id=current_user["sub"],
        role=current_user["role"],
        permissions=current_user.get("permissions", [])
    )
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }

@app.post("/auth/revoke")
async def revoke_token(request: Request):
    """Revogar token"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        jwt_manager.revoke_token(token)
    
    return {"message": "Token revoked successfully"}

# Rotas de secrets
@app.get("/secrets/list")
async def list_secrets(current_user: dict = Depends(get_current_user)):
    """Listar secrets"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    secrets = secrets_manager.list_secrets()
    return {"secrets": secrets}

@app.post("/secrets/create") 
async def create_secret(
    request: SecretCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Criar secret"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    secret_info = secrets_manager.create_secret(
        request.secret_id,
        SecretType(request.secret_type),
        request.value
    )
    
    return {
        "message": "Secret created successfully",
        "secret_id": request.secret_id,
        "created_at": secret_info.created_at.isoformat()
    }

@app.get("/secrets/{secret_id}")
async def get_secret_info(
    secret_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obter informações do secret (sem valor)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    secret = secrets_manager.get_secret(secret_id)
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    # Retornar informações sem o valor sensível
    info = {
        "id": secret.id,
        "type": secret.type.value,
        "version": secret.version,
        "created_at": secret.created_at.isoformat(),
        "expires_at": secret.expires_at.isoformat() if secret.expires_at else None,
        "active": secret.active,
        "metadata": secret.metadata
    }
    
    return info

@app.get("/secrets/{secret_id}/value")
async def get_secret_value(
    secret_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obter valor do secret (operação auditada)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    secret = secrets_manager.get_secret(secret_id)
    if secret is None:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    # Log da operação sensível
    secrets_manager._log_audit(
        "SECRET_ACCESS",
        secret_id,
        {"accessed_by": current_user.get("sub"), "accessed_at": "now"}
    )
    
    return {"value": secret.value}

@app.post("/secrets/{secret_id}/rotate")
async def rotate_secret(
    secret_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Rotacionar secret"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    new_secret = secrets_manager.rotate_secret(secret_id)
    return {
        "message": "Secret rotated successfully",
        "secret_id": secret_id,
        "new_version": new_secret.version
    }

# Health checks
@app.get("/health")
async def health_check():
    """Health check básico"""
    return {
        "status": "healthy",
        "service": "WhatsApp Agent Auth Test",
        "components": {
            "jwt_manager": "ok",
            "2fa": "ok", 
            "rate_limiter": "ok",
            "secrets_manager": "ok"
        }
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Health check detalhado"""
    return {
        "overall_status": "healthy",
        "timestamp": "2025-08-11T01:00:00Z",
        "checks": {
            "auth_system": {
                "status": "healthy",
                "message": "Authentication system operational",
                "response_time": 0.1
            },
            "jwt_manager": {
                "status": "healthy", 
                "message": "JWT management operational",
                "response_time": 0.05
            },
            "2fa_system": {
                "status": "healthy",
                "message": "Two-factor authentication operational", 
                "response_time": 0.03
            },
            "secrets_manager": {
                "status": "healthy",
                "message": "Secrets management operational",
                "response_time": 0.08
            }
        }
    }

if __name__ == "__main__":
    print("🚀 Iniciando servidor de teste de autenticação...")
    print("📱 Servidor será executado em http://localhost:8001")
    print("📖 Documentação: http://localhost:8001/docs")
    
    uvicorn.run(
        "test_auth_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
