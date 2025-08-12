"""
🔐 Sistema de Criptografia de Dados Sensíveis
=============================================

Módulo especializado para criptografia de dados específicos:
- Senhas e credenciais
- Tokens de API
- Dados pessoais (PII)
- Chaves de sessão
- Configurações sensíveis
"""

import os
import json
import base64
from typing import Dict, Any, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from .encryption_service import get_encryption_service
import logging

logger = logging.getLogger(__name__)

@dataclass
class EncryptedData:
    """Estrutura para dados criptografados com metadados"""
    encrypted_value: str
    data_type: str
    timestamp: str
    context: str
    is_encrypted: bool = True

class DataEncryption:
    """Sistema especializado para criptografia de diferentes tipos de dados"""
    
    def __init__(self):
        """Inicializa o sistema de criptografia de dados"""
        self.encryption_service = get_encryption_service()
        
        # Tipos de dados sensíveis e suas configurações
        self.sensitive_data_types = {
            "password": {"min_length": 8, "context": "auth"},
            "api_key": {"min_length": 16, "context": "api"},
            "token": {"min_length": 20, "context": "auth"},
            "secret": {"min_length": 32, "context": "security"},
            "pii": {"min_length": 1, "context": "personal"},
            "database_url": {"min_length": 10, "context": "database"},
            "webhook_secret": {"min_length": 32, "context": "webhook"},
            "jwt_secret": {"min_length": 32, "context": "jwt"},
            "encryption_key": {"min_length": 32, "context": "encryption"}
        }
        
        logger.info("✅ Sistema de criptografia de dados inicializado")
    
    def encrypt_password(self, password: str, user_id: str = None) -> EncryptedData:
        """
        Criptografa senha de usuário
        
        Args:
            password: Senha em texto plano
            user_id: ID do usuário (opcional)
            
        Returns:
            Estrutura com senha criptografada
        """
        try:
            if len(password) < self.sensitive_data_types["password"]["min_length"]:
                raise ValueError("Senha muito curta")
            
            context = f"password:{user_id}" if user_id else "password"
            encrypted_value = self.encryption_service.encrypt(password, context)
            
            result = EncryptedData(
                encrypted_value=encrypted_value,
                data_type="password",
                timestamp=datetime.utcnow().isoformat(),
                context=context
            )
            
            logger.info(f"✅ Senha criptografada {f'para usuário {user_id}' if user_id else ''}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao criptografar senha: {e}")
            raise
    
    def encrypt_api_key(self, api_key: str, service: str) -> EncryptedData:
        """
        Criptografa chave de API
        
        Args:
            api_key: Chave da API
            service: Nome do serviço (ex: "openai", "meta")
            
        Returns:
            Estrutura com chave criptografada
        """
        try:
            if len(api_key) < self.sensitive_data_types["api_key"]["min_length"]:
                raise ValueError("Chave de API muito curta")
            
            context = f"api_key:{service}"
            encrypted_value = self.encryption_service.encrypt(api_key, context)
            
            result = EncryptedData(
                encrypted_value=encrypted_value,
                data_type="api_key",
                timestamp=datetime.utcnow().isoformat(),
                context=context
            )
            
            logger.info(f"✅ Chave de API criptografada para {service}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao criptografar API key: {e}")
            raise
    
    def encrypt_database_credentials(self, db_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Criptografa credenciais de banco de dados
        
        Args:
            db_config: Configuração do banco com senha
            
        Returns:
            Configuração com senha criptografada
        """
        try:
            sensitive_keys = ["password", "user", "database_url"]
            result = db_config.copy()
            
            for key in sensitive_keys:
                if key in result and result[key]:
                    context = f"database:{key}"
                    encrypted_data = EncryptedData(
                        encrypted_value=self.encryption_service.encrypt(result[key], context),
                        data_type="database_credential",
                        timestamp=datetime.utcnow().isoformat(),
                        context=context
                    )
                    result[key] = asdict(encrypted_data)
            
            logger.info("✅ Credenciais de banco criptografadas")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao criptografar credenciais do banco: {e}")
            raise
    
    def encrypt_environment_variables(self, env_dict: Dict[str, str]) -> Dict[str, Any]:
        """
        Criptografa variáveis de ambiente sensíveis
        
        Args:
            env_dict: Dicionário de variáveis de ambiente
            
        Returns:
            Dicionário com variáveis sensíveis criptografadas
        """
        try:
            # Padrões de variáveis sensíveis
            sensitive_patterns = [
                "password", "secret", "key", "token", "auth",
                "api", "webhook", "jwt", "encryption", "private"
            ]
            
            result = env_dict.copy()
            encrypted_count = 0
            
            for var_name, var_value in env_dict.items():
                var_lower = var_name.lower()
                
                # Verificar se é sensível
                is_sensitive = any(pattern in var_lower for pattern in sensitive_patterns)
                
                if is_sensitive and var_value:
                    context = f"env_var:{var_name}"
                    encrypted_data = EncryptedData(
                        encrypted_value=self.encryption_service.encrypt(var_value, context),
                        data_type="environment_variable",
                        timestamp=datetime.utcnow().isoformat(),
                        context=context
                    )
                    result[var_name] = asdict(encrypted_data)
                    encrypted_count += 1
            
            logger.info(f"✅ {encrypted_count} variáveis de ambiente criptografadas")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao criptografar variáveis de ambiente: {e}")
            raise
    
    def encrypt_user_pii(self, user_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Criptografa dados pessoais do usuário (PII)
        
        Args:
            user_data: Dados do usuário
            user_id: ID do usuário
            
        Returns:
            Dados com PII criptografado
        """
        try:
            # Campos PII comuns
            pii_fields = [
                "email", "phone", "cpf", "rg", "address", 
                "birth_date", "full_name", "social_security"
            ]
            
            result = user_data.copy()
            encrypted_count = 0
            
            for field in pii_fields:
                if field in result and result[field]:
                    context = f"pii:{user_id}:{field}"
                    encrypted_data = EncryptedData(
                        encrypted_value=self.encryption_service.encrypt(str(result[field]), context),
                        data_type="pii",
                        timestamp=datetime.utcnow().isoformat(),
                        context=context
                    )
                    result[field] = asdict(encrypted_data)
                    encrypted_count += 1
            
            logger.info(f"✅ {encrypted_count} campos PII criptografados para usuário {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao criptografar PII: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: Union[EncryptedData, Dict, str]) -> str:
        """
        Descriptografa dados criptografados
        
        Args:
            encrypted_data: Dados criptografados (objeto, dict ou string)
            
        Returns:
            Dados descriptografados
        """
        try:
            # Determinar tipo e extrair dados
            if isinstance(encrypted_data, EncryptedData):
                encrypted_value = encrypted_data.encrypted_value
                context = encrypted_data.context
            elif isinstance(encrypted_data, dict):
                if "encrypted_value" in encrypted_data:
                    encrypted_value = encrypted_data["encrypted_value"]
                    context = encrypted_data.get("context", "")
                else:
                    raise ValueError("Estrutura de dados criptografados inválida")
            elif isinstance(encrypted_data, str):
                encrypted_value = encrypted_data
                context = "direct_string"
            else:
                raise ValueError("Tipo de dados criptografados não suportado")
            
            # Descriptografar
            decrypted_value = self.encryption_service.decrypt_to_string(encrypted_value, context)
            
            logger.info(f"✅ Dados descriptografados {f'[{context}]' if context else ''}")
            return decrypted_value
            
        except Exception as e:
            logger.error(f"❌ Erro ao descriptografar dados: {e}")
            raise
    
    def decrypt_environment_variables(self, encrypted_env: Dict[str, Any]) -> Dict[str, str]:
        """
        Descriptografa variáveis de ambiente
        
        Args:
            encrypted_env: Dicionário com variáveis criptografadas
            
        Returns:
            Dicionário com variáveis descriptografadas
        """
        try:
            result = {}
            decrypted_count = 0
            
            for var_name, var_value in encrypted_env.items():
                if isinstance(var_value, dict) and var_value.get("is_encrypted"):
                    # É uma variável criptografada
                    result[var_name] = self.decrypt_data(var_value)
                    decrypted_count += 1
                else:
                    # Variável normal
                    result[var_name] = var_value
            
            logger.info(f"✅ {decrypted_count} variáveis de ambiente descriptografadas")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao descriptografar variáveis de ambiente: {e}")
            raise
    
    def decrypt_user_pii(self, encrypted_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Descriptografa dados pessoais do usuário
        
        Args:
            encrypted_user_data: Dados do usuário com PII criptografado
            
        Returns:
            Dados com PII descriptografado
        """
        try:
            result = {}
            decrypted_count = 0
            
            for field, value in encrypted_user_data.items():
                if isinstance(value, dict) and value.get("is_encrypted"):
                    # É um campo PII criptografado
                    result[field] = self.decrypt_data(value)
                    decrypted_count += 1
                else:
                    # Campo normal
                    result[field] = value
            
            logger.info(f"✅ {decrypted_count} campos PII descriptografados")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao descriptografar PII: {e}")
            raise
    
    def create_encrypted_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria configuração com dados sensíveis criptografados
        
        Args:
            config: Configuração original
            
        Returns:
            Configuração com dados sensíveis criptografados
        """
        try:
            result = {}
            
            for key, value in config.items():
                if isinstance(value, dict):
                    # Processar sub-configurações recursivamente
                    result[key] = self.create_encrypted_config(value)
                elif self._is_sensitive_key(key):
                    # Criptografar valor sensível
                    context = f"config:{key}"
                    encrypted_data = EncryptedData(
                        encrypted_value=self.encryption_service.encrypt(str(value), context),
                        data_type="configuration",
                        timestamp=datetime.utcnow().isoformat(),
                        context=context
                    )
                    result[key] = asdict(encrypted_data)
                else:
                    # Manter valor normal
                    result[key] = value
            
            logger.info("✅ Configuração com criptografia criada")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar configuração criptografada: {e}")
            raise
    
    def load_encrypted_config(self, encrypted_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Carrega configuração descriptografando dados sensíveis
        
        Args:
            encrypted_config: Configuração com dados criptografados
            
        Returns:
            Configuração com dados descriptografados
        """
        try:
            result = {}
            
            for key, value in encrypted_config.items():
                if isinstance(value, dict):
                    if value.get("is_encrypted"):
                        # Descriptografar valor
                        result[key] = self.decrypt_data(value)
                    else:
                        # Processar sub-configuração recursivamente
                        result[key] = self.load_encrypted_config(value)
                else:
                    # Valor normal
                    result[key] = value
            
            logger.info("✅ Configuração descriptografada carregada")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configuração criptografada: {e}")
            raise
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Verifica se uma chave é sensível"""
        key_lower = key.lower()
        sensitive_patterns = [
            "password", "secret", "key", "token", "auth",
            "api", "webhook", "jwt", "encryption", "private",
            "credential", "pass", "pwd"
        ]
        return any(pattern in key_lower for pattern in sensitive_patterns)
    
    def export_encrypted_data(self, data: Dict[str, Any], filename: str) -> str:
        """
        Exporta dados criptografados para arquivo
        
        Args:
            data: Dados para exportar
            filename: Nome do arquivo
            
        Returns:
            Caminho do arquivo exportado
        """
        try:
            export_data = {
                "metadata": {
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "encryption": "AES-256-GCM"
                },
                "data": data
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            # Definir permissões seguras
            os.chmod(filename, 0o600)
            
            logger.info(f"✅ Dados criptografados exportados para {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar dados: {e}")
            raise
    
    def import_encrypted_data(self, filename: str) -> Dict[str, Any]:
        """
        Importa dados criptografados de arquivo
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            Dados importados
        """
        try:
            with open(filename, 'r') as f:
                import_data = json.load(f)
            
            if "data" not in import_data:
                raise ValueError("Arquivo de dados criptografados inválido")
            
            logger.info(f"✅ Dados criptografados importados de {filename}")
            return import_data["data"]
            
        except Exception as e:
            logger.error(f"❌ Erro ao importar dados: {e}")
            raise

# Instância global
_data_encryption = None

def get_data_encryption() -> DataEncryption:
    """Obtém instância global do sistema de criptografia de dados"""
    global _data_encryption
    if _data_encryption is None:
        _data_encryption = DataEncryption()
    return _data_encryption
