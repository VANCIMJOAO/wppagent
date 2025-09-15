# 📖 Referência Completa da API - WhatsApp Agent

> **Documentação técnica completa** da API REST com exemplos detalhados, códigos de erro, autenticação, rate limiting, webhooks e SDKs para integração empresarial.

---

## 🎯 **VISÃO GERAL DA API**

### **Informações Básicas** 📋

#### **Base URL e Versioning**

```
🌐 Produção: https://api.whatsappagent.com/v1
🧪 Staging: https://staging-api.whatsappagent.com/v1
🔧 Local: http://localhost:8000/v1

📋 Versão Atual: v1.2.0
📅 Última Atualização: 2024-01-15
🔄 API Stability: Stable (SLA 99.9%)
```

#### **Formato de Response**

```json
{
  "success": true,
  "data": { },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123def456",
  "meta": {
    "version": "v1.2.0",
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

#### **Content Types Suportados**

- ✅ `application/json` (padrão)
- ✅ `application/x-www-form-urlencoded`
- ✅ `multipart/form-data` (uploads)
- ✅ `text/plain` (webhooks)

---

## 🔐 **AUTENTICAÇÃO E AUTORIZAÇÃO**

### **JWT Authentication**

#### **Login e Obtenção de Token**

```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@empresa.com",
  "password": "senhaSegura123",
  "remember_me": true
}
```

**Response Success:**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": 123,
      "email": "user@empresa.com",
      "name": "João Silva",
      "role": "admin",
      "business_id": 456,
      "permissions": [
        "appointments:read",
        "appointments:write",
        "users:read",
        "analytics:read"
      ]
    }
  },
  "message": "Login realizado com sucesso"
}
```

#### **Refresh Token**

```http
POST /v1/auth/refresh
Content-Type: application/json
Authorization: Bearer {refresh_token}

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### **Verificar Token Atual**

```http
GET /v1/auth/me
Authorization: Bearer {access_token}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "user_id": 123,
    "email": "user@empresa.com",
    "name": "João Silva",
    "role": "admin",
    "business_id": 456,
    "permissions": ["appointments:read", "appointments:write"],
    "token_expires_at": "2024-01-16T10:30:00Z",
    "last_activity": "2024-01-15T14:22:00Z"
  }
}
```

### **Sistema de Permissões RBAC**

#### **Roles Disponíveis**

```json
{
  "roles": {
    "super_admin": {
      "description": "Acesso total ao sistema",
      "permissions": ["*"]
    },
    "business_admin": {
      "description": "Administrador do negócio",
      "permissions": [
        "business:read", "business:write",
        "users:read", "users:write",
        "appointments:*",
        "analytics:read",
        "whatsapp:*"
      ]
    },
    "manager": {
      "description": "Gerente operacional",
      "permissions": [
        "appointments:*",
        "users:read",
        "analytics:read",
        "whatsapp:read"
      ]
    },
    "operator": {
      "description": "Operador padrão",
      "permissions": [
        "appointments:read",
        "appointments:write",
        "whatsapp:read"
      ]
    },
    "readonly": {
      "description": "Apenas leitura",
      "permissions": [
        "appointments:read",
        "users:read",
        "analytics:read"
      ]
    }
  }
}
```

#### **Headers de Autenticação**

```http
# ✅ Formato correto
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

# ✅ Headers adicionais recomendados
X-Request-ID: req_abc123def456
X-Client-Version: web-app-v2.1.0
User-Agent: WhatsAppAgent-WebApp/2.1.0
```

---

## 📋 **ENDPOINTS DE APPOINTMENTS**

### **Listar Appointments**

```http
GET /v1/appointments
Authorization: Bearer {token}
```

#### **Query Parameters**

```http
GET /v1/appointments?
    business_id=123&
    status=confirmed&
    start_date=2024-01-01&
    end_date=2024-01-31&
    user_id=456&
    service_id=789&
    page=1&
    limit=20&
    sort=appointment_date&
    order=desc&
    search=João Silva
```

**Parâmetros Detalhados:**

- `business_id` (int): ID do negócio
- `status` (string): `pending|confirmed|completed|cancelled|no_show`
- `start_date` (date): Data início filtro (YYYY-MM-DD)
- `end_date` (date): Data fim filtro (YYYY-MM-DD)
- `user_id` (int): ID do usuário responsável
- `service_id` (int): ID do serviço
- `page` (int): Página (padrão: 1)
- `limit` (int): Itens por página (max: 100, padrão: 20)
- `sort` (string): Campo ordenação (appointment_date|created_at|contact_name)
- `order` (string): Direção (asc|desc, padrão: desc)
- `search` (string): Busca por nome, telefone ou email

**Response Success:**

```json
{
  "success": true,
  "data": [
    {
      "id": 789,
      "business_id": 123,
      "user_id": 456,
      "service_id": 321,
      "contact_name": "João Silva",
      "contact_phone": "+5511999887766",
      "contact_email": "joao@email.com",
      "appointment_date": "2024-01-20T14:30:00Z",
      "duration_minutes": 60,
      "status": "confirmed",
      "notes": "Cliente preferencial, pontual",
      "service": {
        "id": 321,
        "name": "Consultoria Empresarial",
        "duration_minutes": 60,
        "price": 250.00
      },
      "user": {
        "id": 456,
        "name": "Maria Santos",
        "email": "maria@empresa.com"
      },
      "reminders": [
        {
          "id": 111,
          "type": "whatsapp",
          "scheduled_for": "2024-01-20T12:30:00Z",
          "status": "pending",
          "message": "Lembrete: Seu agendamento é hoje às 14:30"
        }
      ],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    },
    "filters_applied": {
      "business_id": 123,
      "status": "confirmed",
      "date_range": "2024-01-01 to 2024-01-31"
    }
  }
}
```

### **Criar Appointment**

```http
POST /v1/appointments
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "business_id": 123,
  "service_id": 321,
  "contact_name": "João Silva",
  "contact_phone": "+5511999887766",
  "contact_email": "joao@email.com",
  "appointment_date": "2024-01-20T14:30:00Z",
  "duration_minutes": 60,
  "notes": "Cliente preferencial",
  "send_confirmation": true,
  "reminders": [
    {
      "type": "whatsapp",
      "minutes_before": 120,
      "message": "Lembrete personalizado: Seu agendamento é em 2 horas"
    },
    {
      "type": "email",
      "minutes_before": 1440,
      "message": "Lembrete: Você tem um agendamento amanhã"
    }
  ],
  "custom_fields": {
    "preferencia_horario": "manhã",
    "tipo_atendimento": "presencial"
  }
}
```

**Response Success (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": 789,
    "business_id": 123,
    "service_id": 321,
    "contact_name": "João Silva",
    "contact_phone": "+5511999887766",
    "contact_email": "joao@email.com",
    "appointment_date": "2024-01-20T14:30:00Z",
    "duration_minutes": 60,
    "status": "pending",
    "confirmation_code": "AG789XYZ",
    "whatsapp_sent": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "message": "Agendamento criado com sucesso. Confirmação enviada por WhatsApp."
}
```

### **Atualizar Appointment**

```http
PUT /v1/appointments/{appointment_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body (campos opcionais):**

```json
{
  "appointment_date": "2024-01-20T15:00:00Z",
  "status": "confirmed",
  "notes": "Horário alterado conforme solicitação do cliente",
  "notify_changes": true
}
```

### **Cancelar Appointment**

```http
DELETE /v1/appointments/{appointment_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "cancellation_reason": "Cliente solicitou cancelamento",
  "notify_customer": true,
  "refund_payment": false
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "appointment_id": 789,
    "status": "cancelled",
    "cancelled_at": "2024-01-15T11:30:00Z",
    "cancellation_reason": "Cliente solicitou cancelamento",
    "customer_notified": true
  },
  "message": "Agendamento cancelado com sucesso"
}
```

### **Confirmar Appointment via Webhook**

```http
POST /v1/appointments/{appointment_id}/confirm
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "confirmation_code": "AG789XYZ",
  "confirmed_by": "customer",
  "confirmation_method": "whatsapp"
}
```

---

## 👥 **ENDPOINTS DE USUÁRIOS**

### **Listar Usuários**

```http
GET /v1/users
Authorization: Bearer {token}
```

#### **Query Parameters**

```http
GET /v1/users?
    business_id=123&
    role=manager&
    is_active=true&
    page=1&
    limit=20&
    search=maria
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 456,
      "business_id": 123,
      "name": "Maria Santos",
      "email": "maria@empresa.com",
      "role": "manager",
      "is_active": true,
      "permissions": [
        "appointments:read",
        "appointments:write",
        "users:read"
      ],
      "profile": {
        "phone": "+5511888776655",
        "avatar_url": "https://api.whatsappagent.com/uploads/avatars/456.jpg",
        "timezone": "America/Sao_Paulo",
        "language": "pt-BR"
      },
      "stats": {
        "total_appointments": 245,
        "appointments_this_month": 18,
        "avg_rating": 4.8,
        "last_activity": "2024-01-15T09:15:00Z"
      },
      "created_at": "2023-06-15T08:00:00Z",
      "updated_at": "2024-01-15T09:15:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 12,
      "total_pages": 1
    }
  }
}
```

### **Criar Usuário**

```http
POST /v1/users
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "business_id": 123,
  "name": "Carlos Oliveira",
  "email": "carlos@empresa.com",
  "password": "senhaSegura123",
  "role": "operator",
  "is_active": true,
  "profile": {
    "phone": "+5511777665544",
    "timezone": "America/Sao_Paulo",
    "language": "pt-BR",
    "department": "Atendimento"
  },
  "permissions": [
    "appointments:read",
    "appointments:write"
  ],
  "send_welcome_email": true
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": 789,
    "business_id": 123,
    "name": "Carlos Oliveira",
    "email": "carlos@empresa.com",
    "role": "operator",
    "is_active": true,
    "welcome_email_sent": true,
    "created_at": "2024-01-15T11:30:00Z"
  },
  "message": "Usuário criado com sucesso. Email de boas-vindas enviado."
}
```

### **Atualizar Usuário**

```http
PUT /v1/users/{user_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "name": "Carlos Oliveira Santos",
  "role": "manager",
  "permissions": [
    "appointments:read",
    "appointments:write",
    "users:read",
    "analytics:read"
  ],
  "profile": {
    "phone": "+5511777665544",
    "department": "Gerência"
  }
}
```

---

## 🏢 **ENDPOINTS DE BUSINESSES**

### **Obter Dados do Business**

```http
GET /v1/businesses/{business_id}
Authorization: Bearer {token}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "Clínica Exemplo",
    "email": "contato@clinicaexemplo.com",
    "phone": "+5511444333222",
    "document": "12.345.678/0001-90",
    "address": {
      "street": "Rua das Flores, 123",
      "city": "São Paulo",
      "state": "SP",
      "zip_code": "01234-567",
      "country": "Brasil"
    },
    "settings": {
      "timezone": "America/Sao_Paulo",
      "language": "pt-BR",
      "appointment_duration_default": 60,
      "booking_advance_days": 30,
      "cancellation_hours": 24,
      "working_hours": {
        "monday": {"start": "08:00", "end": "18:00"},
        "tuesday": {"start": "08:00", "end": "18:00"},
        "wednesday": {"start": "08:00", "end": "18:00"},
        "thursday": {"start": "08:00", "end": "18:00"},
        "friday": {"start": "08:00", "end": "17:00"},
        "saturday": {"closed": true},
        "sunday": {"closed": true}
      }
    },
    "whatsapp_config": {
      "phone_number": "+5511999888777",
      "business_verified": true,
      "webhook_enabled": true,
      "auto_reply_enabled": true
    },
    "subscription": {
      "plan": "business",
      "status": "active",
      "expires_at": "2024-12-31T23:59:59Z",
      "features": [
        "unlimited_appointments",
        "whatsapp_integration",
        "analytics_advanced",
        "multi_user"
      ]
    },
    "stats": {
      "total_appointments": 1250,
      "total_users": 8,
      "total_services": 12,
      "appointments_this_month": 95
    },
    "created_at": "2023-01-15T08:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### **Atualizar Business**

```http
PUT /v1/businesses/{business_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "name": "Clínica Exemplo - Unidade Centro",
  "phone": "+5511444333222",
  "settings": {
    "appointment_duration_default": 45,
    "working_hours": {
      "monday": {"start": "07:00", "end": "19:00"},
      "saturday": {"start": "08:00", "end": "12:00", "closed": false}
    }
  },
  "whatsapp_config": {
    "auto_reply_enabled": true,
    "auto_reply_message": "Olá! Recebemos sua mensagem e responderemos em breve."
  }
}
```

---

## 🛍️ **ENDPOINTS DE SERVIÇOS**

### **Listar Serviços**

```http
GET /v1/services
Authorization: Bearer {token}
```

**Query Parameters:**

```http
GET /v1/services?business_id=123&is_active=true&category=consulta
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 321,
      "business_id": 123,
      "name": "Consultoria Empresarial",
      "description": "Consultoria especializada em gestão empresarial",
      "category": "consultoria",
      "duration_minutes": 60,
      "price": 250.00,
      "currency": "BRL",
      "is_active": true,
      "booking_settings": {
        "advance_booking_days": 7,
        "cancellation_hours": 24,
        "max_bookings_per_day": 5,
        "buffer_minutes": 15
      },
      "custom_fields": [
        {
          "name": "tipo_consulta",
          "label": "Tipo de Consulta",
          "type": "select",
          "required": true,
          "options": ["Estratégica", "Operacional", "Financeira"]
        }
      ],
      "created_at": "2023-06-15T08:00:00Z",
      "updated_at": "2024-01-10T14:20:00Z"
    }
  ]
}
```

### **Criar Serviço**

```http
POST /v1/services
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "business_id": 123,
  "name": "Consultoria Digital",
  "description": "Consultoria em transformação digital",
  "category": "consultoria",
  "duration_minutes": 90,
  "price": 350.00,
  "currency": "BRL",
  "is_active": true,
  "booking_settings": {
    "advance_booking_days": 14,
    "cancellation_hours": 48,
    "max_bookings_per_day": 3
  }
}
```

---

## 📊 **ENDPOINTS DE ANALYTICS**

### **Dashboard Analytics**

```http
GET /v1/analytics/dashboard
Authorization: Bearer {token}
```

**Query Parameters:**

```http
GET /v1/analytics/dashboard?
    business_id=123&
    period=30d&
    timezone=America/Sao_Paulo
```

**Response:**

```json
{
  "success": true,
  "data": {
    "period": {
      "start": "2023-12-16T00:00:00Z",
      "end": "2024-01-15T23:59:59Z",
      "days": 30
    },
    "overview": {
      "total_appointments": 245,
      "confirmed_appointments": 198,
      "cancelled_appointments": 32,
      "no_show_appointments": 15,
      "confirmation_rate": 80.8,
      "cancellation_rate": 13.1,
      "no_show_rate": 6.1
    },
    "revenue": {
      "total": 15750.00,
      "currency": "BRL",
      "average_per_appointment": 79.55,
      "growth_percentage": 12.5
    },
    "time_analysis": {
      "busiest_days": ["Tuesday", "Thursday", "Wednesday"],
      "busiest_hours": ["14:00", "15:00", "16:00"],
      "average_duration": 58
    },
    "services": [
      {
        "service_id": 321,
        "name": "Consultoria Empresarial",
        "appointments_count": 89,
        "revenue": 8950.00,
        "percentage": 36.3
      }
    ],
    "trends": {
      "appointments_by_day": [
        {"date": "2024-01-01", "count": 8},
        {"date": "2024-01-02", "count": 12},
        {"date": "2024-01-03", "count": 15}
      ],
      "revenue_by_week": [
        {"week": "2024-W01", "revenue": 3200.00},
        {"week": "2024-W02", "revenue": 3800.00}
      ]
    }
  }
}
```

### **Relatório Detalhado**

```http
GET /v1/analytics/report
Authorization: Bearer {token}
```

**Query Parameters:**

```http
GET /v1/analytics/report?
    business_id=123&
    start_date=2024-01-01&
    end_date=2024-01-31&
    format=json&
    include_details=true
```

**Response:**

```json
{
  "success": true,
  "data": {
    "report_id": "RPT_2024_01_15_ABC123",
    "period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-01-31T23:59:59Z"
    },
    "summary": {
      "total_appointments": 428,
      "total_revenue": 27500.00,
      "unique_customers": 156,
      "repeat_customers": 89,
      "customer_retention_rate": 57.1
    },
    "performance_metrics": {
      "appointment_completion_rate": 92.3,
      "average_lead_time": 4.2,
      "customer_satisfaction": 4.6,
      "staff_utilization": 78.5
    },
    "export_url": "https://api.whatsappagent.com/v1/analytics/export/RPT_2024_01_15_ABC123.pdf"
  }
}
```

---

## 📱 **ENDPOINTS WHATSAPP**

### **Enviar Mensagem**

```http
POST /v1/whatsapp/send
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "business_id": 123,
  "to": "+5511999887766",
  "type": "text",
  "message": {
    "text": "Olá João! Seu agendamento foi confirmado para amanhã às 14:30."
  },
  "context": {
    "appointment_id": 789,
    "customer_id": 456
  }
}
```

**Para Template Message:**

```json
{
  "business_id": 123,
  "to": "+5511999887766",
  "type": "template",
  "template": {
    "name": "appointment_confirmation",
    "language": "pt_BR",
    "components": [
      {
        "type": "body",
        "parameters": [
          {"type": "text", "text": "João Silva"},
          {"type": "text", "text": "20/01/2024"},
          {"type": "text", "text": "14:30"}
        ]
      }
    ]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "message_id": "wamid.HBgMNTUxMTk5OTg4Nzc2NhUCABIYFjNBNzc5OUFGMEM1QkY5RTREQzQ3OUEyRQA=",
    "status": "sent",
    "timestamp": "2024-01-15T11:30:00Z",
    "to": "+5511999887766",
    "message_type": "text"
  },
  "message": "Mensagem enviada com sucesso"
}
```

### **Status da Mensagem**

```http
GET /v1/whatsapp/message/{message_id}/status
Authorization: Bearer {token}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "message_id": "wamid.HBgMNTUxMTk5OTg4Nzc2NhUCABIYFjNBNzc5OUFGMEM1QkY5RTREQzQ3OUEyRQA=",
    "status": "delivered",
    "timestamp": "2024-01-15T11:30:00Z",
    "status_history": [
      {"status": "sent", "timestamp": "2024-01-15T11:30:00Z"},
      {"status": "delivered", "timestamp": "2024-01-15T11:30:15Z"}
    ]
  }
}
```

### **Webhook WhatsApp**

```http
POST /v1/webhooks/whatsapp
Content-Type: application/json
X-Hub-Signature-256: sha256=...
```

**Webhook Payload:**

```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "BUSINESS_ACCOUNT_ID",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15551234567",
              "phone_number_id": "PHONE_NUMBER_ID"
            },
            "messages": [
              {
                "from": "5511999887766",
                "id": "wamid.HBgMNTUxMTk5OTg4Nzc2NhUCABIYFjNBNzc5OUFGMEM1QkY5RTREQzQ3OUEyRQA=",
                "timestamp": "1705317000",
                "text": {
                  "body": "Confirmo meu agendamento"
                },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}
```

**Auto-Response Example:**

```json
{
  "success": true,
  "data": {
    "processed": true,
    "auto_response_sent": true,
    "action_taken": "appointment_confirmed",
    "appointment_id": 789
  }
}
```

---

## 🚨 **TRATAMENTO DE ERROS**

### **Códigos de Status HTTP**

#### **Success Codes**

```json
200 OK - Operação realizada com sucesso
201 Created - Recurso criado com sucesso  
202 Accepted - Requisição aceita para processamento
204 No Content - Operação realizada sem retorno de dados
```

#### **Client Error Codes**

```json
400 Bad Request - Dados da requisição inválidos
401 Unauthorized - Token de autenticação inválido ou ausente
403 Forbidden - Permissões insuficientes
404 Not Found - Recurso não encontrado
409 Conflict - Conflito de dados (ex: email já existe)
422 Unprocessable Entity - Dados válidos mas não processáveis
429 Too Many Requests - Rate limit excedido
```

#### **Server Error Codes**

```json
500 Internal Server Error - Erro interno do servidor
502 Bad Gateway - Erro de gateway/proxy
503 Service Unavailable - Serviço temporariamente indisponível
504 Gateway Timeout - Timeout de gateway
```

### **Formato de Erro Padrão**

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Os dados fornecidos são inválidos",
    "details": [
      {
        "field": "email",
        "message": "Email deve ter um formato válido",
        "value": "email_invalido"
      },
      {
        "field": "appointment_date",
        "message": "Data deve ser no futuro",
        "value": "2024-01-10T10:00:00Z"
      }
    ]
  },
  "timestamp": "2024-01-15T11:30:00Z",
  "request_id": "req_abc123def456",
  "path": "/v1/appointments"
}
```

### **Códigos de Erro Específicos**

#### **Authentication Errors**

```json
{
  "AUTH_TOKEN_MISSING": {
    "code": 401,
    "message": "Token de autenticação é obrigatório"
  },
  "AUTH_TOKEN_INVALID": {
    "code": 401,
    "message": "Token de autenticação inválido"
  },
  "AUTH_TOKEN_EXPIRED": {
    "code": 401,
    "message": "Token de autenticação expirado"
  },
  "AUTH_INSUFFICIENT_PERMISSIONS": {
    "code": 403,
    "message": "Permissões insuficientes para esta operação"
  }
}
```

#### **Validation Errors**

```json
{
  "VALIDATION_REQUIRED_FIELD": {
    "code": 422,
    "message": "Campo obrigatório não fornecido"
  },
  "VALIDATION_INVALID_FORMAT": {
    "code": 422,
    "message": "Formato de dados inválido"
  },
  "VALIDATION_PHONE_INVALID": {
    "code": 422,
    "message": "Número de telefone deve estar no formato +5511999999999"
  },
  "VALIDATION_DATE_PAST": {
    "code": 422,
    "message": "Data não pode ser no passado"
  }
}
```

#### **Business Logic Errors**

```json
{
  "APPOINTMENT_SLOT_UNAVAILABLE": {
    "code": 409,
    "message": "Horário não disponível para agendamento"
  },
  "APPOINTMENT_TOO_LATE_TO_CANCEL": {
    "code": 409,
    "message": "Não é possível cancelar com menos de 24 horas de antecedência"
  },
  "WHATSAPP_MESSAGE_FAILED": {
    "code": 502,
    "message": "Falha ao enviar mensagem WhatsApp"
  },
  "BUSINESS_SUBSCRIPTION_EXPIRED": {
    "code": 403,
    "message": "Assinatura do negócio expirada"
  }
}
```

---

## ⚡ **RATE LIMITING**

### **Limites por Endpoint**

```json
{
  "rate_limits": {
    "global": {
      "requests_per_minute": 1000,
      "burst_limit": 50
    },
    "authentication": {
      "login_attempts_per_ip": 5,
      "login_attempts_window": "15_minutes",
      "password_reset_per_email": 3,
      "password_reset_window": "1_hour"
    },
    "whatsapp": {
      "messages_per_minute": 60,
      "messages_per_hour": 1000,
      "messages_per_day": 10000
    },
    "analytics": {
      "report_requests_per_hour": 10,
      "export_requests_per_day": 5
    }
  }
}
```

### **Headers de Rate Limit**

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705317060
X-RateLimit-Retry-After: 60
```

### **Response quando Rate Limit Excedido**

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Limite de requisições excedido",
    "details": {
      "limit": 1000,
      "window": "1 minute",
      "retry_after": 60
    }
  },
  "timestamp": "2024-01-15T11:30:00Z"
}
```

---

## 🔌 **WEBHOOKS**

### **Configuração de Webhooks**

```http
POST /v1/webhooks
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**

```json
{
  "business_id": 123,
  "url": "https://meu-sistema.com/webhooks/whatsapp-agent",
  "events": [
    "appointment.created",
    "appointment.confirmed",
    "appointment.cancelled",
    "appointment.completed",
    "whatsapp.message.received",
    "whatsapp.message.delivered"
  ],
  "is_active": true,
  "secret": "webhook_secret_key_123"
}
```

### **Eventos de Webhook**

#### **Appointment Events**

```json
{
  "event": "appointment.created",
  "timestamp": "2024-01-15T11:30:00Z",
  "data": {
    "appointment": {
      "id": 789,
      "business_id": 123,
      "contact_name": "João Silva",
      "contact_phone": "+5511999887766",
      "appointment_date": "2024-01-20T14:30:00Z",
      "status": "pending"
    }
  }
}
```

```json
{
  "event": "appointment.confirmed",
  "timestamp": "2024-01-15T11:35:00Z",
  "data": {
    "appointment": {
      "id": 789,
      "status": "confirmed",
      "confirmed_at": "2024-01-15T11:35:00Z",
      "confirmed_by": "customer"
    }
  }
}
```

#### **WhatsApp Events**

```json
{
  "event": "whatsapp.message.received",
  "timestamp": "2024-01-15T11:30:00Z",
  "data": {
    "message": {
      "id": "wamid.HBgMNTUxMTk5OTg4Nzc2NhUCABIYFjNBNzc5OUFGMEM1QkY5RTREQzQ3OUEyRQA=",
      "from": "+5511999887766",
      "to": "+5511888777666",
      "type": "text",
      "text": "Confirmo meu agendamento",
      "timestamp": "2024-01-15T11:30:00Z"
    },
    "context": {
      "appointment_id": 789,
      "auto_processed": true,
      "action_taken": "appointment_confirmed"
    }
  }
}
```

### **Verificação de Webhook**

```http
POST /webhook-endpoint
X-Hub-Signature-256: sha256=a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3
Content-Type: application/json
```

**Verificação da Assinatura:**

```python
import hashlib
import hmac

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )
```

---

## 📦 **SDKs E INTEGRAÇÕES**

### **SDK JavaScript/TypeScript**

#### **Instalação**

```bash
npm install @whatsapp-agent/sdk
# ou
yarn add @whatsapp-agent/sdk
```

#### **Configuração**

```typescript
import { WhatsAppAgentAPI } from '@whatsapp-agent/sdk';

const api = new WhatsAppAgentAPI({
  baseURL: 'https://api.whatsappagent.com/v1',
  apiKey: 'seu_token_aqui',
  businessId: 123
});
```

#### **Uso Básico**

```typescript
// Listar appointments
const appointments = await api.appointments.list({
  status: 'confirmed',
  startDate: '2024-01-01',
  endDate: '2024-01-31'
});

// Criar appointment
const newAppointment = await api.appointments.create({
  contactName: 'João Silva',
  contactPhone: '+5511999887766',
  serviceId: 321,
  appointmentDate: '2024-01-20T14:30:00Z',
  sendConfirmation: true
});

// Enviar mensagem WhatsApp
const message = await api.whatsapp.send({
  to: '+5511999887766',
  type: 'text',
  message: {
    text: 'Olá! Seu agendamento foi confirmado.'
  }
});
```

### **SDK Python**

#### **Instalação**

```bash
pip install whatsapp-agent-sdk
```

#### **Uso**

```python
from whatsapp_agent_sdk import WhatsAppAgentAPI

# Configurar cliente
api = WhatsAppAgentAPI(
    base_url='https://api.whatsappagent.com/v1',
    api_key='seu_token_aqui',
    business_id=123
)

# Listar appointments
appointments = await api.appointments.list(
    status='confirmed',
    start_date='2024-01-01',
    end_date='2024-01-31'
)

# Criar appointment
appointment = await api.appointments.create({
    'contact_name': 'João Silva',
    'contact_phone': '+5511999887766',
    'service_id': 321,
    'appointment_date': '2024-01-20T14:30:00Z',
    'send_confirmation': True
})

# Analytics
dashboard = await api.analytics.dashboard(period='30d')
```

### **SDK PHP**

#### **Instalação**

```bash
composer require whatsapp-agent/sdk
```

#### **Uso**

```php
<?php
use WhatsAppAgent\SDK\Client;

$api = new Client([
    'base_url' => 'https://api.whatsappagent.com/v1',
    'api_key' => 'seu_token_aqui',
    'business_id' => 123
]);

// Listar appointments
$appointments = $api->appointments()->list([
    'status' => 'confirmed',
    'start_date' => '2024-01-01',
    'end_date' => '2024-01-31'
]);

// Criar appointment
$appointment = $api->appointments()->create([
    'contact_name' => 'João Silva',
    'contact_phone' => '+5511999887766',
    'service_id' => 321,
    'appointment_date' => '2024-01-20T14:30:00Z',
    'send_confirmation' => true
]);
?>
```

---

## 🧪 **AMBIENTE DE TESTES**

### **Sandbox Environment**

```json
{
  "sandbox": {
    "base_url": "https://sandbox-api.whatsappagent.com/v1",
    "features": [
      "Dados de teste pré-populados",
      "WhatsApp simulado (não envia mensagens reais)",
      "Rate limiting relaxado",
      "Logs detalhados para debugging"
    ],
    "test_credentials": {
      "email": "test@sandbox.whatsappagent.com",
      "password": "test123",
      "business_id": 999
    }
  }
}
```

### **Dados de Teste**

#### **Test Phone Numbers**

```json
{
  "test_numbers": {
    "+5511999999999": "Sempre aceita mensagens",
    "+5511888888888": "Simula erro de entrega",
    "+5511777777777": "Simula número inválido",
    "+5511666666666": "Simula timeout"
  }
}
```

#### **Test Webhook URL**

```
https://webhook.site/#!/unique-id
```

### **Postman Collection**

```json
{
  "info": {
    "name": "WhatsApp Agent API",
    "description": "Coleção completa da API WhatsApp Agent",
    "version": "v1.2.0"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "https://api.whatsappagent.com/v1"
    },
    {
      "key": "token",
      "value": "{{token}}"
    },
    {
      "key": "businessId",
      "value": "123"
    }
  ],
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{token}}"
      }
    ]
  }
}
```

---

## 📋 **CHANGELOG E VERSIONAMENTO**

### **Versão v1.2.0 (2024-01-15)**

#### **✨ Novos Recursos**

- ✅ Suporte a templates WhatsApp Business
- ✅ Webhook events para mensagens
- ✅ Analytics avançados com exportação
- ✅ Custom fields em appointments
- ✅ Rate limiting granular
- ✅ SDK Python oficial

#### **🔧 Melhorias**

- ⚡ Performance de consultas otimizada (90% mais rápido)
- 🔐 Segurança JWT melhorada
- 📝 Documentação expandida
- 🌐 Suporte internacional melhorado

#### **🐛 Correções**

- 🔧 Fix timezone handling em appointments
- 🔧 Fix memory leak em webhooks
- 🔧 Fix WhatsApp message delivery status

### **Versão v1.1.0 (2023-12-01)**

#### **✨ Novos Recursos**

- ✅ Sistema de permissões RBAC
- ✅ Multi-business support
- ✅ Webhook system
- ✅ Analytics dashboard

---

<div align="center">

**📖 API REFERENCE ENTERPRISE COMPLETA**

*Documentação técnica avançada com exemplos e SDKs*

**OpenAPI 3.0** ✅ | **Webhooks** ✅ | **SDKs Oficiais** ✅ | **Rate Limiting** ✅

---

**🔗 Links Úteis**

[📊 OpenAPI Spec](https://api.whatsappagent.com/openapi.json) |
[🧪 Sandbox](https://sandbox-api.whatsappagent.com) |
[📦 SDKs](https://github.com/whatsapp-agent/sdks) |
[💬 Suporte](https://support.whatsappagent.com)

</div>
