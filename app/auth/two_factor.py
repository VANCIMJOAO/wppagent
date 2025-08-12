"""
Sistema de 2FA (Two-Factor Authentication) obrigatório para administradores
Implementa TOTP (Time-based One-Time Password) e códigos de backup
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import redis
import json
from app.config import get_settings

class TwoFactorAuth:
    """Sistema de autenticação de dois fatores"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client = redis.from_url(self.settings.redis_url)
        self.issuer_name = "WhatsApp Agent"
        
        # Configurações de segurança
        self.totp_window = 1  # Janela de tempo (30s antes/depois)
        self.backup_codes_count = 10
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutos
    
    def generate_secret(self, user_id: str) -> str:
        """Gera secret TOTP para um usuário"""
        secret = pyotp.random_base32()
        
        # Salvar secret no Redis
        self.redis_client.setex(
            f"2fa:secret:{user_id}",
            3600,  # 1 hora para confirmação inicial
            json.dumps({
                "secret": secret,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "confirmed": False
            })
        )
        
        return secret
    
    def generate_qr_code(self, user_id: str, user_email: str, secret: str) -> str:
        """Gera QR Code para configuração do 2FA"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        # Gerar QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Converter para base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{qr_base64}"
    
    def confirm_2fa_setup(self, user_id: str, totp_code: str) -> Tuple[bool, List[str]]:
        """Confirma configuração do 2FA com código TOTP"""
        secret_data = self.redis_client.get(f"2fa:secret:{user_id}")
        if not secret_data:
            return False, []
        
        secret_info = json.loads(secret_data.decode())
        secret = secret_info["secret"]
        
        # Verificar código TOTP
        totp = pyotp.TOTP(secret)
        if not totp.verify(totp_code, valid_window=self.totp_window):
            return False, []
        
        # Gerar códigos de backup
        backup_codes = self._generate_backup_codes()
        
        # Salvar configuração permanente
        self.redis_client.set(
            f"2fa:user:{user_id}",
            json.dumps({
                "secret": secret,
                "backup_codes": [self._hash_backup_code(code) for code in backup_codes],
                "enabled": True,
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
                "failed_attempts": 0
            })
        )
        
        # Remover secret temporário
        self.redis_client.delete(f"2fa:secret:{user_id}")
        
        return True, backup_codes
    
    def verify_totp(self, user_id: str, totp_code: str) -> bool:
        """Verifica código TOTP"""
        if self._is_user_locked(user_id):
            return False
        
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa or not user_2fa.get("enabled"):
            return False
        
        secret = user_2fa["secret"]
        totp = pyotp.TOTP(secret)
        
        if totp.verify(totp_code, valid_window=self.totp_window):
            self._reset_failed_attempts(user_id)
            return True
        else:
            self._increment_failed_attempts(user_id)
            return False
    
    def verify_backup_code(self, user_id: str, backup_code: str) -> bool:
        """Verifica código de backup"""
        if self._is_user_locked(user_id):
            return False
        
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa or not user_2fa.get("enabled"):
            return False
        
        hashed_code = self._hash_backup_code(backup_code)
        backup_codes = user_2fa.get("backup_codes", [])
        
        if hashed_code in backup_codes:
            # Remover código usado
            backup_codes.remove(hashed_code)
            user_2fa["backup_codes"] = backup_codes
            
            self.redis_client.set(
                f"2fa:user:{user_id}",
                json.dumps(user_2fa)
            )
            
            self._reset_failed_attempts(user_id)
            return True
        else:
            self._increment_failed_attempts(user_id)
            return False
    
    def is_2fa_enabled(self, user_id: str) -> bool:
        """Verifica se 2FA está habilitado para o usuário"""
        user_2fa = self._get_user_2fa(user_id)
        return user_2fa and user_2fa.get("enabled", False)
    
    def disable_2fa(self, user_id: str) -> bool:
        """Desabilita 2FA para um usuário"""
        if self.redis_client.exists(f"2fa:user:{user_id}"):
            self.redis_client.delete(f"2fa:user:{user_id}")
            return True
        return False
    
    def regenerate_backup_codes(self, user_id: str) -> List[str]:
        """Regenera códigos de backup"""
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa:
            return []
        
        # Gerar novos códigos
        backup_codes = self._generate_backup_codes()
        user_2fa["backup_codes"] = [self._hash_backup_code(code) for code in backup_codes]
        user_2fa["backup_codes_regenerated_at"] = datetime.now(timezone.utc).isoformat()
        
        self.redis_client.set(
            f"2fa:user:{user_id}",
            json.dumps(user_2fa)
        )
        
        return backup_codes
    
    def get_backup_codes_count(self, user_id: str) -> int:
        """Retorna quantidade de códigos de backup disponíveis"""
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa:
            return 0
        
        return len(user_2fa.get("backup_codes", []))
    
    def _generate_backup_codes(self) -> List[str]:
        """Gera códigos de backup aleatórios"""
        codes = []
        for _ in range(self.backup_codes_count):
            # Gerar código de 8 dígitos
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)
        
        return codes
    
    def _hash_backup_code(self, code: str) -> str:
        """Hash do código de backup para armazenamento seguro"""
        salt = self.settings.secret_key.get_secret_value().encode()
        return hashlib.pbkdf2_hmac('sha256', code.encode(), salt, 100000).hex()
    
    def _get_user_2fa(self, user_id: str) -> Optional[Dict]:
        """Busca configurações 2FA do usuário"""
        data = self.redis_client.get(f"2fa:user:{user_id}")
        if data:
            return json.loads(data.decode())
        return None
    
    def _is_user_locked(self, user_id: str) -> bool:
        """Verifica se usuário está bloqueado por tentativas falhadas"""
        lockout_key = f"2fa:lockout:{user_id}"
        return self.redis_client.exists(lockout_key)
    
    def _increment_failed_attempts(self, user_id: str):
        """Incrementa tentativas falhadas"""
        user_2fa = self._get_user_2fa(user_id)
        if not user_2fa:
            return
        
        failed_attempts = user_2fa.get("failed_attempts", 0) + 1
        user_2fa["failed_attempts"] = failed_attempts
        user_2fa["last_failed_attempt"] = datetime.now(timezone.utc).isoformat()
        
        self.redis_client.set(
            f"2fa:user:{user_id}",
            json.dumps(user_2fa)
        )
        
        # Bloquear se excedeu limite
        if failed_attempts >= self.max_failed_attempts:
            self.redis_client.setex(
                f"2fa:lockout:{user_id}",
                self.lockout_duration,
                "locked"
            )
    
    def _reset_failed_attempts(self, user_id: str):
        """Reseta tentativas falhadas"""
        user_2fa = self._get_user_2fa(user_id)
        if user_2fa:
            user_2fa["failed_attempts"] = 0
            if "last_failed_attempt" in user_2fa:
                del user_2fa["last_failed_attempt"]
            
            self.redis_client.set(
                f"2fa:user:{user_id}",
                json.dumps(user_2fa)
            )
        
        # Remover lockout se existir
        self.redis_client.delete(f"2fa:lockout:{user_id}")
    
    def get_2fa_status(self, user_id: str) -> Dict:
        """Retorna status completo do 2FA para o usuário"""
        user_2fa = self._get_user_2fa(user_id)
        
        if not user_2fa:
            return {
                "enabled": False,
                "setup_required": True
            }
        
        return {
            "enabled": user_2fa.get("enabled", False),
            "confirmed_at": user_2fa.get("confirmed_at"),
            "backup_codes_count": len(user_2fa.get("backup_codes", [])),
            "failed_attempts": user_2fa.get("failed_attempts", 0),
            "locked": self._is_user_locked(user_id),
            "setup_required": False
        }


# Instance global
two_factor_auth = TwoFactorAuth()
