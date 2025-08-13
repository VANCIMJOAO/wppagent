# Monitoring Infrastructure Setup for WhatsApp Agent

## Overview
This directory contains the complete monitoring infrastructure setup for the WhatsApp Agent application using Prometheus and Grafana.

## Components

### 1. Prometheus Configuration (`prometheus/`)
- **prometheus.yml**: Main configuration with scraping targets
- **alerts/whatsapp_agent_alerts.yml**: Alerting rules for system health

### 2. Grafana Configuration (`grafana/`)
- **whatsapp_agent_dashboard.json**: Production dashboard with 11 key panels
- **datasources/prometheus.yml**: Prometheus datasource configuration
- **dashboards/dashboard-provider.yml**: Dashboard provider configuration

### 3. Application Integration (`app/utils/metrics.py`)
- **MetricsCollector**: Centralized metrics collection
- **Custom Metrics**: HTTP requests, webhook processing, database operations
- **Business Metrics**: Lead scoring, cache performance

### 4. Middleware Integration (`app/middleware/metrics.py`)
- **MetricsMiddleware**: HTTP request/response monitoring
- **Path Normalization**: Groups similar endpoints for better analytics

## Quick Start

### 1. Start Monitoring Stack
```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Check services
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Dashboards
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Metrics Endpoint**: http://localhost:8000/metrics

### 3. Import Dashboard
1. Open Grafana at http://localhost:3000
2. Login with admin/admin123
3. Go to Dashboards → Import
4. Upload `grafana/whatsapp_agent_dashboard.json`

## Metrics Available

### HTTP Metrics
- `http_requests_total`: Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds`: Request duration histogram

### Webhook Metrics
- `webhook_messages_processed_total`: Messages processed with status
- `webhook_processing_duration_seconds`: Processing time histogram

### Database Metrics
- `database_connections_active/idle`: Connection pool status
- `database_query_duration_seconds`: Query performance

### System Metrics
- `process_resident_memory_bytes`: Memory usage
- `process_cpu_seconds_total`: CPU usage

### Business Metrics
- `lead_scoring_processed_total`: Leads processed by score range
- `lead_scoring_errors_total`: Scoring errors by type
- `cache_hit_rate`: Cache performance percentage

### Rate Limiting
- `rate_limit_hits_total`: Rate limit violations by type

## Alerting Rules

### Critical Alerts
1. **API Down**: Service unavailable
2. **High Error Rate**: >5% error rate for 2 minutes
3. **Slow Response Time**: >2s 95th percentile for 5 minutes
4. **High Memory Usage**: >80% memory usage
5. **Database Issues**: Connection problems or slow queries

### Warning Alerts
1. **Moderate Error Rate**: >2% error rate
2. **Cache Performance**: <70% hit rate
3. **Rate Limiting**: High rate limit hits
4. **Webhook Processing**: Slow processing times

## Dashboard Panels

1. **API Health Status**: Service availability indicator
2. **Request Rate**: Requests per minute by endpoint
3. **Response Time**: 95th and 50th percentile latencies
4. **Error Rate**: 4xx and 5xx error percentages
5. **Webhook Processing**: Message processing metrics
6. **Database Connections**: Connection pool monitoring
7. **Memory Usage**: Application memory consumption
8. **CPU Usage**: Process CPU utilization
9. **Rate Limiting**: Rate limit enforcement stats
10. **Lead Scoring Performance**: Business metrics
11. **Cache Performance**: Cache hit rates and operations

## Production Deployment

### Environment Variables
```bash
# Enable metrics in production
PROMETHEUS_METRICS_ENABLED=true

# Configure retention
PROMETHEUS_RETENTION_DAYS=15

# Security settings
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

### Security Considerations
1. Change default Grafana admin password
2. Configure network security for monitoring ports
3. Enable HTTPS for external access
4. Set up proper authentication for Grafana

### Performance Impact
- Metrics collection adds ~1-2ms per request
- Memory overhead: ~50MB for metrics storage
- Network: ~100KB/minute metrics traffic

## Troubleshooting

### Common Issues
1. **Metrics not appearing**: Check if prometheus_client is installed
2. **Dashboard loading errors**: Verify Prometheus connectivity
3. **High cardinality warnings**: Review metric labels

### Debugging Commands
```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets

# Test alerting rules
curl http://localhost:9090/api/v1/rules
```

## Maintenance

### Regular Tasks
1. Monitor disk usage for metrics storage
2. Review and update alerting thresholds
3. Archive old metrics data
4. Update dashboard queries as needed

### Backup
```bash
# Backup Grafana data
docker exec whatsapp-grafana grafana-cli admin export-dashboard

# Backup Prometheus data
docker cp whatsapp-prometheus:/prometheus ./prometheus-backup
```

## Integration with Railway

For Railway deployment, the monitoring stack can be deployed as separate services:

1. **Prometheus Service**: Deploy with persistent storage
2. **Grafana Service**: Configure with Railway environment variables
3. **Application Service**: Enable metrics endpoint

See deployment documentation for specific Railway configuration.
