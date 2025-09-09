import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from app.utils.logger import get_logger
from app.database import AsyncSessionLocal
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    SYSTEM_ERROR = "system_error"
    API_ERROR = "api_error"
    PERFORMANCE = "performance"
    BUSINESS_METRIC = "business_metric"
    SECURITY = "security"

@dataclass
class Alert:
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    data: Dict = None
    resolved: bool = False

class AlertManager:
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_thresholds = {
            "api_error_rate": 0.05,  # 5%
            "response_time": 2.0,    # 2 segundos
            "failed_messages": 10,   # 10 mensagens falhadas em 5 min
            "db_connections": 0.8,   # 80% do pool
        }
    
    async def check_api_health(self):
        """Verificar saúde das APIs críticas"""
        try:
            # Simular verificação de saúde da API WhatsApp
            # Em produção, isso faria uma chamada real para a API
            health_check = await self._mock_whatsapp_health_check()
            
            if not health_check.get("healthy", False):
                await self.create_alert(
                    alert_id="whatsapp_api_down",
                    alert_type=AlertType.API_ERROR,
                    severity=AlertSeverity.CRITICAL,
                    title="WhatsApp API Indisponível",
                    message="A API do WhatsApp não está respondendo corretamente",
                    data=health_check
                )
            else:
                # Resolver alerta se existir
                await self.resolve_alert("whatsapp_api_down")
                
        except Exception as e:
            logger.error(f"Erro ao verificar saúde da API: {e}")
            await self.create_alert(
                alert_id="health_check_error",
                alert_type=AlertType.SYSTEM_ERROR,
                severity=AlertSeverity.HIGH,
                title="Erro no Health Check",
                message=f"Falha ao verificar saúde da API: {str(e)}",
                data={"error": str(e)}
            )
    
    async def _mock_whatsapp_health_check(self) -> Dict:
        """Mock para simulação de health check da API WhatsApp"""
        import random
        
        # Simular resposta da API (90% chance de sucesso)
        is_healthy = random.random() > 0.1
        
        return {
            "healthy": is_healthy,
            "response_time": random.uniform(0.1, 3.0),
            "status_code": 200 if is_healthy else random.choice([500, 502, 503]),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def check_message_failures(self):
        """Verificar taxa de falhas de mensagens"""
        try:
            async with AsyncSessionLocal() as session:
                # Buscar mensagens dos últimos 5 minutos
                five_min_ago = datetime.utcnow() - timedelta(minutes=5)
                
                # Query simplificada para verificar mensagens (adaptar conforme schema real)
                try:
                    # Simular contagem de mensagens para demonstração
                    stats = await self._mock_message_stats()
                    
                    if stats["sent"] > 0:
                        failure_rate = stats["failed"] / stats["sent"]
                        
                        if failure_rate > self.alert_thresholds["api_error_rate"]:
                            await self.create_alert(
                                alert_id="high_message_failure_rate",
                                alert_type=AlertType.BUSINESS_METRIC,
                                severity=AlertSeverity.HIGH,
                                title="Alta Taxa de Falhas de Mensagens",
                                message=f"Taxa de falhas: {failure_rate:.1%} nos últimos 5 minutos",
                                data={
                                    "failure_rate": failure_rate,
                                    "failed_count": stats["failed"],
                                    "total_sent": stats["sent"]
                                }
                            )
                        else:
                            await self.resolve_alert("high_message_failure_rate")
                            
                except Exception as e:
                    logger.warning(f"Tabela de mensagens não disponível, usando dados simulados: {e}")
                    # Usar dados simulados se a tabela não existir
                    await self._simulate_message_check()
                        
        except Exception as e:
            logger.error(f"Erro ao verificar falhas de mensagens: {e}")
    
    async def _mock_message_stats(self) -> Dict:
        """Mock para estatísticas de mensagens"""
        import random
        
        sent = random.randint(50, 200)
        failed = random.randint(0, int(sent * 0.15))  # Até 15% de falhas
        
        return {
            "sent": sent,
            "failed": failed,
            "total": sent + random.randint(0, 50)
        }
    
    async def _simulate_message_check(self):
        """Simulação de verificação de mensagens"""
        stats = await self._mock_message_stats()
        
        if stats["sent"] > 0:
            failure_rate = stats["failed"] / stats["sent"]
            
            if failure_rate > self.alert_thresholds["api_error_rate"]:
                await self.create_alert(
                    alert_id="high_message_failure_rate_sim",
                    alert_type=AlertType.BUSINESS_METRIC,
                    severity=AlertSeverity.MEDIUM,
                    title="Simulação: Alta Taxa de Falhas",
                    message=f"Taxa simulada de falhas: {failure_rate:.1%}",
                    data=stats
                )
    
    async def check_performance_metrics(self):
        """Verificar métricas de performance"""
        try:
            # Simular coleta de métricas de performance
            metrics = await self._mock_performance_metrics()
            
            # Verificar tempo de resposta médio
            avg_response_time = metrics.get("avg_response_time", 0)
            
            if avg_response_time > self.alert_thresholds["response_time"]:
                await self.create_alert(
                    alert_id="slow_response_time",
                    alert_type=AlertType.PERFORMANCE,
                    severity=AlertSeverity.MEDIUM,
                    title="Tempo de Resposta Elevado",
                    message=f"Tempo médio de resposta: {avg_response_time:.2f}s",
                    data={"avg_response_time": avg_response_time}
                )
            else:
                await self.resolve_alert("slow_response_time")
            
            # Verificar uso de CPU
            cpu_usage = metrics.get("cpu_usage", 0)
            if cpu_usage > 80:
                await self.create_alert(
                    alert_id="high_cpu_usage",
                    alert_type=AlertType.PERFORMANCE,
                    severity=AlertSeverity.HIGH,
                    title="Alto Uso de CPU",
                    message=f"Uso de CPU: {cpu_usage:.1f}%",
                    data={"cpu_usage": cpu_usage}
                )
            else:
                await self.resolve_alert("high_cpu_usage")
            
            # Verificar uso de memória
            memory_usage = metrics.get("memory_usage", 0)
            if memory_usage > 85:
                await self.create_alert(
                    alert_id="high_memory_usage",
                    alert_type=AlertType.PERFORMANCE,
                    severity=AlertSeverity.HIGH,
                    title="Alto Uso de Memória",
                    message=f"Uso de memória: {memory_usage:.1f}%",
                    data={"memory_usage": memory_usage}
                )
            else:
                await self.resolve_alert("high_memory_usage")
                
        except Exception as e:
            logger.error(f"Erro ao verificar métricas de performance: {e}")
    
    async def _mock_performance_metrics(self) -> Dict:
        """Mock para métricas de performance"""
        import random
        import psutil
        
        try:
            # Tentar obter métricas reais do sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Adicionar alguma variação aleatória
            return {
                "avg_response_time": random.uniform(0.5, 3.5),
                "cpu_usage": cpu_percent + random.uniform(-5, 5),
                "memory_usage": memory_percent + random.uniform(-5, 5),
                "disk_usage": psutil.disk_usage('/').percent,
                "active_connections": random.randint(10, 100)
            }
        except ImportError:
            # Se psutil não estiver disponível, usar valores simulados
            return {
                "avg_response_time": random.uniform(0.5, 3.5),
                "cpu_usage": random.uniform(20, 90),
                "memory_usage": random.uniform(30, 90),
                "disk_usage": random.uniform(40, 80),
                "active_connections": random.randint(10, 100)
            }
    
    async def check_database_health(self):
        """Verificar saúde do banco de dados"""
        try:
            async with AsyncSessionLocal() as session:
                # Teste simples de conectividade
                start_time = datetime.utcnow()
                await session.execute(select(1))
                end_time = datetime.utcnow()
                
                response_time = (end_time - start_time).total_seconds()
                
                if response_time > 1.0:  # Se demorar mais de 1 segundo
                    await self.create_alert(
                        alert_id="slow_database",
                        alert_type=AlertType.PERFORMANCE,
                        severity=AlertSeverity.MEDIUM,
                        title="Banco de Dados Lento",
                        message=f"Tempo de resposta do DB: {response_time:.2f}s",
                        data={"db_response_time": response_time}
                    )
                else:
                    await self.resolve_alert("slow_database")
                    
        except Exception as e:
            logger.error(f"Erro ao verificar saúde do banco: {e}")
            await self.create_alert(
                alert_id="database_connection_error",
                alert_type=AlertType.SYSTEM_ERROR,
                severity=AlertSeverity.CRITICAL,
                title="Erro de Conexão com Banco",
                message=f"Falha ao conectar com o banco de dados: {str(e)}",
                data={"error": str(e)}
            )
    
    async def create_alert(
        self, 
        alert_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        data: Dict = None
    ):
        """Criar novo alerta"""
        alert = Alert(
            id=alert_id,
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            data=data or {}
        )
        
        self.active_alerts[alert_id] = alert
        
        # Log baseado na severidade
        if severity == AlertSeverity.CRITICAL:
            logger.critical(f"🚨 CRITICAL ALERT: {title} - {message}")
        elif severity == AlertSeverity.HIGH:
            logger.error(f"🔴 HIGH ALERT: {title} - {message}")
        elif severity == AlertSeverity.MEDIUM:
            logger.warning(f"🟡 MEDIUM ALERT: {title} - {message}")
        else:
            logger.info(f"🔵 LOW ALERT: {title} - {message}")
        
        # Enviar notificações (implementar conforme necessário)
        await self._send_notifications(alert)
    
    async def resolve_alert(self, alert_id: str):
        """Resolver alerta"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            logger.info(f"✅ ALERT RESOLVED: {alert.title}")
            del self.active_alerts[alert_id]
    
    async def _send_notifications(self, alert: Alert):
        """Enviar notificações do alerta"""
        try:
            # Implementar notificações:
            # - Webhook para Slack/Discord
            # - Email para administradores
            # - Push notification no dashboard
            
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
                # Notificação imediata para alertas críticos
                await self._send_webhook_notification(alert)
                await self._log_alert_to_file(alert)
                
        except Exception as e:
            logger.error(f"Erro ao enviar notificações: {e}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """Enviar webhook para sistemas externos"""
        try:
            # Simular envio de webhook
            import aiohttp
            import json
            
            # URL do webhook (configurar via variável de ambiente)
            webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
            
            payload = {
                "text": f"🚨 {alert.title}",
                "attachments": [
                    {
                        "color": "danger" if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH] else "warning",
                        "fields": [
                            {
                                "title": "Severidade",
                                "value": alert.severity.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Tipo",
                                "value": alert.type.value.replace("_", " ").title(),
                                "short": True
                            },
                            {
                                "title": "Mensagem",
                                "value": alert.message,
                                "short": False
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            # Em produção, fazer a requisição HTTP real
            logger.info(f"📤 Webhook notification simulated for: {alert.title}")
            # async with aiohttp.ClientSession() as session:
            #     async with session.post(webhook_url, json=payload) as response:
            #         if response.status == 200:
            #             logger.info(f"Webhook enviado com sucesso para {alert.title}")
                        
        except Exception as e:
            logger.error(f"Erro ao enviar webhook: {e}")
    
    async def _log_alert_to_file(self, alert: Alert):
        """Salvar alerta em arquivo para auditoria"""
        try:
            import json
            import os
            
            log_dir = "logs/alerts"
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = f"{log_dir}/alerts_{datetime.utcnow().strftime('%Y%m%d')}.log"
            
            alert_data = {
                "id": alert.id,
                "type": alert.type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "data": alert.data
            }
            
            with open(log_file, "a") as f:
                f.write(json.dumps(alert_data) + "\n")
                
        except Exception as e:
            logger.error(f"Erro ao salvar alerta em arquivo: {e}")
    
    def get_active_alerts(self, severity: str = None) -> List[Alert]:
        """Obter alertas ativos"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity.value == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_summary(self) -> Dict:
        """Obter resumo dos alertas"""
        alerts = list(self.active_alerts.values())
        
        summary = {
            "total": len(alerts),
            "critical": len([a for a in alerts if a.severity == AlertSeverity.CRITICAL]),
            "high": len([a for a in alerts if a.severity == AlertSeverity.HIGH]),
            "medium": len([a for a in alerts if a.severity == AlertSeverity.MEDIUM]),
            "low": len([a for a in alerts if a.severity == AlertSeverity.LOW]),
            "by_type": {}
        }
        
        for alert_type in AlertType:
            summary["by_type"][alert_type.value] = len([
                a for a in alerts if a.type == alert_type
            ])
        
        return summary
    
    async def clear_resolved_alerts(self):
        """Limpar alertas que foram resolvidos há mais de 1 hora"""
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        resolved_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.resolved and alert.timestamp < cutoff_time
        ]
        
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]
            
        if resolved_alerts:
            logger.info(f"🧹 Limpou {len(resolved_alerts)} alertas resolvidos")

# Instância global
alert_manager = AlertManager()

# Task periódica de monitoramento
async def monitoring_task():
    """Task que roda periodicamente para verificar alertas"""
    logger.info("🔍 Iniciando sistema de monitoramento de alertas")
    
    while True:
        try:
            logger.debug("🔄 Executando ciclo de monitoramento...")
            
            # Executar todas as verificações
            await alert_manager.check_api_health()
            await alert_manager.check_message_failures()
            await alert_manager.check_performance_metrics()
            await alert_manager.check_database_health()
            
            # Limpar alertas antigos resolvidos
            await alert_manager.clear_resolved_alerts()
            
            # Log do status
            summary = alert_manager.get_alert_summary()
            if summary["total"] > 0:
                logger.info(f"📊 Alertas ativos: {summary['total']} "
                          f"(🚨{summary['critical']} 🔴{summary['high']} "
                          f"🟡{summary['medium']} 🔵{summary['low']})")
            
        except Exception as e:
            logger.error(f"Erro no monitoramento: {e}")
        
        # Aguardar 1 minuto antes da próxima verificação
        await asyncio.sleep(60)

# Função para iniciar o monitoramento
async def start_monitoring():
    """Iniciar o sistema de monitoramento"""
    try:
        await monitoring_task()
    except KeyboardInterrupt:
        logger.info("🛑 Sistema de monitoramento interrompido")
    except Exception as e:
        logger.error(f"❌ Erro fatal no sistema de monitoramento: {e}")

# Função para teste manual do sistema
async def test_alert_system():
    """Função para testar o sistema de alertas"""
    logger.info("🧪 Testando sistema de alertas...")
    
    # Criar alertas de teste
    await alert_manager.create_alert(
        alert_id="test_alert_1",
        alert_type=AlertType.SYSTEM_ERROR,
        severity=AlertSeverity.HIGH,
        title="Teste de Alerta",
        message="Este é um alerta de teste do sistema",
        data={"test": True}
    )
    
    await alert_manager.create_alert(
        alert_id="test_alert_2",
        alert_type=AlertType.PERFORMANCE,
        severity=AlertSeverity.MEDIUM,
        title="Teste de Performance",
        message="Alerta de teste para performance",
        data={"metric": "response_time", "value": 2.5}
    )
    
    # Mostrar resumo
    summary = alert_manager.get_alert_summary()
    logger.info(f"📋 Resumo dos alertas: {summary}")
    
    # Resolver um alerta
    await alert_manager.resolve_alert("test_alert_1")
    
    # Mostrar alertas ativos
    active_alerts = alert_manager.get_active_alerts()
    logger.info(f"📋 Alertas ativos: {len(active_alerts)}")
    
    for alert in active_alerts:
        logger.info(f"  - {alert.title} ({alert.severity.value})")

if __name__ == "__main__":
    # Executar teste se rodado diretamente
    asyncio.run(test_alert_system())
