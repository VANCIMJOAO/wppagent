# ==============================
# MULTI-STAGE DOCKERFILE OTIMIZADO
# WhatsApp Agent - Produção v2.0
# ==============================

# Stage 1: Builder - Compilação e dependências
FROM python:3.11-slim as builder

# Metadados
LABEL maintainer="WhatsApp Agent Team"
LABEL version="2.0"
LABEL description="WhatsApp Agent FastAPI Application - Optimized Multi-Stage"

# Otimizações de build
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools
RUN pip install --user --no-warn-script-location -r requirements.txt

# Copiar código fonte
COPY . .

# Compilar bytecode Python para otimização
RUN python -m compileall . -q

# ==============================
# Stage 2: Runtime - Imagem final otimizada
FROM python:3.11-slim as runtime

# 🔒 SEGURANÇA: Criar usuário não-root
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Configurar timezone
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instalar apenas runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root com UID/GID específicos
RUN groupadd -g 1001 whatsapp && \
    useradd -r -u 1001 -g whatsapp -d /home/whatsapp -s /bin/bash whatsapp && \
    mkdir -p /home/whatsapp && \
    chown -R whatsapp:whatsapp /home/whatsapp

# Configurar diretórios
WORKDIR /home/whatsapp/app

# Copiar scripts e arquivos essenciais
COPY --from=builder --chown=whatsapp:whatsapp /app/ /home/whatsapp/app/

# Configurar PATH do Python para o usuário correto
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copiar aplicação do builder
COPY --from=builder --chown=appuser:appuser /app .

# 🔒 SEGURANÇA: Criar estrutura de diretórios com usuário não-root
RUN mkdir -p \
    logs/{app,security,business,errors} \
    backups/{database,configs} \
    config/secrets \
    tmp/crewai \
    && chown -R appuser:appuser logs backups config tmp

# 🔒 SEGURANÇA: Criar diretórios do CrewAI com permissões seguras
RUN mkdir -p \
    /home/appuser/.local/share/app \
    /home/appuser/.local/share/crewai \
    /home/appuser/.cache \
    && chown -R appuser:appuser /home/appuser/.local /home/appuser/.cache \
    && chmod -R 750 /home/appuser/.local \
    && chmod -R 750 /home/appuser/.cache

# Configurar permissões de execução
RUN chmod +x manage.py run_dev.sh 2>/dev/null || true

# Variáveis de ambiente otimizadas
ENV PYTHONPATH=/home/appuser/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FASTAPI_ENV=production
ENV WORKERS=4
ENV MAX_WORKERS=8
ENV WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV WORKER_CONNECTIONS=1000
ENV KEEPALIVE=2
ENV CREWAI_STORAGE_DIR=/home/appuser/.local/share/app
ENV XDG_DATA_HOME=/home/appuser/.local/share
ENV XDG_CACHE_HOME=/home/appuser/.cache
ENV HOME=/home/appuser

# 🔒 SEGURANÇA: Configurar usuário não-root
USER appuser

# Health check otimizado com nosso script personalizado
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD python docker_health_check.py || exit 1

# Expor porta
EXPOSE 8000

# Signal handling otimizado
STOPSIGNAL SIGTERM

# Comando otimizado com configurações de produção
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--access-log", \
     "--loop", "uvloop", \
     "--http", "httptools"]
