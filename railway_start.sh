#!/bin/bash
# 🚄 Railway Startup Script with Enhanced Debug Logging
set -e

echo "==================== RAILWAY STARTUP DEBUG ===================="
echo "🚀 Container startup initiated at $(date)"
echo "📍 Current directory: $(pwd)"
echo "� Current user: $(whoami)"
echo "� Python version: $(python --version)"

echo -e "\n🌐 NETWORK INFO:"
echo "PORT: ${PORT:-'NOT_SET'}"
echo "HOST: ${HOST:-'NOT_SET'}"
echo "Railway PORT: ${RAILWAY_PORT:-'NOT_SET'}"

echo -e "\n� FILE SYSTEM CHECK:"
ls -la
echo -e "\nAPP directory exists:"
ls -la app/ | head -10

echo -e "\n🧪 PYTHON IMPORT TEST:"
python -c "print('✅ Python executable working')"

echo "� Testing uvicorn import..."
python -c "import uvicorn; print('✅ uvicorn import OK')" || {
    echo "❌ uvicorn import failed!"
    python -c "import sys; print('Python path:', sys.path)"
    pip list | grep uvicorn || echo "uvicorn not found in pip list"
    exit 1
}

echo "🔍 Testing app import..."
export RAILWAY_FAST_START=true
python -c "from app.main import app; print('✅ app import OK')" || {
    echo "❌ app import failed!"
    echo "Checking Python path and imports..."
    python -c "import sys; print('sys.path:', sys.path)"
    exit 1
}

echo -e "\n🔧 ENVIRONMENT VARIABLES:"
env | grep -E '^(PORT|HOST|RAILWAY|DATABASE|REDIS|JWT)' | sort

echo -e "\n🌐 NETWORK TEST:"
netstat -tlnp 2>/dev/null || echo "netstat not available"

echo -e "\n🚀 STARTING UVICORN SERVER..."
echo "Command: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"

# Start uvicorn with error handling
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} || {
    echo "❌ uvicorn startup failed!"
    echo "Checking if port is already in use..."
    lsof -i :${PORT:-8000} 2>/dev/null || echo "Port check failed - lsof not available"
    exit 1
}