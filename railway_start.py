#!/usr/bin/env python3
"""
Railway-specific startup script with enhanced logging
This script ensures logs are properly captured by Railway
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Force unbuffered output for Railway
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

def setup_railway_logging():
    """Configure logging specifically for Railway"""
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create a simple formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler],
        force=True
    )
    
    return logging.getLogger(__name__)

def print_railway_info():
    """Print Railway-specific information"""
    print("=" * 60, flush=True)
    print("🚀 RAILWAY STARTUP SCRIPT", flush=True)
    print("=" * 60, flush=True)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}", flush=True)
    print(f"🐍 Python Version: {sys.version}", flush=True)
    print(f"💻 Platform: {sys.platform}", flush=True)
    print(f"📁 Working Directory: {os.getcwd()}", flush=True)
    print(f"🔧 Python Executable: {sys.executable}", flush=True)
    print("", flush=True)
    
    print("🔍 ENVIRONMENT VARIABLES:", flush=True)
    railway_vars = [
        'PORT', 'RAILWAY_ENVIRONMENT', 'RAILWAY_FAST_START', 
        'PYTHONUNBUFFERED', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID'
    ]
    
    for var in railway_vars:
        value = os.getenv(var, 'NOT SET')
        print(f"   {var}: {value}", flush=True)
    
    print("", flush=True)
    print("🔍 ALL ENVIRONMENT VARIABLES (first 20):", flush=True)
    for i, (key, value) in enumerate(os.environ.items()):
        if i >= 20:
            print(f"   ... and {len(os.environ) - 20} more", flush=True)
            break
        print(f"   {key}: {value}", flush=True)
    
    print("=" * 60, flush=True)

def main():
    """Main startup function"""
    # Setup logging
    logger = setup_railway_logging()
    
    # Print Railway information
    print_railway_info()
    
    # Import and start the application
    try:
        print("🔄 Importing FastAPI application...", flush=True)
        from app.main import app
        print("✅ FastAPI application imported successfully", flush=True)
        
        print("🔄 Starting uvicorn server...", flush=True)
        import uvicorn
        
        port = int(os.getenv("PORT", 8000))
        print(f"🌐 Starting server on port: {port}", flush=True)
        
        # Start uvicorn with Railway-optimized settings (SIMPLIFIED)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            use_colors=False,
            loop="asyncio",
            reload=False
        )
        
    except Exception as e:
        print(f"❌ ERROR starting application: {e}", flush=True)
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
