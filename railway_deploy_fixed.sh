#!/bin/bash
# 🚄 Railway Deploy Script - FIXED VERSION
# Script simplificado para deploy no Railway

set -e

echo "==================== RAILWAY DEPLOY FIXED ===================="
echo "🚀 Starting WhatsApp Agent API deployment..."
echo "📍 Current directory: $(pwd)"
echo "👤 Current user: $(whoami)"
echo "🐍 Python version: $(python --version)"

# Set Railway environment variables
export RAILWAY_FAST_START=true
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Get port from Railway or use default
FINAL_PORT=${PORT:-8000}
FINAL_HOST="0.0.0.0"

echo -e "\n🌐 NETWORK CONFIGURATION:"
echo "PORT: $FINAL_PORT"
echo "HOST: $FINAL_HOST"
echo "RAILWAY_ENVIRONMENT: ${RAILWAY_ENVIRONMENT:-'NOT_SET'}"

echo -e "\n🧪 TESTING IMPORTS..."
python -c "from app.main import app; print('✅ App import successful')"

echo -e "\n🚀 STARTING UVICORN SERVER..."
echo "Command: uvicorn app.main:app --host $FINAL_HOST --port $FINAL_PORT --log-level info"

# Start uvicorn with Railway-optimized settings
exec uvicorn app.main:app \
    --host "$FINAL_HOST" \
    --port "$FINAL_PORT" \
    --log-level info \
    --access-log \
    --server-header
