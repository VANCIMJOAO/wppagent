"""
Sistema de JWT com rotação automática de tokens
Implementa refresh tokens, blacklist e rotação de secrets
"""

import jwt
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import json
import redis
from app.config import get_settings

class JWTManager:
    """Manager para JWT com rotação automática e segurança avançada"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = redis.from_url(self.settings.redis_url)
        self.algorithm = "HS256"
        
        # Configurações de tempo
        self.access_token_expire = timedelta(minutes=15)  # 15 min
        self.refresh_token_expire = timedelta(days=7)     # 7 dias
        self.admin_token_expire = timedelta(minutes=5)    # 5 min para admins
        
        # Rotação de secrets
        self.secret_rotation_interval = timedelta(hours=24)  # 24h
        
    def _get_current_secret(self) -> str:
        """Obtém o secret atual com rotação automática"""
        current_time = datetime.now(timezone.utc)
        
        # Verificar se existe secret atual no Redis
        current_secret = self.redis_client.get("jwt:current_secret")
        secret_created = self.redis_client.get("jwt:secret_created")
        
        if current_secret and secret_created:
            created_time = datetime.fromisoformat(secret_created.decode())
            
            # Se o secret ainda é válido, usar ele
            if current_time - created_time < self.secret_rotation_interval:
                return current_secret.decode()
        
        # Gerar novo secret
        new_secret = self._generate_secret()
        
        # Salvar secret anterior como "previous" para validação de tokens antigos
        if current_secret:
            self.redis_client.setex(
                "jwt:previous_secret", 
                int(self.refresh_token_expire.total_seconds()),
                current_secret
            )
        
        # Salvar novo secret
        self.redis_client.set("jwt:current_secret", new_secret)
        self.redis_client.set("jwt:secret_created", current_time.isoformat())
        
        return new_secret
    
    def _generate_secret(self) -> str:
        """Gera um secret criptograficamente seguro"""
        # Combinar múltiplas fontes de entropia
        entropy_sources = [
            os.urandom(32),
            str(datetime.now(timezone.utc).timestamp()).encode(),
            str(uuid.uuid4()).encode(),
            self.settings.secret_key.get_secret_value().encode()
        ]
        
        combined = b''.join(entropy_sources)
        
        # Usar PBKDF2 para derivar o secret final com salt fixo baseado na configuração
        import hashlib
        salt = hashlib.sha256(self.settings.secret_key.get_secret_value().encode()).digest()[:16]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=64,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        derived_key = kdf.derive(combined)
        return derived_key.hex()
    
    def create_access_token(self, user_id: str, role: str = "user", 
                           permissions: list = None) -> str:
        """Cria token de acesso com informações do usuário"""
        if permissions is None:
            permissions = []
            
        now = datetime.now(timezone.utc)
        
        # Token mais curto para admins
        expire_time = (self.admin_token_expire if role == "admin" 
                      else self.access_token_expire)
        
        payload = {
            "sub": user_id,
            "role": role,
            "permissions": permissions,
            "type": "access",
            "iat": now,
            "exp": now + expire_time,
            "jti": str(uuid.uuid4()),  # JWT ID único
            "iss": "whatsapp-agent",
            "aud": "whatsapp-agent-api"
        }
        
        secret = self._get_current_secret()
        return jwt.encode(payload, secret, algorithm=self.algorithm)
    
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
            "aud": "whatsapp-agent-api"
        }
        
        secret = self._get_current_secret()
        token = jwt.encode(payload, secret, algorithm=self.algorithm)
        
        # Salvar refresh token no Redis para controle
        self.redis_client.setex(
            f"refresh_token:{payload['jti']}", 
            int(self.refresh_token_expire.total_seconds()),
            json.dumps({
                "user_id": user_id,
                "created_at": now.isoformat(),
                "active": True
            })
        )
        
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verifica e decodifica token"""
        try:
            # Tentar com secret atual
            secret = self._get_current_secret()
            payload = jwt.decode(
                token, 
                secret, 
                algorithms=[self.algorithm],
                audience="whatsapp-agent-api",
                issuer="whatsapp-agent"
            )
            
        except jwt.InvalidTokenError:
            # Tentar com secret anterior (para tokens emitidos antes da rotação)
            try:
                previous_secret = self.redis_client.get("jwt:previous_secret")
                if previous_secret:
                    payload = jwt.decode(
                        token, 
                        previous_secret.decode(), 
                        algorithms=[self.algorithm],
                        audience="whatsapp-agent-api",
                        issuer="whatsapp-agent"
                    )
                else:
                    raise jwt.InvalidTokenError("Token inválido")
            except jwt.InvalidTokenError:
                raise jwt.InvalidTokenError("Token inválido ou expirado")
        
        # Verificar se token está na blacklist
        jti = payload.get("jti")
        if jti and self.redis_client.exists(f"blacklist:{jti}"):
            raise jwt.InvalidTokenError("Token revogado")
        
        # Verificar se é refresh token e se ainda está ativo
        if payload.get("type") == "refresh":
            refresh_data = self.redis_client.get(f"refresh_token:{jti}")
            if not refresh_data:
                raise jwt.InvalidTokenError("Refresh token inválido")
            
            refresh_info = json.loads(refresh_data.decode())
            if not refresh_info.get("active", False):
                raise jwt.InvalidTokenError("Refresh token revogado")
        
        return payload
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Gera novo access token usando refresh token"""
        try:
            payload = self.verify_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("Token não é refresh token")
            
            user_id = payload["sub"]
            
            # Buscar informações do usuário (role, permissions)
            # Em produção, buscar do banco de dados
            user_info = self._get_user_info(user_id)
            
            # Gerar novos tokens
            new_access_token = self.create_access_token(
                user_id, 
                user_info.get("role", "user"),
                user_info.get("permissions", [])
            )
            
            new_refresh_token = self.create_refresh_token(user_id)
            
            # Revogar refresh token antigo
            self.revoke_token(refresh_token)
            
            return new_access_token, new_refresh_token
            
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Erro ao renovar token: {str(e)}")
    
    def revoke_token(self, token: str) -> bool:
        """Revoga token específico"""
        try:
            payload = self.verify_token(token)
            jti = payload.get("jti")
            
            if not jti:
                return False
            
            # Adicionar à blacklist
            exp = payload.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
                ttl = int((exp_datetime - datetime.now(timezone.utc)).total_seconds())
                
                if ttl > 0:
                    self.redis_client.setex(f"blacklist:{jti}", ttl, "revoked")
            
            # Se for refresh token, marcar como inativo
            if payload.get("type") == "refresh":
                refresh_data = self.redis_client.get(f"refresh_token:{jti}")
                if refresh_data:
                    refresh_info = json.loads(refresh_data.decode())
                    refresh_info["active"] = False
                    self.redis_client.setex(
                        f"refresh_token:{jti}",
                        int(self.refresh_token_expire.total_seconds()),
                        json.dumps(refresh_info)
                    )
            
            return True
            
        except jwt.InvalidTokenError:
            return False
    
    def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoga todos os tokens de um usuário"""
        revoked_count = 0
        
        # Buscar todos os refresh tokens do usuário
        pattern = "refresh_token:*"
        for key in self.redis_client.scan_iter(match=pattern):
            token_data = self.redis_client.get(key)
            if token_data:
                token_info = json.loads(token_data.decode())
                if token_info.get("user_id") == user_id and token_info.get("active"):
                    # Marcar como inativo
                    token_info["active"] = False
                    self.redis_client.setex(
                        key,
                        int(self.refresh_token_expire.total_seconds()),
                        json.dumps(token_info)
                    )
                    revoked_count += 1
        
        return revoked_count
    
    def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Busca informações do usuário (mock - implementar com banco)"""
        # Em produção, buscar do banco de dados
        return {
            "role": "admin" if user_id == "admin" else "user",
            "permissions": ["read", "write"] if user_id == "admin" else ["read"]
        }
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """Obtém informações detalhadas do token"""
        try:
            payload = self.verify_token(token)
            
            return {
                "valid": True,
                "user_id": payload.get("sub"),
                "role": payload.get("role"),
                "permissions": payload.get("permissions", []),
                "type": payload.get("type"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "token_id": payload.get("jti")
            }
            
        except jwt.InvalidTokenError as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def cleanup_expired_tokens(self) -> int:
        """Remove tokens expirados do Redis"""
        cleaned = 0
        
        # Limpar blacklist expirada
        pattern = "blacklist:*"
        for key in self.redis_client.scan_iter(match=pattern):
            if not self.redis_client.exists(key):
                cleaned += 1
        
        # Limpar refresh tokens expirados
        pattern = "refresh_token:*"
        for key in self.redis_client.scan_iter(match=pattern):
            if not self.redis_client.exists(key):
                cleaned += 1
        
        return cleaned


# Instance global
jwt_manager = JWTManager()
