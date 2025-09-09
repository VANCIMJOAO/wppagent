"""
Endpoint de debug para testar autenticação isolada
Apenas para identificar problema com get_current_admin_user
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.routes.admin_auth import get_current_admin_user, AdminUser
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/debug", tags=["Debug"])

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
