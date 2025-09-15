#!/bin/bash
# 🚄 Railway Deploy Script with Docker Registry Resilience
# Handles Railway deployment issues with Docker Hub

set -e

echo "🚄 Preparing Railway deployment with registry resilience..."

# Function to update Dockerfile with different base images
update_dockerfile_base() {
    local base_image="$1"
    echo "🔄 Updating Dockerfile base image to: $base_image"
    
    # Create backup
    cp Dockerfile Dockerfile.backup
    
    # Update base image
    sed -i "s|FROM.*|FROM $base_image|" Dockerfile
}

# Railway-compatible base images (in order of preference)
RAILWAY_IMAGES=(
    # Current working digest
    "python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228"
    
    # Fallback to latest stable
    "python:3.11-slim"
    
    # Alternative Python versions
    "python:3.11.9-slim"
    "python:3.10-slim"
    
    # GitHub Container Registry fallback
    "ghcr.io/python/python:3.11-slim"
)

echo "📋 Available deployment strategies:"
for i in "${!RAILWAY_IMAGES[@]}"; do
    echo "   $((i+1)). ${RAILWAY_IMAGES[i]}"
done

# Try each image strategy
for i in "${!RAILWAY_IMAGES[@]}"; do
    image="${RAILWAY_IMAGES[i]}"
    echo ""
    echo "🔄 Strategy $((i+1))/${#RAILWAY_IMAGES[@]}: Using $image"
    
    # Update Dockerfile
    update_dockerfile_base "$image"
    
    echo "✅ Dockerfile updated for Railway deployment"
    echo "📝 Current FROM line:"
    head -n 3 Dockerfile | grep FROM
    
    echo ""
    echo "🚄 Ready for Railway deployment!"
    echo "💡 Next steps:"
    echo "   1. Commit changes: git add Dockerfile && git commit -m 'fix: update base image for Railway compatibility'"
    echo "   2. Push to trigger Railway deploy: git push origin main"
    echo "   3. Monitor Railway dashboard for build progress"
    
    # Offer to commit automatically
    read -p "🤔 Auto-commit this change? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add Dockerfile railway.toml Dockerfile.railway
        git commit -m "fix(railway): update base image for Railway deployment resilience

- Updated FROM to use specific digest: $image
- Added Railway-specific configuration
- Enhanced Docker registry reliability for Railway platform"
        
        echo "✅ Changes committed!"
        echo "🚀 Push to deploy: git push origin main"
    fi
    
    break  # Exit after first attempt - user can manually retry with other strategies
done

# Cleanup
if [[ -f Dockerfile.backup ]]; then
    echo "💾 Dockerfile backup saved as Dockerfile.backup"
fi

echo ""
echo "🎯 Railway Deployment Tips:"
echo "   • Monitor: railway logs --tail"
echo "   • Status: railway status"
echo "   • Redeploy: railway up"
echo "   • If build fails, try next image strategy in this script"