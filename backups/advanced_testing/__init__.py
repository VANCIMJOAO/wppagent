"""
🚀 TESTES AVANÇADOS - WHATSAPP AGENT
Pacote de testes avançados para validação completa do sistema
"""

__version__ = "1.0.0"
__author__ = "WhatsApp Agent Testing Team"

# Importações para facilitar o uso
from .test_dashboard_integration import TestDashboardIntegration
from .test_stress_load import TestStressAndLoad  
from .test_failure_scenarios import TestFailureScenarios
from .test_end_to_end import TestEndToEndValidation

__all__ = [
    'TestDashboardIntegration',
    'TestStressAndLoad', 
    'TestFailureScenarios',
    'TestEndToEndValidation'
]
