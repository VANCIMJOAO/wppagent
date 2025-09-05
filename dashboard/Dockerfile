FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do dashboard
COPY . .

# Criar usuário não-root para segurança
RUN groupadd -r dashuser && useradd -r -g dashuser dashuser
RUN chown -R dashuser:dashuser /app
USER dashuser

# Expor porta
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8050/ || exit 1

# Comando de execução
CMD ["python", "app.py"]
