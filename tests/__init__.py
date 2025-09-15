# VL-001 Integration Tests Package
"""
Integration tests for WhatsApp Agent.

This package contains end-to-end tests validating:
- Authentication flows with HttpOnly cookies
- CRUD operations for appointments  
- Webhook validation with HMAC signatures
- Critical business logic flows

Tests are designed to work with the complete application stack
including database, Redis cache, and external API integrations.
"""