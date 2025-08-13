# Railway Monitoring Stack Configuration
# Terraform configuration for automated Railway deployment

terraform {
  required_providers {
    railway = {
      source  = "terraform-community-providers/railway"
      version = "~> 0.3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# Generate secure password for Grafana
resource "random_password" "grafana_admin_password" {
  length  = 32
  special = true
}

# Railway Project
resource "railway_project" "monitoring" {
  name        = var.project_name
  description = "WhatsApp Agent Monitoring Infrastructure"
}

# Prometheus Service
resource "railway_service" "prometheus" {
  project_id = railway_project.monitoring.id
  name       = "prometheus"
  
  source {
    repo = var.github_repo
    path = "/"
  }
  
  build {
    dockerfile = "Dockerfile.prometheus"
  }
  
  deploy {
    replicas = 1
    
    environment = {
      PROMETHEUS_RETENTION_TIME = var.prometheus_retention
      PROMETHEUS_CONFIG_PATH   = "/etc/prometheus/prometheus.yml"
    }
  }
}

# Grafana Service
resource "railway_service" "grafana" {
  project_id = railway_project.monitoring.id
  name       = "grafana"
  
  source {
    repo = var.github_repo
    path = "/"
  }
  
  build {
    dockerfile = "Dockerfile.grafana"
  }
  
  deploy {
    replicas = 1
    
    environment = {
      GF_SECURITY_ADMIN_PASSWORD     = random_password.grafana_admin_password.result
      GF_INSTALL_PLUGINS            = "grafana-piechart-panel"
      GF_SERVER_ROOT_URL            = "https://${railway_service.grafana.domain}"
      GF_SECURITY_ALLOW_EMBEDDING   = "true"
      GF_AUTH_ANONYMOUS_ENABLED     = "false"
    }
  }
}

# Custom Domain for Grafana (optional)
resource "railway_custom_domain" "grafana" {
  count      = var.grafana_domain != "" ? 1 : 0
  project_id = railway_project.monitoring.id
  service_id = railway_service.grafana.id
  domain     = var.grafana_domain
}

# Custom Domain for Prometheus (optional)  
resource "railway_custom_domain" "prometheus" {
  count      = var.prometheus_domain != "" ? 1 : 0
  project_id = railway_project.monitoring.id
  service_id = railway_service.prometheus.id
  domain     = var.prometheus_domain
}

# Variables
variable "project_name" {
  description = "Name of the Railway project"
  type        = string
  default     = "whatsapp-agent-monitoring"
}

variable "github_repo" {
  description = "GitHub repository URL"
  type        = string
  default     = "https://github.com/VANCIMJOAO/wppagent"
}

variable "prometheus_retention" {
  description = "Prometheus data retention period"
  type        = string
  default     = "15d"
}

variable "grafana_domain" {
  description = "Custom domain for Grafana (optional)"
  type        = string
  default     = ""
}

variable "prometheus_domain" {
  description = "Custom domain for Prometheus (optional)"
  type        = string
  default     = ""
}

variable "app_url" {
  description = "WhatsApp Agent application URL for metrics scraping"
  type        = string
}

# Outputs
output "grafana_url" {
  description = "Grafana dashboard URL"
  value       = var.grafana_domain != "" ? "https://${var.grafana_domain}" : "https://${railway_service.grafana.domain}"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = var.prometheus_domain != "" ? "https://${var.prometheus_domain}" : "https://${railway_service.prometheus.domain}"
}

output "grafana_admin_password" {
  description = "Grafana admin password"
  value       = random_password.grafana_admin_password.result
  sensitive   = true
}

output "project_id" {
  description = "Railway project ID"
  value       = railway_project.monitoring.id
}

# Data sources for existing services (if needed)
data "railway_project" "app_project" {
  count = var.existing_app_project_id != "" ? 1 : 0
  id    = var.existing_app_project_id
}

variable "existing_app_project_id" {
  description = "Existing Railway project ID for the WhatsApp Agent (optional)"
  type        = string
  default     = ""
}
