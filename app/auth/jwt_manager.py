"""
JWT Manager Simplificado para Railway
=====================================

Versão simplificada sem Redis e rotação complexa
para garantir compatibilidade no ambiente Railway.
"""

import jwt
import uuid
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any

class SimpleJWTManager:
    """JWT Manager simplificado para Railway"""
    
    def __init__(self):
        # Secret fixo das variáveis de ambiente (sem rotação)
        self.secret_key = os.getenv('JWT_SECRET', os.getenv('SECRET_KEY', 'fallback-secret-key'))
        self.algorithm = "HS256"
        
        print(f"🔧 JWT Manager inicializado com secret: {self.secret_key[:10]}...")
        
        # Configurações de tempo para refresh tokens
        self.access_token_expire = timedelta(minutes=15)  # 15 min (conforme especificação)
        self.refresh_token_expire = timedelta(days=30)     # 30 dias
        
    def create_access_token(self, user_id: str, role: str = "admin", 
                           permissions: list = None) -> str:
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
            "aud": "whatsapp-agent-api"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        print(f"🔑 Token criado para {user_id} ({role}) - {token[:20]}...")
        
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifica token de forma simplificada"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                # Removendo audience/issuer para máxima compatibilidade
                options={"verify_aud": False, "verify_iss": False}
            )
            
            print(f"✅ Token válido para usuário: {payload.get('sub')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            print("❌ Token expirado")
            raise jwt.InvalidTokenError("Token expirado")
        except jwt.InvalidTokenError as e:
            print(f"❌ Token inválido: {e}")
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
                "token_id": payload.get("jti")
            }
            
        except jwt.InvalidTokenError as e:
            return {
                "valid": False,
                "error": str(e)
            }


# Instância global simplificada
jwt_manager = SimpleJWTManager()
