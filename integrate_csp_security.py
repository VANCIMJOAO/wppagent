"""
🔧 FastAPI CSP Middleware Integration
====================================

Script para integrar o middleware CSP completo na aplicação FastAPI
e garantir que seja aplicado corretamente em produção.
"""

import os
import sys
from pathlib import Path

def integrate_csp_middleware():
    """Integrate CSP middleware into the main FastAPI app"""
    
    print("🔧 Integrating CSP Middleware into FastAPI application...")
    
    # Check if main app file exists
    app_files = [
        "app/main.py",
        "main.py", 
        "app.py"
    ]
    
    main_app_file = None
    for app_file in app_files:
        if os.path.exists(app_file):
            main_app_file = app_file
            break
    
    if not main_app_file:
        print("❌ Could not find main application file")
        return False
    
    print(f"✅ Found main app file: {main_app_file}")
    
    # Read current content
    with open(main_app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if CSP middleware is already imported
    if "from app.security.csp_manager import CSPMiddleware" in content:
        print("✅ CSP middleware already imported")
    else:
        # Add import
        if "from fastapi import FastAPI" in content:
            content = content.replace(
                "from fastapi import FastAPI",
                "from fastapi import FastAPI\nfrom app.security.csp_manager import CSPMiddleware"
            )
            print("✅ Added CSP middleware import")
    
    # Check if middleware is added to app
    if "app.add_middleware(CSPMiddleware)" in content:
        print("✅ CSP middleware already added to app")
    else:
        # Find where to add middleware
        if "app = FastAPI(" in content:
            # Find the end of FastAPI initialization
            lines = content.split('\n')
            new_lines = []
            app_created = False
            
            for line in lines:
                new_lines.append(line)
                if "app = FastAPI(" in line and not app_created:
                    app_created = True
                elif app_created and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    # First line after app creation, add middleware here
                    new_lines.insert(-1, "")
                    new_lines.insert(-1, "# Add CSP Security Middleware")
                    new_lines.insert(-1, "app.add_middleware(CSPMiddleware)")
                    new_lines.insert(-1, "")
                    app_created = False
            
            content = '\n'.join(new_lines)
            print("✅ Added CSP middleware to app")
    
    # Write back the modified content
    with open(main_app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ CSP middleware integration complete in {main_app_file}")
    
    # Also ensure HTTPS middleware is integrated
    integrate_https_middleware(main_app_file)
    
    return True

def integrate_https_middleware(main_app_file):
    """Ensure HTTPS middleware is also properly integrated"""
    
    with open(main_app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if HTTPS middleware exists and is imported
    https_middleware_path = "app/security/https_middleware.py"
    if os.path.exists(https_middleware_path):
        if "from app.security.https_middleware import HTTPSMiddleware" not in content:
            content = content.replace(
                "from app.security.csp_manager import CSPMiddleware",
                "from app.security.csp_manager import CSPMiddleware\nfrom app.security.https_middleware import HTTPSMiddleware"
            )
            print("✅ Added HTTPS middleware import")
        
        if "app.add_middleware(HTTPSMiddleware)" not in content:
            content = content.replace(
                "app.add_middleware(CSPMiddleware)",
                "app.add_middleware(CSPMiddleware)\napp.add_middleware(HTTPSMiddleware)"
            )
            print("✅ Added HTTPS middleware to app")
        
        with open(main_app_file, 'w', encoding='utf-8') as f:
            f.write(content)

def create_production_startup_script():
    """Create a startup script for production deployment"""
    
    startup_script = '''#!/bin/bash
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
'''
    
    with open("start-production.sh", "w", encoding="utf-8") as f:
        f.write(startup_script)
    
    # Make executable
    os.chmod("start-production.sh", 0o755)
    print("✅ Created production startup script")

def update_requirements():
    """Ensure all security dependencies are in requirements.txt"""
    
    security_deps = [
        "pycryptodome>=3.19.0",
        "cryptography>=41.0.0", 
        "python-jose>=3.3.0",
        "passlib>=1.7.4"
    ]
    
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        with open(requirements_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        added_deps = []
        for dep in security_deps:
            dep_name = dep.split(">=")[0]
            if dep_name not in content:
                content += f"\n{dep}"
                added_deps.append(dep)
        
        if added_deps:
            with open(requirements_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Added security dependencies: {', '.join(added_deps)}")
        else:
            print("✅ All security dependencies already present")
    else:
        print("❌ requirements.txt not found")

def create_dockerfile_with_security():
    """Create/update Dockerfile with security optimizations"""
    
    dockerfile_content = '''# 🐳 Dockerfile with Security Headers
FROM python:3.11-slim

# Security: Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

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
  CMD curl -f http://localhost:8000/health || exit 1

# Start application with security
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    
    with open("Dockerfile", "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    
    print("✅ Created/updated Dockerfile with security optimizations")

def main():
    """Main integration function"""
    
    print("🔧 CSP Security Integration Script")
    print("=" * 50)
    
    try:
        # Step 1: Integrate middleware
        if integrate_csp_middleware():
            print("✅ Step 1: CSP Middleware integrated")
        else:
            print("❌ Step 1: Failed to integrate CSP middleware")
            return False
        
        # Step 2: Create production startup
        create_production_startup_script()
        print("✅ Step 2: Production startup script created")
        
        # Step 3: Update requirements
        update_requirements()
        print("✅ Step 3: Requirements updated")
        
        # Step 4: Create secure Dockerfile
        create_dockerfile_with_security()
        print("✅ Step 4: Dockerfile updated")
        
        print("\n🎉 CSP Security Integration Complete!")
        print("\n📋 Next Steps:")
        print("   1. Commit and push changes")
        print("   2. Deploy to Railway")
        print("   3. Test CSP headers in production")
        print("   4. Monitor CSP violation reports")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
