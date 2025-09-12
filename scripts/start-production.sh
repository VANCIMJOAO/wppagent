#!/bin/bash
# 🚀 Production Startup Script for WhatsApp Agent
# Ensures CSP and security headers are properly loaded

echo "🔧 Starting WhatsApp Agent with Security Headers..."

# Set environment variables for production
export ENVIRONMENT=production
export CSP_REPORT_ONLY=false
export CSP_STRICT_MODE=true

# Ensure all security modules are available
echo "🔒 Verifying security modules..."

if [ -f "app/security/csp_manager.py" ]; then
    echo "✅ CSP Manager found"
else
    echo "❌ CSP Manager missing"
    exit 1
fi

if [ -f "app/security/https_middleware.py" ]; then
    echo "✅ HTTPS Middleware found"
else
    echo "❌ HTTPS Middleware missing"
    exit 1
fi

# Start the application
echo "🚀 Starting application..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT
