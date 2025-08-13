# Railway Monitoring Deployment Values
# Terraform variables file for customizing the deployment

# Project Configuration
project_name = "whatsapp-agent-monitoring"
github_repo  = "https://github.com/VANCIMJOAO/wppagent"

# Monitoring Configuration
prometheus_retention = "15d"

# Application Configuration
app_url = "your-whatsapp-agent.railway.app"

# Custom Domains (optional - leave empty to use Railway domains)
grafana_domain    = ""  # e.g., "grafana.yourdomain.com"
prometheus_domain = ""  # e.g., "prometheus.yourdomain.com"

# If deploying to existing project with WhatsApp Agent
existing_app_project_id = ""  # Railway project ID if app already exists
