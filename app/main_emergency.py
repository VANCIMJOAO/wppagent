"""
🚄 Railway Emergency App - Minimal FastAPI for debugging
This is a minimal version that bypasses all heavy startup operations
"""
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create minimal app
emergency_app = FastAPI(
    title="WhatsApp Agent - Emergency Mode",
    description="Minimal Railway deployment version",
    version="1.0.0"
)

@emergency_app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "WhatsApp Agent Emergency Mode",
        "status": "healthy",
        "mode": "emergency",
        "port": os.getenv('PORT', '8000'),
        "railway_env": os.getenv('RAILWAY_ENVIRONMENT', 'unknown')
    }

@emergency_app.get("/ping")
async def ping():
    """Ping endpoint"""
    return "pong"

@emergency_app.get("/health/simple")
async def health_simple():
    """Simple health check"""
    return {"status": "ok", "service": "whatsapp-agent-emergency"}

@emergency_app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "WhatsApp Agent Emergency",
        "version": "1.0.0",
        "mode": "emergency"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main_emergency:emergency_app", host="0.0.0.0", port=port, reload=False)