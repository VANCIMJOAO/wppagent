from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
HashiCorp Vault Integration para WhatsApp Agent
Gerenciamento seguro de secrets em produção
"""
import os
import logging
import hvac
from typing import Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Configuração do HashiCorp Vault"""
    url: str = os.getenv("VAULT_URL", "http://localhost:8200")
    token: Optional[str] = os.getenv("VAULT_TOKEN")
    role_id: Optional[str] = os.getenv("VAULT_ROLE_ID")
    secret_id: Optional[str] = os.getenv("VAULT_SECRET_ID")
    mount_point: str = os.getenv("VAULT_MOUNT_POINT", "kv")
    namespace: str = os.getenv("VAULT_NAMESPACE", "whatsapp-agent")


class VaultSecretsManager:
    """Gerenciador de secrets usando HashiCorp Vault"""
    
    def __init__(self, config: VaultConfig = None):
        self.config = config or VaultConfig()
        self.client = None
        self._authenticated = False
        
    async def initialize(self) -> bool:
        """Inicializar conexão com Vault"""
        try:
            self.client = hvac.Client(url=self.config.url)
            
            # Verificar se Vault está disponível
            if not self.client.sys.is_initialized():
                logger.error("Vault não está inicializado")
                return False
            
            # Autenticar
            if await self._authenticate():
                self._authenticated = True
                logger.info("✅ Vault conectado e autenticado")
                return True
            else:
                logger.error("❌ Falha na autenticação do Vault")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao conectar no Vault: {e}")
            return False
    
    async def _authenticate(self) -> bool:
        """Autenticar no Vault"""
        try:
            # Método 1: Token direto
            if self.config.token:
                self.client.token = self.config.token
                if self.client.is_authenticated():
                    logger.info("🔑 Autenticado via token")
                    return True
            
            # Método 2: AppRole (recomendado para produção)
            if self.config.role_id and self.config.secret_id:
                auth_response = self.client.auth.approle.login(
                    role_id=self.config.role_id,
                    secret_id=self.config.secret_id
                )
                self.client.token = auth_response['auth']['client_token']
                logger.info("🔑 Autenticado via AppRole")
                return True
            
            # Método 3: Auto-auth via arquivo (Kubernetes, etc.)
            token_file = Path("/var/run/secrets/vault/token")
            if token_file.exists():
                self.client.token = token_file.read_text().strip()
                if self.client.is_authenticated():
                    logger.info("🔑 Autenticado via arquivo de token")
                    return True
            
            logger.error("❌ Nenhum método de autenticação disponível")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro na autenticação: {e}")
            return False
    
    async def get_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """Buscar secret do Vault"""
        if not self._authenticated:
            logger.error("❌ Vault não autenticado")
            return None
        
        try:
            full_path = f"{self.config.namespace}/{path}"
            response = self.client.secrets.kv.v2.read_secret_version(
                path=full_path,
                mount_point=self.config.mount_point
            )
            
            if response and 'data' in response:
                logger.info(f"✅ Secret recuperado: {path}")
                return response['data']['data']
            else:
                logger.warning(f"⚠️ Secret não encontrado: {path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar secret {path}: {e}")
            return None
    
    async def set_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """Armazenar secret no Vault"""
        if not self._authenticated:
            logger.error("❌ Vault não autenticado")
            return False
        
        try:
            full_path = f"{self.config.namespace}/{path}"
            self.client.secrets.kv.v2.create_or_update_secret(
                path=full_path,
                secret=data,
                mount_point=self.config.mount_point
            )
            
            logger.info(f"✅ Secret armazenado: {path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao armazenar secret {path}: {e}")
            return False
    
    async def delete_secret(self, path: str) -> bool:
        """Deletar secret do Vault"""
        if not self._authenticated:
            logger.error("❌ Vault não autenticado")
            return False
        
        try:
            full_path = f"{self.config.namespace}/{path}"
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=full_path,
                mount_point=self.config.mount_point
            )
            
            logger.info(f"✅ Secret deletado: {path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao deletar secret {path}: {e}")
            return False
    
    async def rotate_secret(self, path: str, new_data: Dict[str, Any]) -> bool:
        """Rotacionar secret (manter versões antigas)"""
        if not self._authenticated:
            logger.error("❌ Vault não autenticado")
            return False
        
        try:
            # Vault KV v2 mantém versões automaticamente
            result = await self.set_secret(path, new_data)
            if result:
                logger.info(f"🔄 Secret rotacionado: {path}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao rotacionar secret {path}: {e}")
            return False
    
    async def get_database_credentials(self) -> Optional[Dict[str, str]]:
        """Buscar credenciais do banco de dados"""
        return await self.get_secret("database/credentials")
    
    async def get_api_keys(self) -> Optional[Dict[str, str]]:
        """Buscar chaves de API"""
        return await self.get_secret("apis/keys")
    
    async def get_whatsapp_config(self) -> Optional[Dict[str, str]]:
        """Buscar configurações do WhatsApp"""
        return await self.get_secret("whatsapp/config")
    
    async def close(self):
        """Fechar conexão com Vault"""
        if self.client:
            # Logout para invalidar token
            try:
                self.client.auth.token.revoke_self()
                logger.info("🔒 Token do Vault revogado")
            except:
                pass
            
            self.client = None
            self._authenticated = False


# Instância global
vault_manager = VaultSecretsManager()
