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
    print("🚀 Starting WhatsApp Agent API on Railway", flush=True)
    print(f"🌐 Port: {os.getenv('PORT', '8000')}", flush=True)
    print(f"🏗️ Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'unknown')}", flush=True)

def main():
    """Main startup function"""
    # Setup logging
    logger = setup_railway_logging()
    
    # Print Railway information
    print_railway_info()
    
    # Import and start the application
    try:
        from app.main import app
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
