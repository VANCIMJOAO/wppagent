#!/usr/bin/env python3
"""
⚙️ Configurações Específicas para Testes
Define constantes, URLs e configurações para execução dos testes
"""

import os
from pathlib import Path
from typing import Dict, Any

# 📁 CAMINHOS DO PROJETO
PROJECT_ROOT = Path(__file__).parent.parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
FIXTURES_DIR = TESTS_DIR / "fixtures"
LOGS_DIR = TESTS_DIR / "logs"

# Criar diretórios se não existirem
LOGS_DIR.mkdir(exist_ok=True)

# 🌐 URLs DOS SERVIÇOS
BACKEND_BASE_URL = "http://localhost:8000"
DASHBOARD_BASE_URL = "http://localhost:8501"

# 📡 ENDPOINTS DA API
API_ENDPOINTS = {
    'health': f"{BACKEND_BASE_URL}/health",
    'webhook': f"{BACKEND_BASE_URL}/webhook",
    'metrics': f"{BACKEND_BASE_URL}/metrics",
    'conversations': f"{BACKEND_BASE_URL}/conversations",
    'users': f"{BACKEND_BASE_URL}/users",
    'appointments': f"{BACKEND_BASE_URL}/appointments",
    'services': f"{BACKEND_BASE_URL}/services",
    'cost_monitoring': f"{BACKEND_BASE_URL}/cost-monitoring"
}

# 🗄️ CONFIGURAÇÕES DO BANCO DE DADOS
TEST_DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'whats_agent',
    'username': 'vancimj',
    'password': 'os.getenv("DB_PASSWORD", "SECURE_DB_PASSWORD")'
}

# 📱 CONFIGURAÇÕES DO WHATSAPP (MOCK)
WHATSAPP_CONFIG = {
    'phone_number_id': 'PHONE_NUMBER_ID_TEST',
    'business_account_id': 'BUSINESS_ACCOUNT_ID_TEST',
    'access_token': 'TEST_ACCESS_TOKEN',
    'verify_token': 'TEST_VERIFY_TOKEN',
    'api_version': 'v17.0'
}

# 👥 USUÁRIOS DE TESTE PADRÃO
TEST_USERS = {
    'new_customer': {
        'wa_id': '5511999887766',
        'nome': 'João Silva Teste',
        'telefone': '+5511999887766',
        'email': 'joao.teste@email.com'
    },
    'returning_customer': {
        'wa_id': '5511988776655',
        'nome': 'Maria Santos Teste',
        'telefone': '+5511988776655',
        'email': 'maria.teste@email.com'
    },
    'vip_customer': {
        'wa_id': '5511977665544',
        'nome': 'Pedro Costa VIP',
        'telefone': '+5511977665544',
        'email': 'pedro.vip@email.com'
    },
    'problematic_customer': {
        'wa_id': '5511966554433',
        'nome': 'Ana Problemas',
        'telefone': '+5511966554433',
        'email': 'ana.problemas@email.com'
    }
}

# 🎭 CENÁRIOS DE TESTE
TEST_SCENARIOS = {
    'discovery_flow': {
        'name': 'Descoberta de Serviços',
        'description': 'Cliente novo descobrindo os serviços disponíveis',
        'expected_duration': 30,  # segundos
        'messages': [
            'Olá',
            'Que serviços vocês fazem?',
            'Qual o preço do corte?',
            'Qual o horário de funcionamento?'
        ]
    },
    'booking_flow': {
        'name': 'Fluxo de Agendamento',
        'description': 'Fluxo completo de agendamento de serviço',
        'expected_duration': 60,
        'messages': [
            'Quero agendar um horário',
            'Corte masculino',
            'Amanhã de manhã',
            '10h',
            'Confirmar'
        ]
    },
    'cancellation_flow': {
        'name': 'Cancelamento',
        'description': 'Cliente cancelando agendamento existente',
        'expected_duration': 20,
        'messages': [
            'Preciso cancelar meu agendamento',
            'Sim, tenho certeza',
            'Obrigado'
        ]
    },
    'handoff_flow': {
        'name': 'Transferência para Humano',
        'description': 'Situação que requer atendimento humano',
        'expected_duration': 45,
        'messages': [
            'Vocês cortaram meu cabelo errado!',
            'Quero falar com o gerente',
            'Isso é inaceitável!'
        ]
    },
    'rate_limit_test': {
        'name': 'Teste de Rate Limiting',
        'description': 'Múltiplas mensagens rápidas para testar rate limiting',
        'expected_duration': 10,
        'messages': [
            'Oi', 'Olá', 'Hey', 'Alguém aí?', 'Urgente!',
            'Preciso', 'Rápido', 'Agora', 'Por favor', 'Ei!'
        ]
    }
}

# 🏢 DADOS DA EMPRESA DE TESTE
TEST_BUSINESS_DATA = {
    'name': 'Barbearia do João - Teste',
    'email': 'teste@barbearia.com',
    'phone': '+5511999887766',
    'address': 'Rua dos Testes, 123 - Centro',
    'description': 'Barbearia de testes para automação',
    'opening_hours': {
        'monday': {'open': '09:00', 'close': '19:00'},
        'tuesday': {'open': '09:00', 'close': '19:00'},
        'wednesday': {'open': '09:00', 'close': '19:00'},
        'thursday': {'open': '09:00', 'close': '19:00'},
        'friday': {'open': '09:00', 'close': '20:00'},
        'saturday': {'open': '08:00', 'close': '17:00'},
        'sunday': {'closed': True}
    }
}

# 🛠️ SERVIÇOS DE TESTE
TEST_SERVICES = [
    {
        'name': 'Corte Masculino Teste',
        'description': 'Corte de cabelo masculino para testes',
        'price': 35.00,
        'duration': 30,
        'active': True
    },
    {
        'name': 'Barba Teste',
        'description': 'Serviço de barba para testes',
        'price': 25.00,
        'duration': 20,
        'active': True
    },
    {
        'name': 'Corte + Barba Teste',
        'description': 'Combo completo para testes',
        'price': 50.00,
        'duration': 45,
        'active': True
    }
]

# ⏱️ TIMEOUTS E DELAYS
TIMEOUTS = {
    'api_response': 30,      # Timeout para resposta da API
    'webhook_processing': 15, # Timeout para processamento do webhook
    'database_query': 10,    # Timeout para queries no banco
    'service_startup': 60,   # Timeout para serviços iniciarem
    'llm_response': 45       # Timeout para resposta do LLM
}

DELAYS = {
    'between_messages': 2,   # Delay entre mensagens sequenciais
    'after_webhook': 3,      # Delay após envio de webhook
    'service_check': 5,      # Delay entre verificações de serviço
    'cleanup_wait': 2        # Delay antes de cleanup
}

# 📊 MÉTRICAS E THRESHOLDS
PERFORMANCE_THRESHOLDS = {
    'api_response_time': 2.0,      # segundos
    'webhook_processing_time': 5.0, # segundos
    'llm_response_time': 10.0,     # segundos
    'database_query_time': 1.0,    # segundos
    'memory_usage_mb': 500,        # MB
    'cpu_usage_percent': 80        # %
}

SUCCESS_CRITERIA = {
    'min_success_rate': 95,        # % mínimo de sucesso
    'max_error_rate': 5,           # % máximo de erro
    'min_uptime': 99,              # % mínimo de uptime
    'max_response_time': 3000      # ms máximo de resposta
}

# 🧪 CONFIGURAÇÕES DE TESTE
TEST_CONFIG = {
    'parallel_users': 10,          # Usuários simultâneos para teste de carga
    'test_duration': 300,          # Duração do teste em segundos
    'warmup_period': 30,           # Período de aquecimento
    'cooldown_period': 15,         # Período de resfriamento
    'retry_attempts': 3,           # Tentativas de retry em caso de falha
    'cleanup_between_tests': True, # Limpar dados entre testes
    'capture_screenshots': True,   # Capturar screenshots dos testes UI
    'verbose_logging': True        # Logging detalhado
}

# 📝 TEMPLATES DE MENSAGEM
MESSAGE_TEMPLATES = {
    'greeting': [
        'Olá',
        'Oi',
        'Bom dia',
        'Boa tarde',
        'Boa noite',
        'Hey'
    ],
    'service_inquiry': [
        'Que serviços vocês fazem?',
        'Quais serviços vocês oferecem?',
        'O que vocês fazem?',
        'Lista de serviços',
        'Cardápio de serviços'
    ],
    'booking_request': [
        'Quero agendar',
        'Gostaria de marcar um horário',
        'Posso agendar?',
        'Quero marcar',
        'Preciso agendar'
    ],
    'price_inquiry': [
        'Qual o preço?',
        'Quanto custa?',
        'Valor do serviço',
        'Preço do corte',
        'Quanto é?'
    ],
    'complaints': [
        'Não gostei do atendimento',
        'Quero reclamar',
        'Vocês erraram',
        'Péssimo serviço',
        'Quero falar com o gerente'
    ]
}

# 🎯 EXPECTED RESPONSES (para validação)
EXPECTED_RESPONSES = {
    'greeting': [
        'bem-vindo',
        'olá',
        'bom dia',
        'boa tarde',
        'boa noite',
        'como posso ajudar'
    ],
    'services_list': [
        'corte',
        'barba',
        'preço',
        'r$',
        'serviços'
    ],
    'booking_confirmation': [
        'agendamento',
        'confirmado',
        'marcado',
        'horário',
        'data'
    ],
    'handoff_trigger': [
        'atendente',
        'humano',
        'transferindo',
        'aguarde',
        'gerente'
    ]
}

# 🔧 CONFIGURAÇÕES DO AMBIENTE
ENVIRONMENT_CONFIG = {
    'development': {
        'debug': True,
        'log_level': 'DEBUG',
        'mock_external_apis': True
    },
    'testing': {
        'debug': True,
        'log_level': 'INFO',
        'mock_external_apis': True
    },
    'production': {
        'debug': False,
        'log_level': 'WARNING',
        'mock_external_apis': False
    }
}

# Configuração atual baseada na variável de ambiente
CURRENT_ENV = os.getenv('TEST_ENVIRONMENT', 'testing')
CURRENT_CONFIG = ENVIRONMENT_CONFIG.get(CURRENT_ENV, ENVIRONMENT_CONFIG['testing'])

# 📋 EXPORT ALL SETTINGS
__all__ = [
    'PROJECT_ROOT', 'TESTS_DIR', 'FIXTURES_DIR', 'LOGS_DIR',
    'BACKEND_BASE_URL', 'DASHBOARD_BASE_URL', 'API_ENDPOINTS',
    'TEST_DATABASE_CONFIG', 'WHATSAPP_CONFIG',
    'TEST_USERS', 'TEST_SCENARIOS', 'TEST_BUSINESS_DATA', 'TEST_SERVICES',
    'TIMEOUTS', 'DELAYS', 'PERFORMANCE_THRESHOLDS', 'SUCCESS_CRITERIA',
    'TEST_CONFIG', 'MESSAGE_TEMPLATES', 'EXPECTED_RESPONSES',
    'ENVIRONMENT_CONFIG', 'CURRENT_ENV', 'CURRENT_CONFIG'
]


def get_test_user(user_type: str) -> Dict[str, Any]:
    """🎭 Retorna dados de um usuário de teste específico"""
    return TEST_USERS.get(user_type, TEST_USERS['new_customer'])


def get_test_scenario(scenario_name: str) -> Dict[str, Any]:
    """🎬 Retorna um cenário de teste específico"""
    return TEST_SCENARIOS.get(scenario_name, TEST_SCENARIOS['discovery_flow'])


def get_webhook_url() -> str:
    """📡 Retorna URL do webhook para testes"""
    return API_ENDPOINTS['webhook']


def get_api_endpoint(endpoint_name: str) -> str:
    """🔗 Retorna endpoint específico da API"""
    return API_ENDPOINTS.get(endpoint_name, BACKEND_BASE_URL)


def is_debug_mode() -> bool:
    """🐛 Verifica se está em modo debug"""
    return CURRENT_CONFIG.get('debug', False)


if __name__ == "__main__":
    print("⚙️ CONFIGURAÇÕES DE TESTE")
    print("=" * 50)
    print(f"🌐 Backend URL: {BACKEND_BASE_URL}")
    print(f"📊 Dashboard URL: {DASHBOARD_BASE_URL}")
    print(f"🗄️ Database: {TEST_DATABASE_CONFIG['host']}:{TEST_DATABASE_CONFIG['port']}")
    print(f"🎭 Usuários de teste: {len(TEST_USERS)}")
    print(f"🎬 Cenários de teste: {len(TEST_SCENARIOS)}")
    print(f"🛠️ Serviços de teste: {len(TEST_SERVICES)}")
    print(f"🔧 Ambiente atual: {CURRENT_ENV}")
    print(f"🐛 Debug mode: {is_debug_mode()}")
