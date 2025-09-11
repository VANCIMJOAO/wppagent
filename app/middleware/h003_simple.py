"""
H003 Simple Rate Limiting Test
=============================

Simplified version to test middleware loading in Railway
"""

import logging
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

class H003SimpleMiddleware(BaseHTTPMiddleware):
    """
    Simplified H003 test middleware to verify loading in Railway
    """
    
    def __init__(self, app):
        super().__init__(app)
        logger.info("🧪 H003 Simple Middleware initialized successfully")
    
    async def dispatch(self, request: Request, call_next):
        """Process request with basic rate limiting headers"""
        
        # Add debug headers to verify middleware is active
        response = await call_next(request)
        
        # Add H003 test headers
        response.headers["X-H003-Test"] = "active"
        response.headers["X-H003-Timestamp"] = datetime.now().isoformat()
        response.headers["X-H003-Path"] = str(request.url.path)
        
        # Log middleware activity
        logger.info(f"🧪 H003 Simple: Processed {request.method} {request.url.path}")
        
        return response
