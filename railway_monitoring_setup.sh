#!/bin/bash

# Railway Monitoring Stack Auto-Setup Script
# Automatically configures Prometheus and Grafana services on Railway
# Usage: ./railway_monitoring_setup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
RAILWAY_TOKEN=""
PROJECT_NAME="whatsapp-agent-monitoring"
GRAFANA_ADMIN_PASSWORD="$(openssl rand -base64 32)"
PROMETHEUS_RETENTION="15d"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️ $message${NC}"
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    print_status "INFO" "Checking prerequisites..."
    
    # Check if Railway CLI is installed
    if ! command -v railway &> /dev/null; then
        print_status "FAIL" "Railway CLI not found. Please install it first:"
        echo "npm install -g @railway/cli"
        exit 1
    fi
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        print_status "FAIL" "curl not found. Please install curl."
        exit 1
    fi
    
    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        print_status "WARNING" "jq not found. JSON parsing will be limited."
        echo "Install jq for better JSON handling: sudo apt-get install jq"
    fi
    
    print_status "SUCCESS" "Prerequisites check completed"
}

# Function to setup Railway authentication
setup_railway_auth() {
    print_status "INFO" "Setting up Railway authentication..."
    
    if [ -z "$RAILWAY_TOKEN" ]; then
        print_status "INFO" "Please login to Railway CLI:"
        railway login
        
        if [ $? -eq 0 ]; then
            print_status "SUCCESS" "Railway authentication successful"
        else
            print_status "FAIL" "Railway authentication failed"
            exit 1
        fi
    else
        print_status "INFO" "Using provided Railway token"
        export RAILWAY_TOKEN="$RAILWAY_TOKEN"
    fi
}

# Function to create Railway project
create_railway_project() {
    print_status "INFO" "Creating Railway project: $PROJECT_NAME"
    
    # Create new project
    railway create "$PROJECT_NAME" || {
        print_status "WARNING" "Project may already exist, continuing..."
    }
    
    # Link to project
    railway link "$PROJECT_NAME" || {
        print_status "FAIL" "Failed to link to project"
        exit 1
    }
    
    print_status "SUCCESS" "Railway project setup completed"
}

# Function to deploy Prometheus service
deploy_prometheus() {
    print_status "INFO" "Deploying Prometheus service..."
    
    # Create Prometheus service
    cat > railway-prometheus.yml << EOF
apiVersion: v1
kind: Service
metadata:
  name: prometheus
spec:
  image: prom/prometheus:latest
  restart: always
  variables:
    - name: PROMETHEUS_RETENTION_TIME
      value: "$PROMETHEUS_RETENTION"
  volumes:
    - name: prometheus-config
      mountPath: /etc/prometheus/prometheus.yml
      source: ./prometheus/prometheus.yml
    - name: prometheus-alerts
      mountPath: /etc/prometheus/alerts
      source: ./prometheus/alerts
  ports:
    - containerPort: 9090
      protocol: TCP
EOF

    # Deploy Prometheus
    railway deploy --service prometheus --config railway-prometheus.yml
    
    if [ $? -eq 0 ]; then
        print_status "SUCCESS" "Prometheus service deployed"
    else
        print_status "FAIL" "Prometheus deployment failed"
        exit 1
    fi
}

# Function to deploy Grafana service
deploy_grafana() {
    print_status "INFO" "Deploying Grafana service..."
    
    # Create Grafana service configuration
    cat > railway-grafana.yml << EOF
apiVersion: v1
kind: Service
metadata:
  name: grafana
spec:
  image: grafana/grafana:latest
  restart: always
  variables:
    - name: GF_SECURITY_ADMIN_PASSWORD
      value: "$GRAFANA_ADMIN_PASSWORD"
    - name: GF_INSTALL_PLUGINS
      value: "grafana-piechart-panel"
    - name: GF_SERVER_ROOT_URL
      value: "https://\${RAILWAY_PUBLIC_DOMAIN}"
    - name: GF_SECURITY_ALLOW_EMBEDDING
      value: "true"
    - name: GF_AUTH_ANONYMOUS_ENABLED
      value: "false"
  volumes:
    - name: grafana-datasources
      mountPath: /etc/grafana/provisioning/datasources
      source: ./grafana/datasources
    - name: grafana-dashboards
      mountPath: /etc/grafana/provisioning/dashboards
      source: ./grafana/dashboards
  ports:
    - containerPort: 3000
      protocol: TCP
EOF

    # Deploy Grafana
    railway deploy --service grafana --config railway-grafana.yml
    
    if [ $? -eq 0 ]; then
        print_status "SUCCESS" "Grafana service deployed"
        print_status "INFO" "Grafana admin password: $GRAFANA_ADMIN_PASSWORD"
    else
        print_status "FAIL" "Grafana deployment failed"
        exit 1
    fi
}

# Function to configure environment variables
configure_environment() {
    print_status "INFO" "Configuring environment variables..."
    
    # Set Prometheus variables
    railway variables set PROMETHEUS_RETENTION_TIME="$PROMETHEUS_RETENTION" --service prometheus
    railway variables set PROMETHEUS_CONFIG_PATH="/etc/prometheus/prometheus.yml" --service prometheus
    
    # Set Grafana variables
    railway variables set GF_SECURITY_ADMIN_PASSWORD="$GRAFANA_ADMIN_PASSWORD" --service grafana
    railway variables set GF_INSTALL_PLUGINS="grafana-piechart-panel" --service grafana
    railway variables set GF_SERVER_ROOT_URL="https://\${RAILWAY_PUBLIC_DOMAIN}" --service grafana
    
    print_status "SUCCESS" "Environment variables configured"
}

# Function to setup Grafana via API
setup_grafana_api() {
    local grafana_url=$1
    
    print_status "INFO" "Setting up Grafana via API..."
    
    # Wait for Grafana to be ready
    print_status "INFO" "Waiting for Grafana to start..."
    for i in {1..30}; do
        if curl -s "$grafana_url/api/health" >/dev/null 2>&1; then
            break
        fi
        sleep 10
    done
    
    # Create datasource
    print_status "INFO" "Creating Prometheus datasource..."
    curl -X POST \
        -H "Content-Type: application/json" \
        -u "admin:$GRAFANA_ADMIN_PASSWORD" \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "'$prometheus_url'",
            "access": "proxy",
            "isDefault": true
        }' \
        "$grafana_url/api/datasources"
    
    # Import dashboard
    print_status "INFO" "Importing WhatsApp Agent dashboard..."
    local dashboard_json=$(cat grafana/whatsapp_agent_dashboard.json)
    curl -X POST \
        -H "Content-Type: application/json" \
        -u "admin:$GRAFANA_ADMIN_PASSWORD" \
        -d "{\"dashboard\": $dashboard_json, \"overwrite\": true}" \
        "$grafana_url/api/dashboards/db"
    
    print_status "SUCCESS" "Grafana API setup completed"
}

# Function to get service URLs
get_service_urls() {
    print_status "INFO" "Getting service URLs..."
    
    # Get Prometheus URL
    prometheus_url=$(railway status --service prometheus --json | jq -r '.deployments[0].url' 2>/dev/null || echo "")
    if [ -z "$prometheus_url" ]; then
        prometheus_url="https://prometheus-${PROJECT_NAME}.railway.app"
    fi
    
    # Get Grafana URL
    grafana_url=$(railway status --service grafana --json | jq -r '.deployments[0].url' 2>/dev/null || echo "")
    if [ -z "$grafana_url" ]; then
        grafana_url="https://grafana-${PROJECT_NAME}.railway.app"
    fi
    
    echo "prometheus_url=$prometheus_url"
    echo "grafana_url=$grafana_url"
}

# Function to update Prometheus config for Railway
update_prometheus_config() {
    print_status "INFO" "Updating Prometheus config for Railway..."
    
    # Get the application URL
    app_url=$(railway status --service whatsapp-agent --json | jq -r '.deployments[0].url' 2>/dev/null || echo "")
    if [ -z "$app_url" ]; then
        print_status "WARNING" "Could not get application URL automatically"
        read -p "Enter your WhatsApp Agent Railway URL: " app_url
    fi
    
    # Update prometheus.yml for Railway
    cat > prometheus/prometheus-railway.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/alerts/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

scrape_configs:
  - job_name: 'whatsapp-agent'
    static_configs:
      - targets: ['${app_url#https://}']
    metrics_path: '/metrics'
    scheme: 'https'
    scrape_interval: 15s
    scrape_timeout: 10s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

    print_status "SUCCESS" "Prometheus config updated for Railway"
}

# Function to create deployment summary
create_deployment_summary() {
    print_status "INFO" "Creating deployment summary..."
    
    cat > RAILWAY_DEPLOYMENT_SUMMARY.md << EOF
# Railway Monitoring Stack Deployment Summary

## 🚀 Deployed Services

### Prometheus
- **URL**: $prometheus_url
- **Retention**: $PROMETHEUS_RETENTION
- **Config**: prometheus/prometheus-railway.yml

### Grafana
- **URL**: $grafana_url
- **Username**: admin
- **Password**: $GRAFANA_ADMIN_PASSWORD
- **Dashboard**: WhatsApp Agent Production Dashboard

## 📊 Monitoring Setup

### Accessing Dashboards
1. **Grafana**: Visit $grafana_url
2. **Prometheus**: Visit $prometheus_url
3. **Metrics**: Your app URL + /metrics

### Key Features
- ✅ Automatic dashboard provisioning
- ✅ Prometheus datasource pre-configured
- ✅ WhatsApp Agent dashboard imported
- ✅ Alert rules configured
- ✅ Environment variables set

## 🔧 Next Steps

1. **Verify Metrics**: Check that your app is exposing metrics
2. **Test Alerts**: Validate alerting rules are working
3. **Customize**: Adjust dashboard panels as needed
4. **Security**: Review and update passwords

## 🛠️ Maintenance Commands

\`\`\`bash
# Update services
railway deploy --service prometheus
railway deploy --service grafana

# Check logs
railway logs --service prometheus
railway logs --service grafana

# Update environment variables
railway variables set VAR_NAME=value --service service_name
\`\`\`

## 📱 Monitoring URLs
- **Application**: $app_url
- **Prometheus**: $prometheus_url
- **Grafana**: $grafana_url

Generated on: $(date)
EOF

    print_status "SUCCESS" "Deployment summary created: RAILWAY_DEPLOYMENT_SUMMARY.md"
}

# Main execution function
main() {
    echo "🚀 Railway Monitoring Stack Auto-Setup"
    echo "======================================"
    
    # Check prerequisites
    check_prerequisites
    
    # Setup Railway authentication
    setup_railway_auth
    
    # Create project
    create_railway_project
    
    # Update configs for Railway
    update_prometheus_config
    
    # Deploy services
    deploy_prometheus
    deploy_grafana
    
    # Configure environment
    configure_environment
    
    # Get service URLs
    eval $(get_service_urls)
    
    # Wait for services to be ready
    print_status "INFO" "Waiting for services to be ready..."
    sleep 60
    
    # Setup Grafana via API
    setup_grafana_api "$grafana_url"
    
    # Create deployment summary
    create_deployment_summary
    
    echo ""
    echo "🎉 Railway Monitoring Stack Setup Complete!"
    echo "==========================================="
    echo ""
    echo -e "${GREEN}📊 Grafana Dashboard:${NC} $grafana_url"
    echo -e "${GREEN}📈 Prometheus:${NC} $prometheus_url"
    echo -e "${GREEN}🔑 Grafana Password:${NC} $GRAFANA_ADMIN_PASSWORD"
    echo ""
    echo -e "${BLUE}📋 Full deployment details saved to:${NC} RAILWAY_DEPLOYMENT_SUMMARY.md"
    echo ""
    print_status "SUCCESS" "Monitoring infrastructure is ready for production!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --token)
            RAILWAY_TOKEN="$2"
            shift 2
            ;;
        --project)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --password)
            GRAFANA_ADMIN_PASSWORD="$2"
            shift 2
            ;;
        --retention)
            PROMETHEUS_RETENTION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --token TOKEN        Railway API token (optional, will prompt for login)"
            echo "  --project NAME       Project name (default: whatsapp-agent-monitoring)"
            echo "  --password PASS      Grafana admin password (default: auto-generated)"
            echo "  --retention PERIOD   Prometheus retention period (default: 15d)"
            echo "  --help              Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Execute main function
main "$@"
