"""
🔧 Enhanced API Configuration
============================

Configurações avançadas para documentação da API, incluindo:
- Exemplos detalhados de request/response
- Configuração de security schemes
- Metadata para documentação OpenAPI
- Configuração de CORS para docs

Autor: GitHub Copilot
Status: DOC-001 Task 7 - API Documentation Enhancement
"""

from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Security scheme para documentação
security_scheme = HTTPBearer(
    scheme_name="JWT",
    description="""
    **JWT Authentication with HttpOnly Cookies**

    This API uses secure HttpOnly cookies for authentication.
    For testing in Swagger UI, you can also use Bearer tokens.

    ### How to authenticate:
    1. **Login**: POST `/auth/login` with credentials
    2. **Use cookies**: Automatically handled by browser
    3. **Or use Bearer token**: Add `Authorization: Bearer <token>` header

    ### Token Format:
    ```
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```
    """,
)


def configure_enhanced_openapi(app: FastAPI) -> None:
    """
    Configure enhanced OpenAPI documentation with custom schemas,
    examples, and security definitions.
    """

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            servers=app.servers,
            tags=app.tags_metadata,
        )

        # Add custom security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "HTTPBearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token authentication via Bearer header or HttpOnly cookies",
            },
            "ApiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for external integrations",
            },
        }

        # Add global examples
        openapi_schema["components"]["examples"] = {
            "ErrorResponse": {
                "summary": "Standard Error Response",
                "value": {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid request data",
                        "details": [
                            {
                                "field": "phone_number",
                                "message": "Invalid phone number format",
                                "code": "INVALID_FORMAT",
                            }
                        ],
                        "request_id": "req_abc123456",
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                },
            },
            "SuccessResponse": {
                "summary": "Standard Success Response",
                "value": {
                    "success": True,
                    "message": "Operation completed successfully",
                    "data": {},
                    "timestamp": "2024-01-15T10:30:00Z",
                },
            },
            "PaginatedResponse": {
                "summary": "Paginated List Response",
                "value": {
                    "items": [],
                    "pagination": {
                        "current_page": 1,
                        "total_pages": 5,
                        "total_items": 87,
                        "items_per_page": 20,
                        "has_next": True,
                        "has_previous": False,
                    },
                    "filters_applied": {},
                    "cache_info": {"cache_hit": True, "cache_ttl": 120},
                },
            },
        }

        # Add custom headers
        openapi_schema["components"]["headers"] = {
            "X-RateLimit-Limit": {
                "description": "The number of allowed requests in the current period",
                "schema": {"type": "integer", "example": 100},
            },
            "X-RateLimit-Remaining": {
                "description": "The number of remaining requests in the current period",
                "schema": {"type": "integer", "example": 87},
            },
            "X-RateLimit-Reset": {
                "description": "The timestamp when the rate limit will reset",
                "schema": {"type": "integer", "example": 1704198660},
            },
            "X-Response-Time": {
                "description": "Response processing time in milliseconds",
                "schema": {"type": "string", "example": "145ms"},
            },
            "X-Cache-Status": {
                "description": "Cache hit/miss status",
                "schema": {"type": "string", "enum": ["hit", "miss", "bypass"]},
            },
        }

        # Add custom info
        openapi_schema["info"]["x-logo"] = {
            "url": "https://whatsappagent.com/logo.png",
            "altText": "WhatsApp Agent API",
        }

        openapi_schema["info"]["x-api-features"] = [
            "JWT Authentication with HttpOnly cookies",
            "Real-time WebSocket connections",
            "Comprehensive rate limiting",
            "Detailed error responses",
            "Performance monitoring headers",
            "Automatic API documentation",
        ]

        # Add external documentation
        openapi_schema["externalDocs"] = {
            "description": "Complete API Documentation",
            "url": "https://docs.whatsappagent.com/api",
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi


# Common response examples for reuse
COMMON_RESPONSES = {
    "ValidationError": {
        "description": "❌ Request validation failed",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Invalid request data",
                        "details": [
                            {
                                "field": "phone_number",
                                "message": "Invalid phone number format",
                                "code": "INVALID_FORMAT",
                            }
                        ],
                        "request_id": "req_abc123",
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            }
        },
    },
    "Unauthorized": {
        "description": "🔐 Authentication required",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "AUTH_TOKEN_MISSING",
                        "message": "Authentication token is required",
                        "request_id": "req_abc123",
                    }
                }
            }
        },
    },
    "Forbidden": {
        "description": "🚫 Insufficient permissions",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "AUTH_INSUFFICIENT_PERMISSIONS",
                        "message": "You don't have permission to access this resource",
                        "required_permission": "admin",
                        "current_role": "user",
                    }
                }
            }
        },
    },
    "NotFound": {
        "description": "🔍 Resource not found",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "RESOURCE_NOT_FOUND",
                        "message": "The requested resource was not found",
                        "resource_type": "appointment",
                        "resource_id": 123,
                    }
                }
            }
        },
    },
    "RateLimit": {
        "description": "⚠️ Rate limit exceeded",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Try again later.",
                        "retry_after": 60,
                        "limit": 100,
                        "remaining": 0,
                        "reset_time": "2024-01-15T10:31:00Z",
                    }
                }
            }
        },
        "headers": {
            "X-RateLimit-Limit": {"description": "Request limit per window"},
            "X-RateLimit-Remaining": {"description": "Remaining requests in window"},
            "X-RateLimit-Reset": {"description": "Window reset timestamp"},
        },
    },
    "ServerError": {
        "description": "🔧 Internal server error",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred",
                        "request_id": "req_abc123",
                        "support_reference": "Please contact support with this reference",
                    }
                }
            }
        },
    },
}

# API metadata for documentation
API_METADATA = {
    "title": "🤖 WhatsApp Agent API",
    "description": """
## 🚀 Enterprise WhatsApp Business API

**Comprehensive AI-powered WhatsApp integration** for appointment management, customer engagement, and business automation.

### 🎯 Key Features

- ✅ **Smart Appointment Scheduling** with conflict detection
- ✅ **Real-time WhatsApp Integration** via Meta Business API
- ✅ **AI-Powered Responses** with conversation context
- ✅ **Enterprise Security** with JWT, 2FA, and RBAC
- ✅ **High Performance** with Redis caching and optimized queries
- ✅ **Real-time Updates** via WebSocket connections
- ✅ **Comprehensive Analytics** and reporting dashboard

### 🔐 Authentication

This API uses **JWT tokens with HttpOnly cookies** for maximum security:

1. **Login** → `/auth/login` with credentials
2. **2FA Verification** → `/auth/2fa/verify` (if enabled)
3. **Access Protected Endpoints** → Automatic cookie-based auth
4. **Refresh Tokens** → `/auth/refresh` for token renewal

### 📊 Rate Limiting

- **Standard**: 100 requests/minute
- **Premium**: 1000 requests/minute
- **Enterprise**: Custom limits

### 🔗 External Documentation

- **Complete API Guide**: [docs/api-documentation.md](docs/api-documentation.md)
- **Setup Instructions**: [docs/setup-guide.md](docs/setup-guide.md)
- **Security Practices**: [docs/security-practices.md](docs/security-practices.md)
- **Performance Guide**: [docs/performance-optimization.md](docs/performance-optimization.md)
""",
    "version": "1.0.0",
    "contact": {
        "name": "WhatsApp Agent API Support",
        "url": "https://docs.whatsappagent.com",
        "email": "api-support@whatsappagent.com",
    },
    "license_info": {
        "name": "Enterprise License",
        "url": "https://whatsappagent.com/license",
    },
    "servers": [
        {"url": "https://api.whatsappagent.com", "description": "Production server"},
        {
            "url": "https://staging-api.whatsappagent.com",
            "description": "Staging server",
        },
        {"url": "http://localhost:8000", "description": "Development server"},
    ],
    "tags_metadata": [
        {
            "name": "Authentication",
            "description": "🔐 User authentication, 2FA, JWT token management",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.whatsappagent.com/auth",
            },
        },
        {
            "name": "Appointments",
            "description": "📅 Appointment CRUD operations with smart scheduling",
            "externalDocs": {
                "description": "Appointment Management Guide",
                "url": "https://docs.whatsappagent.com/appointments",
            },
        },
        {
            "name": "WhatsApp",
            "description": "📱 WhatsApp message sending and webhook handling",
            "externalDocs": {
                "description": "WhatsApp Integration Guide",
                "url": "https://docs.whatsappagent.com/whatsapp",
            },
        },
        {
            "name": "Analytics",
            "description": "📊 Business analytics and performance metrics",
            "externalDocs": {
                "description": "Analytics Dashboard Guide",
                "url": "https://docs.whatsappagent.com/analytics",
            },
        },
        {
            "name": "Health",
            "description": "🏥 System health checks and monitoring",
            "externalDocs": {
                "description": "Monitoring & Health Guide",
                "url": "https://docs.whatsappagent.com/monitoring",
            },
        },
        {
            "name": "Admin",
            "description": "⚙️ Administrative functions and system management",
            "externalDocs": {
                "description": "Admin Operations Guide",
                "url": "https://docs.whatsappagent.com/admin",
            },
        },
    ],
}


def get_enhanced_response_examples():
    """
    Get enhanced response examples for common API patterns
    """
    return {
        "appointment_created": {
            "summary": "Appointment created successfully",
            "value": {
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
                "confirmation_token": "abc123def456",
                "whatsapp_message_sent": True,
                "estimated_duration": 60,
                "webhook_events": [
                    {
                        "event": "appointment_created",
                        "status": "sent",
                        "timestamp": "2024-01-15T10:35:01Z",
                    }
                ],
            },
        },
        "appointment_list": {
            "summary": "List of appointments with pagination",
            "value": {
                "appointments": [
                    {
                        "id": 123,
                        "user_id": 456,
                        "contact_name": "João Silva",
                        "appointment_date": "2024-01-20",
                        "appointment_time": "14:30:00",
                        "status": "confirmed",
                        "service": {
                            "id": 101,
                            "name": "Consulta Médica",
                            "duration": 60,
                        },
                    }
                ],
                "pagination": {
                    "current_page": 1,
                    "total_pages": 5,
                    "total_items": 87,
                    "items_per_page": 20,
                },
                "performance_info": {"query_time_ms": 23.45, "cache_status": "hit"},
            },
        },
        "health_check": {
            "summary": "System health status",
            "value": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "components": {
                    "database": "healthy",
                    "redis": "healthy",
                    "meta_api": "healthy",
                },
                "version": "1.0.0",
                "uptime": 86400,
            },
        },
    }
