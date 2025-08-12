"""
🔐 Serviço de Criptografia AES-256-GCM
======================================

Sistema robusto para criptografia de dados sensíveis com:
- AES-256-GCM (autenticação + criptografia)
- Derivação de chaves com PBKDF2
- Salts únicos por operação
- Verificação de integridade automática
"""

import os
import base64
import secrets
from typing import Union, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    """Serviço de criptografia AES-256-GCM para dados sensíveis"""
    
    def __init__(self, master_key: str = None):
        """
        Inicializa o serviço de criptografia
        
        Args:
            master_key: Chave mestre base64. Se None, usa variável de ambiente.
        """
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY')
        if not self.master_key:
            raise ValueError("❌ ENCRYPTION_MASTER_KEY não configurada")
        
        # Decodificar chave mestre
        try:
            self.master_key_bytes = base64.urlsafe_b64decode(self.master_key.encode())
        except Exception as e:
            raise ValueError(f"❌ Chave mestre inválida: {e}")
        
        logger.info("✅ Serviço de criptografia inicializado")
    
    def _derive_key(self, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Deriva uma chave de 256 bits usando PBKDF2
        
        Args:
            salt: Salt único para a derivação
            iterations: Número de iterações (padrão: 100,000)
            
        Returns:
            Chave derivada de 32 bytes
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(self.master_key_bytes)
    
    def encrypt(self, data: Union[str, bytes], context: str = "") -> str:
        """
        Criptografa dados usando AES-256-GCM
        
        Args:
            data: Dados para criptografar (string ou bytes)
            context: Contexto adicional para auditoria
            
        Returns:
            String base64 com formato: salt.nonce.ciphertext.tag
        """
        try:
            # Converter para bytes se necessário
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Gerar salt e nonce únicos
            salt = secrets.token_bytes(16)  # 128 bits
            nonce = secrets.token_bytes(12)  # 96 bits (recomendado para GCM)
            
            # Derivar chave específica
            key = self._derive_key(salt)
            
            # Criar cipher AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Criptografar dados
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Obter tag de autenticação
            tag = encryptor.tag
            
            # Combinar todos os componentes
            encrypted_data = salt + nonce + ciphertext + tag
            
            # Codificar em base64
            result = base64.urlsafe_b64encode(encrypted_data).decode('ascii')
            
            logger.info(f"✅ Dados criptografados com sucesso {f'[{context}]' if context else ''}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro na criptografia: {e}")
            raise
    
    def decrypt(self, encrypted_data: str, context: str = "") -> bytes:
        """
        Descriptografa dados AES-256-GCM
        
        Args:
            encrypted_data: String base64 criptografada
            context: Contexto adicional para auditoria
            
        Returns:
            Dados descriptografados em bytes
        """
        try:
            # Decodificar base64
            data = base64.urlsafe_b64decode(encrypted_data.encode('ascii'))
            
            # Extrair componentes
            salt = data[:16]      # 16 bytes
            nonce = data[16:28]   # 12 bytes
            tag = data[-16:]      # 16 bytes (últimos)
            ciphertext = data[28:-16]  # Resto
            
            # Derivar chave
            key = self._derive_key(salt)
            
            # Criar cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Descriptografar e verificar integridade
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            logger.info(f"✅ Dados descriptografados com sucesso {f'[{context}]' if context else ''}")
            return plaintext
            
        except Exception as e:
            logger.error(f"❌ Erro na descriptografia: {e}")
            raise
    
    def decrypt_to_string(self, encrypted_data: str, context: str = "") -> str:
        """
        Descriptografa dados e retorna como string UTF-8
        
        Args:
            encrypted_data: String base64 criptografada
            context: Contexto adicional para auditoria
            
        Returns:
            String descriptografada
        """
        return self.decrypt(encrypted_data, context).decode('utf-8')
    
    def encrypt_sensitive_dict(self, data: dict, sensitive_keys: list) -> dict:
        """
        Criptografa chaves sensíveis em um dicionário
        
        Args:
            data: Dicionário com dados
            sensitive_keys: Lista de chaves para criptografar
            
        Returns:
            Dicionário com chaves sensíveis criptografadas
        """
        result = data.copy()
        
        for key in sensitive_keys:
            if key in result and result[key] is not None:
                original_value = str(result[key])
                result[key] = self.encrypt(original_value, f"dict_key:{key}")
                result[f"{key}_encrypted"] = True
        
        return result
    
    def decrypt_sensitive_dict(self, data: dict, sensitive_keys: list) -> dict:
        """
        Descriptografa chaves sensíveis em um dicionário
        
        Args:
            data: Dicionário com dados criptografados
            sensitive_keys: Lista de chaves para descriptografar
            
        Returns:
            Dicionário com chaves sensíveis descriptografadas
        """
        result = data.copy()
        
        for key in sensitive_keys:
            if key in result and result.get(f"{key}_encrypted"):
                encrypted_value = result[key]
                result[key] = self.decrypt_to_string(encrypted_value, f"dict_key:{key}")
                result.pop(f"{key}_encrypted", None)
        
        return result
    
    def generate_master_key(self) -> str:
        """
        Gera uma nova chave mestre de 256 bits
        
        Returns:
            Chave mestre em base64
        """
        key = secrets.token_bytes(32)  # 256 bits
        return base64.urlsafe_b64encode(key).decode('ascii')
    
    def validate_encrypted_data(self, encrypted_data: str) -> bool:
        """
        Valida se os dados criptografados são válidos
        
        Args:
            encrypted_data: String base64 para validar
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            # Tentar decodificar base64
            data = base64.urlsafe_b64decode(encrypted_data.encode('ascii'))
            
            # Verificar tamanho mínimo (salt + nonce + tag = 44 bytes)
            if len(data) < 44:
                return False
            
            # Estrutura parece válida
            return True
            
        except Exception:
            return False

# Instância global do serviço
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Obtém instância global do serviço de criptografia"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
