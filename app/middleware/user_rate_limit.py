"""
Middleware de Rate Limiting por Usuário
Contr        # Configurar Redis
        if redis_client:
            self.redis = redis_client
        else:
            try:
                redis_url = get_redis_config_for_service("UserRateLimitMiddleware")
                self.redis = redis.from_url(redis_url, decode_responses=True)
                logger.info(f"✅ Redis connection initialized for rate limiting")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                logger.warning("⚠️ Rate limiting will be disabled due to Redis connection failure")
                self.redis = Nonea de requisições por usuário autenticado
"""

import time
import json
import asyncio
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis.asyncio as redis

from app.config import get_settings
from app.utils.redis_helper import get_redis_config_for_service
from app.config.rate_limit_config import (
    ENDPOINT_RATE_LIMITS,
    USER_TYPE_MULTIPLIERS, 
    ENDPOINT_USER_OVERRIDES,
    REDIS_CONFIG,
    LOGGING_CONFIG,
    RATE_LIMIT_HEADERS,
    GRACEFUL_DEGRADATION,
    EXEMPT_ENDPOINTS
)

logger = logging.getLogger(__name__)
config = get_settings()

class UserRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de Rate Limiting por Usuário
    
    Funcionalidades:
    - Rate limiting granular por usuário autenticado
    - Configuração flexível por endpoint e método HTTP
    - Headers informativos sobre limites
    - Logging de violações para análise
    - Diferentes limites por tipo de usuário
    - Graceful degradation se Redis falhar
    """
    
    def __init__(self, app, redis_client=None):
        super().__init__(app)
        
        # Configurar Redis
        if redis_client:
            self.redis = redis_client
        else:
            # 🚀 FORÇAR Railway Redis diretamente (ignorar config por enquanto)
            redis_url = "redis://default:SvSHiMNuuQEtmIUgGIEGqPpXsdZeInDG@yamanote.proxy.rlwy.net:14106"
            logger.info("🚀 FORCED Railway Redis URL (bypassing config)")
            
            # DEBUG: também mostrar o que vem do config
            config_url = config.redis_url
            logger.info(f"🔍 Config redis_url would be: {config_url}")
            
            try:
                self.redis = redis.from_url(redis_url, decode_responses=True)
                logger.info(f"✅ Redis connection initialized with Railway URL")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                logger.warning("⚠️ Rate limiting will be disabled due to Redis connection failure")
                self.redis = None
        
        # Configurações de limite por endpoint e método
        self.limits = ENDPOINT_RATE_LIMITS
        
        # Limites especiais por tipo de usuário
        self.user_type_multipliers = USER_TYPE_MULTIPLIERS
        
        # Cache local para evitar múltiplas consultas Redis
        self._cache = {}
        self._cache_ttl = 60  # Cache por 1 minuto
        
        logger.info("UserRateLimitMiddleware initialized with Redis and flexible endpoint limits")
    
    async def dispatch(self, request: Request, call_next):
        """Processar requisição com rate limiting"""
        
        logger.debug(f"Rate limiting middleware started for {request.url.path}")
        
        # Pular rate limiting para certos paths
        if self._should_skip_rate_limiting(request):
            logger.debug(f"Skipping rate limiting for {request.url.path}")
            return await call_next(request)
        
        logger.debug(f"Getting user info for {request.url.path}")
        # Obter informações do usuário
        user_info = await self._get_user_info(request)
        
        if not user_info:
            logger.debug(f"No user info, handling IP rate limiting for {request.url.path}")
            # Se não há usuário autenticado, usar rate limiting básico por IP
            return await self._handle_ip_rate_limiting(request, call_next)
        
        user_id = user_info['id']
        user_type = user_info.get('type', 'regular')
        endpoint_key = self._get_endpoint_key(request)
        
        logger.debug(f"User rate limiting for user {user_id}, endpoint {endpoint_key}")
        
        # Obter configuração de limite
        limit_config = self._get_limit_config(endpoint_key, user_type)
        
        try:
            # Verificar rate limit
            rate_limit_result = await self._check_rate_limit(user_id, endpoint_key, limit_config)
            
            if rate_limit_result['exceeded']:
                logger.debug(f"Rate limit exceeded for user {user_id}")
                return await self._handle_rate_limit_exceeded(rate_limit_result, limit_config)
            
            # Incrementar contador
            await self._increment_counter(user_id, endpoint_key, limit_config)
            
            logger.debug(f"Calling next middleware for user {user_id}")
            # Processar requisição
            response = await call_next(request)
            
            if response:
                logger.debug(f"Adding rate limit headers for user {user_id}")
                # Adicionar headers de rate limit
                await self._add_rate_limit_headers(response, user_id, endpoint_key, limit_config)
                
                logger.debug(f"Rate limiting completed successfully for user {user_id}")
                return response
            else:
                logger.error(f"No response received from call_next for user {user_id}")
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=500,
                    content={"error": "No response from downstream middleware"}
                )
            
        except Exception as e:
            # Graceful degradation - se Redis falhar, permitir requisição
            logger.error(f"Rate limiting failed for user {user_id}: {e}")
            logger.warning("Rate limiting disabled due to Redis error - allowing request")
            
            try:
                response = await call_next(request)
                if response:
                    response.headers["X-RateLimit-Status"] = "disabled-error"
                    logger.debug(f"Rate limiting error handled, returning response")
                    return response
                else:
                    logger.error(f"No response received in error handler for user {user_id}")
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=500,
                        content={"error": "No response in error handler"}
                    )
            except Exception as final_e:
                logger.error(f"Final error handler failed for user {user_id}: {final_e}")
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=500,
                    content={"error": "Critical middleware error"}
                )
    
    def _should_skip_rate_limiting(self, request: Request) -> bool:
        """Verificar se deve pular rate limiting"""
        skip_paths = [
            '/docs',
            '/redoc', 
            '/openapi.json',
            '/favicon.ico',
            '/static/',
            '/metrics'  # Prometheus metrics
        ]
        
        path = request.url.path
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def _get_user_info(self, request: Request) -> Optional[Dict]:
        """Obter informações do usuário autenticado"""
        try:
            # Verificar se há usuário no estado da requisição (setado por auth middleware)
            if hasattr(request.state, 'current_user'):
                user = request.state.current_user
                return {
                    'id': getattr(user, 'id', None) or getattr(user, 'user_id', None),
                    'username': getattr(user, 'username', 'unknown'),
                    'type': getattr(user, 'user_type', 'regular')
                }
            
            # Verificar token JWT no header
            auth_header = request.headers.get('authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                # Aqui poderia decodificar o JWT para obter user info
                # Por simplicidade, usar hash do token como user_id
                user_id = abs(hash(token)) % 1000000
                return {
                    'id': user_id,
                    'username': f'token_user_{user_id}',
                    'type': 'regular'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    async def _handle_ip_rate_limiting(self, request: Request, call_next):
        """Rate limiting básico por IP para usuários não autenticados"""
        try:
            client_ip = self._get_client_ip(request)
            endpoint_key = self._get_endpoint_key(request)
            
            # Usar limites reduzidos para IPs não autenticados
            limit_config = {
                'requests': 100,  # 100/hour por IP
                'window': 3600,
                'burst': 10
            }
            
            try:
                rate_limit_result = await self._check_rate_limit(f"ip:{client_ip}", endpoint_key, limit_config)
                
                if rate_limit_result['exceeded']:
                    return await self._handle_rate_limit_exceeded(rate_limit_result, limit_config)
                
                await self._increment_counter(f"ip:{client_ip}", endpoint_key, limit_config)
                
                response = await call_next(request)
                await self._add_rate_limit_headers(response, f"ip:{client_ip}", endpoint_key, limit_config)
                
                return response
                
            except Exception as e:
                logger.error(f"IP rate limiting failed: {e}")
                response = await call_next(request)
                if response:
                    response.headers["X-RateLimit-Status"] = "ip-error"
                return response
                
        except Exception as e:
            logger.error(f"Critical error in IP rate limiting: {e}")
            # Fallback final - sempre retornar uma resposta
            try:
                response = await call_next(request)
                if response:
                    response.headers["X-RateLimit-Status"] = "critical-error"
                return response
            except Exception as final_e:
                logger.error(f"Final fallback failed: {final_e}")
                # Se tudo falhar, retornar erro 500
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=500,
                    content={"error": "Internal rate limiting error"}
                )
    
    def _get_client_ip(self, request: Request) -> str:
        """Obter IP real do cliente considerando proxies"""
        # Verificar headers de proxy
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip.strip()
        
        # Usar IP direto
        return request.client.host if request.client else 'unknown'
    
    def _get_endpoint_key(self, request: Request) -> str:
        """Gerar chave única para endpoint"""
        method = request.method
        path = request.url.path
        
        # Normalizar path removendo IDs dinâmicos
        normalized_path = self._normalize_path(path)
        
        return f"{method} {normalized_path}"
    
    def _normalize_path(self, path: str) -> str:
        """Normalizar path substituindo IDs por placeholders"""
        import re
        
        # Substituir IDs numéricos
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Substituir UUIDs
        path = re.sub(r'/[0-9a-f-]{36}', '/{uuid}', path, flags=re.IGNORECASE)
        
        # Substituir outros padrões comuns
        path = re.sub(r'/[a-f0-9]{32}', '/{hash}', path, flags=re.IGNORECASE)
        
        return path
    
    def _get_limit_config(self, endpoint_key: str, user_type: str) -> Dict:
        """Obter configuração de limite para endpoint e tipo de usuário"""
        # Buscar configuração específica
        base_config = self.limits.get(endpoint_key, self.limits['default']).copy()
        
        # Aplicar multiplicador por tipo de usuário
        multiplier = self.user_type_multipliers.get(user_type, 1.0)
        
        base_config['requests'] = int(base_config['requests'] * multiplier)
        base_config['burst'] = int(base_config.get('burst', 10) * multiplier)
        
        return base_config
    
    async def _check_rate_limit(self, user_id: str, endpoint_key: str, config: Dict) -> Dict:
        """Verificar se rate limit foi excedido"""
        
        # Se Redis não está disponível, permitir requisição
        if not self.redis:
            logger.debug("Redis not available, skipping rate limit check")
            return {
                'exceeded': False,
                'current_requests': 0,
                'limit': config['requests'],
                'reset_time': int(time.time()) + config['window'],
                'retry_after': 0
            }
        
        current_time = int(time.time())
        window_start = current_time - config['window']
        
        # Chaves Redis
        main_key = f"rate_limit:user:{user_id}:{endpoint_key}"
        burst_key = f"rate_limit:burst:user:{user_id}:{endpoint_key}"
        
        try:
            # Usar pipeline para operações atômicas
            pipe = self.redis.pipeline()
            
            # Limpar entradas antigas da janela deslizante
            pipe.zremrangebyscore(main_key, 0, window_start)
            pipe.zremrangebyscore(burst_key, 0, current_time - 60)  # Burst window de 1 minuto
            
            # Contar requisições na janela atual
            pipe.zcard(main_key)
            pipe.zcard(burst_key)
            
            results = await pipe.execute()
            current_requests = results[2]
            burst_requests = results[3]
            
            # Verificar limite principal
            if current_requests >= config['requests']:
                logger.warning(f"Rate limit exceeded for {user_id} on {endpoint_key}: {current_requests}/{config['requests']}")
                return {
                    'exceeded': True,
                    'current': current_requests,
                    'limit': config['requests'],
                    'window': config['window'],
                    'type': 'main'
                }
            
            # Verificar burst limit
            if burst_requests >= config.get('burst', 10):
                logger.warning(f"Burst limit exceeded for {user_id} on {endpoint_key}: {burst_requests}/{config.get('burst', 10)}")
                return {
                    'exceeded': True,
                    'current': burst_requests,
                    'limit': config.get('burst', 10),
                    'window': 60,
                    'type': 'burst'
                }
            
            return {
                'exceeded': False,
                'current': current_requests,
                'limit': config['requests'],
                'burst_current': burst_requests,
                'burst_limit': config.get('burst', 10)
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Em caso de erro, não bloquear
            return {'exceeded': False, 'current': 0, 'limit': config['requests']}
    
    async def _increment_counter(self, user_id: str, endpoint_key: str, config: Dict):
        """Incrementar contadores de rate limit"""
        
        # Se Redis não está disponível, skip
        if not self.redis:
            logger.debug("Redis not available, skipping counter increment")
            return
            
        current_time = time.time()
        
        main_key = f"rate_limit:user:{user_id}:{endpoint_key}"
        burst_key = f"rate_limit:burst:user:{user_id}:{endpoint_key}"
        
        try:
            pipe = self.redis.pipeline()
            
            # Adicionar timestamp atual
            pipe.zadd(main_key, {str(current_time): current_time})
            pipe.zadd(burst_key, {str(current_time): current_time})
            
            # Definir expiração
            pipe.expire(main_key, config['window'] + 60)  # +60s de buffer
            pipe.expire(burst_key, 120)  # 2 minutos para burst
            
            await pipe.execute()
            
        except Exception as e:
            logger.error(f"Rate limit increment failed: {e}")
    
    async def _handle_rate_limit_exceeded(self, rate_limit_result: Dict, config: Dict) -> Response:
        """Lidar com rate limit excedido"""
        current_time = int(time.time())
        
        # Calcular retry-after
        if rate_limit_result['type'] == 'burst':
            retry_after = 60  # 1 minuto para burst
        else:
            retry_after = config['window']
        
        # Log da violação
        violation_log = {
            'timestamp': datetime.now().isoformat(),
            'type': rate_limit_result['type'],
            'current': rate_limit_result['current'],
            'limit': rate_limit_result['limit'],
            'window': rate_limit_result['window'],
            'retry_after': retry_after
        }
        
        logger.warning(f"Rate limit violation: {json.dumps(violation_log)}")
        
        # Resposta de erro
        error_detail = {
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {rate_limit_result['limit']} per {rate_limit_result['window']} seconds",
            "current_requests": rate_limit_result['current'],
            "limit": rate_limit_result['limit'],
            "window_seconds": rate_limit_result['window'],
            "retry_after_seconds": retry_after,
            "type": rate_limit_result['type']
        }
        
        headers = {
            "X-RateLimit-Limit": str(rate_limit_result['limit']),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(current_time + retry_after),
            "Retry-After": str(retry_after),
            "Content-Type": "application/json"
        }
        
        return Response(
            content=json.dumps(error_detail),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers
        )
    
    async def _add_rate_limit_headers(self, response: Response, user_id: str, endpoint_key: str, config: Dict):
        """Adicionar headers de rate limit à resposta"""
        
        # Se Redis não está disponível, adicionar headers básicos
        if not self.redis:
            response.headers["X-RateLimit-Limit"] = str(config['requests'])
            response.headers["X-RateLimit-Remaining"] = str(config['requests'])
            response.headers["X-RateLimit-Status"] = "redis-unavailable"
            return
            
        try:
            current_time = int(time.time())
            
            # Obter contagem atual
            main_key = f"rate_limit:user:{user_id}:{endpoint_key}"
            window_start = current_time - config['window']
            
            current_count = await self.redis.zcount(main_key, window_start, current_time)
            remaining = max(0, config['requests'] - current_count)
            reset_time = current_time + config['window']
            
            # Adicionar headers
            response.headers["X-RateLimit-Limit"] = str(config['requests'])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-RateLimit-Window"] = str(config['window'])
            
            if 'burst' in config:
                burst_key = f"rate_limit:burst:user:{user_id}:{endpoint_key}"
                burst_current = await self.redis.zcount(burst_key, current_time - 60, current_time)
                burst_remaining = max(0, config['burst'] - burst_current)
                
                response.headers["X-RateLimit-Burst-Limit"] = str(config['burst'])
                response.headers["X-RateLimit-Burst-Remaining"] = str(burst_remaining)
            
        except Exception as e:
            logger.error(f"Failed to add rate limit headers: {e}")
            # Adicionar headers básicos mesmo com erro
            response.headers["X-RateLimit-Limit"] = str(config['requests'])
            response.headers["X-RateLimit-Status"] = "error"
    
    async def get_user_rate_limit_status(self, user_id: str, endpoint: str = None) -> Dict:
        """Obter status de rate limit para usuário específico"""
        try:
            if endpoint:
                endpoints = [endpoint]
            else:
                # Obter todos os endpoints para o usuário
                pattern = f"rate_limit:user:{user_id}:*"
                keys = await self.redis.keys(pattern)
                endpoints = [key.split(':')[-1] for key in keys]
            
            status = {}
            current_time = int(time.time())
            
            for ep in endpoints:
                config = self._get_limit_config(ep, 'regular')  # Usar tipo regular como padrão
                main_key = f"rate_limit:user:{user_id}:{ep}"
                window_start = current_time - config['window']
                
                current_count = await self.redis.zcount(main_key, window_start, current_time)
                remaining = max(0, config['requests'] - current_count)
                
                status[ep] = {
                    'current': current_count,
                    'limit': config['requests'],
                    'remaining': remaining,
                    'window': config['window'],
                    'reset_at': current_time + config['window']
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {}
    
    async def reset_user_rate_limit(self, user_id: str, endpoint: str = None):
        """Resetar rate limit para usuário específico"""
        try:
            if endpoint:
                pattern = f"rate_limit:user:{user_id}:{endpoint}"
            else:
                pattern = f"rate_limit:user:{user_id}:*"
            
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Reset rate limit for user {user_id}, endpoint: {endpoint or 'all'}")
            
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")

# Instância global do middleware para uso em endpoints
user_rate_limiter = None

def get_user_rate_limiter() -> UserRateLimitMiddleware:
    """Obter instância global do rate limiter"""
    global user_rate_limiter
    if user_rate_limiter is None:
        user_rate_limiter = UserRateLimitMiddleware(None)
    return user_rate_limiter
