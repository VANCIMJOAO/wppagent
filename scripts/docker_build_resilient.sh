#!/bin/bash
# 🐳 Docker Build Script with Registry Failover
# Handles Docker Hub outages and registry issues

set -e

echo "🐳 Starting resilient Docker build..."

# List of potential base images to try
IMAGES=(
    "python:3.11.9-slim-bookworm"
    "python:3.11-slim"
    "python:3.11.9-slim"
    "python@sha256:5d15266bbc7e2968c74fb93e8b54e70f4a21aae1f0e36e37b8a8e6fcf4b0a42b"
)

# Alternative registries
ALT_REGISTRIES=(
    ""  # Docker Hub (default)
    "ghcr.io/"
    "quay.io/"
)

BUILD_SUCCESS=false
ATTEMPT=1
MAX_ATTEMPTS=5

for registry in "${ALT_REGISTRIES[@]}"; do
    for image in "${IMAGES[@]}"; do
        if [ "$BUILD_SUCCESS" = true ]; then
            break 2
        fi
        
        FULL_IMAGE="${registry}${image}"
        echo "🔄 Attempt $ATTEMPT/$MAX_ATTEMPTS: Trying image $FULL_IMAGE"
        
        # Create temporary Dockerfile with current image
        cat > Dockerfile.temp << EOF
# 🐳 Auto-generated Dockerfile with Fallback Image
FROM $FULL_IMAGE

# Security: Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with retry
RUN pip install --no-cache-dir --retries 5 --timeout 120 -r requirements.txt

# Copy application code
COPY . .

# Set ownership to app user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

        # Try building with current image
        if timeout 300 docker build -f Dockerfile.temp -t whatsapp-agent:latest . 2>/dev/null; then
            echo "✅ Build successful with image: $FULL_IMAGE"
            BUILD_SUCCESS=true
            
            # Update main Dockerfile with working image
            sed -i "s|FROM.*|FROM $FULL_IMAGE|" Dockerfile
            echo "📝 Updated Dockerfile with working base image"
            break 2
        else
            echo "❌ Build failed with image: $FULL_IMAGE"
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
        if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
            break 2
        fi
        
        sleep 5  # Wait before next attempt
    done
done

# Cleanup
rm -f Dockerfile.temp

if [ "$BUILD_SUCCESS" = true ]; then
    echo "🎉 Docker build completed successfully!"
    echo "🏷️  Image tagged as: whatsapp-agent:latest"
    
    # Show image info
    docker images whatsapp-agent:latest
    
    exit 0
else
    echo "💥 All build attempts failed!"
    echo "🔍 Possible issues:"
    echo "   - Docker Hub registry issues (500 Internal Server Error)"
    echo "   - Network connectivity problems"
    echo "   - Rate limiting"
    echo ""
    echo "🛠️  Solutions to try:"
    echo "   1. Wait a few minutes and retry"
    echo "   2. Use 'docker system prune' to clear cache"
    echo "   3. Check Docker Hub status: https://status.docker.com/"
    echo "   4. Try manual pull: docker pull python:3.11-slim"
    
    exit 1
fi