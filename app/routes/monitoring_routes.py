"""
Rotas de Monitoramento e Dashboard
=================================

Endpoints para visualizar métricas, SLA e alertas do sistema.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, Dict, Any, List
import json
from datetime import datetime, timedelta

from app.services.comprehensive_monitoring import (
    monitoring_system, 
    get_monitoring_dashboard,
    SLAMetric,
    BusinessMetric,
    AlertSeverity
)
from app.utils.logger import get_logger
from app.config.config_factory import ConfigFactory

logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/dashboard", response_class=JSONResponse)
async def get_dashboard_data(
    period_minutes: int = Query(default=60, ge=5, le=10080, description="Período em minutos"),
    include_details: bool = Query(default=False, description="Incluir detalhes completos")
):
    """
    Obter dados do dashboard de monitoramento
    """
    try:
        config = ConfigFactory.get_singleton_config()
        
        if not config.metrics_enabled:
            raise HTTPException(
                status_code=503,
                detail="Monitoramento não está habilitado"
            )
        
        # Obter dados do dashboard
        dashboard_data = get_monitoring_dashboard()
        
        # Obter status do SLA para o período especificado
        sla_status = monitoring_system.sla_monitor.get_sla_status(period_minutes)
        
        # Obter métricas de negócio
        business_summary = monitoring_system.business_metrics.get_business_summary(
            days=max(1, period_minutes // 1440)  # Converter minutos para dias
        )
        
        response_data = {
            "dashboard": dashboard_data,
            "sla_status": sla_status,
            "business_summary": business_summary,
            "period_minutes": period_minutes,
            "timestamp": datetime.now().isoformat()
        }
        
        if include_details:
            response_data["system_details"] = {
                "config": {
                    "environment": config.environment.value,
                    "metrics_enabled": config.metrics_enabled,
                    "alerting_enabled": config.alerting_enabled,
                    "prometheus_enabled": config.prometheus_enabled,
                    "sla_thresholds": {
                        "response_time_ms": config.sla_response_time_ms,
                        "uptime_percentage": config.sla_uptime_percentage,
                        "error_rate_percentage": config.sla_error_rate_percentage
                    }
                },
                "buffer_sizes": {
                    "sla_metrics": {
                        metric.value: len(monitoring_system.sla_monitor.metrics_buffer.get(metric, []))
                        for metric in SLAMetric
                    },
                    "business_metrics": {
                        metric.value: len(monitoring_system.business_metrics.metrics_buffer.get(metric, []))
                        for metric in BusinessMetric
                    }
                }
            }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Erro ao obter dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/dashboard/html", response_class=HTMLResponse)
async def get_dashboard_html():
    """
    Dashboard HTML simples para visualização
    """
    try:
        dashboard_data = get_monitoring_dashboard()
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WhatsApp Agent - Dashboard de Monitoramento</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5; 
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                }}
                .header {{ 
                    text-align: center; 
                    margin-bottom: 30px; 
                    padding-bottom: 20px; 
                    border-bottom: 2px solid #e0e0e0; 
                }}
                .metrics-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; 
                    margin-bottom: 30px; 
                }}
                .metric-card {{ 
                    background: #f8f9fa; 
                    padding: 20px; 
                    border-radius: 8px; 
                    border-left: 4px solid #007bff; 
                }}
                .metric-title {{ 
                    font-weight: bold; 
                    color: #333; 
                    margin-bottom: 10px; 
                }}
                .metric-value {{ 
                    font-size: 24px; 
                    font-weight: bold; 
                    color: #007bff; 
                }}
                .metric-unit {{ 
                    font-size: 14px; 
                    color: #666; 
                }}
                .status-healthy {{ 
                    color: #28a745; 
                }}
                .status-warning {{ 
                    color: #ffc107; 
                }}
                .status-critical {{ 
                    color: #dc3545; 
                }}
                .alerts-section {{ 
                    margin-top: 30px; 
                }}
                .alert-item {{ 
                    background: #fff3cd; 
                    border: 1px solid #ffeaa7; 
                    padding: 15px; 
                    border-radius: 4px; 
                    margin-bottom: 10px; 
                }}
                .alert-critical {{ 
                    background: #f8d7da; 
                    border-color: #f5c6cb; 
                }}
                .alert-high {{ 
                    background: #fff3cd; 
                    border-color: #ffeaa7; 
                }}
                .footer {{ 
                    text-align: center; 
                    margin-top: 30px; 
                    padding-top: 20px; 
                    border-top: 1px solid #e0e0e0; 
                    color: #666; 
                }}
                .refresh-btn {{ 
                    background: #007bff; 
                    color: white; 
                    border: none; 
                    padding: 10px 20px; 
                    border-radius: 4px; 
                    cursor: pointer; 
                    margin: 10px; 
                }}
                .system-info {{ 
                    background: #e9ecef; 
                    padding: 15px; 
                    border-radius: 4px; 
                    margin-bottom: 20px; 
                }}
                pre {{ 
                    background: #f8f9fa; 
                    padding: 15px; 
                    border-radius: 4px; 
                    overflow-x: auto; 
                    font-size: 12px; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 WhatsApp Agent - Dashboard de Monitoramento</h1>
                    <p>Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <button class="refresh-btn" onclick="location.reload()">🔄 Atualizar</button>
                </div>
                
                <!-- Informações do Sistema -->
                <div class="system-info">
                    <h3>ℹ️ Informações do Sistema</h3>
                    <p><strong>Ambiente:</strong> {dashboard_data['system_info']['config']['environment']}</p>
                    <p><strong>Monitoramento:</strong> {'✅ Habilitado' if dashboard_data['system_info']['monitoring_enabled'] else '❌ Desabilitado'}</p>
                    <p><strong>Alertas:</strong> {'✅ Habilitado' if dashboard_data['system_info']['alerting_enabled'] else '❌ Desabilitado'}</p>
                    <p><strong>Uptime (24h):</strong> {dashboard_data['system_info']['uptime_percentage']:.2f}%</p>
                </div>
                
                <!-- Métricas de SLA -->
                <h2>📊 Status do SLA</h2>
                <div class="metrics-grid">
        """
        
        # Adicionar métricas de SLA
        sla_status = dashboard_data.get('sla_status', {}).get('metrics', {})
        for metric_name, metric_data in sla_status.items():
            if metric_data.get('current_value') is not None:
                is_healthy = metric_data.get('is_healthy', True)
                status_class = 'status-healthy' if is_healthy else 'status-critical'
                
                html_content += f"""
                    <div class="metric-card">
                        <div class="metric-title">{metric_name.replace('_', ' ').title()}</div>
                        <div class="metric-value {status_class}">
                            {metric_data['current_value']:.2f}
                            <span class="metric-unit">{metric_data['unit']}</span>
                        </div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">
                            Threshold: {metric_data['warning_threshold']:.2f}{metric_data['unit']} 
                            {'✅' if is_healthy else '⚠️'}
                        </div>
                    </div>
                """
        
        # Adicionar métricas de negócio
        html_content += """
                </div>
                
                <h2>💼 Métricas de Negócio</h2>
                <div class="metrics-grid">
        """
        
        business_metrics = dashboard_data.get('business_metrics', {}).get('metrics', {})
        for metric_name, metric_data in business_metrics.items():
            current_period = metric_data.get('current_period', {})
            trends = metric_data.get('trends', {})
            
            if current_period.get('total') is not None:
                trend_icon = '📈' if trends.get('direction') == 'up' else '📉' if trends.get('direction') == 'down' else '➡️'
                
                html_content += f"""
                    <div class="metric-card">
                        <div class="metric-title">{metric_name.replace('_', ' ').title()}</div>
                        <div class="metric-value">
                            {current_period['total']:.0f}
                        </div>
                        <div style="font-size: 12px; color: #666; margin-top: 5px;">
                            Média: {current_period['average']:.2f} | Tendência: {trend_icon} {trends.get('percentage', 0):.1f}%
                        </div>
                    </div>
                """
        
        # Adicionar alertas ativos
        html_content += """
                </div>
                
                <div class="alerts-section">
                    <h2>🚨 Alertas Ativos</h2>
        """
        
        active_alerts = dashboard_data.get('active_alerts', [])
        if active_alerts:
            for alert in active_alerts:
                alert_class = f"alert-{alert['severity']}"
                html_content += f"""
                    <div class="alert-item {alert_class}">
                        <strong>{alert['title']}</strong><br>
                        {alert['description']}<br>
                        <small>Severity: {alert['severity'].upper()} | Metric: {alert['metric']}</small>
                    </div>
                """
        else:
            html_content += '<p style="color: #28a745;">✅ Nenhum alerta ativo</p>'
        
        # Adicionar dados JSON para debug
        html_content += f"""
                </div>
                
                <details style="margin-top: 30px;">
                    <summary>🔧 Dados Brutos (JSON)</summary>
                    <pre>{json.dumps(dashboard_data, indent=2, ensure_ascii=False)}</pre>
                </details>
                
                <div class="footer">
                    <p>WhatsApp Agent Monitoring System | Atualização automática a cada 30 segundos</p>
                </div>
            </div>
            
            <script>
                // Auto-refresh a cada 30 segundos
                setTimeout(function() {{
                    location.reload();
                }}, 30000);
            </script>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard HTML: {e}")
        return f"""
        <html>
        <body>
            <h1>Erro no Dashboard</h1>
            <p>Erro ao carregar dados de monitoramento: {str(e)}</p>
            <a href="/monitoring/dashboard/html">Tentar novamente</a>
        </body>
        </html>
        """


@router.get("/alerts")
async def get_alerts(
    active_only: bool = Query(default=True, description="Apenas alertas ativos"),
    severity: Optional[str] = Query(default=None, description="Filtrar por severidade")
):
    """
    Obter lista de alertas
    """
    try:
        if active_only:
            alerts = list(monitoring_system.sla_monitor.active_alerts.values())
        else:
            alerts = monitoring_system.sla_monitor.alert_history
        
        # Filtrar por severidade se especificado
        if severity:
            try:
                severity_enum = AlertSeverity(severity.lower())
                alerts = [alert for alert in alerts if alert.severity == severity_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Severidade inválida: {severity}")
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts),
            "active_only": active_only,
            "severity_filter": severity
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/sla")
async def get_sla_metrics(period_minutes: int = Query(default=60, ge=5, le=10080)):
    """
    Obter métricas de SLA detalhadas
    """
    try:
        sla_status = monitoring_system.sla_monitor.get_sla_status(period_minutes)
        
        return {
            "sla_metrics": sla_status,
            "thresholds": {
                metric.value: {
                    "warning": threshold.warning_threshold,
                    "critical": threshold.critical_threshold,
                    "unit": threshold.unit,
                    "description": threshold.description
                }
                for metric, threshold in monitoring_system.sla_monitor.thresholds.items()
            },
            "period_minutes": period_minutes
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas de SLA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/business")
async def get_business_metrics(days: int = Query(default=7, ge=1, le=90)):
    """
    Obter métricas de negócio detalhadas
    """
    try:
        business_summary = monitoring_system.business_metrics.get_business_summary(days)
        
        return {
            "business_metrics": business_summary,
            "available_metrics": [metric.value for metric in BusinessMetric],
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas de negócio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/simulate-load")
async def simulate_load(
    requests: int = Query(default=10, ge=1, le=100),
    response_time_range: tuple = Query(default=(100, 3000), description="Range de tempo de resposta em ms")
):
    """
    Simular carga para testar o sistema de monitoramento
    """
    try:
        import random
        
        results = []
        
        for i in range(requests):
            # Simular diferentes endpoints
            endpoints = ['/webhook', '/conversations', '/bookings', '/health', '/api/test']
            endpoint = random.choice(endpoints)
            
            # Simular diferentes métodos
            method = random.choice(['GET', 'POST', 'PUT'])
            
            # Simular tempo de resposta
            response_time = random.uniform(response_time_range[0], response_time_range[1])
            
            # Simular status code (90% sucesso)
            status_code = 200 if random.random() < 0.9 else random.choice([400, 500, 503])
            
            # Registrar métrica
            await monitoring_system.record_api_call(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time,
                user_id=f"test_user_{i}"
            )
            
            results.append({
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'response_time_ms': round(response_time, 2)
            })
        
        return {
            "message": f"Simulação concluída: {requests} requisições",
            "results": results,
            "summary": {
                "total_requests": len(results),
                "avg_response_time": round(sum(r['response_time_ms'] for r in results) / len(results), 2),
                "success_rate": len([r for r in results if r['status_code'] < 400]) / len(results) * 100
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na simulação de carga: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def monitoring_health():
    """
    Health check do sistema de monitoramento
    """
    try:
        config = ConfigFactory.get_singleton_config()
        
        return {
            "status": "healthy",
            "monitoring_enabled": config.metrics_enabled,
            "alerting_enabled": config.alerting_enabled,
            "business_metrics_enabled": config.business_metrics_enabled,
            "active_alerts": len(monitoring_system.sla_monitor.active_alerts),
            "uptime_percentage": monitoring_system.sla_monitor.uptime_tracker.get_uptime_percentage(60),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro no health check de monitoramento: {e}")
        raise HTTPException(status_code=500, detail=str(e))
