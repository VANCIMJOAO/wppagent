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

# Copy startup script
COPY railway_start.sh .
RUN chmod +x railway_start.sh

# Set ownership to app user
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check (using python instead of curl)
HEALTHCHECK --interval=30s --timeout=20s --start-period=120s --retries=5 \
  CMD python -c "import urllib.request, os; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\", \"8000\")}/ping', timeout=15)" || exit 1

# Start application with debug logging
CMD ["./railway_start.sh"]
