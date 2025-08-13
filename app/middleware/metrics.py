"""
Custom HTTP Middleware for Request/Response Metrics
Integrates with Prometheus metrics to monitor all HTTP requests
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.metrics import metrics_collector
from app.utils.logger import get_logger

logger = get_logger(__name__)

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics for Prometheus monitoring
    """
    
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Normalize path for better grouping (remove IDs, etc.)
        normalized_path = self._normalize_path(path)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            metrics_collector.record_http_request(
                method=method,
                endpoint=normalized_path,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            metrics_collector.record_http_request(
                method=method,
                endpoint=normalized_path,
                status_code=500,
                duration=duration
            )
            
            logger.error(f"Error in metrics middleware: {e}")
            raise
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for better metric grouping
        Replace dynamic segments with placeholders
        """
        try:
            # Common patterns to normalize
            patterns = [
                (r'/webhook/\d+', '/webhook/{id}'),
                (r'/user/[^/]+', '/user/{id}'),
                (r'/conversation/\d+', '/conversation/{id}'),
                (r'/message/\d+', '/message/{id}'),
                (r'/client/[^/]+', '/client/{id}'),
            ]
            
            normalized = path
            for pattern, replacement in patterns:
                import re
                normalized = re.sub(pattern, replacement, normalized)
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Error normalizing path {path}: {e}")
            return path
