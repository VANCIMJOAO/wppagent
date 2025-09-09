"""
Endpoint de debug para testar autenticação isolada
Apenas para identificar problema com get_current_admin_user
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.services.jwt_manager import jwt_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/debug", tags=["Debug"])
security = HTTPBearer()

@router.get("/auth-test")
async def test_authentication(
    current_admin: AdminUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Endpoint simples para testar se get_current_admin_user funciona
    """
    try:
        logger.info(f"🔍 Debug auth test: user {current_admin.id} ({current_admin.username})")
        
        return {
            "success": True,
            "user_id": current_admin.id,
            "username": current_admin.username,
            "is_active": current_admin.is_active,
            "message": "Authentication working correctly"
        }
        
    except Exception as e:
        logger.error(f"❌ Debug auth test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Authentication failed in debug endpoint"
        }

@router.get("/auth-simple")
async def debug_auth_simple(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Debug de autenticação SEM get_current_admin_user"""
    try:
        token = credentials.credentials
        logger.info(f"🔍 Debug auth simple - Token: {token[:30]}...")
        
        # Verificar token diretamente com JWT manager
        try:
            payload = jwt_manager.verify_token(token)
            logger.info(f"✅ Token payload: {payload}")
            
            return {
                "status": "success", 
                "user_id": payload.get("sub"),
                "role": payload.get("role"),
                "permissions": payload.get("permissions"),
                "token_type": payload.get("type"),
                "message": "Token verificado com sucesso"
            }
            
        except Exception as token_error:
            logger.error(f"❌ Token verification error: {token_error}")
            raise HTTPException(status_code=401, detail=f"Token inválido: {str(token_error)}")
            
    except Exception as e:
        logger.error(f"❌ Auth simple error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@router.get("/jwt-info")
async def debug_jwt_info():
    """Informações do JWT Manager"""
    try:
        return {
            "jwt_manager_available": jwt_manager is not None,
            "has_secret": hasattr(jwt_manager, 'secret_key') if jwt_manager else False,
        }
    except Exception as e:
        logger.error(f"❌ JWT info error: {e}")
        return {"error": str(e)}
