# 📚 API Documentation - WhatsApp Agent v2.0

> **Comprehensive API Reference** with 355 endpoints, advanced security features, performance optimizations, and enterprise-grade compliance.

---

## 🎯 **API OVERVIEW**

### **Base Information**
- **Base URL**: `https://api.whatsappagent.com`  
- **API Version**: `v2.0.0`
- **Protocol**: `HTTPS only`
- **Format**: `JSON`
- **Charset**: `UTF-8`
- **Total Endpoints**: `355`

### **Architecture Overview** 🏗️
```
📦 API Categories (355 endpoints total)
├── 🛡️ Admin System (78 endpoints)
│   ├── Backup Management (10 endpoints)
│   ├── Rate Limiting Control (8 endpoints)
│   ├── User Management (15 endpoints)
│   └── System Administration (45 endpoints)
├── 🔐 Authentication & Security (16 endpoints)
│   ├── Login/Logout/Refresh (5 endpoints)
│   ├── Two-Factor Authentication (6 endpoints)
│   └── Session Management (5 endpoints)
├── 📊 Health & Monitoring (31 endpoints)
│   ├── System Health (8 endpoints)
│   ├── Performance Metrics (12 endpoints)
│   └── Documentation (11 endpoints)
├── 🔗 WhatsApp Webhooks (7 endpoints)
├── 🛡️ LGPD Compliance (8 endpoints)
├── 🧪 Demo & Testing (12 endpoints)
└── 🚀 Core Business API (203 endpoints)
    ├── Conversations & Messages (45 endpoints)
    ├── Appointments (38 endpoints)
    ├── Client Management (32 endpoints)
    ├── Analytics & BI (25 endpoints)
    ├── Real-time WebSocket (15 endpoints)
    ├── Export System (18 endpoints)
    └── Business Logic (30 endpoints)
```

### **Key Features** ✨
- 🍪 **HttpOnly Cookie Authentication** (XSS protection)
- 🔒 **2FA with backup codes** (TOTP support)
- 🛡️ **Advanced Rate Limiting** (per-user, per-IP, per-webhook)
- 🚫 **DDoS Protection** (automated blocking)
- 📝 **Log Sanitization** (LGPD compliant)
- 🎯 **CSP Headers** (content security policy)
- ⚡ **N+1 Query Elimination** (optimized database)
- 🗄️ **Redis Cache** (intelligent invalidation)
- 📈 **Real-time Analytics** (WebSocket powered)
- 📄 **LGPD Compliance** (data portability, retention)

---

## 🔐 **AUTHENTICATION & SECURITY**

### **HttpOnly Cookie Authentication System**

O sistema utiliza cookies HttpOnly para máxima segurança, prevenindo ataques XSS e CSRF.

#### **1. Login Principal**
```http
POST /auth/auth/login
Content-Type: application/json

{
  "username": "admin@company.com",
  "password": "secure_password_123",
  "remember_me": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Login realizado com sucesso",
    "user_id": 123,
    "permissions": ["admin", "read", "write"],
    "expires_at": "2025-09-15T14:00:00Z",
    "requires_2fa": true,
    "session_id": "sess_abc123...",
    "last_login": "2025-09-15T13:00:00Z"
  }
}
```

**Cookies Definidos Automaticamente:**
- `access_token`: JWT principal (HttpOnly, Secure, SameSite=Strict, 1h TTL)
- `refresh_token`: Token refresh (HttpOnly, Secure, SameSite=Strict, 7d TTL)
- `csrf_token`: Proteção CSRF (Secure, SameSite=Strict)

#### **2. Two-Factor Authentication**
```http
POST /auth/auth/2fa/setup
Cookie: access_token=...; csrf_token=...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "secret": "JBSWY3DPEHPK3PXP",
    "backup_codes": [
      "12345678", "87654321", "11223344", 
      "55667788", "99887766", "44332211"
    ],
    "recovery_url": "https://app.com/auth/recovery?token=...",
    "expires_in": 300
  }
}
```

```http
POST /auth/auth/2fa/verify
Content-Type: application/json
Cookie: access_token=...; csrf_token=...

{
  "token": "123456",
  "type": "totp"
}
```

```http
POST /auth/auth/2fa/confirm
Content-Type: application/json
Cookie: access_token=...

{
  "token": "654321",
  "backup_code_acknowledged": true
}
```

#### **3. Session Management**
```http
POST /auth/auth/refresh
Cookie: refresh_token=...
```

```http
POST /auth/auth/logout
Cookie: access_token=...; refresh_token=...
```

```http
GET /auth/auth/rate-limit/status
Cookie: access_token=...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "requests_remaining": 85,
    "reset_time": "2025-09-15T14:00:00Z",
    "window_size": "1 hour",
    "limit": 100,
    "current_usage": 15
  }
}
```

---

## 🛡️ **ADMIN SYSTEM (78 ENDPOINTS)**

### **Backup Management**
```http
GET    /admin/backup/status              # Status do sistema
POST   /admin/backup/trigger             # Executar backup manual
GET    /admin/backup/list                # Listar backups
GET    /admin/backup/download/{filename} # Download backup
DELETE /admin/backup/cleanup             # Limpeza automática
POST   /admin/backup/schedule/update     # Atualizar schedule
GET    /admin/backup/logs                # Logs de backup
GET    /admin/backup/health              # Health check backup
POST   /admin/backup/verify/{filename}   # Verificar integridade
GET    /admin/backup/config              # Configuração atual
```

### **Rate Limiting & DDoS Protection** 
```http
GET    /admin/h003/overview              # Dashboard rate limiting
GET    /admin/h003/stats/{client_ip}     # Estatísticas por IP
DELETE /admin/h003/clear/{client_ip}     # Remover bloqueio
GET    /admin/h003/logs                  # Logs detalhados
POST   /admin/h003/test/compliance       # Teste H003 compliance
GET    /admin/h003/health-check-test     # Teste health check exemption
GET    /admin/rate-limit/config          # Configuração atual
POST   /admin/rate-limit/config/update   # Atualizar configuração
GET    /admin/rate-limit/health          # Health rate limiting
POST   /admin/rate-limit/reset           # Reset contadores
```

### **User Management**
```http
POST   /admin/create                     # Criar usuário admin
POST   /admin/create-initial-admin       # Setup inicial
GET    /admin/me                         # Info admin atual
POST   /admin/login                      # Login administrativo
POST   /admin/logout                     # Logout administrativo
POST   /admin/debug-admin                # Debug modo admin
GET    /admin/debug-jwt                  # Debug JWT tokens
GET    /admin/health                     # Health check auth
```

---

## 📊 **HEALTH & MONITORING (31 ENDPOINTS)**

### **System Health**
```http
GET /health                    # Health check básico
GET /health/detailed          # Health check detalhado
GET /database/health          # Status banco de dados
GET /cache/api/cache/health   # Status Redis cache
GET /analytics/health         # Status analytics
GET /api/alerts/health        # Status sistema alertas
GET /api/lgpd/health         # Status compliance LGPD
GET /api/rbac/health         # Status RBAC system
```

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-15T13:30:00Z",
  "version": "2.0.0",
  "environment": "production",
  "uptime_seconds": 86400,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 12,
      "active_connections": 15,
      "query_performance": "optimized"
    },
    "redis_cache": {
      "status": "healthy",
      "hit_rate": "94.8%",
      "memory_usage": "67.2MB",
      "invalidation_events": 1247
    },
    "rate_limiting": {
      "status": "active",
      "blocked_ips": 3,
      "requests_per_minute": 1580
    },
    "lgpd_compliance": {
      "status": "compliant",
      "retention_policies": "active",
      "data_requests": 45
    }
  }
}
```

### **Documentation & API**
```http
GET /docs                     # Documentação OpenAPI
GET /openapi.json            # Schema OpenAPI
GET /redoc                   # Documentação ReDoc
```

---

## 🔗 **WHATSAPP WEBHOOKS (7 ENDPOINTS)**

### **Core Webhook System**
```http
POST /webhook                 # Webhook principal WhatsApp
GET  /webhook/verify         # Verificação webhook
GET  /webhook/stats          # Estatísticas webhook
GET  /webhook/performance-stats  # Métricas performance
POST /webhook/clear-cache    # Limpar cache webhook
POST /debug/webhook-test     # Teste webhook (dev)
GET  /public/webhook-secret-info  # Info pública webhook
```

**Webhook Payload Example:**
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "business_account_id",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "5511999999999",
          "phone_number_id": "123456789"
        },
        "messages": [{
          "from": "5511888888888",
          "id": "wamid.HBgMNTUxMQ==",
          "timestamp": "1694781234",
          "text": {"body": "Olá, gostaria de agendar uma consulta"},
          "type": "text"
        }]
      },
      "field": "messages"
    }]
  }]
}
```

---

## 🛡️ **LGPD COMPLIANCE (8 ENDPOINTS)**

### **Data Rights Management**
```http
GET  /api/lgpd/my-data                    # Dados pessoais
POST /api/lgpd/data-portability          # Solicitar portabilidade
GET  /api/lgpd/data-portability/{id}/download  # Download dados
POST /api/lgpd/delete-account            # Exclusão de conta
GET  /api/lgpd/privacy-policy            # Política privacidade
GET  /api/lgpd/user-rights               # Direitos do usuário
GET  /api/lgpd/data-processing-report    # Relatório processamento
POST /api/lgpd/apply-retention-policies  # Aplicar retenção
```

**Data Portability Response:**
```json
{
  "success": true,
  "data": {
    "request_id": "lgpd_req_123456",
    "status": "processing",
    "estimated_completion": "2025-09-16T13:30:00Z",
    "data_categories": [
      "personal_info", "appointments", "messages", 
      "preferences", "analytics_data"
    ],
    "format": "JSON",
    "encryption": "AES-256",
    "retention_period": "30 days"
  }
}
```

---

## 🚀 **CORE BUSINESS API (203 ENDPOINTS)**

### **🎯 Conversations & Messages (45 endpoints)**

#### **Optimized Queries (N+1 Elimination)**
```http
GET /api/v1/conversations?include=messages,client,business&limit=20
Authorization: Cookie (HttpOnly)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "conversations": [{
      "id": 123,
      "client_id": 456,
      "business_id": 789,
      "status": "active",
      "last_message_at": "2025-09-15T13:25:00Z",
      "unread_count": 3,
      "client": {
        "id": 456,
        "name": "João Silva",
        "phone": "+5511999999999",
        "preferences": {"language": "pt-BR"}
      },
      "business": {
        "id": 789,
        "name": "Clínica Saúde",
        "category": "healthcare"
      },
      "messages": [{
        "id": 1001,
        "content": "Olá, gostaria de agendar uma consulta",
        "direction": "inbound",
        "timestamp": "2025-09-15T13:25:00Z",
        "status": "delivered",
        "message_type": "text"
      }],
      "performance_metrics": {
        "query_time_ms": 45,
        "cache_hit": true,
        "n_plus_one_eliminated": true
      }
    }],
    "pagination": {
      "current_page": 1,
      "total_pages": 12,
      "total_items": 234,
      "has_next": true
    }
  }
}
```

#### **Real-time Messages**
```http
POST /api/v1/conversations/{id}/messages
Content-Type: application/json
Cookie: access_token=...

{
  "content": "Sua consulta está confirmada para amanhã às 14:30",
  "message_type": "text",
  "template_name": "appointment_confirmation",
  "template_params": {
    "appointment_time": "14:30",
    "appointment_date": "16/09/2025"
  },
  "priority": "high"
}
```

### **📅 Appointments (38 endpoints)**

#### **Performance Optimized**
```http
GET /api/v1/appointments?optimize=true&include=client,service,business
```

**Optimizations Applied:**
- ✅ **N+1 Query Elimination**: Single query with joins
- ✅ **Redis Caching**: 5-minute cache with intelligent invalidation
- ✅ **Database Indexing**: Optimized indexes on date, status
- ✅ **Query Analytics**: Real-time performance monitoring

```http
POST /api/v1/appointments
Content-Type: application/json
Cookie: access_token=...

{
  "client_id": 456,
  "service_id": 101,
  "business_id": 789,
  "appointment_date": "2025-09-16",
  "appointment_time": "14:30:00",
  "notes": "Consulta de rotina",
  "auto_confirm": false,
  "send_whatsapp": true,
  "reminder_settings": {
    "enabled": true,
    "intervals": ["24h", "2h", "30m"]
  }
}
```

### **📊 Advanced Analytics & BI (25 endpoints)**

#### **Business Intelligence Dashboard**
```http
GET /analytics/advanced/dashboard-summary
Cookie: access_token=...
```

```http
GET /analytics/advanced/conversion-funnel
GET /analytics/advanced/churn-prediction  
GET /analytics/advanced/customer-segmentation
GET /analytics/advanced/roi-metrics
```

**Analytics Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_appointments": 1247,
      "conversion_rate": 0.847,
      "average_revenue": 156.78,
      "customer_satisfaction": 4.6,
      "churn_prediction": {
        "high_risk_clients": 23,
        "predicted_churn_rate": 0.12,
        "retention_opportunities": 156
      }
    },
    "funnel_analysis": {
      "stages": [
        {"stage": "contact", "count": 1000, "conversion": 1.0},
        {"stage": "interest", "count": 850, "conversion": 0.85},
        {"stage": "appointment", "count": 720, "conversion": 0.72},
        {"stage": "completed", "count": 610, "conversion": 0.61}
      ]
    },
    "generated_at": "2025-09-15T13:30:00Z",
    "cache_info": {"hit": true, "ttl": 300}
  }
}
```

### **🌐 Real-time WebSocket (15 endpoints)**

#### **WebSocket Connections**
```javascript
// Client-side connection
const ws = new WebSocket('wss://api.whatsappagent.com/api/websocket/ws');

// Available channels:
ws.send(JSON.stringify({
  "action": "subscribe",
  "channel": "appointments",
  "filters": {"business_id": 789}
}));

ws.send(JSON.stringify({
  "action": "subscribe", 
  "channel": "messages",
  "filters": {"conversation_id": 123}
}));
```

**WebSocket Routes:**
```http
WebSocket /api/websocket/ws                    # Conexão principal
WebSocket /api/websocket/ws/chat              # Chat tempo real
WebSocket /api/websocket/ws/notifications     # Notificações
WebSocket /api/websocket/ws/appointments      # Updates agendamentos
WebSocket /api/websocket/ws/analytics         # Métricas tempo real
```

### **📄 Export System (18 endpoints)**

#### **Data Export**
```http
GET /api/export/conversations/csv?date_from=2025-09-01&date_to=2025-09-15
GET /api/export/appointments/excel?business_id=789
GET /api/export/analytics/pdf?type=monthly_report
POST /api/reports/generate
```

**Export Request:**
```json
{
  "report_type": "comprehensive",
  "format": "excel",
  "data_sources": ["appointments", "conversations", "analytics"],
  "date_range": {
    "start": "2025-09-01",
    "end": "2025-09-15"
  },
  "filters": {
    "business_id": 789,
    "include_sensitive": false
  },
  "delivery": {
    "method": "download", 
    "encryption": true,
    "password_protected": true
  }
}
```

---

## 🛡️ **ADVANCED SECURITY FEATURES**

### **Rate Limiting System**

#### **Multi-layer Protection**
- 🚦 **User-based**: 100 req/min per authenticated user
- 🌐 **IP-based**: 200 req/min per IP address  
- 🔗 **Webhook-specific**: 100 req/min per webhook endpoint
- 🚨 **DDoS Protection**: Automatic IP blocking for abuse

#### **Rate Limit Headers**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1694781600
X-RateLimit-Retry-After: 45
```

### **Content Security Policy (CSP)**
```http
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self';
  frame-ancestors 'none';
```

### **Log Sanitization (S002 Protection)**
Proteção automática contra exposição de dados sensíveis:
- 🔒 **PII Sanitization**: CPF, RG, cartões de crédito
- 🔑 **Credential Protection**: Senhas, tokens, API keys
- 📞 **Phone Number Masking**: Últimos 4 dígitos apenas
- 📧 **Email Masking**: Domínio preservado, usuário mascarado

### **HTTPS & Security Headers**
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
X-Permitted-Cross-Domain-Policies: none
Referrer-Policy: strict-origin-when-cross-origin
```

---

## ⚡ **PERFORMANCE & OPTIMIZATION**

### **Database Optimizations (PF-001)**
- ✅ **N+1 Query Elimination**: Eager loading com joins otimizados
- ✅ **Query Performance Monitoring**: Alertas automáticos para queries lentas
- ✅ **Database Connection Pooling**: Pool otimizado para alta concorrência
- ✅ **Index Optimization**: Indexes automáticos baseados em usage patterns

### **Redis Cache System**
- 🗄️ **Intelligent Invalidation**: 10 eventos de cache configurados
- ⚡ **Cache Hit Rate**: 94.8% average hit rate
- 🔄 **Auto-refresh**: Background cache warming
- 📊 **Cache Analytics**: Detailed metrics e monitoring

**Cache Events:**
```javascript
// Automatic cache invalidation events
CacheEvent.APPOINTMENT_CREATED   → Invalidates 10 patterns
CacheEvent.APPOINTMENT_UPDATED   → Invalidates 7 patterns  
CacheEvent.CONVERSATION_CREATED  → Invalidates 8 patterns
CacheEvent.CLIENT_UPDATED        → Invalidates 6 patterns
// ... total 10 cache events configured
```

---

## 📖 **ERROR HANDLING & STATUS CODES**

### **Standardized Response Format (C002)**
```json
{
  "success": true|false,
  "data": { ... },
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... },
    "timestamp": "2025-09-15T13:30:00Z",
    "trace_id": "req_123456789"
  },
  "meta": {
    "version": "2.0.0",
    "endpoint": "/api/v1/appointments",
    "method": "GET",
    "cache_info": { ... },
    "performance": {
      "query_time_ms": 45,
      "total_time_ms": 67
    }
  }
}
```

### **HTTP Status Codes**
- `200` OK - Sucesso
- `201` Created - Recurso criado
- `400` Bad Request - Dados inválidos
- `401` Unauthorized - Não autenticado
- `403` Forbidden - Sem permissão
- `404` Not Found - Recurso não encontrado
- `429` Too Many Requests - Rate limit excedido
- `500` Internal Server Error - Erro interno

### **Error Codes**
- `AUTH001` - Token inválido ou expirado
- `AUTH002` - 2FA necessário
- `RATE001` - Rate limit excedido
- `LGPD001` - Violação política privacidade
- `PERF001` - Query performance degradada
- `CACHE001` - Cache miss crítico

---

## 🧪 **DEMO & TESTING ENDPOINTS (12 ENDPOINTS)**

### **Performance Demos**
```http
GET /appointments-demo/before        # Queries não otimizadas
GET /appointments-demo/after         # Queries otimizadas (PF-001)
GET /performance-demo/appointments/optimized  # Demo N+1 elimination
GET /performance-demo/conversations/batch-with-counts  # Batch loading
```

### **Error Demos**
```http
GET /appointments-demo/error-demo           # Demonstração error handling
GET /appointments-demo/validation-error-demo  # Validation errors
GET /appointments-demo/server-error-demo    # Server error simulation
```

### **Health Demos**
```http
GET /health-demo/comprehensive              # Health check demo
```

---

## 🔧 **DEVELOPMENT & TESTING**

### **Debug Endpoints** (Development Only)
```http
GET /admin/debug-jwt                 # Debug JWT tokens
POST /admin/debug-admin             # Debug admin functions
POST /debug/webhook-test            # Test webhook functionality
```

### **CORS Configuration**
```javascript
// Allowed origins (development)
origins: [
  'http://localhost:3000',
  'http://localhost:3001', 
  'http://127.0.0.1:3000',
  'https://localhost:3000',
  'http://localhost:8501',
  'http://localhost:8000',
  'http://127.0.0.1:8000'
]

// Methods allowed
methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH']
```

---

## 📝 **CHANGELOG & VERSION HISTORY**

### **v2.0.0** (Current)
- ✅ **355 endpoints** total
- ✅ **HttpOnly Cookie Authentication** 
- ✅ **Advanced Rate Limiting** (H003)
- ✅ **N+1 Query Elimination** (PF-001)
- ✅ **LGPD Compliance** system
- ✅ **Log Sanitization** (S002)
- ✅ **Real-time WebSocket** support
- ✅ **Advanced Analytics** & BI
- ✅ **Export System** (CSV/Excel/PDF)

### **v1.0.0**
- Basic API structure
- Simple JWT authentication
- Core business endpoints

---

## 📞 **SUPPORT & CONTACT**

- **Documentation**: `/docs` (OpenAPI)
- **Health Check**: `/health`
- **Status Page**: `https://status.whatsappagent.com`
- **Support**: `support@whatsappagent.com`

---

*Last updated: 2025-09-15 | API Version: 2.0.0 | Documentation Version: 2.1*