"""
Secrets Manager para gerenciamento seguro de tokens e chaves
Implementa rotação automática, versionamento e auditoria
"""

import os
import json
import hashlib
import secrets
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
from app.config import get_settings

class SecretType(Enum):
    """Tipos de secrets"""
    API_KEY = "api_key"
    JWT_SECRET = "jwt_secret"
    WEBHOOK_SECRET = "webhook_secret"
    DATABASE_PASSWORD = "database_password"
    ENCRYPTION_KEY = "encryption_key"
    WHATSAPP_TOKEN = "whatsapp_token"
    ADMIN_PASSWORD = "admin_password"

@dataclass
class Secret:
    """Estrutura de um secret"""
    id: str
    type: SecretType
    value: str
    version: int
    created_at: datetime
    expires_at: Optional[datetime]
    rotated_at: Optional[datetime]
    metadata: Dict[str, Any]
    active: bool

class SecretsManager:
    """Manager para secrets com rotação automática"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = redis.from_url(self.settings.redis_url)
        
        # Configurar criptografia
        self.master_key = self._derive_master_key()
        self.cipher = Fernet(self.master_key)
        
        # Configurações de rotação por tipo
        self.rotation_intervals = {
            SecretType.JWT_SECRET: timedelta(days=1),
            SecretType.WEBHOOK_SECRET: timedelta(days=30),
            SecretType.API_KEY: timedelta(days=90),
            SecretType.WHATSAPP_TOKEN: timedelta(days=180),
            SecretType.ENCRYPTION_KEY: timedelta(days=365),
            SecretType.DATABASE_PASSWORD: timedelta(days=90),
            SecretType.ADMIN_PASSWORD: timedelta(days=30)
        }
        
        # Configurações de retenção de versões
        self.version_retention = {
            SecretType.JWT_SECRET: 3,      # Manter 3 versões
            SecretType.WEBHOOK_SECRET: 2,  # Manter 2 versões  
            SecretType.API_KEY: 5,         # Manter 5 versões
            SecretType.WHATSAPP_TOKEN: 2,  # Manter 2 versões
            SecretType.ENCRYPTION_KEY: 10, # Manter 10 versões
            SecretType.DATABASE_PASSWORD: 3,
            SecretType.ADMIN_PASSWORD: 3
        }
    
    def _derive_master_key(self) -> bytes:
        """Deriva a chave mestra a partir da configuração"""
        password = self.settings.secret_key.get_secret_value().encode()
        salt = b"whatsapp_agent_secrets_salt_2024"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def create_secret(self, secret_id: str, secret_type: SecretType, 
                     value: Optional[str] = None, metadata: Dict = None) -> Secret:
        """Cria novo secret"""
        if metadata is None:
            metadata = {}
        
        # Gerar valor se não fornecido
        if value is None:
            value = self._generate_secret_value(secret_type)
        
        # Calcular expiração
        rotation_interval = self.rotation_intervals.get(secret_type)
        expires_at = None
        if rotation_interval:
            expires_at = datetime.now(timezone.utc) + rotation_interval
        
        # Criar secret
        secret = Secret(
            id=secret_id,
            type=secret_type,
            value=value,
            version=1,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            rotated_at=None,
            metadata=metadata,
            active=True
        )
        
        # Salvar no Redis
        self._save_secret(secret)
        
        # Log de auditoria
        self._log_audit("secret_created", secret_id, {
            "type": secret_type.value,
            "version": 1
        })
        
        return secret
    
    def get_secret(self, secret_id: str, version: Optional[int] = None) -> Optional[Secret]:
        """Obtém secret (versão ativa ou específica)"""
        if version is None:
            # Buscar versão ativa
            active_version = self.redis_client.get(f"secrets:active:{secret_id}")
            if not active_version:
                return None
            version = int(active_version.decode())
        
        # Buscar versão específica
        secret_data = self.redis_client.get(f"secrets:data:{secret_id}:v{version}")
        if not secret_data:
            return None
        
        # Descriptografar e deserializar
        decrypted_data = self.cipher.decrypt(secret_data)
        secret_dict = json.loads(decrypted_data.decode())
        
        # Converter de volta para Secret
        secret_dict["type"] = SecretType(secret_dict["type"])
        secret_dict["created_at"] = datetime.fromisoformat(secret_dict["created_at"])
        
        if secret_dict["expires_at"]:
            secret_dict["expires_at"] = datetime.fromisoformat(secret_dict["expires_at"])
        
        if secret_dict["rotated_at"]:
            secret_dict["rotated_at"] = datetime.fromisoformat(secret_dict["rotated_at"])
        
        return Secret(**secret_dict)
    
    def rotate_secret(self, secret_id: str, new_value: Optional[str] = None) -> Secret:
        """Rotaciona secret criando nova versão"""
        current_secret = self.get_secret(secret_id)
        if not current_secret:
            raise ValueError(f"Secret {secret_id} não encontrado")
        
        # Gerar novo valor
        if new_value is None:
            new_value = self._generate_secret_value(current_secret.type)
        
        # Criar nova versão
        new_version = current_secret.version + 1
        expires_at = None
        rotation_interval = self.rotation_intervals.get(current_secret.type)
        if rotation_interval:
            expires_at = datetime.now(timezone.utc) + rotation_interval
        
        new_secret = Secret(
            id=secret_id,
            type=current_secret.type,
            value=new_value,
            version=new_version,
            created_at=current_secret.created_at,
            expires_at=expires_at,
            rotated_at=datetime.now(timezone.utc),
            metadata=current_secret.metadata.copy(),
            active=True
        )
        
        # Desativar versão anterior
        current_secret.active = False
        self._save_secret(current_secret)
        
        # Salvar nova versão
        self._save_secret(new_secret)
        
        # Atualizar versão ativa
        self.redis_client.set(f"secrets:active:{secret_id}", new_version)
        
        # Limpar versões antigas
        self._cleanup_old_versions(secret_id, current_secret.type)
        
        # Log de auditoria
        self._log_audit("secret_rotated", secret_id, {
            "old_version": current_secret.version,
            "new_version": new_version
        })
        
        return new_secret
    
    def revoke_secret(self, secret_id: str, version: Optional[int] = None) -> bool:
        """Revoga secret ou versão específica"""
        if version is None:
            # Revogar todas as versões
            versions = self._get_all_versions(secret_id)
            revoked_count = 0
            
            for v in versions:
                secret = self.get_secret(secret_id, v)
                if secret:
                    secret.active = False
                    self._save_secret(secret)
                    revoked_count += 1
            
            # Remover versão ativa
            self.redis_client.delete(f"secrets:active:{secret_id}")
            
            self._log_audit("secret_revoked_all", secret_id, {
                "versions_revoked": revoked_count
            })
            
            return revoked_count > 0
        else:
            # Revogar versão específica
            secret = self.get_secret(secret_id, version)
            if not secret:
                return False
            
            secret.active = False
            self._save_secret(secret)
            
            # Se era a versão ativa, encontrar próxima ativa
            if self._is_active_version(secret_id, version):
                self._update_active_version(secret_id)
            
            self._log_audit("secret_revoked", secret_id, {
                "version": version
            })
            
            return True
    
    def check_expiring_secrets(self, days_ahead: int = 7) -> List[Dict]:
        """Verifica secrets que expiram em X dias"""
        expiring = []
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        # Buscar todos os secrets ativos
        active_keys = self.redis_client.keys("secrets:active:*")
        
        for key in active_keys:
            secret_id = key.decode().split(":")[-1]
            secret = self.get_secret(secret_id)
            
            if secret and secret.expires_at and secret.expires_at <= cutoff_date:
                expiring.append({
                    "id": secret_id,
                    "type": secret.type.value,
                    "expires_at": secret.expires_at.isoformat(),
                    "days_remaining": (secret.expires_at - datetime.now(timezone.utc)).days
                })
        
        return expiring
    
    def auto_rotate_expired_secrets(self) -> List[str]:
        """Rotaciona automaticamente secrets expirados"""
        rotated = []
        now = datetime.now(timezone.utc)
        
        # Buscar secrets expirados
        active_keys = self.redis_client.keys("secrets:active:*")
        
        for key in active_keys:
            secret_id = key.decode().split(":")[-1]
            secret = self.get_secret(secret_id)
            
            if (secret and secret.expires_at and 
                secret.expires_at <= now and secret.active):
                
                try:
                    self.rotate_secret(secret_id)
                    rotated.append(secret_id)
                    
                    self._log_audit("secret_auto_rotated", secret_id, {
                        "expired_at": secret.expires_at.isoformat()
                    })
                    
                except Exception as e:
                    self._log_audit("secret_rotation_failed", secret_id, {
                        "error": str(e)
                    })
        
        return rotated
    
    def list_secrets(self, secret_type: Optional[SecretType] = None) -> List[Dict]:
        """Lista todos os secrets (sem valores)"""
        secrets = []
        active_keys = self.redis_client.keys("secrets:active:*")
        
        for key in active_keys:
            secret_id = key.decode().split(":")[-1]
            secret = self.get_secret(secret_id)
            
            if secret and (secret_type is None or secret.type == secret_type):
                secrets.append({
                    "id": secret_id,
                    "type": secret.type.value,
                    "version": secret.version,
                    "created_at": secret.created_at.isoformat(),
                    "expires_at": secret.expires_at.isoformat() if secret.expires_at else None,
                    "rotated_at": secret.rotated_at.isoformat() if secret.rotated_at else None,
                    "active": secret.active,
                    "metadata": secret.metadata
                })
        
        return secrets
    
    def _save_secret(self, secret: Secret):
        """Salva secret criptografado no Redis"""
        # Serializar para JSON
        secret_dict = asdict(secret)
        secret_dict["type"] = secret.type.value
        secret_dict["created_at"] = secret.created_at.isoformat()
        
        if secret.expires_at:
            secret_dict["expires_at"] = secret.expires_at.isoformat()
        
        if secret.rotated_at:
            secret_dict["rotated_at"] = secret.rotated_at.isoformat()
        
        # Criptografar
        encrypted_data = self.cipher.encrypt(json.dumps(secret_dict).encode())
        
        # Salvar no Redis
        key = f"secrets:data:{secret.id}:v{secret.version}"
        self.redis_client.set(key, encrypted_data)
        
        # Atualizar versão ativa se necessário
        if secret.active:
            self.redis_client.set(f"secrets:active:{secret.id}", secret.version)
    
    def _generate_secret_value(self, secret_type: SecretType) -> str:
        """Gera valor apropriado para tipo de secret"""
        if secret_type == SecretType.JWT_SECRET:
            return secrets.token_urlsafe(64)
        elif secret_type == SecretType.API_KEY:
            return f"sk_{secrets.token_urlsafe(32)}"
        elif secret_type == SecretType.WEBHOOK_SECRET:
            return secrets.token_hex(32)
        elif secret_type == SecretType.ENCRYPTION_KEY:
            return secrets.token_urlsafe(32)
        elif secret_type in [SecretType.ADMIN_PASSWORD, SecretType.DATABASE_PASSWORD]:
            # Senha complexa
            chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
            return ''.join(secrets.choice(chars) for _ in range(16))
        else:
            return secrets.token_urlsafe(32)
    
    def _get_all_versions(self, secret_id: str) -> List[int]:
        """Obtém todas as versões de um secret"""
        pattern = f"secrets:data:{secret_id}:v*"
        keys = self.redis_client.keys(pattern)
        
        versions = []
        for key in keys:
            version_str = key.decode().split(":v")[-1]
            versions.append(int(version_str))
        
        return sorted(versions)
    
    def _cleanup_old_versions(self, secret_id: str, secret_type: SecretType):
        """Remove versões antigas baseado na política de retenção"""
        max_versions = self.version_retention.get(secret_type, 3)
        versions = self._get_all_versions(secret_id)
        
        if len(versions) > max_versions:
            # Manter apenas as versões mais recentes
            versions_to_delete = versions[:-max_versions]
            
            for version in versions_to_delete:
                key = f"secrets:data:{secret_id}:v{version}"
                self.redis_client.delete(key)
    
    def _is_active_version(self, secret_id: str, version: int) -> bool:
        """Verifica se é a versão ativa"""
        active_version = self.redis_client.get(f"secrets:active:{secret_id}")
        return active_version and int(active_version.decode()) == version
    
    def _update_active_version(self, secret_id: str):
        """Atualiza versão ativa para a mais recente ativa"""
        versions = self._get_all_versions(secret_id)
        
        # Buscar versão mais recente que ainda está ativa
        for version in reversed(versions):
            secret = self.get_secret(secret_id, version)
            if secret and secret.active:
                self.redis_client.set(f"secrets:active:{secret_id}", version)
                return
        
        # Nenhuma versão ativa encontrada
        self.redis_client.delete(f"secrets:active:{secret_id}")
    
    def _log_audit(self, action: str, secret_id: str, details: Dict):
        """Log de auditoria"""
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "secret_id": secret_id,
            "details": details
        }
        
        # Salvar no Redis
        self.redis_client.lpush("secrets:audit", json.dumps(audit_entry))
        self.redis_client.ltrim("secrets:audit", 0, 10000)  # Manter últimos 10k eventos
    
    def get_audit_log(self, secret_id: Optional[str] = None, 
                     limit: int = 100) -> List[Dict]:
        """Obtém log de auditoria"""
        entries = self.redis_client.lrange("secrets:audit", 0, limit - 1)
        audit_log = [json.loads(entry.decode()) for entry in entries]
        
        if secret_id:
            audit_log = [entry for entry in audit_log 
                        if entry.get("secret_id") == secret_id]
        
        return audit_log


# Instance global
secrets_manager = SecretsManager()
