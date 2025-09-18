"""
Debug endpoint temporário para verificar configuração do middleware
"""

from fastapi import APIRouter
from app.auth.middleware import AuthenticationMiddleware

router = APIRouter(prefix="/debug", tags=["Debug"])

@router.get("/public-endpoints")
async def get_public_endpoints():
    """Retorna lista de endpoints públicos configurados no middleware"""
    # Simular instância do middleware para pegar endpoints
    middleware = AuthenticationMiddleware(app=None, secrets_manager=None)
    
    return {
        "public_endpoints": sorted(list(middleware.public_endpoints)),
        "total_count": len(middleware.public_endpoints),
        "meta_endpoints": [ep for ep in middleware.public_endpoints if "meta" in ep],
        "webhook_endpoints": [ep for ep in middleware.public_endpoints if "webhook" in ep]
    }

@router.get("/test-path-check/{path:path}")
async def test_path_check(path: str):
    """Testa se um path específico seria considerado público"""
    middleware = AuthenticationMiddleware(app=None, secrets_manager=None)
    
    # Reproduzir lógica _is_public_endpoint
    is_public = False
    matched_endpoints = []
    
    for public_path in middleware.public_endpoints:
        exact_match = path == public_path
        prefix_match = path.startswith(public_path + "/")
        
        if exact_match or prefix_match:
            is_public = True
            matched_endpoints.append({
                "endpoint": public_path,
                "exact_match": exact_match,
                "prefix_match": prefix_match
            })
    
    return {
        "path": path,
        "is_public": is_public,
        "matched_endpoints": matched_endpoints,
        "total_public_endpoints": len(middleware.public_endpoints)
    }