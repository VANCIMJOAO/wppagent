"""
JWT Manager Simplificado para Railway
=====================================

Versão simplificada sem Redis e rotação complexa
para garantir compatibilidade no ambiente Railway.
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

# OB-001: Logs estruturados
from app.utils.structured_logger import get_structured_logger

logger = get_structured_logger("jwt-manager")


class SimpleJWTManager:
    """JWT Manager simplificado para Railway"""

    def __init__(self):
        # Secret fixo das variáveis de ambiente (sem rotação)
        self.secret_key = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "fallback-secret-key"
        self.algorithm = "HS256"

        logger.info(
            "jwt_manager_initialized",
            algorithm=self.algorithm,
            secret_length=len(self.secret_key),
            secret_preview=self.secret_key[:10] + "...",
        )

        # Configurações de tempo para refresh tokens
        self.access_token_expire = timedelta(
            hours=2
        )  # 2 horas (mais tempo para evitar logout frequente)
        self.refresh_token_expire = timedelta(days=30)  # 30 dias

    def create_access_token(
        self, user_id: str, role: str = "admin", permissions: list = None
    ) -> str:
        """Cria token de acesso compatível com middleware"""
        if permissions is None:
            permissions = ["read", "write", "admin"] if role == "admin" else ["read"]

        now = datetime.now(timezone.utc)

        payload = {
            "sub": user_id,
            "role": role,
            "permissions": permissions,
            "type": "access",  # Campo obrigatório para middleware
            "iat": now,
            "exp": now + self.access_token_expire,
            "jti": str(uuid.uuid4()),  # JWT ID único obrigatório
            "iss": "whatsapp-agent",
            "aud": "whatsapp-agent-api",
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        logger.info(
            "access_token_created",
            user_id=user_id,
            role=role,
            permissions_count=len(permissions) if permissions else 0,
            token_preview=token[:20] + "...",
            expires_in_minutes=self.access_token_expire.total_seconds() / 60,
            jti=payload["jti"],
        )

        return token

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifica token de forma simplificada"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                # Removendo audience/issuer para máxima compatibilidade
                options={"verify_aud": False, "verify_iss": False},
            )

            logger.info(
                "token_verified",
                user_id=payload.get("sub"),
                role=payload.get("role"),
                token_type=payload.get("type"),
                jti=payload.get("jti"),
            )

            return payload

        except jwt.ExpiredSignatureError:
            logger.warning(
                "token_expired", token_preview=token[:20] + "..." if token else "empty"
            )
            raise jwt.InvalidTokenError("Token expirado")
        except jwt.InvalidTokenError as e:
            logger.error(
                "token_invalid",
                error_type=type(e).__name__,
                error_message=str(e),
                token_preview=token[:20] + "..." if token else "empty",
            )
            raise jwt.InvalidTokenError(f"Token inválido: {str(e)}")

    def create_refresh_token(self, user_id: str) -> str:
        """Cria token de refresh"""
        now = datetime.now(timezone.utc)

        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + self.refresh_token_expire,
            "jti": str(uuid.uuid4()),
            "iss": "whatsapp-agent",
            "aud": "whatsapp-agent-api",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def get_token_info(self, token: str) -> Dict[str, Any]:
        """Obtém informações do token"""
        try:
            payload = self.verify_token(token)

            return {
                "valid": True,
                "user_id": payload.get("sub"),
                "role": payload.get("role"),
                "permissions": payload.get("permissions", []),
                "type": payload.get("type"),
                "expires_at": payload.get("exp"),
                "token_id": payload.get("jti"),
            }

        except jwt.InvalidTokenError as e:
            return {"valid": False, "error": str(e)}

    def get_current_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do usuário atual a partir do token (para WebSocket)"""
        try:
            payload = self.verify_token(token)
            return {
                "id": payload.get("sub"),
                "user_id": payload.get("sub"),
                "role": payload.get("role", "user"),
                "permissions": payload.get("permissions", []),
            }
        except jwt.InvalidTokenError:
            return None


# Instância global simplificada
jwt_manager = SimpleJWTManager()


# Função global para compatibilidade
def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Função global para compatibilidade com WebSocket"""
    return jwt_manager.get_current_user_from_token(token)
