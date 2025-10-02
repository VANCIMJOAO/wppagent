# 🐳 Dockerfile with Security Headers and Resilient Image Pull
# Using specific digest for Railway deployment reliability
FROM python:3.11-slim@sha256:a0939570b38cddeb861b8e75d20b1c8218b21562b18f301171904b544e8cf228

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

# Railway-optimized Health check - use /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request, os; port = os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health', timeout=5)" || exit 1

# Start application with Railway-optimized settings and detailed logging
CMD ["sh", "-c", "echo 'Starting WhatsApp Agent API...' && echo 'PORT='$PORT && echo 'RAILWAY_ENVIRONMENT='$RAILWAY_ENVIRONMENT && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info --access-log --timeout-keep-alive 30"]
