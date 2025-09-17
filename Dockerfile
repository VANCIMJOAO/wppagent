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

# Enhanced Health check - socket based for Railway
HEALTHCHECK --interval=45s --timeout=30s --start-period=180s --retries=3 \
  CMD python -c "import socket, os; s=socket.socket(); s.settimeout(10); s.connect(('localhost', int(os.environ.get('PORT', '8000')))); s.close()" || exit 1

# Start application with debug logging
CMD ["./railway_start.sh"]
