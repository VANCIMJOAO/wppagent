# Railway Monitoring Setup - Automated Deployment Guide

## 🎯 Overview

This directory contains **3 different automated approaches** to deploy Prometheus + Grafana monitoring stack on Railway:

1. **🚀 Quick Deploy** - One-command deployment (Recommended)
2. **🐍 Python Setup** - Full-featured Python automation
3. **🛠️ Bash Setup** - Comprehensive bash automation
4. **⚡ Terraform** - Infrastructure as Code (Advanced)

## 🚀 Option 1: Quick Deploy (Recommended)

**Fastest way to get monitoring running on Railway:**

```bash
# 1. Make sure you're in the project directory
cd /path/to/whats_agent

# 2. Run the quick deploy script
./railway_quick_deploy.sh

# 3. Follow the prompts:
#    - Enter your WhatsApp Agent Railway URL
#    - Wait 2-3 minutes for deployment
#    - Access Grafana and import dashboard manually
```

**What it does:**
- ✅ Creates separate Railway projects for Prometheus and Grafana
- ✅ Generates secure Grafana password
- ✅ Updates configuration files automatically
- ✅ Deploys both services using Dockerfiles
- ✅ Provides deployment summary with URLs and credentials

## 🐍 Option 2: Python Setup (Full-Featured)

**Most robust automation with error handling and API integration:**

```bash
# 1. Install dependencies
pip install requests

# 2. Run Python setup
python railway_monitoring_setup.py

# Optional arguments:
python railway_monitoring_setup.py --project my-monitoring --retention 30d
```

**Features:**
- ✅ Complete API integration with Grafana
- ✅ Automatic dashboard import
- ✅ Service health verification
- ✅ Comprehensive error handling
- ✅ Detailed deployment summary

## 🛠️ Option 3: Bash Setup (Comprehensive)

**Full-featured bash automation with Railway CLI integration:**

```bash
# 1. Run the bash setup
./railway_monitoring_setup.sh

# Optional arguments:
./railway_monitoring_setup.sh --project custom-name --retention 30d --password mypassword
```

**Features:**
- ✅ Project creation and linking
- ✅ Environment variable configuration
- ✅ Service deployment automation
- ✅ API-based Grafana setup
- ✅ Comprehensive logging

## ⚡ Option 4: Terraform (Infrastructure as Code)

**For teams who want version-controlled infrastructure:**

```bash
# 1. Install Terraform
# 2. Initialize Terraform
terraform init

# 3. Plan deployment
terraform plan

# 4. Apply infrastructure
terraform apply
```

**Benefits:**
- ✅ Version-controlled infrastructure
- ✅ Reproducible deployments
- ✅ Team collaboration
- ✅ State management

## 📋 Prerequisites

### All Options:
- Railway CLI installed: `npm install -g @railway/cli`
- Railway account and authentication: `railway login`
- curl installed (usually pre-installed)

### Python Option:
- Python 3.7+
- `pip install requests`

### Terraform Option:
- Terraform installed
- Railway Terraform provider configured

## 🎯 Quick Comparison

| Feature | Quick Deploy | Python | Bash | Terraform |
|---------|-------------|--------|------|-----------|
| **Setup Time** | ~5 min | ~10 min | ~15 min | ~20 min |
| **Automation Level** | High | Very High | High | Very High |
| **Error Handling** | Basic | Excellent | Good | Good |
| **Dashboard Import** | Manual | Automatic | Automatic | Manual |
| **Customization** | Limited | High | High | Very High |
| **Production Ready** | Yes | Yes | Yes | Yes |

## 📊 What Gets Deployed

All options deploy:

### 🔍 Prometheus Service
- **Image**: `prom/prometheus:latest`
- **Config**: Custom Railway-optimized configuration
- **Retention**: 15 days (configurable)
- **Targets**: Your WhatsApp Agent + self-monitoring

### 📈 Grafana Service  
- **Image**: `grafana/grafana:latest`
- **Dashboard**: WhatsApp Agent production dashboard
- **Datasource**: Pre-configured Prometheus connection
- **Security**: Auto-generated admin password

### 🛡️ Features
- ✅ 11-panel production dashboard
- ✅ 10 critical alerting rules
- ✅ Custom metrics integration
- ✅ System and business metrics
- ✅ Automatic service discovery

## 🚀 Post-Deployment Steps

After any deployment method:

### 1. Verify Services
```bash
# Check if services are running
curl https://your-prometheus.railway.app/-/healthy
curl https://your-grafana.railway.app/api/health
```

### 2. Access Grafana
- URL: `https://your-grafana.railway.app`
- Username: `admin`
- Password: (provided in deployment summary)

### 3. Verify Metrics
- Check your app metrics: `https://your-app.railway.app/metrics`
- Verify Prometheus targets: Prometheus → Status → Targets

### 4. Import Dashboard (if not automatic)
- Grafana → Dashboards → Import
- Upload: `grafana/whatsapp_agent_dashboard.json`

## 🔧 Troubleshooting

### Common Issues:

1. **Services not starting**
   ```bash
   railway logs --service prometheus
   railway logs --service grafana
   ```

2. **Metrics not appearing**
   - Verify app URL in prometheus-railway.yml
   - Check if `/metrics` endpoint is accessible
   - Verify prometheus_client is installed in your app

3. **Dashboard not loading**
   - Check Prometheus datasource connection in Grafana
   - Verify dashboard JSON format

4. **Authentication issues**
   ```bash
   railway login
   railway whoami
   ```

### Get Help:
- Railway docs: https://docs.railway.app
- Prometheus docs: https://prometheus.io/docs
- Grafana docs: https://grafana.com/docs

## 🎉 Success Indicators

Your monitoring stack is ready when:

- ✅ Prometheus UI accessible and showing targets as "UP"
- ✅ Grafana dashboard loading with live data
- ✅ WhatsApp Agent metrics visible in dashboard
- ✅ Alerts configured and firing (if applicable)
- ✅ All service health checks passing

## 📱 Example URLs

After deployment, you'll get URLs like:
- **Prometheus**: `https://prometheus-whatsapp-monitoring.railway.app`
- **Grafana**: `https://grafana-whatsapp-monitoring.railway.app`
- **Your App**: `https://your-whatsapp-agent.railway.app`

Choose the option that best fits your needs and technical preferences! 🚀
