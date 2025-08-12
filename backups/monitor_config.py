# Sistema de Monitoramento - Configuração e Alertas
# ================================================

# Configurações do Monitor (adicionar ao config.py ou .env)

# 📱 CONFIGURAÇÕES DE ALERTA
ADMIN_PHONE = "+5511999999999"  # Número do administrador para alertas
ALERT_COOLDOWN_MINUTES = 30     # Intervalo mínimo entre alertas (minutos)

# 🔍 CONFIGURAÇÕES DE THRESHOLDS
MEMORY_WARNING_THRESHOLD = 80   # % de uso de memória para warning
MEMORY_CRITICAL_THRESHOLD = 90  # % de uso de memória para crítico
CPU_WARNING_THRESHOLD = 80      # % de uso de CPU para warning  
CPU_CRITICAL_THRESHOLD = 95     # % de uso de CPU para crítico
DISK_WARNING_THRESHOLD = 85     # % de uso de disco para warning
DISK_CRITICAL_THRESHOLD = 95    # % de uso de disco para crítico

# ⏰ CONFIGURAÇÕES DE MONITORAMENTO
DEFAULT_CHECK_INTERVAL = 300    # Intervalo padrão de verificação (segundos)
API_TIMEOUT = 10               # Timeout para APIs externas (segundos)
DB_CONNECTION_TIMEOUT = 5      # Timeout para conexão DB (segundos)

# 📊 CONFIGURAÇÕES DE RELATÓRIOS
SAVE_REPORTS = True            # Salvar relatórios automáticos
REPORTS_RETENTION_DAYS = 30    # Dias para manter relatórios
MAX_LOG_SIZE_MB = 100         # Tamanho máximo dos logs (MB)
