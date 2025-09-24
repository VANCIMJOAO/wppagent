"""
Serviço de Cache para Autenticação
Otimiza performance do login com cache Redis
"""

import json
import hashlib
from typing import Optional, Dict, Any
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import AdminUser
from app.utils.logger import get_logger
from app.services.cache_service_optimized import OptimizedCacheService, CacheType

logger = get_logger(__name__)


class AuthCacheService:
    """Serviço de cache para otimizar autenticação"""
    
    def __init__(self):
        self.cache = OptimizedCacheService()
        self.cache_ttl = 300  # 5 minutos
        self.user_cache_ttl = 1800  # 30 minutos para dados do usuário
    
    def _get_user_cache_key(self, username: str) -> str:
        """Gera chave de cache para usuário"""
        return f"auth:user:{hashlib.md5(username.encode()).hexdigest()}"
    
    def _get_password_attempt_key(self, username: str) -> str:
        """Gera chave para tentativas de senha"""
        return f"auth:attempts:{hashlib.md5(username.encode()).hexdigest()}"
    
    async def get_cached_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Busca usuário no cache
        
        Args:
            username: Nome do usuário
            
        Returns:
            Dados do usuário em cache ou None
        """
        try:
            cache_key = self._get_user_cache_key(username)
            cached_data = await self.cache.get(cache_key, CacheType.USER_CONTEXT)
            
            if cached_data:
                logger.debug(f"Cache hit para usuário: {username}")
                return json.loads(cached_data)
            
            logger.debug(f"Cache miss para usuário: {username}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário no cache: {e}")
            return None
    
    async def cache_user(self, username: str, user_data: Dict[str, Any]) -> bool:
        """
        Armazena dados do usuário no cache
        
        Args:
            username: Nome do usuário
            user_data: Dados do usuário
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            cache_key = self._get_user_cache_key(username)
            await self.cache.set(
                cache_key, 
                json.dumps(user_data, default=str), 
                CacheType.USER_CONTEXT,
                self.user_cache_ttl
            )
            logger.debug(f"Usuário armazenado no cache: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar usuário no cache: {e}")
            return False
    
    async def get_user_with_cache(self, username: str, session: AsyncSession) -> Optional[AdminUser]:
        """
        Busca usuário com cache otimizado
        
        Args:
            username: Nome do usuário
            session: Sessão do banco de dados
            
        Returns:
            AdminUser ou None
        """
        try:
            # 1. Tentar buscar no cache primeiro
            cached_data = await self.get_cached_user(username)
            
            if cached_data:
                # Verificar se os dados ainda são válidos
                if cached_data.get('is_active', False):
                    # Criar objeto AdminUser a partir dos dados em cache
                    user = AdminUser()
                    user.id = cached_data['id']
                    user.username = cached_data['username']
                    user.email = cached_data['email']
                    user.password_hash = cached_data['password_hash']
                    user.is_active = cached_data['is_active']
                    user.created_at = cached_data.get('created_at')
                    user.updated_at = cached_data.get('updated_at')
                    
                    logger.info(f"✅ Usuário carregado do cache: {username}")
                    return user
            
            # 2. Cache miss - buscar no banco
            logger.info(f"🔍 Buscando usuário no banco: {username}")
            result = await session.execute(
                select(AdminUser).where(AdminUser.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # 3. Armazenar no cache para próximas consultas
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'updated_at': user.updated_at.isoformat() if user.updated_at else None
                }
                await self.cache_user(username, user_data)
                logger.info(f"✅ Usuário carregado do banco e armazenado no cache: {username}")
            
            return user
            
        except Exception as e:
            logger.error(f"Erro ao buscar usuário com cache: {e}")
            return None
    
    async def invalidate_user_cache(self, username: str) -> bool:
        """
        Invalida cache do usuário
        
        Args:
            username: Nome do usuário
            
        Returns:
            True se invalidado com sucesso
        """
        try:
            cache_key = self._get_user_cache_key(username)
            await self.cache.delete(cache_key, CacheType.USER_CONTEXT)
            logger.info(f"Cache invalidado para usuário: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao invalidar cache do usuário: {e}")
            return False
    
    async def track_password_attempt(self, username: str, success: bool) -> int:
        """
        Rastreia tentativas de senha para rate limiting
        
        Args:
            username: Nome do usuário
            success: Se a tentativa foi bem-sucedida
            
        Returns:
            Número de tentativas recentes
        """
        try:
            attempt_key = self._get_password_attempt_key(username)
            
            if success:
                # Limpar tentativas em caso de sucesso
                await self.cache.delete(attempt_key)
                return 0
            else:
                # Incrementar tentativas
                attempts = await self.cache.get(attempt_key)
                if attempts:
                    attempts = int(attempts) + 1
                else:
                    attempts = 1
                
                await self.cache.set(attempt_key, str(attempts), CacheType.USER_CONTEXT, 900)  # 15 minutos
                return attempts
                
        except Exception as e:
            logger.error(f"Erro ao rastrear tentativa de senha: {e}")
            return 0
    
    async def get_password_attempts(self, username: str) -> int:
        """
        Obtém número de tentativas de senha recentes
        
        Args:
            username: Nome do usuário
            
        Returns:
            Número de tentativas
        """
        try:
            attempt_key = self._get_password_attempt_key(username)
            attempts = await self.cache.get(attempt_key, CacheType.USER_CONTEXT)
            return int(attempts) if attempts else 0
            
        except Exception as e:
            logger.error(f"Erro ao obter tentativas de senha: {e}")
            return 0


# Instância global do serviço de cache
auth_cache_service = AuthCacheService()
