# 📚 API Documentation - WhatsApp Agent

> **Comprehensive API Reference** with authentication flows, detailed examples, error responses, rate limiting, and complete endpoint coverage for enterprise integration.

---

## 🎯 **API OVERVIEW**

### **Base Information**
- **Base URL**: `https://api.whatsappagent.com`  
- **API Version**: `v1.0.0`
- **Protocol**: `HTTPS only`
- **Format**: `JSON`
- **Charset**: `UTF-8`

### **Key Features** ✨
- 🔐 **JWT Authentication** with refresh tokens
- 🛡️ **Role-based access control** (RBAC)  
- ⚡ **Rate limiting** (100 req/min standard, 1000 req/min premium)
- 📊 **Real-time WebSocket** support
- 🔄 **Pagination** on all list endpoints
- 🎯 **Comprehensive filtering** and search
- 📈 **Performance metrics** in response headers

---

## 🔐 **AUTHENTICATION**

### **Authentication Flow**

#### **1. Initial Login** 
```http
POST /auth/login
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
  "token_type": "bearer",
  "expires_in": 3600,
  "requires_2fa": true,
  "user_info": {
    "id": 123,
    "username": "admin@company.com",
    "role": "admin",
    "permissions": ["read", "write", "admin"],
    "business_id": 456
  }
}
```

**Notes:**
- ✅ Access token set as **HttpOnly cookie** (no token in response body)
- ✅ Refresh token set as **secure HttpOnly cookie**
- ✅ If `requires_2fa: true`, proceed to 2FA verification
- ✅ Login attempt logged for security audit

#### **2. Two-Factor Authentication (if enabled)**
```http
POST /auth/2fa/verify
Content-Type: application/json

{
  "code": "123456",
  "type": "totp"
}
```

**Response:**
```json
{
  "success": true,
  "message": "2FA verification successful",
  "session_token": "session_abc123...",
  "expires_in": 3600
}
```

#### **3. Token Refresh**
```http
POST /auth/refresh
```

**Response:**
```json
{
  "token_type": "bearer", 
  "expires_in": 3600,
  "user_info": {
    "id": 123,
    "username": "admin@company.com"
  }
}
```

#### **4. Logout**
```http
POST /auth/logout
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

### **Authorization Headers**

For requests requiring authentication, the JWT token is automatically included via **HttpOnly cookies**. No manual header management required.

**For API key authentication** (external integrations):
```http
Authorization: Bearer YOUR_API_KEY
X-API-Key: YOUR_API_KEY
```

---

## 📋 **CORE ENDPOINTS**

### **🏥 Health Check**

#### **Basic Health**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "uptime": 86400,
  "components": {
    "database": "healthy",
    "redis": "healthy", 
    "meta_api": "healthy",
    "webhook": "healthy"
  }
}
```

#### **Detailed Health** (Admin only)
```http
GET /health/detailed
Authorization: Required (Admin role)
```

**Response:**
```json
{
  "status": "healthy",
  "detailed_status": {
    "database": {
      "status": "healthy",
      "response_time_ms": 15,
      "active_connections": 12,
      "max_connections": 100
    },
    "redis": {
      "status": "healthy", 
      "response_time_ms": 2,
      "memory_usage": "45.2MB",
      "hit_rate": "94.5%"
    },
    "meta_api": {
      "status": "healthy",
      "response_time_ms": 145,
      "rate_limit_remaining": 95
    },
    "webhook": {
      "status": "healthy",
      "last_received": "2024-01-15T10:29:45Z",
      "success_rate": "99.8%"
    }
  },
  "performance_metrics": {
    "cpu_usage": "23.5%",
    "memory_usage": "67.2%",
    "disk_usage": "45.1%"
  }
}
```

### **📅 Appointments Management**

#### **List Appointments**
```http
GET /appointments?limit=20&page=1&status=confirmed&date_from=2024-01-01&date_to=2024-01-31
Authorization: Required
```

**Query Parameters:**
- `limit` (int, optional): Results per page (max: 100, default: 10)
- `page` (int, optional): Page number (default: 1)  
- `status` (string, optional): Filter by status (`pending`, `confirmed`, `completed`, `cancelled`)
- `date_from` (string, optional): Start date filter (YYYY-MM-DD)
- `date_to` (string, optional): End date filter (YYYY-MM-DD)
- `user_id` (int, optional): Filter by user ID
- `business_id` (int, optional): Filter by business ID

**Response:**
```json
{
  "appointments": [
    {
      "id": 123,
      "user_id": 456,
      "business_id": 789,
      "service_id": 101,
      "phone_number": "+5511999999999",
      "contact_name": "João Silva",
      "appointment_date": "2024-01-20",
      "appointment_time": "14:30:00",
      "status": "confirmed",
      "notes": "Consulta de rotina",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "user": {
        "id": 456,
        "name": "João Silva",
        "email": "joao@email.com",
        "phone": "+5511999999999"
      },
      "business": {
        "id": 789,
        "name": "Clínica Saúde",
        "address": "Rua das Flores, 123"
      },
      "service": {
        "id": 101,
        "name": "Consulta Médica",
        "duration": 60,
        "price": "150.00"
      }
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 87,
    "items_per_page": 20,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "status": "confirmed",
    "date_from": "2024-01-01",
    "date_to": "2024-01-31"
  },
  "cache_info": {
    "cache_hit": true,
    "cache_ttl": 120,
    "generated_at": "2024-01-15T10:30:00Z"
  }
}
```

#### **Create Appointment**
```http
POST /appointments
Content-Type: application/json
Authorization: Required
```

**Request Body:**
```json
{
  "user_id": 456,
  "business_id": 789,
  "service_id": 101,
  "phone_number": "+5511999999999",
  "contact_name": "João Silva",
  "appointment_date": "2024-01-25",
  "appointment_time": "15:30:00",
  "notes": "Primeira consulta",
  "auto_confirm": false
}
```

**Response (201 Created):**
```json
{
  "id": 124,
  "user_id": 456,
  "business_id": 789,
  "service_id": 101,
  "phone_number": "+5511999999999",
  "contact_name": "João Silva", 
  "appointment_date": "2024-01-25",
  "appointment_time": "15:30:00",
  "status": "pending",
  "notes": "Primeira consulta",
  "created_at": "2024-01-15T10:35:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "confirmation_token": "abc123...",
  "whatsapp_message_sent": true,
  "webhook_events": [
    {
      "event": "appointment_created",
      "status": "sent",
      "timestamp": "2024-01-15T10:35:01Z"
    }
  ]
}
```

#### **Update Appointment**
```http
PUT /appointments/124
Content-Type: application/json
Authorization: Required
```

**Request Body:**
```json
{
  "appointment_date": "2024-01-26",
  "appointment_time": "16:00:00",
  "status": "confirmed",
  "notes": "Horário alterado pelo cliente"
}
```

#### **Delete Appointment**
```http
DELETE /appointments/124
Authorization: Required (Admin or Owner)
```

**Response (204 No Content)**

### **📞 WhatsApp Integration**

#### **Send Message**
```http
POST /webhook/send-message
Content-Type: application/json
Authorization: Required
```

**Request Body:**
```json
{
  "phone_number": "+5511999999999",
  "message": "Olá! Sua consulta está confirmada para amanhã às 14:30.",
  "message_type": "text",
  "template_name": "appointment_confirmation",
  "template_params": {
    "customer_name": "João",
    "appointment_date": "20/01/2024",
    "appointment_time": "14:30"
  }
}
```

**Response:**
```json
{
  "message_id": "wamid.abc123...",
  "status": "sent",
  "timestamp": "2024-01-15T10:40:00Z",
  "delivery_status": "pending",
  "phone_number": "+5511999999999",
  "cost": 0.05,
  "template_used": "appointment_confirmation"
}
```

#### **Webhook Incoming** (Meta → Your API)
```http
POST /webhook
Content-Type: application/json
X-Hub-Signature-256: sha256=...
```

**Request Body (Message Received):**
```json
{
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "business_account_id",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "5511999999999",
              "phone_number_id": "phone_id"
            },
            "messages": [
              {
                "from": "5511888888888",
                "id": "wamid.xyz789...",
                "timestamp": "1704198600",
                "text": {
                  "body": "Sim, confirmo minha consulta"
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

### **📊 Analytics**

#### **Get Analytics Dashboard**
```http
GET /analytics/dashboard?period=30d&business_id=789
Authorization: Required
```

**Response:**
```json
{
  "period": "30d",
  "business_id": 789,
  "summary": {
    "total_appointments": 245,
    "total_messages": 1203,
    "conversion_rate": "89.5%",
    "customer_satisfaction": "4.7",
    "revenue": "36750.00"
  },
  "appointments": {
    "by_status": {
      "completed": 198,
      "confirmed": 32,
      "pending": 10,
      "cancelled": 5
    },
    "by_day": [
      {"date": "2024-01-01", "count": 8},
      {"date": "2024-01-02", "count": 12},
      {"date": "2024-01-03", "count": 6}
    ]
  },
  "messages": {
    "sent": 892,
    "received": 311,
    "delivery_rate": "98.2%",
    "response_rate": "34.9%"
  },
  "top_services": [
    {"service_id": 101, "name": "Consulta Médica", "count": 87},
    {"service_id": 102, "name": "Exame", "count": 45}
  ]
}
```

---

## ⚠️ **ERROR RESPONSES**

### **Standard Error Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "appointment_date",
        "message": "Date must be in the future",
        "code": "INVALID_DATE"
      }
    ],
    "request_id": "req_abc123...",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### **HTTP Status Codes**

| Code | Name | Description | Example |
|------|------|-------------|---------|
| `200` | OK | Request successful | Data retrieved |
| `201` | Created | Resource created | Appointment created |
| `204` | No Content | Successful deletion | Appointment deleted |
| `400` | Bad Request | Invalid request data | Missing required field |
| `401` | Unauthorized | Authentication required | Invalid token |
| `403` | Forbidden | Insufficient permissions | Admin access required |
| `404` | Not Found | Resource not found | Appointment not found |
| `409` | Conflict | Resource conflict | Appointment time conflict |
| `422` | Unprocessable Entity | Validation error | Invalid phone format |
| `429` | Too Many Requests | Rate limit exceeded | API quota exceeded |
| `500` | Internal Server Error | Server error | Database connection failed |
| `503` | Service Unavailable | Service temporarily down | Maintenance mode |

### **Error Codes Reference**

#### **Authentication Errors**
- `AUTH_TOKEN_MISSING`: No authentication token provided
- `AUTH_TOKEN_INVALID`: Invalid or expired token
- `AUTH_TOKEN_EXPIRED`: Token has expired, refresh required
- `AUTH_2FA_REQUIRED`: Two-factor authentication required
- `AUTH_2FA_INVALID`: Invalid 2FA code
- `AUTH_INSUFFICIENT_PERMISSIONS`: User lacks required permissions

#### **Validation Errors**
- `VALIDATION_ERROR`: General validation failure
- `REQUIRED_FIELD_MISSING`: Required field not provided
- `INVALID_FORMAT`: Field format is invalid
- `INVALID_DATE`: Date is invalid or in wrong format
- `INVALID_PHONE`: Phone number format is invalid
- `INVALID_EMAIL`: Email format is invalid

#### **Business Logic Errors**
- `APPOINTMENT_CONFLICT`: Appointment time already booked
- `APPOINTMENT_NOT_FOUND`: Appointment does not exist
- `USER_NOT_FOUND`: User does not exist
- `BUSINESS_NOT_FOUND`: Business does not exist
- `SERVICE_NOT_FOUND`: Service does not exist
- `SCHEDULE_UNAVAILABLE`: Requested time slot not available

#### **Rate Limiting Errors**
- `RATE_LIMIT_EXCEEDED`: Too many requests from IP
- `QUOTA_EXCEEDED`: Monthly API quota exceeded
- `CONCURRENT_LIMIT`: Too many concurrent requests

#### **WhatsApp API Errors**
- `WHATSAPP_API_ERROR`: Error from Meta WhatsApp API
- `WHATSAPP_INVALID_PHONE`: Phone number not registered with WhatsApp
- `WHATSAPP_MESSAGE_FAILED`: Failed to send WhatsApp message
- `WHATSAPP_TEMPLATE_NOT_FOUND`: Message template not found

---

## 🚦 **RATE LIMITING**

### **Rate Limit Headers**
Every API response includes rate limiting information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1704198660
X-RateLimit-Window: 60
```

### **Rate Limiting Tiers**

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|-----------------|---------------|--------------|
| **Free** | 30 | 500 | 5,000 |
| **Standard** | 100 | 2,000 | 20,000 |
| **Premium** | 1,000 | 10,000 | 100,000 |
| **Enterprise** | Custom | Custom | Custom |

### **Rate Limit Response (429)**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again later.",
    "retry_after": 60,
    "limit": 100,
    "remaining": 0,
    "reset_time": "2024-01-15T10:31:00Z"
  }
}
```

---

## 🔌 **WEBHOOKS**

### **Webhook Configuration**
Configure webhooks to receive real-time events:

```http
POST /webhooks/configure
Content-Type: application/json
Authorization: Required (Admin)
```

**Request:**
```json
{
  "url": "https://your-app.com/webhooks/whatsapp",
  "events": [
    "message_received",
    "message_delivered", 
    "appointment_created",
    "appointment_updated"
  ],
  "secret": "your_webhook_secret"
}
```

### **Webhook Events**

#### **Message Received**
```json
{
  "event": "message_received",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "message_id": "wamid.abc123...",
    "from": "+5511888888888",
    "to": "+5511999999999",
    "message_type": "text",
    "content": "Quero agendar uma consulta",
    "timestamp": "1704198600"
  }
}
```

#### **Appointment Created**
```json
{
  "event": "appointment_created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "appointment_id": 124,
    "user_id": 456,
    "business_id": 789,
    "appointment_date": "2024-01-25",
    "appointment_time": "15:30:00",
    "status": "pending"
  }
}
```

### **Webhook Verification**
All webhooks include HMAC signature for verification:

```python
import hmac
import hashlib

def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload.encode(), 
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## 🔧 **SDKs & LIBRARIES**

### **Python SDK**
```python
from whatsapp_agent import WhatsAppAgentAPI

# Initialize client
client = WhatsAppAgentAPI(
    api_key="your_api_key",
    base_url="https://api.whatsappagent.com"
)

# Create appointment
appointment = await client.appointments.create({
    "user_id": 456,
    "business_id": 789,
    "service_id": 101,
    "phone_number": "+5511999999999",
    "contact_name": "João Silva",
    "appointment_date": "2024-01-25",
    "appointment_time": "15:30:00"
})

# Send WhatsApp message
message = await client.messages.send({
    "phone_number": "+5511999999999",
    "message": "Sua consulta foi confirmada!",
    "template": "appointment_confirmation"
})
```

### **JavaScript/Node.js SDK**
```javascript
const WhatsAppAgent = require('@whatsappagent/api');

const client = new WhatsAppAgent({
    apiKey: 'your_api_key',
    baseURL: 'https://api.whatsappagent.com'
});

// Create appointment
const appointment = await client.appointments.create({
    user_id: 456,
    business_id: 789,
    service_id: 101,
    phone_number: '+5511999999999',
    contact_name: 'João Silva',
    appointment_date: '2024-01-25',
    appointment_time: '15:30:00'
});

// Send message
const message = await client.messages.send({
    phone_number: '+5511999999999',
    message: 'Sua consulta foi confirmada!',
    template: 'appointment_confirmation'
});
```

---

## 📊 **PERFORMANCE METRICS**

### **Response Time Targets**
- ✅ **Health Check**: < 50ms
- ✅ **Authentication**: < 200ms  
- ✅ **List Endpoints**: < 300ms
- ✅ **Create/Update**: < 500ms
- ✅ **WhatsApp Send**: < 1000ms

### **Performance Headers**
```http
X-Response-Time: 145ms
X-DB-Query-Time: 23ms
X-Cache-Status: hit
X-Server-ID: api-01
```

---

## 🔍 **TESTING**

### **Postman Collection**
Import our comprehensive Postman collection:
```
https://api.whatsappagent.com/docs/postman/collection.json
```

### **OpenAPI/Swagger**
Interactive API documentation available at:
```
https://api.whatsappagent.com/docs
```

### **Testing Endpoints**

#### **Test Authentication**
```bash
curl -X POST https://api.whatsappagent.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"test123"}'
```

#### **Test Health Check**
```bash
curl -X GET https://api.whatsappagent.com/health
```

#### **Test with Rate Limiting**
```bash
# This will trigger rate limiting after 100 requests
for i in {1..105}; do
  curl -X GET https://api.whatsappagent.com/health
done
```

---

## 🆘 **SUPPORT**

### **API Status Page**
Real-time API status and incidents:
```
https://status.whatsappagent.com
```

### **Support Channels**
- 📧 **API Support**: api-support@whatsappagent.com
- 💬 **Developer Chat**: https://discord.gg/whatsappagent
- 📚 **Documentation**: https://docs.whatsappagent.com
- 🐛 **Bug Reports**: https://github.com/whatsappagent/api/issues

### **Response Times**
- 🔥 **Critical**: < 1 hour
- ⚠️ **High**: < 4 hours  
- 📋 **Medium**: < 24 hours
- 💡 **Low**: < 72 hours

---

<div align="center">

**🚀 ENTERPRISE API DOCUMENTATION**

*Complete reference for production integration*

**API Uptime: 99.9%** | **Response Time: <300ms** | **Rate Limit: 1000/min**

</div>