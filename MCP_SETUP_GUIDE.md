# 🔧 MCPs Configuration for WhatsApp Agent

## Installed MCPs and their purposes:

### Essential MCPs (Phase 1)
- **GitHub MCP**: Version control, CI/CD, issues management
- **Postgres MCP**: Database queries, performance analysis, migrations
- **Docker MCP**: Container management, debugging, optimization

### Development MCPs (Phase 2)  
- **Testing MCP**: Automated testing, coverage reports
- **Time MCP**: Scheduling, timezone handling, cron jobs
- **Memory MCP**: Context persistence, knowledge base

### Production MCPs (Phase 3)
- **Kubernetes MCP**: Scaling, orchestration, cluster management
- **AWS/GCP MCP**: Cloud infrastructure, storage, CDN
- **Slack MCP**: Notifications, alerts, communication

### Integration MCPs (Phase 4)
- **API/HTTP MCP**: External API testing, monitoring, load testing

## Configuration Files

### GitHub MCP
```json
{
  "github": {
    "repository": "vancim/whats_agent",
    "token": "ghp_your_token_here",
    "default_branch": "main",
    "workflows": {
      "ci_cd": ".github/workflows/ci-cd.yml",
      "deploy": "railway"
    }
  }
}
```

### Postgres MCP
```json
{
  "postgres": {
    "host": "localhost",
    "port": 5432,
    "database": "whatsapp_agent", 
    "user": "vancimj",
    "password": "your_secure_password",
    "ssl": true,
    "pool_size": 20
  }
}
```

### Docker MCP
```json
{
  "docker": {
    "socket": "/var/run/docker.sock",
    "compose_file": "/home/vancim/whats_agent/docker-compose.yml",
    "containers": [
      "whatsapp_app",
      "whatsapp_postgres", 
      "whatsapp_redis",
      "whatsapp_nginx",
      "whatsapp_grafana",
      "whatsapp_prometheus"
    ]
  }
}
```

## Common Commands

### GitHub Operations
- `Claude, commit changes and push to main`
- `Claude, create PR for feature branch`
- `Claude, check CI/CD status`
- `Claude, create release tag v2.1.0`

### Database Operations
- `Claude, show slow queries from last hour`
- `Claude, analyze table sizes and suggest optimizations`
- `Claude, run migration and verify schema`
- `Claude, backup database to backups/`

### Docker Operations  
- `Claude, restart whatsapp_app container`
- `Claude, check container resource usage`
- `Claude, update docker-compose and rebuild`
- `Claude, check all container health status`

### Testing Operations
- `Claude, run full test suite with coverage`
- `Claude, generate tests for new WhatsApp features`
- `Claude, run security validation tests`
- `Claude, performance test the API endpoints`

### Monitoring & Alerts
- `Claude, check Grafana dashboards for anomalies`
- `Claude, analyze Prometheus metrics for last 24h`
- `Claude, send status report to Slack`
- `Claude, check Railway deployment status`

## Integration with Existing Tools

### Railway Integration
- MCPs will work alongside your Railway deployment
- GitHub MCP can trigger Railway deploys via webhooks
- Monitor Railway services through custom metrics

### Grafana/Prometheus Integration
- MCPs can query Prometheus for metrics
- Generate custom dashboards based on MCP data
- Alert integration via Slack MCP

### WhatsApp Agent Integration
- Time MCP for scheduling WhatsApp messages
- Memory MCP for conversation context
- API MCP for testing Meta/WhatsApp APIs

## Security Considerations

### Credentials Management
- Store tokens in environment variables
- Use Railway secrets for production
- Rotate credentials regularly

### Access Control
- Limit MCP permissions to project scope
- Use read-only access where possible
- Audit MCP actions through logs

## Troubleshooting

### Common Issues
1. **GitHub MCP not connecting**: Check token permissions
2. **Postgres MCP timeout**: Verify connection string and firewall
3. **Docker MCP permission denied**: Add user to docker group
4. **Memory MCP data loss**: Check persistent storage configuration

### Debug Commands
- `Claude, check MCP connection status`
- `Claude, validate all configurations`
- `Claude, show recent MCP error logs`
- `Claude, test database connectivity`

## Performance Optimization

### Best Practices
- Use connection pooling for database MCPs
- Cache frequently accessed data in Memory MCP
- Batch operations when possible
- Monitor MCP resource usage

### Scaling Considerations
- Kubernetes MCP for horizontal scaling
- Cloud MCPs for infrastructure scaling
- Load balancing through API MCP
- Auto-scaling based on metrics

---

**Note**: Remember to configure each MCP with appropriate credentials and permissions before first use. Test in development environment before applying to production.
