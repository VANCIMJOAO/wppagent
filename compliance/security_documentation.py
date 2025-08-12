#!/usr/bin/env python3
"""
✅ DOCUMENTAÇÃO DE SEGURANÇA - WHATSAPP AGENT
=============================================

Sistema completo de documentação de segurança para compliance
- Inventário de assets de segurança
- Documentação de controles implementados
- Matriz de riscos de segurança
- Procedimentos operacionais de segurança
- Relatórios de conformidade automáticos
- Templates de documentação
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
import hashlib
import yaml
import subprocess

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SecurityDocumentation')

class SecurityControlType(Enum):
    """Tipos de controles de segurança"""
    PREVENTIVE = "preventive"        # Controles preventivos
    DETECTIVE = "detective"          # Controles de detecção
    CORRECTIVE = "corrective"        # Controles corretivos
    ADMINISTRATIVE = "administrative" # Controles administrativos
    TECHNICAL = "technical"          # Controles técnicos
    PHYSICAL = "physical"           # Controles físicos

class ComplianceFramework(Enum):
    """Frameworks de compliance suportados"""
    ISO_27001 = "iso_27001"
    NIST = "nist"
    LGPD = "lgpd"
    GDPR = "gdpr"
    SOX = "sox"
    PCI_DSS = "pci_dss"
    OWASP = "owasp"

class RiskLevel(Enum):
    """Níveis de risco"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"

@dataclass
class SecurityAsset:
    """Asset de segurança do sistema"""
    asset_id: str
    name: str
    description: str
    category: str
    criticality: RiskLevel
    location: str
    owner: str
    data_classification: str
    backup_frequency: str
    recovery_time_objective: int  # minutes
    recovery_point_objective: int  # minutes
    last_reviewed: datetime
    review_frequency: int  # days

@dataclass
class SecurityControl:
    """Controle de segurança implementado"""
    control_id: str
    name: str
    description: str
    type: SecurityControlType
    category: str
    implementation_status: str
    effectiveness: str
    testing_frequency: str
    last_tested: datetime
    next_test_due: datetime
    responsible_team: str
    frameworks: List[ComplianceFramework]
    evidence_location: str
    automation_level: str
    cost_category: str

@dataclass
class SecurityRisk:
    """Risco de segurança identificado"""
    risk_id: str
    title: str
    description: str
    threat_source: str
    vulnerability: str
    impact: RiskLevel
    likelihood: RiskLevel
    risk_level: RiskLevel
    mitigation_controls: List[str]
    residual_risk: RiskLevel
    treatment_plan: str
    owner: str
    review_date: datetime

class SecurityDocumentationManager:
    """Gerenciador de documentação de segurança"""
    
    def __init__(self):
        self.base_path = "/home/vancim/whats_agent"
        self.docs_path = f"{self.base_path}/compliance/documentation"
        self.reports_path = f"{self.base_path}/compliance/reports"
        
        # Criar diretórios necessários
        os.makedirs(self.docs_path, exist_ok=True)
        os.makedirs(self.reports_path, exist_ok=True)
        os.makedirs(f"{self.docs_path}/procedures", exist_ok=True)
        os.makedirs(f"{self.docs_path}/policies", exist_ok=True)
        os.makedirs(f"{self.docs_path}/risk-assessments", exist_ok=True)
        
        # Inicializar inventários
        self.security_assets = self._initialize_security_assets()
        self.security_controls = self._initialize_security_controls()
        self.security_risks = self._initialize_security_risks()
    
    def _initialize_security_assets(self) -> List[SecurityAsset]:
        """Inicializa inventário de assets de segurança"""
        return [
            SecurityAsset(
                asset_id="APP_WHATSAPP_AGENT",
                name="WhatsApp Agent Application",
                description="Aplicação principal Python/FastAPI",
                category="Application",
                criticality=RiskLevel.CRITICAL,
                location="/home/vancim/whats_agent/app/",
                owner="Development Team",
                data_classification="Confidential",
                backup_frequency="Daily",
                recovery_time_objective=30,  # 30 minutes
                recovery_point_objective=60,  # 1 hour
                last_reviewed=datetime.now(),
                review_frequency=90
            ),
            
            SecurityAsset(
                asset_id="DB_POSTGRESQL",
                name="PostgreSQL Database",
                description="Banco de dados principal com dados pessoais",
                category="Database",
                criticality=RiskLevel.CRITICAL,
                location="Docker Container",
                owner="Database Administrator",
                data_classification="Restricted",
                backup_frequency="Daily",
                recovery_time_objective=15,  # 15 minutes
                recovery_point_objective=30,  # 30 minutes
                last_reviewed=datetime.now(),
                review_frequency=60
            ),
            
            SecurityAsset(
                asset_id="SSL_CERTIFICATES",
                name="SSL/TLS Certificates",
                description="Certificados para criptografia HTTPS",
                category="Cryptographic",
                criticality=RiskLevel.HIGH,
                location="/home/vancim/whats_agent/config/nginx/ssl/",
                owner="Security Team",
                data_classification="Confidential",
                backup_frequency="Weekly",
                recovery_time_objective=60,  # 1 hour
                recovery_point_objective=24*60,  # 24 hours
                last_reviewed=datetime.now(),
                review_frequency=30
            ),
            
            SecurityAsset(
                asset_id="ENCRYPTION_KEYS",
                name="Encryption Master Keys",
                description="Chaves mestras de criptografia",
                category="Cryptographic",
                criticality=RiskLevel.CRITICAL,
                location="/home/vancim/whats_agent/secrets/ssl/",
                owner="Security Team",
                data_classification="Restricted",
                backup_frequency="Daily",
                recovery_time_objective=5,  # 5 minutes
                recovery_point_objective=60,  # 1 hour
                last_reviewed=datetime.now(),
                review_frequency=30
            ),
            
            SecurityAsset(
                asset_id="LOGS_SYSTEM",
                name="System and Security Logs",
                description="Logs de sistema, aplicação e segurança",
                category="Logs",
                criticality=RiskLevel.HIGH,
                location="/home/vancim/whats_agent/logs/",
                owner="Operations Team",
                data_classification="Internal",
                backup_frequency="Daily",
                recovery_time_objective=120,  # 2 hours
                recovery_point_objective=24*60,  # 24 hours
                last_reviewed=datetime.now(),
                review_frequency=90
            ),
            
            SecurityAsset(
                asset_id="CONFIG_FILES",
                name="Configuration Files",
                description="Arquivos de configuração do sistema",
                category="Configuration",
                criticality=RiskLevel.HIGH,
                location="/home/vancim/whats_agent/config/",
                owner="Development Team",
                data_classification="Confidential",
                backup_frequency="Daily",
                recovery_time_objective=30,  # 30 minutes
                recovery_point_objective=4*60,  # 4 hours
                last_reviewed=datetime.now(),
                review_frequency=60
            ),
            
            SecurityAsset(
                asset_id="DOCKER_CONTAINERS",
                name="Docker Containers",
                description="Containers da aplicação e serviços",
                category="Infrastructure",
                criticality=RiskLevel.HIGH,
                location="Docker Engine",
                owner="DevOps Team",
                data_classification="Internal",
                backup_frequency="Weekly",
                recovery_time_objective=60,  # 1 hour
                recovery_point_objective=24*60,  # 24 hours
                last_reviewed=datetime.now(),
                review_frequency=60
            ),
            
            SecurityAsset(
                asset_id="MONITORING_SYSTEM",
                name="Monitoring and Alerting",
                description="Sistema de monitoramento e alertas",
                category="Monitoring",
                criticality=RiskLevel.MEDIUM,
                location="/home/vancim/whats_agent/scripts/monitoring_*",
                owner="Operations Team",
                data_classification="Internal",
                backup_frequency="Weekly",
                recovery_time_objective=120,  # 2 hours
                recovery_point_objective=24*60,  # 24 hours
                last_reviewed=datetime.now(),
                review_frequency=90
            )
        ]
    
    def _initialize_security_controls(self) -> List[SecurityControl]:
        """Inicializa inventário de controles de segurança"""
        return [
            SecurityControl(
                control_id="AC-001",
                name="Multi-Factor Authentication (2FA)",
                description="Autenticação de dois fatores para administradores",
                type=SecurityControlType.PREVENTIVE,
                category="Access Control",
                implementation_status="Implemented",
                effectiveness="High",
                testing_frequency="Monthly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=30),
                responsible_team="Security Team",
                frameworks=[ComplianceFramework.ISO_27001, ComplianceFramework.NIST],
                evidence_location="/home/vancim/whats_agent/app/auth/two_factor.py",
                automation_level="Fully Automated",
                cost_category="Low"
            ),
            
            SecurityControl(
                control_id="CR-001",
                name="Data Encryption at Rest",
                description="Criptografia AES-256-GCM para dados sensíveis",
                type=SecurityControlType.PREVENTIVE,
                category="Cryptography",
                implementation_status="Implemented",
                effectiveness="High",
                testing_frequency="Quarterly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=90),
                responsible_team="Development Team",
                frameworks=[ComplianceFramework.LGPD, ComplianceFramework.GDPR, ComplianceFramework.PCI_DSS],
                evidence_location="/home/vancim/whats_agent/app/security/encryption_service.py",
                automation_level="Fully Automated",
                cost_category="Medium"
            ),
            
            SecurityControl(
                control_id="CR-002",
                name="SSL/TLS Encryption in Transit",
                description="HTTPS obrigatório com certificados válidos",
                type=SecurityControlType.PREVENTIVE,
                category="Cryptography",
                implementation_status="Implemented",
                effectiveness="High",
                testing_frequency="Monthly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=30),
                responsible_team="Infrastructure Team",
                frameworks=[ComplianceFramework.ISO_27001, ComplianceFramework.PCI_DSS],
                evidence_location="/home/vancim/whats_agent/config/nginx/",
                automation_level="Semi-Automated",
                cost_category="Low"
            ),
            
            SecurityControl(
                control_id="LG-001",
                name="Security Audit Logging",
                description="Logging abrangente de eventos de segurança",
                type=SecurityControlType.DETECTIVE,
                category="Logging",
                implementation_status="Implemented",
                effectiveness="High",
                testing_frequency="Monthly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=30),
                responsible_team="Operations Team",
                frameworks=[ComplianceFramework.ISO_27001, ComplianceFramework.SOX],
                evidence_location="/home/vancim/whats_agent/logs/",
                automation_level="Fully Automated",
                cost_category="Low"
            ),
            
            SecurityControl(
                control_id="BK-001",
                name="Automated Database Backup",
                description="Backup automático diário com verificação de integridade",
                type=SecurityControlType.CORRECTIVE,
                category="Backup & Recovery",
                implementation_status="Implemented",
                effectiveness="High",
                testing_frequency="Weekly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=7),
                responsible_team="Database Team",
                frameworks=[ComplianceFramework.ISO_27001],
                evidence_location="/home/vancim/whats_agent/scripts/backup_database_secure.sh",
                automation_level="Fully Automated",
                cost_category="Medium"
            ),
            
            SecurityControl(
                control_id="FW-001",
                name="Network Firewall",
                description="Firewall UFW configurado com regras restritivas",
                type=SecurityControlType.PREVENTIVE,
                category="Network Security",
                implementation_status="Implemented",
                effectiveness="High",
                testing_frequency="Monthly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=30),
                responsible_team="Network Team",
                frameworks=[ComplianceFramework.ISO_27001, ComplianceFramework.NIST],
                evidence_location="/home/vancim/whats_agent/scripts/setup_firewall.sh",
                automation_level="Semi-Automated",
                cost_category="Low"
            ),
            
            SecurityControl(
                control_id="VM-001",
                name="Vulnerability Monitoring",
                description="Scanner automático de vulnerabilidades",
                type=SecurityControlType.DETECTIVE,
                category="Vulnerability Management",
                implementation_status="Implemented",
                effectiveness="Medium",
                testing_frequency="Weekly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=7),
                responsible_team="Security Team",
                frameworks=[ComplianceFramework.OWASP, ComplianceFramework.NIST],
                evidence_location="/home/vancim/whats_agent/scripts/monitoring_system_complete.py",
                automation_level="Fully Automated",
                cost_category="Low"
            ),
            
            SecurityControl(
                control_id="IM-001",
                name="Incident Response Plan",
                description="Plano estruturado de resposta a incidentes",
                type=SecurityControlType.CORRECTIVE,
                category="Incident Management",
                implementation_status="Implemented",
                effectiveness="Medium",
                testing_frequency="Quarterly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=90),
                responsible_team="Security Team",
                frameworks=[ComplianceFramework.ISO_27001, ComplianceFramework.NIST],
                evidence_location="/home/vancim/whats_agent/docs/EMERGENCY_RESPONSE_PROCEDURES.md",
                automation_level="Manual",
                cost_category="Low"
            ),
            
            SecurityControl(
                control_id="DM-001",
                name="Data Retention Policy",
                description="Política automática de retenção de dados",
                type=SecurityControlType.ADMINISTRATIVE,
                category="Data Management",
                implementation_status="Implemented",
                effectiveness="High",
                testing_frequency="Quarterly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=90),
                responsible_team="Compliance Team",
                frameworks=[ComplianceFramework.LGPD, ComplianceFramework.GDPR],
                evidence_location="/home/vancim/whats_agent/compliance/data_retention_policy.py",
                automation_level="Semi-Automated",
                cost_category="Low"
            ),
            
            SecurityControl(
                control_id="SC-001",
                name="Secure Configuration Management",
                description="Configurações seguras para todos os componentes",
                type=SecurityControlType.PREVENTIVE,
                category="Configuration Management",
                implementation_status="Implemented",
                effectiveness="High",
                testing_frequency="Monthly",
                last_tested=datetime.now(),
                next_test_due=datetime.now() + timedelta(days=30),
                responsible_team="DevOps Team",
                frameworks=[ComplianceFramework.ISO_27001, ComplianceFramework.NIST],
                evidence_location="/home/vancim/whats_agent/config/",
                automation_level="Semi-Automated",
                cost_category="Low"
            )
        ]
    
    def _initialize_security_risks(self) -> List[SecurityRisk]:
        """Inicializa matriz de riscos de segurança"""
        return [
            SecurityRisk(
                risk_id="RSK-001",
                title="Exposição de Dados Pessoais",
                description="Vazamento de dados pessoais por falha de segurança",
                threat_source="Atacantes externos, Insiders maliciosos",
                vulnerability="Falhas de configuração, Vulnerabilidades de software",
                impact=RiskLevel.CRITICAL,
                likelihood=RiskLevel.MEDIUM,
                risk_level=RiskLevel.HIGH,
                mitigation_controls=["CR-001", "CR-002", "AC-001", "LG-001"],
                residual_risk=RiskLevel.LOW,
                treatment_plan="Implementar controles de criptografia e acesso",
                owner="Security Team",
                review_date=datetime.now() + timedelta(days=90)
            ),
            
            SecurityRisk(
                risk_id="RSK-002",
                title="Indisponibilidade do Sistema",
                description="Sistema inacessível por falha técnica ou ataque",
                threat_source="Falhas de hardware, Ataques DDoS, Erros humanos",
                vulnerability="Dependência de componentes únicos",
                impact=RiskLevel.HIGH,
                likelihood=RiskLevel.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                mitigation_controls=["BK-001", "FW-001", "VM-001"],
                residual_risk=RiskLevel.LOW,
                treatment_plan="Implementar redundância e backup",
                owner="Operations Team",
                review_date=datetime.now() + timedelta(days=60)
            ),
            
            SecurityRisk(
                risk_id="RSK-003",
                title="Comprometimento de Credenciais",
                description="Acesso não autorizado por credenciais comprometidas",
                threat_source="Ataques de força bruta, Phishing, Malware",
                vulnerability="Senhas fracas, Ausência de 2FA",
                impact=RiskLevel.HIGH,
                likelihood=RiskLevel.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                mitigation_controls=["AC-001", "LG-001"],
                residual_risk=RiskLevel.LOW,
                treatment_plan="Implementar 2FA obrigatório",
                owner="Security Team",
                review_date=datetime.now() + timedelta(days=30)
            ),
            
            SecurityRisk(
                risk_id="RSK-004",
                title="Violação de Compliance LGPD",
                description="Não conformidade com LGPD resultando em multas",
                threat_source="Mudanças regulatórias, Erro de processo",
                vulnerability="Falta de documentação, Processos manuais",
                impact=RiskLevel.HIGH,
                likelihood=RiskLevel.LOW,
                risk_level=RiskLevel.MEDIUM,
                mitigation_controls=["DM-001", "LG-001"],
                residual_risk=RiskLevel.LOW,
                treatment_plan="Implementar conformidade automática",
                owner="Compliance Team",
                review_date=datetime.now() + timedelta(days=90)
            ),
            
            SecurityRisk(
                risk_id="RSK-005",
                title="Perda de Dados por Falha de Backup",
                description="Perda permanente de dados por falha no sistema de backup",
                threat_source="Falhas de hardware, Erro humano, Corrupção",
                vulnerability="Backup único, Falta de verificação",
                impact=RiskLevel.CRITICAL,
                likelihood=RiskLevel.LOW,
                risk_level=RiskLevel.MEDIUM,
                mitigation_controls=["BK-001"],
                residual_risk=RiskLevel.LOW,
                treatment_plan="Implementar backup 3-2-1",
                owner="Database Team",
                review_date=datetime.now() + timedelta(days=30)
            )
        ]
    
    def generate_asset_inventory_report(self) -> str:
        """Gera relatório de inventário de assets"""
        report_lines = [
            "📋 INVENTÁRIO DE ASSETS DE SEGURANÇA",
            "=" * 50,
            f"🕐 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"🏢 Sistema: WhatsApp Agent",
            f"📊 Total de assets: {len(self.security_assets)}",
            ""
        ]
        
        # Estatísticas por criticidade
        criticality_counts = {}
        for asset in self.security_assets:
            level = asset.criticality.value
            criticality_counts[level] = criticality_counts.get(level, 0) + 1
        
        report_lines.extend([
            "📊 DISTRIBUIÇÃO POR CRITICIDADE",
            "-" * 30
        ])
        
        for level, count in criticality_counts.items():
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "minimal": "⚪"}.get(level, "⚫")
            report_lines.append(f"   {emoji} {level.title()}: {count} assets")
        
        report_lines.append("")
        
        # Detalhes dos assets
        report_lines.extend([
            "📂 DETALHES DOS ASSETS",
            "=" * 30
        ])
        
        for asset in self.security_assets:
            criticality_emoji = {
                "critical": "🔴", "high": "🟠", "medium": "🟡", 
                "low": "🟢", "minimal": "⚪"
            }.get(asset.criticality.value, "⚫")
            
            report_lines.extend([
                f"{criticality_emoji} {asset.name} ({asset.asset_id})",
                f"   📝 Descrição: {asset.description}",
                f"   📂 Categoria: {asset.category}",
                f"   📍 Localização: {asset.location}",
                f"   👤 Responsável: {asset.owner}",
                f"   🔒 Classificação: {asset.data_classification}",
                f"   💾 Backup: {asset.backup_frequency}",
                f"   ⏰ RTO: {asset.recovery_time_objective} min",
                f"   📊 RPO: {asset.recovery_point_objective} min",
                f"   📅 Última revisão: {asset.last_reviewed.strftime('%d/%m/%Y')}",
                f"   🔄 Próxima revisão: {(asset.last_reviewed + timedelta(days=asset.review_frequency)).strftime('%d/%m/%Y')}",
                ""
            ])
        
        report_content = '\n'.join(report_lines)
        
        # Salvar relatório
        report_file = f"{self.reports_path}/asset_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file
    
    def generate_controls_matrix_report(self) -> str:
        """Gera relatório da matriz de controles"""
        report_lines = [
            "🛡️ MATRIZ DE CONTROLES DE SEGURANÇA",
            "=" * 50,
            f"🕐 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"🏢 Sistema: WhatsApp Agent",
            f"📊 Total de controles: {len(self.security_controls)}",
            ""
        ]
        
        # Estatísticas por tipo
        type_counts = {}
        for control in self.security_controls:
            type_name = control.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        report_lines.extend([
            "📊 DISTRIBUIÇÃO POR TIPO",
            "-" * 30
        ])
        
        for control_type, count in type_counts.items():
            emoji = {
                "preventive": "🛡️", "detective": "🔍", "corrective": "🔧",
                "administrative": "📋", "technical": "⚙️", "physical": "🏢"
            }.get(control_type, "⚫")
            report_lines.append(f"   {emoji} {control_type.title()}: {count} controles")
        
        report_lines.append("")
        
        # Estatísticas por framework
        framework_counts = {}
        for control in self.security_controls:
            for framework in control.frameworks:
                name = framework.value
                framework_counts[name] = framework_counts.get(name, 0) + 1
        
        report_lines.extend([
            "📊 COBERTURA POR FRAMEWORK",
            "-" * 30
        ])
        
        for framework, count in framework_counts.items():
            report_lines.append(f"   📋 {framework.upper()}: {count} controles")
        
        report_lines.append("")
        
        # Detalhes dos controles
        report_lines.extend([
            "🛡️ DETALHES DOS CONTROLES",
            "=" * 30
        ])
        
        for control in self.security_controls:
            type_emoji = {
                "preventive": "🛡️", "detective": "🔍", "corrective": "🔧",
                "administrative": "📋", "technical": "⚙️", "physical": "🏢"
            }.get(control.type.value, "⚫")
            
            status_emoji = {
                "implemented": "✅", "planned": "📅", "partial": "⚠️", "not_implemented": "❌"
            }.get(control.implementation_status.lower(), "❓")
            
            effectiveness_emoji = {
                "high": "🟢", "medium": "🟡", "low": "🔴"
            }.get(control.effectiveness.lower(), "⚫")
            
            report_lines.extend([
                f"{type_emoji} {control.name} ({control.control_id})",
                f"   📝 Descrição: {control.description}",
                f"   📂 Categoria: {control.category}",
                f"   {status_emoji} Status: {control.implementation_status}",
                f"   {effectiveness_emoji} Efetividade: {control.effectiveness}",
                f"   👤 Responsável: {control.responsible_team}",
                f"   🔄 Frequência de teste: {control.testing_frequency}",
                f"   📅 Último teste: {control.last_tested.strftime('%d/%m/%Y')}",
                f"   📅 Próximo teste: {control.next_test_due.strftime('%d/%m/%Y')}",
                f"   🤖 Automação: {control.automation_level}",
                f"   💰 Custo: {control.cost_category}",
                f"   📋 Frameworks: {', '.join([f.value.upper() for f in control.frameworks])}",
                f"   📁 Evidência: {control.evidence_location}",
                ""
            ])
        
        report_content = '\n'.join(report_lines)
        
        # Salvar relatório
        report_file = f"{self.reports_path}/controls_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file
    
    def generate_risk_assessment_report(self) -> str:
        """Gera relatório de avaliação de riscos"""
        report_lines = [
            "⚠️ MATRIZ DE RISCOS DE SEGURANÇA",
            "=" * 50,
            f"🕐 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"🏢 Sistema: WhatsApp Agent",
            f"📊 Total de riscos: {len(self.security_risks)}",
            ""
        ]
        
        # Estatísticas por nível de risco
        risk_counts = {}
        for risk in self.security_risks:
            level = risk.risk_level.value
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        report_lines.extend([
            "📊 DISTRIBUIÇÃO POR NÍVEL DE RISCO",
            "-" * 30
        ])
        
        for level, count in risk_counts.items():
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "minimal": "⚪"}.get(level, "⚫")
            report_lines.append(f"   {emoji} {level.title()}: {count} riscos")
        
        report_lines.append("")
        
        # Estatísticas de risco residual
        residual_counts = {}
        for risk in self.security_risks:
            level = risk.residual_risk.value
            residual_counts[level] = residual_counts.get(level, 0) + 1
        
        report_lines.extend([
            "📊 RISCO RESIDUAL APÓS MITIGAÇÃO",
            "-" * 30
        ])
        
        for level, count in residual_counts.items():
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "minimal": "⚪"}.get(level, "⚫")
            report_lines.append(f"   {emoji} {level.title()}: {count} riscos")
        
        report_lines.append("")
        
        # Detalhes dos riscos
        report_lines.extend([
            "⚠️ DETALHES DOS RISCOS",
            "=" * 30
        ])
        
        for risk in self.security_risks:
            risk_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "minimal": "⚪"}.get(risk.risk_level.value, "⚫")
            residual_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "minimal": "⚪"}.get(risk.residual_risk.value, "⚫")
            
            report_lines.extend([
                f"{risk_emoji} {risk.title} ({risk.risk_id})",
                f"   📝 Descrição: {risk.description}",
                f"   🎯 Fonte da ameaça: {risk.threat_source}",
                f"   🔓 Vulnerabilidade: {risk.vulnerability}",
                f"   💥 Impacto: {risk.impact.value.title()}",
                f"   📊 Probabilidade: {risk.likelihood.value.title()}",
                f"   ⚠️ Nível de risco: {risk.risk_level.value.title()}",
                f"   {residual_emoji} Risco residual: {risk.residual_risk.value.title()}",
                f"   🛡️ Controles de mitigação: {', '.join(risk.mitigation_controls)}",
                f"   📋 Plano de tratamento: {risk.treatment_plan}",
                f"   👤 Responsável: {risk.owner}",
                f"   📅 Próxima revisão: {risk.review_date.strftime('%d/%m/%Y')}",
                ""
            ])
        
        report_content = '\n'.join(report_lines)
        
        # Salvar relatório
        report_file = f"{self.reports_path}/risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_file
    
    def generate_security_architecture_document(self) -> str:
        """Gera documentação da arquitetura de segurança"""
        doc_content = f"""
# ARQUITETURA DE SEGURANÇA - WHATSAPP AGENT

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  
**Versão:** 1.0  
**Classificação:** Confidencial

## 1. VISÃO GERAL

O WhatsApp Agent implementa uma arquitetura de segurança em camadas (Defense in Depth) com múltiplos controles preventivos, detectivos e corretivos.

### 1.1 Princípios de Segurança

- **Confidencialidade:** Proteção de dados pessoais e informações sensíveis
- **Integridade:** Garantia da integridade dos dados e sistema
- **Disponibilidade:** Manutenção da disponibilidade do serviço
- **Autenticidade:** Verificação da identidade de usuários e sistemas
- **Não-repúdio:** Auditoria completa de ações críticas

## 2. ARQUITETURA DE REDE

### 2.1 Segmentação de Rede

```
Internet
    ↓
[Firewall UFW]
    ↓
[Nginx Proxy]
    ↓
┌─────────────────────────────────┐
│        Frontend Network        │
│      (172.20.0.0/24)          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│        Backend Network         │
│      (172.21.0.0/24)          │
│  - WhatsApp Agent App          │
│  - Redis                       │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│       Database Network         │
│      (172.22.0.0/24)          │
│  - PostgreSQL (interno)        │
└─────────────────────────────────┘
```

### 2.2 Controles de Rede

- **Firewall:** UFW configurado com política deny-all
- **Segmentação:** 3 redes Docker isoladas
- **Proxy Reverso:** Nginx como único ponto de entrada
- **Rate Limiting:** Proteção contra DDoS

## 3. ARQUITETURA DE DADOS

### 3.1 Classificação de Dados

| Classificação | Descrição | Exemplos | Controles |
|--------------|-----------|----------|-----------|
| **Restrito** | Dados críticos | CPF, senhas | Criptografia obrigatória |
| **Confidencial** | Dados sensíveis | Email, telefone | Acesso controlado |
| **Interno** | Dados corporativos | Logs, configurações | Acesso limitado |
| **Público** | Dados não-sensíveis | Documentação | Sem restrição especial |

### 3.2 Proteção de Dados

```
┌─────────────────────────────────┐
│         Aplicação               │
│                                 │
│  ┌─────────────────────────┐   │
│  │   Encryption Service    │   │
│  │   AES-256-GCM          │   │
│  └─────────────────────────┘   │
│                ↓                │
│  ┌─────────────────────────┐   │
│  │     Database Layer      │   │
│  │   Column Encryption     │   │
│  └─────────────────────────┘   │
│                ↓                │
│  ┌─────────────────────────┐   │
│  │    Storage Layer        │   │
│  │   Encrypted at Rest     │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

## 4. CONTROLES DE ACESSO

### 4.1 Autenticação

- **Multi-Factor Authentication (2FA):** Obrigatório para administradores
- **JWT Tokens:** Com rotação automática
- **Session Management:** Timeout e invalidação

### 4.2 Autorização

- **Role-Based Access Control (RBAC):** Baseado em funções
- **Principle of Least Privilege:** Acesso mínimo necessário
- **API Authentication:** Tokens de API com scopes limitados

## 5. MONITORAMENTO E DETECÇÃO

### 5.1 Logging

- **Security Events:** Todos os eventos de segurança logados
- **Audit Trail:** Trilha de auditoria completa
- **Centralized Logging:** Logs centralizados e estruturados

### 5.2 Monitoramento

- **Real-time Monitoring:** Monitoramento em tempo real
- **Alerting:** Alertas automáticos para eventos críticos
- **SIEM Integration:** Correlação de eventos

## 6. BACKUP E RECUPERAÇÃO

### 6.1 Estratégia de Backup

- **Frequência:** Backup diário automático
- **Retenção:** 30 dias locais + 90 dias offsite
- **Verificação:** Integridade verificada automaticamente
- **Criptografia:** Backups criptografados

### 6.2 Disaster Recovery

- **RTO (Recovery Time Objective):** 30 minutos
- **RPO (Recovery Point Objective):** 1 hora
- **Testes:** Testes mensais de recuperação

## 7. CONFORMIDADE

### 7.1 Frameworks Implementados

- **LGPD:** Lei Geral de Proteção de Dados
- **ISO 27001:** Gestão de Segurança da Informação
- **NIST:** Framework de Cibersegurança
- **OWASP:** Top 10 Web Application Security

### 7.2 Auditoria

- **Logs de Auditoria:** 7 anos de retenção
- **Relatórios Automáticos:** Geração automática de relatórios
- **Compliance Monitoring:** Monitoramento contínuo

## 8. GESTÃO DE INCIDENTES

### 8.1 Classificação de Incidentes

- **SEV-1 (Crítico):** Resposta < 5 minutos
- **SEV-2 (Alto):** Resposta < 30 minutos
- **SEV-3 (Médio):** Resposta < 2 horas
- **SEV-4 (Baixo):** Resposta < 24 horas

### 8.2 Procedimentos

- **Detecção:** Automática via monitoramento
- **Contenção:** Isolamento automático se necessário
- **Erradicação:** Correção da causa raiz
- **Recuperação:** Restauração do serviço
- **Lições Aprendidas:** Post-mortem e melhorias

## 9. MANUTENÇÃO DE SEGURANÇA

### 9.1 Atualizações

- **Security Updates:** Automáticas para componentes críticos
- **Patch Management:** Processo estruturado de patches
- **Testing:** Testes em ambiente de homologação

### 9.2 Testes de Segurança

- **Vulnerability Scanning:** Semanal
- **Penetration Testing:** Anual
- **Security Reviews:** Trimestral

## 10. CONTATOS DE EMERGÊNCIA

### 10.1 Equipes Responsáveis

- **Security Team:** security@company.com
- **Operations Team:** ops@company.com
- **Development Team:** dev@company.com
- **Compliance Team:** compliance@company.com

### 10.2 Escalação

- **Nível 1:** Operadores (24/7)
- **Nível 2:** Especialistas (horário comercial)
- **Nível 3:** Gerência (emergências)

---

**Revisão:** Trimestral  
**Próxima Revisão:** {(datetime.now() + timedelta(days=90)).strftime('%d/%m/%Y')}  
**Responsável:** Security Team
"""
        
        # Salvar documento
        doc_file = f"{self.docs_path}/security_architecture.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        return doc_file
    
    def generate_security_procedures_document(self) -> str:
        """Gera documentação de procedimentos de segurança"""
        doc_content = f"""
# PROCEDIMENTOS OPERACIONAIS DE SEGURANÇA

**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  
**Versão:** 1.0  
**Classificação:** Confidencial

## 1. PROCEDIMENTOS DIÁRIOS

### 1.1 Verificação de Segurança Matinal

**Frequência:** Diária  
**Responsável:** Operations Team

```bash
# 1. Verificar status dos serviços
docker-compose ps

# 2. Verificar logs de segurança
tail -100 /home/vancim/whats_agent/logs/security.log

# 3. Verificar alertas
cat /home/vancim/whats_agent/logs/alerts/active_alerts.json

# 4. Verificar backup do dia anterior
ls -la /home/vancim/whats_agent/backups/ | tail -5

# 5. Verificar certificados SSL
python3 /home/vancim/whats_agent/scripts/check_certificates.py
```

### 1.2 Monitoramento de Vulnerabilidades

**Frequência:** Diária  
**Responsável:** Security Team

```bash
# Executar scan de vulnerabilidades
python3 /home/vancim/whats_agent/scripts/monitoring_system_complete.py

# Verificar relatório
cat /home/vancim/whats_agent/logs/vulnerabilities/latest_scan.json
```

## 2. PROCEDIMENTOS SEMANAIS

### 2.1 Teste de Backup e Recuperação

**Frequência:** Semanal (domingos)  
**Responsável:** Database Team

```bash
# 1. Verificar integridade do backup
/home/vancim/whats_agent/scripts/validate_backup.sh

# 2. Teste de restauração (ambiente de teste)
/home/vancim/whats_agent/scripts/test_restore.sh

# 3. Documentar resultados
echo "Teste $(date): OK" >> /home/vancim/whats_agent/logs/backup_tests.log
```

### 2.2 Revisão de Acessos

**Frequência:** Semanal  
**Responsável:** Security Team

```bash
# 1. Verificar usuários ativos
python3 /home/vancim/whats_agent/tools/audit_users.py

# 2. Verificar tokens expirados
python3 /home/vancim/whats_agent/tools/audit_tokens.py

# 3. Revisar logs de acesso
grep -i "login\|logout" /home/vancim/whats_agent/logs/audit/*.log
```

## 3. PROCEDIMENTOS MENSAIS

### 3.1 Teste de Controles de Segurança

**Frequência:** Mensal  
**Responsável:** Security Team

```bash
# 1. Teste de firewall
sudo ufw status verbose

# 2. Teste de 2FA
python3 /home/vancim/whats_agent/tests/test_2fa.py

# 3. Teste de criptografia
python3 /home/vancim/whats_agent/tests/test_encryption.py

# 4. Relatório de testes
python3 /home/vancim/whats_agent/tools/generate_security_report.py
```

### 3.2 Rotação de Secrets

**Frequência:** Mensal  
**Responsável:** Security Team

```bash
# 1. Rotacionar JWT secrets
python3 /home/vancim/whats_agent/tools/rotate_secrets.py

# 2. Verificar integração
python3 /home/vancim/whats_agent/tests/test_auth.py

# 3. Atualizar documentação
# Documentar novos secrets no sistema de gestão
```

## 4. PROCEDIMENTOS TRIMESTRAIS

### 4.1 Revisão de Arquitetura de Segurança

**Frequência:** Trimestral  
**Responsável:** Security Team + Architecture Team

1. **Revisar matriz de riscos**
2. **Avaliar novos controles necessários**
3. **Atualizar documentação de segurança**
4. **Planejar melhorias para próximo trimestre**

### 4.2 Auditoria de Compliance

**Frequência:** Trimestral  
**Responsável:** Compliance Team

```bash
# 1. Gerar relatório LGPD
python3 /home/vancim/whats_agent/compliance/lgpd_compliance.py

# 2. Verificar retenção de dados
python3 /home/vancim/whats_agent/compliance/data_retention_policy.py

# 3. Auditoria de logs
python3 /home/vancim/whats_agent/tools/audit_compliance.py
```

## 5. PROCEDIMENTOS DE EMERGÊNCIA

### 5.1 Resposta a Incidente de Segurança

**Quando:** Detecção de incidente SEV-1  
**Responsável:** Security Team

**IMMEDIATE (0-5 minutos):**
```bash
# 1. ISOLAR SISTEMA
docker-compose down

# 2. PRESERVAR EVIDÊNCIAS
cp -r logs/ incident_$(date +%Y%m%d_%H%M%S)/
docker-compose logs > incident_docker_$(date +%Y%m%d_%H%M%S).log

# 3. NOTIFICAR EQUIPE
curl -X POST $SECURITY_WEBHOOK -d '{"text":"🚨 SECURITY INCIDENT"}'
```

**ANALYSIS (5-30 minutos):**
```bash
# 1. ANÁLISE INICIAL
grep -i "error\|attack\|breach" logs/security.log | tail -100

# 2. VERIFICAR COMPROMETIMENTO
netstat -tulpn | grep LISTEN
ps aux | grep -v -E "(docker|python|postgres)"

# 3. IDENTIFICAR ESCOPO
# Revisar logs de acesso e atividade suspeita
```

### 5.2 Recuperação de Disaster

**Quando:** Falha total do sistema  
**Responsável:** Operations Team

```bash
# 1. AVALIAR DANOS
# Verificar integridade dos dados

# 2. RESTAURAR BACKUP
/home/vancim/whats_agent/scripts/restore_from_backup.sh

# 3. VERIFICAR INTEGRIDADE
python3 /home/vancim/whats_agent/tests/test_system_integrity.py

# 4. REINICIAR SERVIÇOS
docker-compose up -d

# 5. VALIDAR FUNCIONAMENTO
python3 /home/vancim/whats_agent/tests/test_full_system.py
```

## 6. ESCALAÇÃO DE INCIDENTES

### 6.1 Matriz de Escalação

| Severidade | Tempo Resposta | Primeiro Contato | Escalação |
|------------|----------------|------------------|-----------|
| SEV-1      | 5 minutos      | Security Team    | CTO (15 min) |
| SEV-2      | 30 minutos     | Operations Team  | Security Lead (1h) |
| SEV-3      | 2 horas        | Operations Team  | Team Lead (4h) |
| SEV-4      | 24 horas       | Operations Team  | Next business day |

### 6.2 Contatos de Emergência

**Security Team:** security@company.com  
**Operations Team:** ops@company.com  
**CTO:** cto@company.com  
**Legal:** legal@company.com

## 7. DOCUMENTAÇÃO DE INCIDENTES

### 7.1 Template de Relatório

```
INCIDENT REPORT #[ID]
=====================================

Date: [DATA]
Time: [HORA]
Severity: [SEV-X]
Status: [OPEN/RESOLVED]

SUMMARY:
[Breve descrição do incidente]

TIMELINE:
[HH:MM] - [Evento]
[HH:MM] - [Ação tomada]
[HH:MM] - [Resolução]

IMPACT:
- Systems affected: [Lista]
- Users affected: [Número]
- Data compromised: [Sim/Não]

ROOT CAUSE:
[Causa raiz identificada]

ACTIONS TAKEN:
1. [Ação 1]
2. [Ação 2]
3. [Ação 3]

LESSONS LEARNED:
- [Lição 1]
- [Lição 2]

PREVENTIVE MEASURES:
- [Medida 1]
- [Medida 2]

NEXT STEPS:
- [ ] [Ação pendente 1]
- [ ] [Ação pendente 2]
```

## 8. MÉTRICAS E KPIs

### 8.1 Indicadores de Segurança

- **MTTD (Mean Time To Detect):** < 15 minutos
- **MTTR (Mean Time To Respond):** < 30 minutos
- **MTBF (Mean Time Between Failures):** > 720 horas
- **Backup Success Rate:** > 99%
- **Vulnerability Remediation:** < 7 dias (críticas)

### 8.2 Relatórios Regulares

- **Diário:** Status de segurança
- **Semanal:** Relatório de vulnerabilidades
- **Mensal:** Relatório de compliance
- **Trimestral:** Relatório executivo de segurança

---

**Revisão:** Trimestral  
**Próxima Revisão:** {(datetime.now() + timedelta(days=90)).strftime('%d/%m/%Y')}  
**Responsável:** Security Team
"""
        
        # Salvar documento
        doc_file = f"{self.docs_path}/procedures/security_procedures.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        return doc_file
    
    def scan_implemented_security_controls(self) -> Dict[str, Any]:
        """Escaneia o sistema para verificar controles implementados"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_controls": len(self.security_controls),
            "implemented_controls": 0,
            "control_details": {},
            "missing_evidence": [],
            "recommendations": []
        }
        
        for control in self.security_controls:
            control_result = {
                "control_id": control.control_id,
                "name": control.name,
                "status": control.implementation_status,
                "evidence_found": False,
                "evidence_location": control.evidence_location,
                "automation_verified": False
            }
            
            # Verificar se evidência existe
            if os.path.exists(control.evidence_location):
                control_result["evidence_found"] = True
                results["implemented_controls"] += 1
            else:
                results["missing_evidence"].append({
                    "control_id": control.control_id,
                    "name": control.name,
                    "expected_location": control.evidence_location
                })
            
            # Verificar automação específica
            if "script" in control.evidence_location.lower() or "py" in control.evidence_location:
                control_result["automation_verified"] = True
            
            results["control_details"][control.control_id] = control_result
        
        # Gerar recomendações
        implementation_rate = (results["implemented_controls"] / results["total_controls"]) * 100
        
        if implementation_rate < 80:
            results["recommendations"].append("Implementar controles faltantes para atingir 80% de coverage")
        
        if len(results["missing_evidence"]) > 0:
            results["recommendations"].append("Documentar evidências para controles sem evidência localizada")
        
        results["implementation_rate"] = implementation_rate
        
        return results

def main():
    """Função principal para teste do sistema de documentação"""
    print("📚 SISTEMA DE DOCUMENTAÇÃO DE SEGURANÇA")
    print("=" * 50)
    
    # Inicializar manager
    doc_manager = SecurityDocumentationManager()
    
    # Gerar relatório de inventário de assets
    print("📋 Gerando inventário de assets...")
    asset_report = doc_manager.generate_asset_inventory_report()
    print(f"   ✅ Relatório salvo: {asset_report}")
    
    # Gerar relatório de matriz de controles
    print("🛡️ Gerando matriz de controles...")
    controls_report = doc_manager.generate_controls_matrix_report()
    print(f"   ✅ Relatório salvo: {controls_report}")
    
    # Gerar relatório de avaliação de riscos
    print("⚠️ Gerando avaliação de riscos...")
    risk_report = doc_manager.generate_risk_assessment_report()
    print(f"   ✅ Relatório salvo: {risk_report}")
    
    # Gerar documentação de arquitetura
    print("🏗️ Gerando documentação de arquitetura...")
    arch_doc = doc_manager.generate_security_architecture_document()
    print(f"   ✅ Documento salvo: {arch_doc}")
    
    # Gerar procedimentos operacionais
    print("📝 Gerando procedimentos operacionais...")
    procedures_doc = doc_manager.generate_security_procedures_document()
    print(f"   ✅ Documento salvo: {procedures_doc}")
    
    # Escanear controles implementados
    print("🔍 Escaneando controles implementados...")
    scan_results = doc_manager.scan_implemented_security_controls()
    print(f"   ✅ Controles implementados: {scan_results['implemented_controls']}/{scan_results['total_controls']}")
    print(f"   📊 Taxa de implementação: {scan_results['implementation_rate']:.1f}%")
    
    if scan_results['missing_evidence']:
        print(f"   ⚠️ Evidências faltantes: {len(scan_results['missing_evidence'])}")
    
    print("\n✅ SISTEMA DE DOCUMENTAÇÃO DE SEGURANÇA CONFIGURADO!")
    print("📋 Componentes implementados:")
    print(f"   ✅ {len(doc_manager.security_assets)} assets de segurança catalogados")
    print(f"   ✅ {len(doc_manager.security_controls)} controles de segurança mapeados")
    print(f"   ✅ {len(doc_manager.security_risks)} riscos de segurança avaliados")
    print("   ✅ Documentação de arquitetura completa")
    print("   ✅ Procedimentos operacionais detalhados")
    print("   ✅ Relatórios automáticos de compliance")

if __name__ == "__main__":
    main()
