from app.utils.logger import get_logger

logger = get_logger(__name__)
"""
Sistema de Rate Limiting Robusto para WhatsApp Agent
=====================================================

Este módulo implementa um sistema avançado de rate limiting para proteger endpoints críticos
contra ataques de força bruta, DDoS e uso abusivo do sistema.

Recursos:
- Rate limiting por IP, usuário e endpoint
- Múltiplas estratégias de rate limiting
- Janelas deslizantes e token bucket
- Proteção contra ataques distribuídos
- Logs detalhados de tentativas suspeitas
- Configuração flexível por endpoint
- Suporte a Redis para ambientes distribuídos
"""

import time
import json
import redis
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from functools import wraps
import ipaddress

# Configurar logging para rate limiting
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimitStrategy(Enum):
    """Estratégias de rate limiting disponíveis"""
    FIXED_WINDOW = "fixed_window"          # Janela fixa
    SLIDING_WINDOW = "sliding_window"      # Janela deslizante
    TOKEN_BUCKET = "token_bucket"          # Balde de tokens
    LEAKY_BUCKET = "leaky_bucket"          # Balde vazado
    ADAPTIVE = "adaptive"                  # Adaptativo baseado no comportamento

class RateLimitLevel(Enum):
    """Níveis de severidade do rate limiting"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    LOCKDOWN = 5

@dataclass
class RateLimitConfig:
    """Configuração para rate limiting"""
    requests_per_window: int = 60          # Requests permitidos por janela
    window_size: int = 60                  # Tamanho da janela em segundos
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_limit: int = 10                  # Limite de rajada
    burst_window: int = 1                  # Janela de rajada em segundos
    block_duration: int = 300              # Duração do bloqueio em segundos
    max_violations: int = 5                # Violações antes do bloqueio
    whitelist_ips: List[str] = None        # IPs na lista branca
    blacklist_ips: List[str] = None        # IPs na lista negra
    level: RateLimitLevel = RateLimitLevel.MEDIUM

@dataclass
class RateLimitResult:
    """Resultado da verificação de rate limiting"""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    reason: str = ""
    violation_count: int = 0

class RateLimitException(Exception):
    """Exceção customizada para rate limiting"""
    def __init__(self, message: str, retry_after: int = None, details: Dict = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.details = details or {}

class IPAddressValidator:
    """Validador e classificador de endereços IP"""
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Validar se é um IP válido"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Verificar se é um IP privado"""
        try:
            return ipaddress.ip_address(ip).is_private
        except ValueError:
            return False
    
    @staticmethod
    def is_suspicious_ip(ip: str) -> bool:
        """Detectar IPs suspeitos (Tor, VPN conhecidas, etc.)"""
        # Lista básica de ranges suspeitos
        suspicious_ranges = [
            "192.168.1.0/24",  # Exemplo - ranges privados suspeitos
            "10.0.0.0/8",       # Redes internas que não deveriam acessar externamente
        ]
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            for range_str in suspicious_ranges:
                if ip_obj in ipaddress.ip_network(range_str):
                    return True
        except ValueError:
            pass
        
        return False

class RateLimitStorage:
    """Sistema de armazenamento para dados de rate limiting"""
    
    def __init__(self, use_redis: bool = False, redis_url: str = None):
        self.use_redis = use_redis
        self.local_storage = defaultdict(dict)
        self.lock = threading.Lock()
        
        if use_redis and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("✅ Conectado ao Redis para rate limiting")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao conectar Redis, usando storage local: {e}")
                self.use_redis = False
                self.redis_client = None
        else:
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Dict]:
        """Obter dados do storage"""
        if self.use_redis and self.redis_client:
            try:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            except Exception as e:
                logger.error(f"❌ Erro ao ler do Redis: {e}")
                return None
        else:
            with self.lock:
                return self.local_storage.get(key)
    
    def set(self, key: str, value: Dict, ttl: int = 3600):
        """Armazenar dados no storage"""
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                logger.error(f"❌ Erro ao escrever no Redis: {e}")
        else:
            with self.lock:
                self.local_storage[key] = value
                # Limpar dados antigos periodicamente
                self._cleanup_local_storage()
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Incrementar contador atomicamente"""
        if self.use_redis and self.redis_client:
            try:
                return self.redis_client.incr(key, amount)
            except Exception as e:
                logger.error(f"❌ Erro ao incrementar no Redis: {e}")
                return 0
        else:
            with self.lock:
                current = self.local_storage.get(key, 0)
                new_value = current + amount
                self.local_storage[key] = new_value
                return new_value
    
    def _cleanup_local_storage(self):
        """Limpar dados antigos do storage local"""
        # Implementar limpeza baseada em timestamp se necessário
        pass

class AdvancedRateLimiter:
    """Sistema avançado de rate limiting com múltiplas estratégias"""
    
    def __init__(self, storage: RateLimitStorage = None):
        self.storage = storage or RateLimitStorage()
        self.configs = {}
        self.violation_tracker = defaultdict(list)
        self.blocked_ips = {}
        self.ip_validator = IPAddressValidator()
        
        # Configurações padrão por tipo de endpoint
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Configurar limites padrão para diferentes tipos de endpoint"""
        self.configs = {
            # Endpoints de autenticação (mais restritivos)
            'auth_login': RateLimitConfig(
                requests_per_window=5,
                window_size=300,  # 5 minutos
                burst_limit=2,
                block_duration=900,  # 15 minutos
                max_violations=3,
                level=RateLimitLevel.CRITICAL
            ),
            
            # APIs públicas (moderadamente restritivas)
            'api_public': RateLimitConfig(
                requests_per_window=100,
                window_size=60,
                burst_limit=20,
                block_duration=300,
                max_violations=5,
                level=RateLimitLevel.MEDIUM
            ),
            
            # Dashboard (menos restritivo para usuários autenticados)
            'dashboard': RateLimitConfig(
                requests_per_window=200,
                window_size=60,
                burst_limit=50,
                block_duration=60,
                max_violations=10,
                level=RateLimitLevel.LOW
            ),
            
            # Envio de mensagens (muito restritivo)
            'send_message': RateLimitConfig(
                requests_per_window=30,
                window_size=60,
                burst_limit=5,
                block_duration=600,  # 10 minutos
                max_violations=3,
                level=RateLimitLevel.HIGH
            ),
            
            # Upload de arquivos (restritivo)
            'file_upload': RateLimitConfig(
                requests_per_window=10,
                window_size=300,  # 5 minutos
                burst_limit=2,
                block_duration=1800,  # 30 minutos
                max_violations=2,
                level=RateLimitLevel.HIGH
            )
        }
    
    def add_config(self, endpoint: str, config: RateLimitConfig):
        """Adicionar configuração personalizada para endpoint"""
        self.configs[endpoint] = config
        logger.info(f"📝 Configuração de rate limiting adicionada para {endpoint}")
    
    def check_rate_limit(self, ip: str, endpoint: str, user_id: str = None) -> RateLimitResult:
        """Verificar se a requisição deve ser permitida"""
        # Verificar se IP está bloqueado
        if self._is_ip_blocked(ip):
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=datetime.now() + timedelta(seconds=self.blocked_ips.get(ip, 300)),
                retry_after=self.blocked_ips.get(ip, 300),
                reason="IP bloqueado por violações repetidas"
            )
        
        # Verificar listas branca/negra
        config = self.configs.get(endpoint, self.configs['api_public'])
        
        if config.blacklist_ips and ip in config.blacklist_ips:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=datetime.now() + timedelta(seconds=config.block_duration),
                reason="IP na lista negra"
            )
        
        if config.whitelist_ips and ip in config.whitelist_ips:
            return RateLimitResult(
                allowed=True,
                remaining=config.requests_per_window,
                reset_time=datetime.now() + timedelta(seconds=config.window_size),
                reason="IP na lista branca"
            )
        
        # Verificar limite baseado na estratégia configurada
        if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(ip, endpoint, user_id, config)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(ip, endpoint, user_id, config)
        elif config.strategy == RateLimitStrategy.ADAPTIVE:
            return self._check_adaptive(ip, endpoint, user_id, config)
        else:
            return self._check_fixed_window(ip, endpoint, user_id, config)
    
    def _check_sliding_window(self, ip: str, endpoint: str, user_id: str, config: RateLimitConfig) -> RateLimitResult:
        """Implementar rate limiting com janela deslizante"""
        now = time.time()
        key = self._get_rate_limit_key(ip, endpoint, user_id)
        
        # Obter histórico de requisições
        data = self.storage.get(key) or {'requests': [], 'violations': 0}
        requests = deque(data.get('requests', []))
        
        # Remover requisições fora da janela
        cutoff_time = now - config.window_size
        while requests and requests[0] < cutoff_time:
            requests.popleft()
        
        # Verificar limite de rajada (burst)
        recent_requests = [r for r in requests if r > now - config.burst_window]
        if len(recent_requests) >= config.burst_limit:
            self._record_violation(ip, endpoint, "Burst limit exceeded")
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=datetime.now() + timedelta(seconds=config.burst_window),
                retry_after=config.burst_window,
                reason="Limite de rajada excedido",
                violation_count=data.get('violations', 0) + 1
            )
        
        # Verificar limite da janela principal
        if len(requests) >= config.requests_per_window:
            self._record_violation(ip, endpoint, "Window limit exceeded")
            oldest_request = requests[0]
            reset_time = oldest_request + config.window_size
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=datetime.fromtimestamp(reset_time),
                retry_after=int(reset_time - now),
                reason="Limite da janela excedido",
                violation_count=data.get('violations', 0) + 1
            )
        
        # Permitir requisição
        requests.append(now)
        
        # Salvar dados atualizados
        self.storage.set(key, {
            'requests': list(requests),
            'violations': data.get('violations', 0)
        }, ttl=config.window_size * 2)
        
        remaining = config.requests_per_window - len(requests)
        next_reset = now + config.window_size
        
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_time=datetime.fromtimestamp(next_reset),
            reason="Permitido"
        )
    
    def _check_token_bucket(self, ip: str, endpoint: str, user_id: str, config: RateLimitConfig) -> RateLimitResult:
        """Implementar rate limiting com token bucket"""
        now = time.time()
        key = self._get_rate_limit_key(ip, endpoint, user_id)
        
        data = self.storage.get(key) or {
            'tokens': config.requests_per_window,
            'last_refill': now
        }
        
        # Calcular tokens a serem adicionados
        time_passed = now - data['last_refill']
        tokens_to_add = (time_passed / config.window_size) * config.requests_per_window
        
        # Atualizar tokens
        current_tokens = min(
            config.requests_per_window,
            data['tokens'] + tokens_to_add
        )
        
        if current_tokens < 1:
            # Não há tokens suficientes
            time_to_next_token = config.window_size / config.requests_per_window
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=datetime.fromtimestamp(now + time_to_next_token),
                retry_after=int(time_to_next_token),
                reason="Tokens insuficientes"
            )
        
        # Consumir um token
        current_tokens -= 1
        
        # Salvar estado atualizado
        self.storage.set(key, {
            'tokens': current_tokens,
            'last_refill': now
        }, ttl=config.window_size * 2)
        
        return RateLimitResult(
            allowed=True,
            remaining=int(current_tokens),
            reset_time=datetime.fromtimestamp(now + config.window_size),
            reason="Token consumido"
        )
    
    def _check_adaptive(self, ip: str, endpoint: str, user_id: str, config: RateLimitConfig) -> RateLimitResult:
        """Rate limiting adaptativo baseado no comportamento"""
        # Analisar padrões de comportamento
        behavior_score = self._calculate_behavior_score(ip, endpoint, user_id)
        
        # Ajustar limites baseado no score
        if behavior_score >= 0.8:  # Comportamento suspeito
            adjusted_config = RateLimitConfig(
                requests_per_window=config.requests_per_window // 4,
                window_size=config.window_size,
                burst_limit=config.burst_limit // 2,
                block_duration=config.block_duration * 2,
                max_violations=config.max_violations // 2,
                level=RateLimitLevel.CRITICAL
            )
        elif behavior_score >= 0.6:  # Comportamento questionável
            adjusted_config = RateLimitConfig(
                requests_per_window=config.requests_per_window // 2,
                window_size=config.window_size,
                burst_limit=config.burst_limit,
                block_duration=config.block_duration,
                max_violations=config.max_violations,
                level=RateLimitLevel.HIGH
            )
        else:  # Comportamento normal
            adjusted_config = config
        
        # Usar janela deslizante com configuração ajustada
        return self._check_sliding_window(ip, endpoint, user_id, adjusted_config)
    
    def _calculate_behavior_score(self, ip: str, endpoint: str, user_id: str) -> float:
        """Calcular score de comportamento suspeito (0.0 = normal, 1.0 = muito suspeito)"""
        score = 0.0
        
        # Verificar se IP é suspeito
        if self.ip_validator.is_suspicious_ip(ip):
            score += 0.3
        
        # Verificar histórico de violações
        violations = len(self.violation_tracker.get(ip, []))
        if violations > 5:
            score += 0.4
        elif violations > 2:
            score += 0.2
        
        # Verificar padrões de tempo (requests muito rápidas)
        key = self._get_rate_limit_key(ip, endpoint, user_id)
        data = self.storage.get(key) or {'requests': []}
        requests = data.get('requests', [])
        
        if len(requests) >= 3:
            recent_requests = requests[-3:]
            intervals = [recent_requests[i] - recent_requests[i-1] for i in range(1, len(recent_requests))]
            avg_interval = sum(intervals) / len(intervals)
            
            if avg_interval < 0.1:  # Muito rápido (suspeito de bot)
                score += 0.3
            elif avg_interval < 0.5:
                score += 0.1
        
        return min(1.0, score)
    
    def _check_fixed_window(self, ip: str, endpoint: str, user_id: str, config: RateLimitConfig) -> RateLimitResult:
        """Implementar rate limiting com janela fixa"""
        now = time.time()
        window_start = int(now // config.window_size) * config.window_size
        key = f"{self._get_rate_limit_key(ip, endpoint, user_id)}:{window_start}"
        
        current_count = self.storage.increment(key)
        
        if current_count > config.requests_per_window:
            self._record_violation(ip, endpoint, "Fixed window limit exceeded")
            reset_time = window_start + config.window_size
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=datetime.fromtimestamp(reset_time),
                retry_after=int(reset_time - now),
                reason="Limite da janela fixa excedido"
            )
        
        remaining = config.requests_per_window - current_count
        reset_time = window_start + config.window_size
        
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_time=datetime.fromtimestamp(reset_time),
            reason="Permitido"
        )
    
    def _get_rate_limit_key(self, ip: str, endpoint: str, user_id: str = None) -> str:
        """Gerar chave única para rate limiting"""
        components = [ip, endpoint]
        if user_id:
            components.append(user_id)
        
        key_string = ":".join(components)
        return f"rate_limit:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _record_violation(self, ip: str, endpoint: str, reason: str):
        """Registrar violação de rate limiting"""
        now = datetime.now()
        
        # Registrar no tracker de violações
        if ip not in self.violation_tracker:
            self.violation_tracker[ip] = []
        
        self.violation_tracker[ip].append({
            'timestamp': now,
            'endpoint': endpoint,
            'reason': reason
        })
        
        # Limpar violações antigas (> 24 horas)
        cutoff = now - timedelta(days=1)
        self.violation_tracker[ip] = [
            v for v in self.violation_tracker[ip]
            if v['timestamp'] > cutoff
        ]
        
        # Verificar se deve bloquear IP
        config = self.configs.get(endpoint, self.configs['api_public'])
        recent_violations = [
            v for v in self.violation_tracker[ip]
            if v['timestamp'] > now - timedelta(hours=1)
        ]
        
        if len(recent_violations) >= config.max_violations:
            self._block_ip(ip, config.block_duration)
        
        # Log da violação
        logger.warning(
            f"🚨 Rate limit violation - IP: {ip}, Endpoint: {endpoint}, "
            f"Reason: {reason}, Violations: {len(recent_violations)}"
        )
    
    def _block_ip(self, ip: str, duration: int):
        """Bloquear IP por um período específico"""
        self.blocked_ips[ip] = duration
        
        # Agendar desbloqueio
        def unblock():
            time.sleep(duration)
            if ip in self.blocked_ips:
                del self.blocked_ips[ip]
                logger.info(f"🔓 IP desbloqueado: {ip}")
        
        threading.Thread(target=unblock, daemon=True).start()
        
        logger.error(f"🔒 IP bloqueado: {ip} por {duration} segundos")
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Verificar se IP está bloqueado"""
        return ip in self.blocked_ips
    
    def get_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do rate limiting"""
        total_violations = sum(len(violations) for violations in self.violation_tracker.values())
        blocked_ips_count = len(self.blocked_ips)
        
        return {
            'total_violations': total_violations,
            'blocked_ips': blocked_ips_count,
            'blocked_ip_list': list(self.blocked_ips.keys()),
            'violation_by_ip': {
                ip: len(violations) 
                for ip, violations in self.violation_tracker.items()
            },
            'configs': {
                endpoint: asdict(config) 
                for endpoint, config in self.configs.items()
            }
        }

# Instância global do rate limiter
rate_limiter = AdvancedRateLimiter()

def rate_limit(endpoint: str = 'default', get_ip_func: callable = None, get_user_id_func: callable = None):
    """
    Decorator para aplicar rate limiting em funções
    
    Args:
        endpoint: Nome do endpoint para configuração específica
        get_ip_func: Função para extrair IP da requisição
        get_user_id_func: Função para extrair ID do usuário
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extrair IP e user_id
            ip = "127.0.0.1"  # Default
            user_id = None
            
            if get_ip_func:
                try:
                    ip = get_ip_func(*args, **kwargs)
                except:
                    pass
            
            if get_user_id_func:
                try:
                    user_id = get_user_id_func(*args, **kwargs)
                except:
                    pass
            
            # Verificar rate limiting
            result = rate_limiter.check_rate_limit(ip, endpoint, user_id)
            
            if not result.allowed:
                raise RateLimitException(
                    f"Rate limit exceeded: {result.reason}",
                    retry_after=result.retry_after,
                    details={
                        'endpoint': endpoint,
                        'remaining': result.remaining,
                        'reset_time': result.reset_time.isoformat(),
                        'violation_count': result.violation_count
                    }
                )
            
            # Executar função original
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Funções utilitárias para integração com Flask/Dash
def get_client_ip_from_request(request=None):
    """Extrair IP do cliente da requisição Flask"""
    if not request:
        try:
            from flask import request as flask_request
            request = flask_request
        except ImportError:
            return "127.0.0.1"
    
    # Verificar headers de proxy
    forwarded_ips = request.headers.get('X-Forwarded-For')
    if forwarded_ips:
        return forwarded_ips.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.remote_addr or "127.0.0.1"

def create_rate_limit_response(result: RateLimitResult) -> Dict[str, Any]:
    """Criar resposta estruturada para rate limiting"""
    return {
        'error': 'Rate limit exceeded',
        'message': result.reason,
        'retry_after': result.retry_after,
        'remaining': result.remaining,
        'reset_time': result.reset_time.isoformat() if result.reset_time else None,
        'violation_count': result.violation_count
    }

if __name__ == "__main__":
    # Teste básico do sistema
    limiter = AdvancedRateLimiter()
    
    # Teste normal
    result = limiter.check_rate_limit("192.168.1.1", "test_endpoint")
    logger.info(f"Teste 1 - Permitido: {result.allowed}, Restante: {result.remaining}")
    
    # Teste de limite
    for i in range(65):  # Exceder limite padrão
        result = limiter.check_rate_limit("192.168.1.2", "api_public")
        if not result.allowed:
            logger.info(f"Teste 2 - Bloqueado na tentativa {i+1}: {result.reason}")
            break
    
    # Mostrar estatísticas
    stats = limiter.get_stats()
    logger.info(f"Estatísticas: {json.dumps(stats, indent=2, default=str)}")
