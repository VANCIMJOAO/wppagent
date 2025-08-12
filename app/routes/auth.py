"""
Rotas de autenticação e autorização
Implementa login, 2FA, refresh tokens, revogação e gerenciamento de secrets
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
import secrets
import hashlib
from datetime import datetime, timezone, timedelta

from ..auth.jwt_manager import jwt_manager
from ..auth.two_factor import two_factor_auth
from ..auth.rate_limiter import rate_limiter
from ..auth.secrets_manager import secrets_manager, SecretType
from ..auth.middleware import get_current_user, require_admin, require_2fa

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Modelos Pydantic
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_2fa: bool = False
    user_info: Dict

class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]

class TwoFactorVerifyRequest(BaseModel):
    code: str
    type: str = "totp"  # totp ou backup

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RevokeTokenRequest(BaseModel):
    token: str
    revoke_all: bool = False

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """Endpoint de login com verificação de credenciais"""
    
    # Verificar rate limiting específico para login
    allowed, rate_result = rate_limiter.check_rate_limit(
        http_request, None, "auth"
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Try again in {rate_result.get('retry_after', 60)} seconds"
        )
    
    # Verificar credenciais (mock - implementar com banco real)
    user_id, role = await _verify_credentials(request.username, request.password)
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Verificar se 2FA está habilitado
    requires_2fa = two_factor_auth.is_2fa_enabled(user_id)
    
    if requires_2fa:
        # Gerar token temporário para 2FA
        temp_token = jwt_manager.create_access_token(
            user_id, role, ["2fa_pending"]
        )
        
        return LoginResponse(
            access_token=temp_token,
            refresh_token="",
            expires_in=300,  # 5 minutos para completar 2FA
            requires_2fa=True,
            user_info={
                "user_id": user_id,
                "role": role,
                "2fa_required": True
            }
        )
    
    # Gerar tokens finais
    permissions = _get_user_permissions(role)
    access_token = jwt_manager.create_access_token(user_id, role, permissions)
    refresh_token = jwt_manager.create_refresh_token(user_id)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=900 if role == "admin" else 3600,  # 15min admin, 1h user
        requires_2fa=False,
        user_info={
            "user_id": user_id,
            "role": role,
            "permissions": permissions
        }
    )

@router.post("/2fa/setup")
async def setup_2fa(user: Dict = Depends(get_current_user)):
    """Configurar 2FA para usuário"""
    user_id = user["user_id"]
    
    # Verificar se 2FA já está habilitado
    if two_factor_auth.is_2fa_enabled(user_id):
        raise HTTPException(
            status_code=400,
            detail="2FA already enabled for this user"
        )
    
    # Gerar secret e QR code
    secret = two_factor_auth.generate_secret(user_id)
    
    # Mock email - em produção buscar do banco
    user_email = f"{user_id}@whatsapp-agent.com"
    qr_code = two_factor_auth.generate_qr_code(user_id, user_email, secret)
    
    return TwoFactorSetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=[]  # Será gerado após confirmação
    )

@router.post("/2fa/confirm")
async def confirm_2fa(
    request: TwoFactorVerifyRequest,
    user: Dict = Depends(get_current_user)
):
    """Confirmar configuração de 2FA"""
    user_id = user["user_id"]
    
    success, backup_codes = two_factor_auth.confirm_2fa_setup(user_id, request.code)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid 2FA code"
        )
    
    return {
        "message": "2FA enabled successfully",
        "backup_codes": backup_codes
    }

@router.post("/2fa/verify")
async def verify_2fa(
    request: TwoFactorVerifyRequest,
    user: Dict = Depends(get_current_user)
):
    """Verificar código 2FA e completar login"""
    user_id = user["user_id"]
    
    # Verificar se está em estado de 2FA pendente
    if "2fa_pending" not in user.get("permissions", []):
        raise HTTPException(
            status_code=400,
            detail="2FA verification not required"
        )
    
    # Verificar código
    success = False
    if request.type == "totp":
        success = two_factor_auth.verify_totp(user_id, request.code)
    elif request.type == "backup":
        success = two_factor_auth.verify_backup_code(user_id, request.code)
    
    if not success:
        raise HTTPException(
            status_code=401,
            detail="Invalid 2FA code"
        )
    
    # Gerar tokens finais
    role = user["role"]
    permissions = _get_user_permissions(role)
    access_token = jwt_manager.create_access_token(user_id, role, permissions)
    refresh_token = jwt_manager.create_refresh_token(user_id)
    
    # Criar sessão 2FA
    session_token = secrets.token_urlsafe(32)
    session_key = f"2fa_session:{user_id}:{session_token}"
    rate_limiter.redis_client.setex(session_key, 3600, "valid")  # 1 hora
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900 if role == "admin" else 3600,
        "2fa_session": session_token
    }

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """Renovar access token usando refresh token"""
    try:
        access_token, new_refresh_token = jwt_manager.refresh_access_token(
            request.refresh_token
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 3600
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid refresh token: {str(e)}"
        )

@router.post("/revoke")
async def revoke_token(
    request: RevokeTokenRequest,
    user: Dict = Depends(get_current_user)
):
    """Revogar token específico ou todos os tokens do usuário"""
    
    if request.revoke_all:
        # Revogar todos os tokens do usuário
        count = jwt_manager.revoke_all_user_tokens(user["user_id"])
        return {
            "message": f"Revoked {count} tokens",
            "revoked_count": count
        }
    else:
        # Revogar token específico
        success = jwt_manager.revoke_token(request.token)
        if success:
            return {"message": "Token revoked successfully"}
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid token or already revoked"
            )

@router.post("/revoke-all")
async def revoke_all_tokens(user: Dict = Depends(require_admin)):
    """Revogar TODOS os tokens expostos (emergência)"""
    
    # Forçar rotação do JWT secret
    secrets_manager.rotate_secret("jwt_secret")
    
    # Isso invalidará TODOS os tokens JWT existentes
    return {
        "message": "All JWT tokens revoked by rotating secret",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/status")
async def auth_status(user: Dict = Depends(get_current_user)):
    """Status da autenticação do usuário atual"""
    user_id = user["user_id"]
    
    # Obter status do 2FA
    twofa_status = two_factor_auth.get_2fa_status(user_id)
    
    # Obter informações do token
    return {
        "user_id": user_id,
        "role": user["role"],
        "permissions": user["permissions"],
        "2fa": twofa_status,
        "token_id": user["token_id"]
    }

@router.get("/2fa/backup-codes")
async def get_backup_codes_count(user: Dict = Depends(get_current_user)):
    """Obter quantidade de códigos de backup restantes"""
    user_id = user["user_id"]
    count = two_factor_auth.get_backup_codes_count(user_id)
    
    return {
        "backup_codes_remaining": count,
        "low_backup_codes": count <= 2
    }

@router.post("/2fa/regenerate-backup-codes")
async def regenerate_backup_codes(user: Dict = Depends(require_2fa)):
    """Regenerar códigos de backup"""
    user_id = user["user_id"]
    backup_codes = two_factor_auth.regenerate_backup_codes(user_id)
    
    return {
        "backup_codes": backup_codes,
        "message": "New backup codes generated. Store them safely!"
    }

@router.delete("/2fa/disable")
async def disable_2fa(user: Dict = Depends(require_admin)):
    """Desabilitar 2FA (apenas admins)"""
    user_id = user["user_id"]
    
    success = two_factor_auth.disable_2fa(user_id)
    
    if success:
        return {"message": "2FA disabled successfully"}
    else:
        raise HTTPException(
            status_code=400,
            detail="2FA not enabled for this user"
        )

@router.get("/rate-limit/status")
async def rate_limit_status(
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """Status atual dos rate limits"""
    return rate_limiter.get_rate_limit_status(request, user["user_id"])

@router.get("/security/events")
async def security_events(
    limit: int = 50,
    user: Dict = Depends(require_admin)
):
    """Eventos de segurança recentes"""
    events = rate_limiter.get_security_events(limit)
    return {"events": events}

# Funções auxiliares
async def _verify_credentials(username: str, password: str) -> tuple[Optional[str], Optional[str]]:
    """Verificar credenciais do usuário (mock)"""
    # Em produção, verificar no banco de dados com hash
    
    # Mock de usuários
    users = {
        "admin": {
            "password_hash": hashlib.sha256("SECURE_PASSWORD_FROM_ENV".encode()).hexdigest(),
            "role": "admin"
        },
        "user": {
            "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
            "role": "user"
        }
    }
    
    user_data = users.get(username)
    if not user_data:
        return None, None
    
    # Verificar senha (usar bcrypt em produção)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user_data["password_hash"]:
        return None, None
    
    return username, user_data["role"]

def _get_user_permissions(role: str) -> List[str]:
    """Obter permissões baseadas no role"""
    if role == "admin":
        return [
            "read", "write", "delete", "admin", 
            "user_management", "api_access", "secrets_management"
        ]
    elif role == "user":
        return ["read", "api_access"]
    else:
        return ["read"]
