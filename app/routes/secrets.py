"""
Rotas para gerenciamento de secrets
Implementa CRUD, rotação automática e auditoria de secrets
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone

from ..auth.secrets_manager import secrets_manager, SecretType
from ..auth.middleware import require_admin

router = APIRouter(prefix="/secrets", tags=["Secrets Management"])

# Modelos Pydantic
class CreateSecretRequest(BaseModel):
    secret_id: str
    secret_type: str
    value: Optional[str] = None
    metadata: Optional[Dict] = None

class RotateSecretRequest(BaseModel):
    new_value: Optional[str] = None

class SecretResponse(BaseModel):
    id: str
    type: str
    version: int
    created_at: str
    expires_at: Optional[str]
    rotated_at: Optional[str]
    active: bool
    metadata: Dict

@router.post("/create")
async def create_secret(
    request: CreateSecretRequest,
    user: Dict = Depends(require_admin)
):
    """Criar novo secret"""
    try:
        secret_type = SecretType(request.secret_type)
    except ValueError:
        valid_types = [t.value for t in SecretType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid secret type. Valid types: {valid_types}"
        )
    
    # Verificar se secret já existe
    existing = secrets_manager.get_secret(request.secret_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Secret {request.secret_id} already exists"
        )
    
    secret = secrets_manager.create_secret(
        request.secret_id,
        secret_type,
        request.value,
        request.metadata or {}
    )
    
    return {
        "message": "Secret created successfully",
        "secret_id": secret.id,
        "version": secret.version,
        "expires_at": secret.expires_at.isoformat() if secret.expires_at else None
    }

@router.get("/list")
async def list_secrets(
    secret_type: Optional[str] = None,
    user: Dict = Depends(require_admin)
):
    """Listar todos os secrets (sem valores)"""
    type_filter = None
    if secret_type:
        try:
            type_filter = SecretType(secret_type)
        except ValueError:
            valid_types = [t.value for t in SecretType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid secret type. Valid types: {valid_types}"
            )
    
    secrets = secrets_manager.list_secrets(type_filter)
    return {"secrets": secrets}

@router.get("/{secret_id}")
async def get_secret_info(
    secret_id: str,
    version: Optional[int] = None,
    user: Dict = Depends(require_admin)
):
    """Obter informações de um secret (sem o valor)"""
    secret = secrets_manager.get_secret(secret_id, version)
    
    if not secret:
        raise HTTPException(
            status_code=404,
            detail=f"Secret {secret_id} not found"
        )
    
    return SecretResponse(
        id=secret.id,
        type=secret.type.value,
        version=secret.version,
        created_at=secret.created_at.isoformat(),
        expires_at=secret.expires_at.isoformat() if secret.expires_at else None,
        rotated_at=secret.rotated_at.isoformat() if secret.rotated_at else None,
        active=secret.active,
        metadata=secret.metadata
    )

@router.get("/{secret_id}/value")
async def get_secret_value(
    secret_id: str,
    version: Optional[int] = None,
    user: Dict = Depends(require_admin)
):
    """Obter valor de um secret (operação sensível)"""
    secret = secrets_manager.get_secret(secret_id, version)
    
    if not secret:
        raise HTTPException(
            status_code=404,
            detail=f"Secret {secret_id} not found"
        )
    
    # Log de auditoria para acesso ao valor
    secrets_manager._log_audit("secret_value_accessed", secret_id, {
        "accessed_by": user["user_id"],
        "version": secret.version
    })
    
    return {
        "secret_id": secret.id,
        "value": secret.value,
        "version": secret.version,
        "warning": "This value should be stored securely and not logged"
    }

@router.post("/{secret_id}/rotate")
async def rotate_secret(
    secret_id: str,
    request: RotateSecretRequest,
    background_tasks: BackgroundTasks,
    user: Dict = Depends(require_admin)
):
    """Rotacionar secret criando nova versão"""
    secret = secrets_manager.get_secret(secret_id)
    
    if not secret:
        raise HTTPException(
            status_code=404,
            detail=f"Secret {secret_id} not found"
        )
    
    new_secret = secrets_manager.rotate_secret(secret_id, request.new_value)
    
    # Agendar notificação para aplicações dependentes
    background_tasks.add_task(
        _notify_secret_rotation,
        secret_id,
        secret.version,
        new_secret.version
    )
    
    return {
        "message": "Secret rotated successfully",
        "old_version": secret.version,
        "new_version": new_secret.version,
        "expires_at": new_secret.expires_at.isoformat() if new_secret.expires_at else None
    }

@router.delete("/{secret_id}")
async def revoke_secret(
    secret_id: str,
    version: Optional[int] = None,
    user: Dict = Depends(require_admin)
):
    """Revogar secret ou versão específica"""
    success = secrets_manager.revoke_secret(secret_id, version)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Secret {secret_id} not found or already revoked"
        )
    
    if version:
        return {
            "message": f"Secret {secret_id} version {version} revoked successfully"
        }
    else:
        return {
            "message": f"All versions of secret {secret_id} revoked successfully"
        }

@router.get("/expiring/check")
async def check_expiring_secrets(
    days_ahead: int = 7,
    user: Dict = Depends(require_admin)
):
    """Verificar secrets que expiram em X dias"""
    expiring = secrets_manager.check_expiring_secrets(days_ahead)
    
    return {
        "expiring_secrets": expiring,
        "count": len(expiring),
        "days_ahead": days_ahead
    }

@router.post("/expiring/auto-rotate")
async def auto_rotate_expired(
    background_tasks: BackgroundTasks,
    user: Dict = Depends(require_admin)
):
    """Rotacionar automaticamente secrets expirados"""
    rotated = secrets_manager.auto_rotate_expired_secrets()
    
    # Agendar notificações
    for secret_id in rotated:
        background_tasks.add_task(_notify_secret_rotation, secret_id, None, None)
    
    return {
        "message": f"Auto-rotated {len(rotated)} expired secrets",
        "rotated_secrets": rotated
    }

@router.get("/{secret_id}/audit")
async def get_secret_audit_log(
    secret_id: str,
    limit: int = 50,
    user: Dict = Depends(require_admin)
):
    """Obter log de auditoria de um secret"""
    audit_log = secrets_manager.get_audit_log(secret_id, limit)
    
    return {
        "secret_id": secret_id,
        "audit_events": audit_log
    }

@router.get("/audit/all")
async def get_all_audit_logs(
    limit: int = 100,
    user: Dict = Depends(require_admin)
):
    """Obter todos os logs de auditoria"""
    audit_log = secrets_manager.get_audit_log(None, limit)
    
    return {
        "audit_events": audit_log,
        "total_events": len(audit_log)
    }

@router.post("/emergency/revoke-all")
async def emergency_revoke_all(
    confirm: str,
    user: Dict = Depends(require_admin)
):
    """Revogação de emergência de TODOS os secrets"""
    if confirm != "EMERGENCY_REVOKE_ALL_SECRETS":
        raise HTTPException(
            status_code=400,
            detail="Invalid confirmation string"
        )
    
    # Obter lista de todos os secrets
    all_secrets = secrets_manager.list_secrets()
    revoked_count = 0
    
    for secret_info in all_secrets:
        success = secrets_manager.revoke_secret(secret_info["id"])
        if success:
            revoked_count += 1
    
    # Log crítico de segurança
    secrets_manager._log_audit("emergency_revoke_all", "ALL_SECRETS", {
        "revoked_by": user["user_id"],
        "revoked_count": revoked_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": "EMERGENCY: All secrets revoked",
        "revoked_count": revoked_count,
        "warning": "All applications using these secrets will stop working"
    }

@router.get("/health/status")
async def secrets_health_status(user: Dict = Depends(require_admin)):
    """Status de saúde do sistema de secrets"""
    # Verificar secrets expirados
    expired = secrets_manager.check_expiring_secrets(0)  # Já expirados
    expiring_soon = secrets_manager.check_expiring_secrets(7)  # Expirando em 7 dias
    
    # Contar secrets por tipo
    all_secrets = secrets_manager.list_secrets()
    by_type = {}
    for secret in all_secrets:
        secret_type = secret["type"]
        by_type[secret_type] = by_type.get(secret_type, 0) + 1
    
    return {
        "total_secrets": len(all_secrets),
        "secrets_by_type": by_type,
        "expired_secrets": len(expired),
        "expiring_soon": len(expiring_soon),
        "health_status": "healthy" if len(expired) == 0 else "warning"
    }

# Funções auxiliares
async def _notify_secret_rotation(secret_id: str, old_version: Optional[int], 
                                new_version: Optional[int]):
    """Notificar aplicações sobre rotação de secret"""
    # Em produção, implementar notificações via webhook, email, etc.
    print(f"SECRET ROTATED: {secret_id} from v{old_version} to v{new_version}")
    
    # Aqui você poderia:
    # 1. Enviar webhook para aplicações dependentes
    # 2. Enviar email para administradores
    # 3. Atualizar sistema de deployment
    # 4. Notificar sistema de monitoramento
