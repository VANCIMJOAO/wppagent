import logging
import sys
import os
from datetime import datetime

# Setup básico de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def test_basic_startup():
    """Teste básico de startup"""
    logger.info("🚄 RAILWAY DEBUG - Iniciando testes...")
    logger.info(f"🚄 Python version: {sys.version}")
    logger.info(f"🚄 Port: {os.getenv('PORT', 'NOT_SET')}")
    logger.info(f"🚄 Railway env: {os.getenv('RAILWAY_ENVIRONMENT', 'NOT_SET')}")
    
    try:
        logger.info("🚄 Testing FastAPI import...")
        from fastapi import FastAPI
        logger.info("🚄 FastAPI import OK")
        
        logger.info("🚄 Testing Uvicorn import...")
        import uvicorn
        logger.info("🚄 Uvicorn import OK")
        
        logger.info("🚄 Creating minimal FastAPI app...")
        app = FastAPI(title="Railway Debug")
        
        @app.get("/health")
        async def health():
            return {"status": "ok", "timestamp": datetime.now().isoformat()}
            
        @app.get("/ping")  
        async def ping():
            return {"status": "pong"}
            
        logger.info("🚄 FastAPI app created successfully")
        
        # Test port binding
        port = int(os.getenv('PORT', '8000'))
        logger.info(f"🚄 Starting server on port {port}...")
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"🚄 FATAL ERROR: {str(e)}")
        import traceback
        logger.error(f"🚄 TRACEBACK: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    test_basic_startup()
