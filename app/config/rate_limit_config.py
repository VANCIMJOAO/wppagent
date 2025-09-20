"""
Configuração de Rate Limiting por Usuário
"""

# Configurações de limite por endpoint (requests per window)
ENDPOINT_RATE_LIMITS = {
    # Health checks - alto volume permitido
    "GET /health": {"requests": 1000, "window": 60},
    "HEAD /health": {"requests": 1000, "window": 60},
    "GET /health/detailed": {"requests": 100, "window": 60},
    # Webhook - crítico, limite moderado
    "POST /webhook": {"requests": 500, "window": 60, "burst": 50},
    "GET /webhook/status": {"requests": 100, "window": 60},
    # Autenticação - limite restrito por segurança
    "POST /auth/login": {"requests": 10, "window": 300, "burst": 3},  # 5 min window
    "POST /auth/refresh": {"requests": 20, "window": 60, "burst": 5},
    "POST /auth/logout": {"requests": 5, "window": 60},
    # Admin endpoints - limite alto para admins, será multiplicado
    "POST /admin/auth/login": {"requests": 20, "window": 300, "burst": 5},
    "GET /admin/rate-limit/status": {"requests": 100, "window": 60},
    "POST /admin/rate-limit/reset": {"requests": 50, "window": 60},
    "GET /admin/rate-limit/config": {"requests": 100, "window": 60},
    "POST /admin/rate-limit/config/update": {"requests": 20, "window": 60},
    # RBAC endpoints - aumentar limites
    "GET /admin/rbac/permissions": {"requests": 200, "window": 60},
    "GET /admin/rbac/roles": {"requests": 200, "window": 60},
    "GET /admin/rbac/users": {"requests": 200, "window": 60},
    "POST /admin/rbac/assign": {"requests": 100, "window": 60},
    # Export endpoints - aumentar limites
    "GET /admin/export/appointments/csv": {"requests": 50, "window": 60},
    "GET /admin/export/conversations/excel": {"requests": 50, "window": 60},
    "GET /admin/export/analytics/pdf": {"requests": 50, "window": 60},
    # LGPD endpoints - aumentar limites
    "GET /admin/lgpd/dashboard": {"requests": 100, "window": 60},
    "GET /admin/lgpd/audit": {"requests": 100, "window": 60},
    "GET /admin/lgpd/export": {"requests": 50, "window": 60},
    "GET /admin/lgpd/retention": {"requests": 50, "window": 60},
    # Dashboard endpoints - limite moderado
    "GET /dashboard": {"requests": 200, "window": 60},
    "GET /dashboard/analytics": {"requests": 100, "window": 60},
    "GET /dashboard/clients": {"requests": 300, "window": 60},
    "GET /dashboard/conversations": {"requests": 500, "window": 60},
    "GET /dashboard/appointments": {"requests": 200, "window": 60},
    # API endpoints de dados
    "GET /clients": {"requests": 100, "window": 60},
    "POST /clients": {"requests": 20, "window": 60},
    "PUT /clients": {"requests": 50, "window": 60},
    "DELETE /clients": {"requests": 10, "window": 60},
    "GET /conversations": {"requests": 200, "window": 60},
    "POST /conversations": {"requests": 100, "window": 60},
    "GET /appointments": {"requests": 150, "window": 60},
    "POST /appointments": {"requests": 30, "window": 60},
    "PUT /appointments": {"requests": 50, "window": 60},
    # WebSocket - limite alto para tempo real
    "GET /ws": {"requests": 10, "window": 60},  # Conexões WebSocket
    # Backup endpoints - admin apenas, limite restrito
    "GET /admin/backup/status": {"requests": 50, "window": 60},
    "POST /admin/backup/trigger": {"requests": 5, "window": 300},  # 5 min window
    "GET /admin/backup/list": {"requests": 30, "window": 60},
    "DELETE /admin/backup/cleanup": {"requests": 3, "window": 600},  # 10 min window
    # Security endpoints - limite muito restrito
    "POST /security/encrypt": {"requests": 50, "window": 60},
    "POST /security/decrypt": {"requests": 50, "window": 60},
    # Metrics e monitoring - limite alto
    "GET /metrics": {"requests": 500, "window": 60},
    "GET /admin/alerts/status": {"requests": 100, "window": 60},
    # Default para endpoints não especificados
    "default": {"requests": 60, "window": 60, "burst": 10},
}

# Multiplicadores por tipo de usuário
USER_TYPE_MULTIPLIERS = {
    "admin": 2.0,  # Admins têm 2x o limite
    "premium": 1.5,  # Usuários premium têm 1.5x o limite
    "regular": 1.0,  # Usuários regulares têm limite normal
    "guest": 0.5,  # Visitantes têm metade do limite
}

# Configurações especiais por endpoint para diferentes tipos de usuário
ENDPOINT_USER_OVERRIDES = {
    # Admins têm limites ainda maiores para endpoints críticos
    "admin": {
        "POST /admin/backup/trigger": {"requests": 10, "window": 300},
        "DELETE /admin/backup/cleanup": {"requests": 10, "window": 600},
        "POST /admin/rate-limit/config/update": {"requests": 50, "window": 60},
    },
    # Usuários premium têm limites maiores para dashboard
    "premium": {
        "GET /dashboard/analytics": {"requests": 200, "window": 60},
        "GET /conversations": {"requests": 400, "window": 60},
    },
    # Guests têm limites muito restritos
    "guest": {
        "POST /webhook": {"requests": 50, "window": 60, "burst": 5},
        "GET /dashboard": {"requests": 30, "window": 60},
        "default": {"requests": 20, "window": 60, "burst": 3},
    },
}

# Configurações de Redis para rate limiting
REDIS_CONFIG = {
    "key_prefix": "rate_limit",
    "ip_key_prefix": "rate_limit:ip",
    "ttl_buffer": 10,  # Segundos extras para TTL das chaves
    "cleanup_interval": 3600,  # Limpeza de chaves expiradas (1 hora)
}

# Configurações de logging para rate limiting
LOGGING_CONFIG = {
    "log_violations": True,
    "log_level": "INFO",
    "include_user_agent": True,
    "include_ip": True,
    "violation_log_format": "Rate limit violation: {user_id} - {endpoint} - {violation_type} - {current}/{limit}",
    "performance_log_threshold": 0.1,  # Log se check demorar mais que 100ms
}

# Headers HTTP para rate limiting
RATE_LIMIT_HEADERS = {
    "limit_header": "X-RateLimit-Limit",
    "remaining_header": "X-RateLimit-Remaining",
    "reset_header": "X-RateLimit-Reset",
    "retry_after_header": "Retry-After",
}

# Configurações de degradação graciosa
GRACEFUL_DEGRADATION = {
    "redis_timeout": 1.0,  # Timeout para operações Redis (segundos)
    "max_retries": 2,  # Tentativas de reconexão Redis
    "fallback_mode": "allow",  # "allow" ou "deny" quando Redis não disponível
    "health_check_interval": 30,  # Verificar saúde do Redis a cada 30s
}

# Endpoints que são isentos de rate limiting
EXEMPT_ENDPOINTS = {
    "GET /health",  # Health check básico sempre permitido
    "HEAD /health",  # Health check HEAD sempre permitido
    "GET /ping",  # Railway healthcheck sempre permitido
    "HEAD /ping",  # Railway healthcheck HEAD sempre permitido
    "OPTIONS /*",  # Preflight CORS sempre permitido
}
