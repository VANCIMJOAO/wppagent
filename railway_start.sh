#!/bin/bash
# 🚄 Railway Startup Script with Enhanced Debug Logging
set -e

echo "==================== RAILWAY STARTUP DEBUG ===================="
echo "🚀 Container startup initiated at $(date)"
echo "📍 Current directory: $(pwd)"
echo "👤 Current user: $(whoami)"
echo "🐍 Python version: $(python --version)"

# Railway Environment Detection
echo -e "\n🔍 RAILWAY ENVIRONMENT DETECTION:"
if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "✅ Railway environment detected: $RAILWAY_ENVIRONMENT"
    export RAILWAY_DETECTED=true
else
    echo "❌ Railway environment not detected"
    export RAILWAY_DETECTED=false
fi

echo -e "\n🌐 NETWORK INFO:"
echo "PORT: ${PORT:-'NOT_SET'}"
echo "HOST: ${HOST:-'NOT_SET'}"
echo "Railway PORT: ${RAILWAY_PORT:-'NOT_SET'}"
echo "Railway PUBLIC DOMAIN: ${RAILWAY_PUBLIC_DOMAIN:-'NOT_SET'}"
echo "Railway PRIVATE DOMAIN: ${RAILWAY_PRIVATE_DOMAIN:-'NOT_SET'}"

# Railway-specific port handling
if [ "$RAILWAY_DETECTED" = "true" ]; then
    # Use Railway PORT or default to 8000
    FINAL_PORT=${PORT:-8000}
    FINAL_HOST="0.0.0.0"
    echo "🚄 Railway mode: Using port $FINAL_PORT on host $FINAL_HOST"
else
    FINAL_PORT=${PORT:-8000}
    FINAL_HOST=${HOST:-"0.0.0.0"}
    echo "🏠 Local mode: Using port $FINAL_PORT on host $FINAL_HOST"
fi

echo -e "\n📁 FILE SYSTEM CHECK:"
ls -la
echo -e "\nAPP directory exists:"
ls -la app/ | head -10

echo -e "\n🧪 PYTHON IMPORT TEST:"
python -c "print('✅ Python executable working')"

echo "🔍 Testing uvicorn import..."
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
netstat -tlnp 2>/dev/null || echo "⚠️ netstat not available"

# Test port binding capability with Railway-specific checks
echo "🔌 Testing port binding on $FINAL_PORT..."
python -c "
import socket
port = $FINAL_PORT
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', port))
    s.close()
    print(f'✅ Port {port} is available for binding')
except Exception as e:
    print(f'❌ Port {port} binding test failed: {e}')
    exit(1)
"

echo -e "\n🚀 STARTING UVICORN SERVER WITH RAILWAY OPTIMIZATIONS..."
echo "Command: uvicorn app.main:app --host $FINAL_HOST --port $FINAL_PORT --log-level info"

# Railway-specific uvicorn configuration
if [ "$RAILWAY_DETECTED" = "true" ]; then
    echo "🚄 Using Railway-optimized uvicorn settings"
    # Railway production settings
    exec uvicorn app.main:app \
        --host "$FINAL_HOST" \
        --port "$FINAL_PORT" \
        --log-level info \
        --access-log \
        --server-header \
        --forwarded-allow-ips="*" \
        --proxy-headers || {
        echo "❌ Railway uvicorn startup failed!"
        echo "Checking if port is already in use..."
        lsof -i :$FINAL_PORT 2>/dev/null || echo "Port check failed - lsof not available"
        exit 1
    }
else
    echo "🏠 Using local development settings"
    # Local development settings
    exec uvicorn app.main:app \
        --host "$FINAL_HOST" \
        --port "$FINAL_PORT" \
        --log-level info \
        --access-log \
        --server-header || {
        echo "❌ Local uvicorn startup failed!"
        echo "Checking if port is already in use..."
        lsof -i :$FINAL_PORT 2>/dev/null || echo "Port check failed - lsof not available"
        exit 1
    }
fi