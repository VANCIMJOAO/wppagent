#!/usr/bin/env python3
"""
🚨 SISTEMA DE ALERTAS EM TEMPO REAL
==================================

Configura e executa alertas de segurança em tempo real
"""

import os
import sys
import json
import time
import asyncio
import smtplib
import requests
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

sys.path.append('/home/vancim/whats_agent')

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('AlertSystem')

class RealTimeAlerts:
    """Sistema de alertas em tempo real"""
    
    def __init__(self):
        self.alerts_dir = Path("/home/vancim/whats_agent/logs/alerts")
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurações de notificação
        self.config = {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": os.getenv("ALERT_EMAIL_USER", "admin@whatsapp-agent.com"),
                "password": os.getenv("ALERT_EMAIL_PASS", ""),
                "to_email": os.getenv("ALERT_EMAIL_TO", "admin@whatsapp-agent.com")
            },
            "slack": {
                "enabled": True,
                "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
                "channel": "#security-alerts"
            },
            "whatsapp": {
                "enabled": False,  # Implementar se necessário
                "api_key": os.getenv("WHATSAPP_API_KEY", ""),
                "phone_number": os.getenv("ALERT_PHONE", "")
            },
            "file": {
                "enabled": True,
                "alerts_file": self.alerts_dir / "real_time_alerts.log"
            }
        }
        
        # Thresholds de alerta
        self.thresholds = {
            "cpu_critical": 95,
            "cpu_warning": 85,
            "memory_critical": 95,
            "memory_warning": 85,
            "disk_critical": 95,
            "disk_warning": 85,
            "failed_logins": 5,
            "response_time_critical": 5000,  # ms
            "response_time_warning": 2000,   # ms
            "error_rate_critical": 10,      # %
            "error_rate_warning": 5         # %
        }
        
        # Estado dos alertas (para evitar spam)
        self.alert_state = {}
        self.cooldown_period = 300  # 5 minutos
    
    async def monitor_system_continuously(self):
        """Monitorar sistema continuamente em tempo real"""
        logger.info("🚨 Iniciando monitoramento de alertas em tempo real")
        
        while True:
            try:
                # Verificar recursos do sistema
                await self._check_system_resources()
                
                # Verificar logs de aplicação
                await self._check_application_logs()
                
                # Verificar segurança
                await self._check_security_events()
                
                # Verificar serviços
                await self._check_services_health()
                
                # Aguardar antes do próximo ciclo
                await asyncio.sleep(60)  # Verificar a cada minuto
                
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                await asyncio.sleep(30)
    
    async def _check_system_resources(self):
        """Verificar recursos do sistema"""
        import psutil
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.thresholds["cpu_critical"]:
            await self._send_alert("CRITICAL", "high_cpu", {
                "message": f"CPU crítico: {cpu_percent}%",
                "value": cpu_percent,
                "threshold": self.thresholds["cpu_critical"]
            })
        elif cpu_percent > self.thresholds["cpu_warning"]:
            await self._send_alert("WARNING", "high_cpu", {
                "message": f"CPU alto: {cpu_percent}%",
                "value": cpu_percent,
                "threshold": self.thresholds["cpu_warning"]
            })
        
        # Memória
        memory = psutil.virtual_memory()
        if memory.percent > self.thresholds["memory_critical"]:
            await self._send_alert("CRITICAL", "high_memory", {
                "message": f"Memória crítica: {memory.percent}%",
                "value": memory.percent,
                "threshold": self.thresholds["memory_critical"],
                "available": f"{memory.available / 1024**3:.1f}GB"
            })
        elif memory.percent > self.thresholds["memory_warning"]:
            await self._send_alert("WARNING", "high_memory", {
                "message": f"Memória alta: {memory.percent}%",
                "value": memory.percent,
                "threshold": self.thresholds["memory_warning"]
            })
        
        # Disco
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > self.thresholds["disk_critical"]:
            await self._send_alert("CRITICAL", "high_disk", {
                "message": f"Disco crítico: {disk_percent:.1f}%",
                "value": disk_percent,
                "threshold": self.thresholds["disk_critical"],
                "free_space": f"{disk.free / 1024**3:.1f}GB"
            })
        elif disk_percent > self.thresholds["disk_warning"]:
            await self._send_alert("WARNING", "high_disk", {
                "message": f"Disco alto: {disk_percent:.1f}%",
                "value": disk_percent,
                "threshold": self.thresholds["disk_warning"]
            })
    
    async def _check_application_logs(self):
        """Verificar logs de aplicação por erros"""
        app_log = Path("/home/vancim/whats_agent/logs/app.log")
        error_log = Path("/home/vancim/whats_agent/logs/errors.log")
        
        # Verificar últimas entradas de erro
        for log_file in [app_log, error_log]:
            if log_file.exists():
                await self._scan_log_for_errors(log_file)
    
    async def _scan_log_for_errors(self, log_file: Path):
        """Escanear arquivo de log por erros recentes"""
        try:
            # Ler últimas 100 linhas
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]
            
            critical_errors = 0
            warning_errors = 0
            
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ['critical', 'fatal', 'emergency']):
                    critical_errors += 1
                elif any(keyword in line_lower for keyword in ['error', 'exception', 'traceback']):
                    warning_errors += 1
            
            if critical_errors > 0:
                await self._send_alert("CRITICAL", "application_errors", {
                    "message": f"{critical_errors} erros críticos encontrados em {log_file.name}",
                    "log_file": str(log_file),
                    "critical_count": critical_errors
                })
            elif warning_errors > 3:  # Mais de 3 erros em 100 linhas
                await self._send_alert("WARNING", "application_errors", {
                    "message": f"{warning_errors} erros encontrados em {log_file.name}",
                    "log_file": str(log_file),
                    "warning_count": warning_errors
                })
                
        except Exception as e:
            logger.error(f"Erro ao escanear log {log_file}: {e}")
    
    async def _check_security_events(self):
        """Verificar eventos de segurança"""
        security_log = Path("/home/vancim/whats_agent/logs/audit/security_audit.log")
        
        if security_log.exists():
            try:
                # Ler últimas 50 linhas
                with open(security_log, 'r') as f:
                    lines = f.readlines()[-50:]
                
                # Contar eventos críticos recentes
                recent_time = datetime.now(timezone.utc).timestamp() - 3600  # Última hora
                
                for line in lines:
                    try:
                        if line.strip() and line.startswith('{'):
                            event = json.loads(line)
                            event_time = datetime.fromisoformat(event.get('timestamp', '')).timestamp()
                            
                            if event_time > recent_time and event.get('severity') == 'CRITICAL':
                                await self._send_alert("CRITICAL", "security_event", {
                                    "message": f"Evento de segurança crítico: {event.get('event_type')}",
                                    "event_details": event.get('details', {}),
                                    "timestamp": event.get('timestamp')
                                })
                    except (json.JSONDecodeError, ValueError):
                        continue
                        
            except Exception as e:
                logger.error(f"Erro ao verificar eventos de segurança: {e}")
    
    async def _check_services_health(self):
        """Verificar saúde dos serviços"""
        services_to_check = [
            {"name": "PostgreSQL", "host": "localhost", "port": 5432},
            {"name": "Redis", "host": "localhost", "port": 6379},
            {"name": "WhatsApp Agent API", "url": "http://localhost:8000/health"}
        ]
        
        for service in services_to_check:
            if "url" in service:
                # Verificar via HTTP
                try:
                    import httpx
                    async with httpx.AsyncClient(timeout=10) as client:
                        response = await client.get(service["url"])
                        if response.status_code != 200:
                            await self._send_alert("WARNING", "service_down", {
                                "message": f"Serviço {service['name']} com problemas",
                                "status_code": response.status_code,
                                "url": service["url"]
                            })
                except Exception as e:
                    await self._send_alert("CRITICAL", "service_down", {
                        "message": f"Serviço {service['name']} inacessível",
                        "error": str(e),
                        "url": service["url"]
                    })
            else:
                # Verificar via socket
                import socket
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((service["host"], service["port"]))
                    sock.close()
                    
                    if result != 0:
                        await self._send_alert("CRITICAL", "service_down", {
                            "message": f"Serviço {service['name']} inacessível",
                            "host": service["host"],
                            "port": service["port"]
                        })
                except Exception as e:
                    await self._send_alert("CRITICAL", "service_down", {
                        "message": f"Erro ao verificar {service['name']}",
                        "error": str(e)
                    })
    
    async def _send_alert(self, severity: str, alert_type: str, details: dict):
        """Enviar alerta através de múltiplos canais"""
        # Verificar cooldown
        alert_key = f"{alert_type}_{severity}"
        current_time = time.time()
        
        if alert_key in self.alert_state:
            if current_time - self.alert_state[alert_key] < self.cooldown_period:
                return  # Em cooldown, não enviar
        
        self.alert_state[alert_key] = current_time
        
        # Criar objeto do alerta
        alert = {
            "id": f"alert_{int(current_time)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "type": alert_type,
            "details": details,
            "hostname": os.uname().nodename
        }
        
        # Log do alerta
        logger.warning(f"🚨 ALERTA {severity}: {details.get('message', 'Alerta sem mensagem')}")
        
        # Enviar através de diferentes canais
        await self._send_to_file(alert)
        await self._send_to_email(alert)
        await self._send_to_slack(alert)
        # await self._send_to_whatsapp(alert)  # Implementar se necessário
    
    async def _send_to_file(self, alert: dict):
        """Salvar alerta em arquivo"""
        if not self.config["file"]["enabled"]:
            return
        
        try:
            alerts_file = self.config["file"]["alerts_file"]
            with open(alerts_file, 'a') as f:
                f.write(json.dumps(alert) + '\n')
        except Exception as e:
            logger.error(f"Erro ao salvar alerta em arquivo: {e}")
    
    async def _send_to_email(self, alert: dict):
        """Enviar alerta por email"""
        if not self.config["email"]["enabled"] or not self.config["email"]["password"]:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["email"]["username"]
            msg['To'] = self.config["email"]["to_email"]
            msg['Subject'] = f"🚨 ALERTA {alert['severity']} - WhatsApp Agent"
            
            # Corpo do email
            body = f"""
ALERTA DE SEGURANÇA - WHATSAPP AGENT
====================================

Severidade: {alert['severity']}
Tipo: {alert['type']}
Timestamp: {alert['timestamp']}
Hostname: {alert['hostname']}

Detalhes:
{json.dumps(alert['details'], indent=2)}

---
Este é um alerta automático do sistema de monitoramento.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Enviar email
            server = smtplib.SMTP(self.config["email"]["smtp_server"], self.config["email"]["smtp_port"])
            server.starttls()
            server.login(self.config["email"]["username"], self.config["email"]["password"])
            text = msg.as_string()
            server.sendmail(self.config["email"]["username"], self.config["email"]["to_email"], text)
            server.quit()
            
            logger.info(f"📧 Alerta enviado por email para {self.config['email']['to_email']}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
    
    async def _send_to_slack(self, alert: dict):
        """Enviar alerta para Slack"""
        if not self.config["slack"]["enabled"] or not self.config["slack"]["webhook_url"]:
            return
        
        try:
            # Cores baseadas na severidade
            color_map = {
                "CRITICAL": "#FF0000",
                "WARNING": "#FFA500",
                "INFO": "#00FF00"
            }
            
            # Emoji baseado na severidade
            emoji_map = {
                "CRITICAL": "🔴",
                "WARNING": "🟡",
                "INFO": "🟢"
            }
            
            slack_message = {
                "username": "WhatsApp Agent Monitor",
                "channel": self.config["slack"]["channel"],
                "attachments": [
                    {
                        "color": color_map.get(alert["severity"], "#808080"),
                        "title": f"{emoji_map.get(alert['severity'], '⚪')} ALERTA {alert['severity']}",
                        "text": alert["details"].get("message", "Alerta sem mensagem"),
                        "fields": [
                            {
                                "title": "Tipo",
                                "value": alert["type"],
                                "short": True
                            },
                            {
                                "title": "Hostname",
                                "value": alert["hostname"],
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert["timestamp"],
                                "short": False
                            }
                        ],
                        "footer": "WhatsApp Agent Monitoring System",
                        "ts": int(time.time())
                    }
                ]
            }
            
            response = requests.post(
                self.config["slack"]["webhook_url"],
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("📱 Alerta enviado para Slack")
            else:
                logger.error(f"Erro ao enviar para Slack: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erro ao enviar para Slack: {e}")

async def main():
    """Função principal"""
    print("🚨 SISTEMA DE ALERTAS EM TEMPO REAL")
    print("=" * 50)
    
    # Criar diretórios necessários
    os.makedirs("/home/vancim/whats_agent/logs/alerts", exist_ok=True)
    
    # Inicializar sistema de alertas
    alert_system = RealTimeAlerts()
    
    print("📋 Configurações de alerta:")
    print(f"   📧 Email: {'✅ Habilitado' if alert_system.config['email']['enabled'] else '❌ Desabilitado'}")
    print(f"   📱 Slack: {'✅ Habilitado' if alert_system.config['slack']['enabled'] else '❌ Desabilitado'}")
    print(f"   📁 Arquivo: {'✅ Habilitado' if alert_system.config['file']['enabled'] else '❌ Desabilitado'}")
    
    print("\n🔧 Thresholds configurados:")
    for key, value in alert_system.thresholds.items():
        print(f"   {key}: {value}")
    
    print("\n🚨 Iniciando monitoramento em tempo real...")
    print("   (Pressione Ctrl+C para parar)")
    
    try:
        # Testar envio de alerta
        await alert_system._send_alert("INFO", "system_start", {
            "message": "Sistema de alertas iniciado com sucesso",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Iniciar monitoramento contínuo
        await alert_system.monitor_system_continuously()
        
    except KeyboardInterrupt:
        print("\n🛑 Parando sistema de alertas...")
        
        # Enviar alerta de parada
        await alert_system._send_alert("INFO", "system_stop", {
            "message": "Sistema de alertas parado pelo usuário",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return 0
    except Exception as e:
        logger.error(f"Erro no sistema de alertas: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
