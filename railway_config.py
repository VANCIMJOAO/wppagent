# 🚄 Fast Startup Configuration for Railway
# This file controls which services are initialized during startup
# Set to False for faster Railway deployment, True for full production

# Core Services (always enabled)
ENABLE_DATABASE = True
ENABLE_CACHE = True

# Heavy Services (disable for faster Railway startup)
ENABLE_LGPD_SCHEDULER = False  # Heavy database operations
ENABLE_BACKUP_SCHEDULER = False  # Background tasks
ENABLE_DATABASE_OPTIMIZER = False  # Complex DB analysis
ENABLE_CDN_MANAGER = False  # File system operations
ENABLE_WEBSOCKET_MANAGER = False  # Complex async operations
ENABLE_RBAC_SERVICE = False  # Database schema operations

# Set to True for production deployment
RAILWAY_FAST_START = True