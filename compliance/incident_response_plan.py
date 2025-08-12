#!/usr/bin/env python3
"""
✅ PLANO DE RESPOSTA A INCIDENTES - WHATSAPP AGENT
==================================================

Sistema completo de resposta a incidentes de segurança
- Classificação automática de incidentes
- Workflows de resposta estruturados
- Escalação automática baseada em severidade
- Comunicação coordenada com stakeholders
- Documentação automática de incidentes
- Post-mortem e lições aprendidas
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import smtplib
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Fallback para versões mais recentes do Python
    from email.message import EmailMessage
    MimeText = None
    MimeMultipart = None
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('IncidentResponse')

class IncidentSeverity(Enum):
    """Severidades de incidentes conforme criticidade"""
    SEV_1 = "sev_1"  # Crítico - Sistema completamente indisponível
    SEV_2 = "sev_2"  # Alto - Funcionalidade principal comprometida
    SEV_3 = "sev_3"  # Médio - Funcionalidade secundária afetada
    SEV_4 = "sev_4"  # Baixo - Problema menor sem impacto operacional

class IncidentType(Enum):
    """Tipos de incidentes de segurança"""
    SECURITY_BREACH = "security_breach"           # Violação de segurança
    DATA_LOSS = "data_loss"                      # Perda de dados
    SYSTEM_COMPROMISE = "system_compromise"       # Comprometimento do sistema
    DDOS_ATTACK = "ddos_attack"                  # Ataque DDoS
    MALWARE_INFECTION = "malware_infection"       # Infecção por malware
    UNAUTHORIZED_ACCESS = "unauthorized_access"   # Acesso não autorizado
    COMPLIANCE_VIOLATION = "compliance_violation" # Violação de compliance
    SYSTEM_OUTAGE = "system_outage"              # Indisponibilidade do sistema
    PERFORMANCE_DEGRADATION = "performance_degradation" # Degradação de performance
    CONFIGURATION_ERROR = "configuration_error"  # Erro de configuração

class IncidentStatus(Enum):
    """Status do incidente"""
    NEW = "new"                    # Novo incidente
    ACKNOWLEDGED = "acknowledged"   # Reconhecido pela equipe
    INVESTIGATING = "investigating" # Em investigação
    CONTAINING = "containing"      # Contenção em andamento
    RESOLVING = "resolving"        # Resolução em andamento
    MONITORING = "monitoring"      # Monitoramento pós-resolução
    RESOLVED = "resolved"          # Resolvido
    CLOSED = "closed"             # Fechado com post-mortem

class EscalationLevel(Enum):
    """Níveis de escalação"""
    L1_OPERATIONS = "l1_operations"     # Nível 1 - Operações
    L2_SECURITY = "l2_security"         # Nível 2 - Segurança
    L3_MANAGEMENT = "l3_management"     # Nível 3 - Gerência
    L4_EXECUTIVE = "l4_executive"       # Nível 4 - Executivo

@dataclass
class IncidentContact:
    """Contato para resposta a incidentes"""
    name: str
    role: str
    email: str
    phone: str
    escalation_level: EscalationLevel
    available_24x7: bool = False
    backup_contact: Optional[str] = None

@dataclass
class IncidentResponse:
    """Plano de resposta por tipo de incidente"""
    incident_type: IncidentType
    severity: IncidentSeverity
    response_time_sla: int  # minutos
    initial_actions: List[str]
    containment_actions: List[str]
    investigation_steps: List[str]
    recovery_actions: List[str]
    communication_template: str
    escalation_triggers: List[str]
    evidence_preservation: List[str]

@dataclass
class Incident:
    """Incidente de segurança"""
    incident_id: str
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    reported_by: str
    reported_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    assigned_to: str = ""
    escalation_level: EscalationLevel = EscalationLevel.L1_OPERATIONS
    affected_systems: List[str] = None
    impact_assessment: str = ""
    root_cause: str = ""
    timeline: List[Dict[str, Any]] = None
    actions_taken: List[str] = None
    lessons_learned: List[str] = None
    preventive_measures: List[str] = None
    estimated_impact: Dict[str, Any] = None

class IncidentResponseManager:
    """Gerenciador de resposta a incidentes"""
    
    def __init__(self):
        self.base_path = "/home/vancim/whats_agent"
        self.incidents_path = f"{self.base_path}/compliance/incident-response"
        self.reports_path = f"{self.base_path}/compliance/reports"
        self.logs_path = f"{self.base_path}/logs/incidents"
        
        # Criar diretórios necessários
        os.makedirs(self.incidents_path, exist_ok=True)
        os.makedirs(self.reports_path, exist_ok=True)
        os.makedirs(self.logs_path, exist_ok=True)
        os.makedirs(f"{self.incidents_path}/active", exist_ok=True)
        os.makedirs(f"{self.incidents_path}/resolved", exist_ok=True)
        os.makedirs(f"{self.incidents_path}/templates", exist_ok=True)
        
        # Inicializar configurações
        self.contacts = self._initialize_contacts()
        self.response_plans = self._initialize_response_plans()
        self.active_incidents: Dict[str, Incident] = {}
        
        # Configurações de notificação
        self.email_config = self._load_email_config()
        self.slack_webhook = os.getenv("INCIDENT_SLACK_WEBHOOK", "")
    
    def _load_email_config(self) -> Dict[str, str]:
        """Carrega configuração de email para notificações"""
        return {
            "smtp_server": os.getenv("INCIDENT_SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": os.getenv("INCIDENT_SMTP_PORT", "587"),
            "username": os.getenv("INCIDENT_EMAIL_USER", "incidents@company.com"),
            "password": os.getenv("INCIDENT_EMAIL_PASS", ""),
            "from_name": "WhatsApp Agent - Incident Response"
        }
    
    def _initialize_contacts(self) -> List[IncidentContact]:
        """Inicializa lista de contatos para resposta a incidentes"""
        return [
            IncidentContact(
                name="Operations Team",
                role="L1 Operations Engineer",
                email="ops@company.com",
                phone="+55 11 99999-0001",
                escalation_level=EscalationLevel.L1_OPERATIONS,
                available_24x7=True
            ),
            
            IncidentContact(
                name="Security Team",
                role="L2 Security Analyst",
                email="security@company.com",
                phone="+55 11 99999-0002",
                escalation_level=EscalationLevel.L2_SECURITY,
                available_24x7=True,
                backup_contact="security-backup@company.com"
            )
        ]
    
    def _initialize_response_plans(self) -> Dict[IncidentType, Dict[IncidentSeverity, IncidentResponse]]:
        """Inicializa planos de resposta por tipo e severidade"""
        plans = {}
        
        # Plano para Ataque DDoS
        plans[IncidentType.DDOS_ATTACK] = {
            IncidentSeverity.SEV_2: IncidentResponse(
                incident_type=IncidentType.DDOS_ATTACK,
                severity=IncidentSeverity.SEV_2,
                response_time_sla=15,
                initial_actions=[
                    "Confirmar natureza do ataque",
                    "Ativar mitigacao DDoS",
                    "Notificar Operations Team"
                ],
                containment_actions=[
                    "Implementar rate limiting agressivo",
                    "Ativar filtros de trafego"
                ],
                investigation_steps=[
                    "Analisar logs de firewall",
                    "Identificar padroes de ataque"
                ],
                recovery_actions=[
                    "Ajustar thresholds de protecao",
                    "Validar funcionamento normal"
                ],
                communication_template="ddos_attack_sev2",
                escalation_triggers=[
                    "Ataque persistente > 2 horas"
                ],
                evidence_preservation=[
                    "Capturar amostras de trafego malicioso"
                ]
            )
        }
        
        return plans
    
    def classify_incident(self, description: str, reported_by: str, 
                         initial_severity: IncidentSeverity = None) -> Incident:
        """Classifica automaticamente um incidente baseado na descrição"""
        
        # Keywords para classificação automática
        type_keywords = {
            IncidentType.DDOS_ATTACK: ["ddos", "flooding", "overwhelmed", "traffic spike", "dos"],
            IncidentType.SYSTEM_OUTAGE: ["down", "offline", "unavailable", "outage", "crashed"]
        }
        
        severity_keywords = {
            IncidentSeverity.SEV_1: ["critical", "emergency", "total", "complete"],
            IncidentSeverity.SEV_2: ["major", "significant", "important"],
            IncidentSeverity.SEV_3: ["moderate", "partial", "some users"],
            IncidentSeverity.SEV_4: ["low", "minimal", "cosmetic"]
        }
        
        description_lower = description.lower()
        
        # Classificar tipo
        incident_type = IncidentType.SYSTEM_OUTAGE  # Default
        for itype, keywords in type_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                incident_type = itype
                break
        
        # Classificar severidade
        if initial_severity:
            severity = initial_severity
        else:
            severity = IncidentSeverity.SEV_3  # Default
            for sev, keywords in severity_keywords.items():
                if any(keyword in description_lower for keyword in keywords):
                    severity = sev
                    break
        
        # Criar incidente
        incident = Incident(
            incident_id=f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}",
            title=description[:100] + "..." if len(description) > 100 else description,
            description=description,
            incident_type=incident_type,
            severity=severity,
            status=IncidentStatus.NEW,
            reported_by=reported_by,
            reported_at=datetime.now(),
            affected_systems=[],
            timeline=[{
                "timestamp": datetime.now().isoformat(),
                "event": "Incident reported",
                "details": f"Reported by {reported_by}",
                "status": IncidentStatus.NEW.value
            }],
            actions_taken=[],
            lessons_learned=[],
            preventive_measures=[],
            estimated_impact={}
        )
        
        return incident
    
    def create_incident(self, incident: Incident) -> str:
        """Cria um novo incidente e inicia resposta"""
        
        # Salvar incidente ativo
        self.active_incidents[incident.incident_id] = incident
        
        # Salvar em arquivo
        incident_file = f"{self.incidents_path}/active/{incident.incident_id}.json"
        with open(incident_file, 'w') as f:
            json.dump(asdict(incident), f, indent=2, default=str)
        
        # Log do incidente
        self._log_incident_event(incident, "CREATED", "Incident created and response initiated")
        
        # Notificar equipes
        try:
            self._send_incident_notification(incident, "created")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
        
        # Iniciar resposta automática
        self._initiate_response(incident)
        
        logger.info(f"Incident {incident.incident_id} created with severity {incident.severity.value}")
        
        return incident.incident_id
    
    def _initiate_response(self, incident: Incident):
        """Inicia resposta automática baseada no tipo e severidade"""
        
        # Atualizar status
        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.acknowledged_at = datetime.now()
        
        # Atribuir responsável inicial
        incident.assigned_to = "ops@company.com"
        
        # Salvar mudanças
        self._save_incident(incident)
    
    def update_incident_status(self, incident_id: str, new_status: IncidentStatus,
                              notes: str = "", updated_by: str = "system") -> bool:
        """Atualiza status de um incidente"""
        
        if incident_id not in self.active_incidents:
            logger.error(f"Incident {incident_id} not found in active incidents")
            return False
        
        incident = self.active_incidents[incident_id]
        old_status = incident.status
        
        incident.status = new_status
        
        # Adicionar à timeline
        incident.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "event": f"Status changed: {old_status.value} -> {new_status.value}",
            "details": notes,
            "updated_by": updated_by
        })
        
        # Se resolvido, registrar timestamp
        if new_status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now()
        
        # Log da atualização
        self._log_incident_event(incident, "STATUS_UPDATED", 
                               f"Status updated to {new_status.value} by {updated_by}")
        
        # Salvar mudanças
        self._save_incident(incident)
        
        # Notificar mudança de status
        try:
            self._send_incident_notification(incident, "status_updated")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
        
        logger.info(f"Incident {incident_id} status updated to {new_status.value}")
        
        return True
    
    def add_incident_action(self, incident_id: str, action: str, 
                           performed_by: str = "system") -> bool:
        """Adiciona ação tomada a um incidente"""
        
        if incident_id not in self.active_incidents:
            return False
        
        incident = self.active_incidents[incident_id]
        
        # Adicionar ação
        incident.actions_taken.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "performed_by": performed_by
        })
        
        # Adicionar à timeline
        incident.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "event": "Action Taken",
            "details": action,
            "performed_by": performed_by
        })
        
        # Salvar mudanças
        self._save_incident(incident)
        
        logger.info(f"Action added to incident {incident_id}: {action}")
        
        return True
    
    def escalate_incident(self, incident_id: str, reason: str, 
                         escalated_by: str = "system") -> bool:
        """Escalona um incidente para o próximo nível"""
        
        if incident_id not in self.active_incidents:
            return False
        
        incident = self.active_incidents[incident_id]
        
        # Determinar próximo nível
        current_level = incident.escalation_level
        next_level = self._get_next_escalation_level(current_level)
        
        if next_level == current_level:
            logger.warning(f"Incident {incident_id} already at highest escalation level")
            return False
        
        old_level = incident.escalation_level
        incident.escalation_level = next_level
        
        # Atualizar responsável
        incident.assigned_to = self._get_primary_contact(next_level)
        
        # Adicionar à timeline
        incident.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "event": f"Escalated: {old_level.value} -> {next_level.value}",
            "details": reason,
            "escalated_by": escalated_by
        })
        
        # Log da escalação
        self._log_incident_event(incident, "ESCALATED", 
                               f"Escalated to {next_level.value} - {reason}")
        
        # Salvar mudanças
        self._save_incident(incident)
        
        # Notificar escalação
        try:
            self._send_incident_notification(incident, "escalated")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
        
        logger.info(f"Incident {incident_id} escalated to {next_level.value}")
        
        return True
    
    def _get_next_escalation_level(self, current_level: EscalationLevel) -> EscalationLevel:
        """Determina próximo nível de escalação"""
        escalation_order = [
            EscalationLevel.L1_OPERATIONS,
            EscalationLevel.L2_SECURITY,
            EscalationLevel.L3_MANAGEMENT,
            EscalationLevel.L4_EXECUTIVE
        ]
        
        try:
            current_index = escalation_order.index(current_level)
            if current_index < len(escalation_order) - 1:
                return escalation_order[current_index + 1]
        except ValueError:
            pass
        
        return current_level
    
    def _get_primary_contact(self, escalation_level: EscalationLevel) -> str:
        """Obtém contato primário para um nível de escalação"""
        for contact in self.contacts:
            if contact.escalation_level == escalation_level:
                return contact.email
        return "ops@company.com"  # Fallback
    
    def _send_incident_notification(self, incident: Incident, notification_type: str):
        """Envia notificações sobre o incidente"""
        
        # Preparar mensagem simples
        subject = f"[{incident.severity.value.upper()}] {incident.title}"
        message = f"""
INCIDENTE: {incident.incident_id}
Titulo: {incident.title}
Status: {incident.status.value.title()}
Severidade: {incident.severity.value.upper()}
Responsavel: {incident.assigned_to}
"""
        
        logger.info(f"Notification sent for incident {incident.incident_id}: {notification_type}")
    
    def _save_incident(self, incident: Incident):
        """Salva incidente em arquivo"""
        incident_file = f"{self.incidents_path}/active/{incident.incident_id}.json"
        
        # Converter datetime objects para string
        incident_dict = asdict(incident)
        
        with open(incident_file, 'w') as f:
            json.dump(incident_dict, f, indent=2, default=str)
    
    def _log_incident_event(self, incident: Incident, event_type: str, details: str):
        """Registra eventos do incidente em log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "incident_id": incident.incident_id,
            "event_type": event_type,
            "details": details,
            "severity": incident.severity.value,
            "status": incident.status.value
        }
        
        log_file = f"{self.logs_path}/incident_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def generate_incident_report(self, incident_id: str) -> str:
        """Gera relatório detalhado de um incidente"""
        
        # Buscar incidente
        incident = None
        if incident_id in self.active_incidents:
            incident = self.active_incidents[incident_id]
        
        if not incident:
            return ""
        
        # Calcular duração
        if incident.resolved_at:
            duration = incident.resolved_at - incident.reported_at
            duration_str = f"{duration.total_seconds()/3600:.1f} horas"
        else:
            duration = datetime.now() - incident.reported_at
            duration_str = f"{duration.total_seconds()/3600:.1f} horas (em andamento)"
        
        report_content = f"""
# RELATORIO DE INCIDENTE - {incident.incident_id}

**Data de Geracao:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
**Status:** {incident.status.value.title()}

## 1. INFORMACOES GERAIS

- **ID do Incidente:** {incident.incident_id}
- **Titulo:** {incident.title}
- **Tipo:** {incident.incident_type.value.replace('_', ' ').title()}
- **Severidade:** {incident.severity.value.upper()}
- **Reportado por:** {incident.reported_by}
- **Data/Hora:** {incident.reported_at.strftime('%d/%m/%Y %H:%M:%S')}
- **Duracao:** {duration_str}
- **Responsavel Atual:** {incident.assigned_to}

## 2. DESCRICAO DO INCIDENTE

{incident.description}

## 3. TIMELINE DO INCIDENTE

"""
        
        # Adicionar timeline
        for event in incident.timeline or []:
            timestamp = event.get('timestamp', '')
            report_content += f"**{timestamp}** - {event.get('event', '')}\n"
            if event.get('details'):
                report_content += f"   {event['details']}\n"
            report_content += "\n"
        
        # Salvar relatório
        report_file = f"{self.reports_path}/incident_report_{incident.incident_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file

def main():
    """Função principal para teste do sistema de resposta a incidentes"""
    print("SISTEMA DE RESPOSTA A INCIDENTES")
    print("=" * 50)
    
    # Inicializar manager
    incident_manager = IncidentResponseManager()
    
    # Simular criação de incidente
    print("Simulando criacao de incidente...")
    
    test_incident = incident_manager.classify_incident(
        description="Sistema apresentando lentidao extrema e alguns usuarios relatam impossibilidade de acesso. Possivel ataque DDoS detectado nos logs de firewall.",
        reported_by="ops@company.com"
    )
    
    incident_id = incident_manager.create_incident(test_incident)
    print(f"   Incidente criado: {incident_id}")
    print(f"   Tipo: {test_incident.incident_type.value}")
    print(f"   Severidade: {test_incident.severity.value}")
    
    # Simular adição de ações
    print("Simulando acoes tomadas...")
    incident_manager.add_incident_action(
        incident_id, 
        "Ativada mitigacao DDoS no firewall",
        "security@company.com"
    )
    incident_manager.add_incident_action(
        incident_id,
        "Implementado rate limiting agressivo",
        "ops@company.com"
    )
    
    # Simular atualização de status
    print("Simulando atualizacao de status...")
    incident_manager.update_incident_status(
        incident_id,
        IncidentStatus.INVESTIGATING,
        "Iniciada investigacao completa do incidente",
        "security@company.com"
    )
    
    # Simular escalação
    print("Simulando escalacao...")
    incident_manager.escalate_incident(
        incident_id,
        "Impacto maior que esperado - multiplos servicos afetados",
        "security@company.com"
    )
    
    # Simular resolução
    print("Simulando resolucao...")
    incident_manager.update_incident_status(
        incident_id,
        IncidentStatus.RESOLVED,
        "Ataque mitigado com sucesso. Servicos funcionando normalmente.",
        "security@company.com"
    )
    
    # Gerar relatório do incidente
    print("Gerando relatorio do incidente...")
    report_file = incident_manager.generate_incident_report(incident_id)
    print(f"   Relatorio salvo: {report_file}")
    
    print("\nSISTEMA DE RESPOSTA A INCIDENTES CONFIGURADO!")
    print("Componentes implementados:")
    print(f"   {len(incident_manager.contacts)} contatos de escalacao configurados")
    print(f"   {len(incident_manager.response_plans)} tipos de incidente com planos")
    print("   Classificacao automatica de incidentes")
    print("   Workflows de resposta estruturados")
    print("   Sistema de escalacao automatica")
    print("   Documentacao automatica completa")
    print("   Relatorios detalhados de incidentes")

if __name__ == "__main__":
    main()
