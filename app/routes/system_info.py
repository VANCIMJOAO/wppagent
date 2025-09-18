"""
ENDPOINT DE VERIFICAÇÃO DE DEPLOY - SISTEMA
==========================================
Endpoint para verificar se mudanças estão aplicadas no Railway
"""

from fastapi import APIRouter
from datetime import datetime
import os
import sys

router = APIRouter(prefix="/system", tags=["System Info"])

@router.get("/deploy-info")
async def get_deploy_info():
    """Retorna informações sobre o deploy atual"""
    
    # Tentar importar o middleware para verificar configuração
    try:
        from app.auth.middleware import AuthMiddleware
        middleware = AuthMiddleware(app=None)
        public_endpoints = sorted(list(middleware.public_endpoints))
        middleware_ok = True
        middleware_error = None
    except Exception as e:
        public_endpoints = []
        middleware_ok = False
        middleware_error = str(e)
    
    # Informações do sistema
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "deploy_status": "active",
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "environment_vars": {
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
            "RAILWAY_PROJECT_ID": os.getenv("RAILWAY_PROJECT_ID"),
            "PORT": os.getenv("PORT")
        },
        "middleware_config": {
            "middleware_ok": middleware_ok,
            "middleware_error": middleware_error,
            "public_endpoints_count": len(public_endpoints),
            "public_endpoints": public_endpoints,
            "meta_endpoints": [ep for ep in public_endpoints if "meta" in ep],
            "debug_endpoints": [ep for ep in public_endpoints if "debug" in ep]
        },
        "git_info": {
            "commit_message": "feat(debug): add middleware debug endpoint to investigate public endpoint issue",
            "last_update": "2025-09-18T17:00:00Z"
        }
    }

@router.get("/test-middleware")
async def test_middleware_live():
    """Testa middleware ao vivo"""
    
    try:
        from app.auth.middleware import AuthMiddleware
        middleware = AuthMiddleware(app=None)
        
        test_paths = [
            "/meta/webhook/verify",
            "/debug/public-endpoints", 
            "/health",
            "/ping"
        ]
        
        results = {}
        for path in test_paths:
            results[path] = middleware._is_public_endpoint(path)
        
        return {
            "middleware_test": "success",
            "test_results": results,
            "critical_path_public": results.get("/meta/webhook/verify", False)
        }
    
    except Exception as e:
        return {
            "middleware_test": "error",
            "error": str(e)
        }