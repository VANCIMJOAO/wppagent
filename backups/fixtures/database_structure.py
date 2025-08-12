#!/usr/bin/env python3
"""
🗄️ Gerador da Estrutura Completa do Banco de Dados para Testes
Analisa o banco PostgreSQL atual e gera dados de exemplo realísticos
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import uuid

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import sync_engine, SessionLocal
from app.models.database import *
from app.config import settings


class DatabaseStructureGenerator:
    """🔍 Analisador e Gerador de Estrutura do Banco de Dados"""
    
    def __init__(self):
        self.structure = {}
        self.sample_data = {}
        self.relationships = {}
        self.constraints = {}
        
    def analyze_database_structure(self):
        """📋 Analisa estrutura atual do banco de dados"""
        print("🔍 Analisando estrutura do banco de dados...")
        
        try:
            # Conectar ao banco
            inspector = inspect(sync_engine)
            
            # Obter lista de tabelas
            tables = inspector.get_table_names()
            print(f"📊 Encontradas {len(tables)} tabelas: {tables}")
            
            # Analisar cada tabela
            for table_name in tables:
                print(f"📋 Analisando tabela: {table_name}")
                
                # Colunas
                columns = inspector.get_columns(table_name)
                
                # Chaves primárias
                pk_constraint = inspector.get_pk_constraint(table_name)
                
                # Chaves estrangeiras
                foreign_keys = inspector.get_foreign_keys(table_name)
                
                # Índices
                indexes = inspector.get_indexes(table_name)
                
                # Armazenar estrutura
                self.structure[table_name] = {
                    'columns': columns,
                    'primary_key': pk_constraint,
                    'foreign_keys': foreign_keys,
                    'indexes': indexes
                }
                
                print(f"  ✅ {len(columns)} colunas")
                print(f"  🔑 PK: {pk_constraint.get('constrained_columns', [])}")
                print(f"  🔗 FK: {len(foreign_keys)} relacionamentos")
                
        except Exception as e:
            print(f"❌ Erro ao analisar banco: {e}")
            
        return self.structure
    
    def get_current_data_samples(self):
        """📊 Obtém amostras dos dados atuais"""
        print("📊 Coletando amostras de dados atuais...")
        
        session = SessionLocal()
        try:
            # Verificar dados existentes em cada tabela
            tables_to_sample = [
                'users', 'messages', 'conversations', 'appointments', 
                'services', 'businesses', 'business_hours', 'blocked_times',
                'company_info', 'bot_configurations', 'business_policies',
                'message_templates', 'payment_methods'
            ]
            
            for table_name in tables_to_sample:
                try:
                    # Contar registros
                    count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                    count_result = session.execute(count_query).scalar()
                    
                    if count_result > 0:
                        # Obter amostra (máximo 5 registros)
                        sample_query = text(f"SELECT * FROM {table_name} LIMIT 5")
                        sample_result = session.execute(sample_query).fetchall()
                        
                        # Converter para dict
                        if sample_result:
                            columns = sample_result[0].keys()
                            samples = []
                            for row in sample_result:
                                row_dict = {}
                                for i, col in enumerate(columns):
                                    value = row[i]
                                    # Converter datetime para string
                                    if isinstance(value, datetime):
                                        value = value.isoformat()
                                    elif isinstance(value, uuid.UUID):
                                        value = str(value)
                                    row_dict[col] = value
                                samples.append(row_dict)
                            
                            self.sample_data[table_name] = {
                                'count': count_result,
                                'samples': samples
                            }
                            
                            print(f"  📋 {table_name}: {count_result} registros")
                        
                except Exception as e:
                    print(f"  ⚠️ Erro em {table_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Erro ao coletar amostras: {e}")
        finally:
            session.close()
            
        return self.sample_data
    
    def generate_realistic_test_data(self):
        """🎭 Gera dados de teste realísticos baseados na estrutura"""
        print("🎭 Gerando dados de teste realísticos...")
        
        test_data = {
            # 👥 USUÁRIOS DE TESTE
            'users': [
                {
                    'wa_id': '5511999887766',
                    'nome': 'João Silva',
                    'telefone': '+5511999887766',
                    'email': 'joao.silva@email.com',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'wa_id': '5511988776655',
                    'nome': 'Maria Santos',
                    'telefone': '+5511988776655',
                    'email': 'maria.santos@email.com',
                    'created_at': (datetime.now() - timedelta(days=1)).isoformat()
                },
                {
                    'wa_id': '5511977665544',
                    'nome': 'Pedro Costa',
                    'telefone': '+5511977665544',
                    'email': 'pedro.costa@email.com',
                    'created_at': (datetime.now() - timedelta(days=2)).isoformat()
                },
                {
                    'wa_id': '5511966554433',
                    'nome': 'Ana Oliveira',
                    'telefone': '+5511966554433',
                    'email': 'ana.oliveira@email.com',
                    'created_at': (datetime.now() - timedelta(days=5)).isoformat()
                },
                {
                    'wa_id': '5511955443322',
                    'nome': 'Carlos Pereira',
                    'telefone': '+5511955443322',
                    'email': 'carlos.pereira@email.com',
                    'created_at': (datetime.now() - timedelta(days=10)).isoformat()
                }
            ],
            
            # 💬 CONVERSAS DE TESTE
            'conversations': [
                {
                    'user_id': 1,  # João Silva
                    'status': 'ativa',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'last_message_at': datetime.now().isoformat()
                },
                {
                    'user_id': 2,  # Maria Santos
                    'status': 'finalizada',
                    'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'updated_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'last_message_at': (datetime.now() - timedelta(hours=1)).isoformat()
                },
                {
                    'user_id': 3,  # Pedro Costa
                    'status': 'aguardando',
                    'created_at': (datetime.now() - timedelta(hours=6)).isoformat(),
                    'updated_at': (datetime.now() - timedelta(hours=3)).isoformat(),
                    'last_message_at': (datetime.now() - timedelta(hours=3)).isoformat()
                }
            ],
            
            # 📱 MENSAGENS DE TESTE
            'messages': [
                {
                    'user_id': 1,
                    'conversation_id': 1,
                    'direction': 'in',
                    'message_id': 'wamid.test_001',
                    'content': 'Olá! Gostaria de agendar um horário para corte de cabelo',
                    'message_type': 'text',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'user_id': 1,
                    'conversation_id': 1,
                    'direction': 'out',
                    'message_id': 'wamid.test_002',
                    'content': 'Olá João! Claro, vou te ajudar com o agendamento. Qual dia você prefere?',
                    'message_type': 'text',
                    'created_at': (datetime.now() + timedelta(seconds=30)).isoformat()
                },
                {
                    'user_id': 2,
                    'conversation_id': 2,
                    'direction': 'in',
                    'message_id': 'wamid.test_003',
                    'content': 'Quais serviços vocês oferecem?',
                    'message_type': 'text',
                    'created_at': (datetime.now() - timedelta(hours=2)).isoformat()
                },
                {
                    'user_id': 3,
                    'conversation_id': 3,
                    'direction': 'in',
                    'message_id': 'wamid.test_004',
                    'content': 'Preciso cancelar meu agendamento de amanhã',
                    'message_type': 'text',
                    'created_at': (datetime.now() - timedelta(hours=6)).isoformat()
                }
            ],
            
            # 🏢 SERVIÇOS DE TESTE
            'services': [
                {
                    'name': 'Corte Masculino',
                    'description': 'Corte de cabelo masculino tradicional e moderno',
                    'price': 35.00,
                    'duration': 30,
                    'active': True,
                    'created_at': (datetime.now() - timedelta(days=30)).isoformat()
                },
                {
                    'name': 'Barba',
                    'description': 'Aparar e modelar barba com navalha',
                    'price': 25.00,
                    'duration': 20,
                    'active': True,
                    'created_at': (datetime.now() - timedelta(days=30)).isoformat()
                },
                {
                    'name': 'Corte + Barba',
                    'description': 'Combo completo: corte de cabelo + barba',
                    'price': 50.00,
                    'duration': 45,
                    'active': True,
                    'created_at': (datetime.now() - timedelta(days=30)).isoformat()
                },
                {
                    'name': 'Sobrancelha',
                    'description': 'Design e limpeza de sobrancelhas masculinas',
                    'price': 15.00,
                    'duration': 15,
                    'active': True,
                    'created_at': (datetime.now() - timedelta(days=30)).isoformat()
                }
            ],
            
            # 📅 AGENDAMENTOS DE TESTE
            'appointments': [
                {
                    'user_id': 1,
                    'service_id': 1,
                    'date_time': (datetime.now() + timedelta(days=1, hours=10)).isoformat(),
                    'status': 'confirmado',
                    'notes': 'Cliente preferencial - corte degradê',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'user_id': 2,
                    'service_id': 3,
                    'date_time': (datetime.now() + timedelta(days=2, hours=14)).isoformat(),
                    'status': 'pendente',
                    'notes': 'Primeira vez na barbearia',
                    'created_at': (datetime.now() - timedelta(hours=1)).isoformat()
                },
                {
                    'user_id': 4,
                    'service_id': 2,
                    'date_time': (datetime.now() - timedelta(days=1, hours=16)).isoformat(),
                    'status': 'concluido',
                    'notes': 'Cliente satisfeito',
                    'created_at': (datetime.now() - timedelta(days=2)).isoformat()
                }
            ],
            
            # 🏪 INFORMAÇÕES DA EMPRESA
            'company_info': [
                {
                    'name': 'Barbearia do João',
                    'address': 'Rua das Flores, 123 - Centro',
                    'phone': '+5511999887766',
                    'email': 'contato@barbeariajao.com.br',
                    'description': 'A melhor barbearia da região, com profissionais experientes',
                    'created_at': (datetime.now() - timedelta(days=100)).isoformat()
                }
            ],
            
            # ⏰ HORÁRIOS DE FUNCIONAMENTO
            'business_hours': [
                {'day_of_week': 1, 'open_time': '09:00', 'close_time': '19:00', 'is_open': True},
                {'day_of_week': 2, 'open_time': '09:00', 'close_time': '19:00', 'is_open': True},
                {'day_of_week': 3, 'open_time': '09:00', 'close_time': '19:00', 'is_open': True},
                {'day_of_week': 4, 'open_time': '09:00', 'close_time': '19:00', 'is_open': True},
                {'day_of_week': 5, 'open_time': '09:00', 'close_time': '20:00', 'is_open': True},
                {'day_of_week': 6, 'open_time': '08:00', 'close_time': '17:00', 'is_open': True},
                {'day_of_week': 0, 'open_time': None, 'close_time': None, 'is_open': False}
            ]
        }
        
        # 🎭 CENÁRIOS DE TESTE ESPECÍFICOS
        test_scenarios = {
            'new_customer_discovery': {
                'description': 'Cliente novo descobrindo serviços',
                'user': test_data['users'][0],
                'messages_flow': [
                    {'direction': 'in', 'content': 'Olá'},
                    {'direction': 'out', 'content': 'Olá! Bem-vindo à Barbearia do João! Como posso ajudá-lo?'},
                    {'direction': 'in', 'content': 'Que serviços vocês fazem?'},
                    {'direction': 'out', 'content': 'Oferecemos: Corte Masculino (R$ 35), Barba (R$ 25), Corte + Barba (R$ 50), Sobrancelha (R$ 15)'},
                    {'direction': 'in', 'content': 'Qual o horário de funcionamento?'},
                    {'direction': 'out', 'content': 'Funcionamos de Segunda a Sábado: Seg-Sex: 9h às 19h, Sáb: 8h às 17h. Domingo fechado.'}
                ]
            },
            
            'complete_booking_workflow': {
                'description': 'Fluxo completo de agendamento',
                'user': test_data['users'][1],
                'messages_flow': [
                    {'direction': 'in', 'content': 'Quero agendar um corte'},
                    {'direction': 'out', 'content': 'Perfeito! Qual serviço você gostaria? 1) Corte Masculino 2) Corte + Barba'},
                    {'direction': 'in', 'content': '1'},
                    {'direction': 'out', 'content': 'Ótima escolha! Para quando você gostaria de agendar?'},
                    {'direction': 'in', 'content': 'Amanhã de manhã'},
                    {'direction': 'out', 'content': 'Tenho disponível amanhã às 10h, 11h ou 14h. Qual prefere?'},
                    {'direction': 'in', 'content': '10h'},
                    {'direction': 'out', 'content': 'Agendamento confirmado! João Silva - Corte Masculino - Amanhã às 10h. Te envio lembrete 1h antes!'}
                ]
            },
            
            'handoff_scenario': {
                'description': 'Cenário que necessita transferência para humano',
                'user': test_data['users'][2],
                'messages_flow': [
                    {'direction': 'in', 'content': 'Vocês cortaram meu cabelo errado ontem!'},
                    {'direction': 'out', 'content': 'Sinto muito pelo ocorrido! Vou transferir você para nosso atendente para resolver isso da melhor forma.'},
                    {'direction': 'in', 'content': 'Quero meu dinheiro de volta'},
                    {'direction': 'out', 'content': 'Entendo sua frustração. Um atendente humano vai cuidar do seu caso agora. Aguarde um momento.'}
                ]
            },
            
            'rate_limit_test': {
                'description': 'Teste de rate limiting',
                'user': test_data['users'][3],
                'rapid_messages': [
                    'Oi', 'Olá', 'Hey', 'Alguém aí?', 'Urgente!', 
                    'Preciso agendar', 'Rápido', 'Agora', 'Por favor', 'Ei!'
                ]
            },
            
            'vip_customer_crewai': {
                'description': 'Cliente VIP que deve acionar CrewAI',
                'user': test_data['users'][4],
                'messages_flow': [
                    {'direction': 'in', 'content': 'Olá, sou cliente há 5 anos e gostaria de um atendimento especial para meu casamento'},
                    {'direction': 'out', 'content': 'Olá Carlos! É um prazer atendê-lo! Para seu casamento, vou acionar nossa equipe especializada...'},
                    {'direction': 'in', 'content': 'Preciso de corte, barba, sobrancelha e talvez algum tratamento especial'},
                    {'direction': 'out', 'content': 'Perfeito! Vou montar um pacote especial para você...'}
                ]
            }
        }
        
        return {
            'test_data': test_data,
            'test_scenarios': test_scenarios
        }
    
    def save_structure_to_file(self):
        """💾 Salva estrutura completa em arquivo JSON"""
        print("💾 Salvando estrutura em arquivo...")
        
        # Criar diretório se não existir
        output_dir = Path(__file__).parent
        output_dir.mkdir(exist_ok=True)
        
        # Gerar dados de teste
        test_data_complete = self.generate_realistic_test_data()
        
        # Estrutura completa
        complete_structure = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'database_url': 'postgresql://vancimj:***@localhost:5432/whats_agent',
                'total_tables': len(self.structure),
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'database_schema': self.structure,
            'current_data_samples': self.sample_data,
            'test_data': test_data_complete['test_data'],
            'test_scenarios': test_data_complete['test_scenarios'],
            'api_endpoints': {
                'webhook': '/webhook',
                'health': '/health',
                'metrics': '/metrics',
                'conversations': '/conversations',
                'users': '/users',
                'appointments': '/appointments',
                'services': '/services'
            },
            'backend_urls': {
                'fastapi': 'http://localhost:8000',
                'dashboard': 'http://localhost:8501',
                'webhook_test': 'http://localhost:8000/webhook'
            }
        }
        
        # Salvar JSON
        output_file = output_dir / 'database_structure.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_structure, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Estrutura salva em: {output_file}")
        print(f"📊 {len(self.structure)} tabelas analisadas")
        print(f"📋 {len(self.sample_data)} tabelas com dados")
        print(f"🎭 {len(test_data_complete['test_scenarios'])} cenários de teste criados")
        
        return output_file

    def create_summary_report(self):
        """📊 Cria relatório resumido da estrutura"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DA ESTRUTURA DO BANCO DE DADOS")
        print("="*60)
        
        if self.structure:
            for table_name, table_info in self.structure.items():
                print(f"\n📋 Tabela: {table_name.upper()}")
                print(f"   🔹 Colunas: {len(table_info['columns'])}")
                
                # Mostrar colunas principais
                important_cols = []
                for col in table_info['columns']:
                    col_name = col['name']
                    col_type = str(col['type'])
                    if col_name in ['id', 'user_id', 'created_at', 'name', 'status']:
                        important_cols.append(f"{col_name}({col_type})")
                
                if important_cols:
                    print(f"   🔹 Principais: {', '.join(important_cols[:3])}")
                
                # Relacionamentos
                if table_info['foreign_keys']:
                    fks = [f"{fk['constrained_columns'][0]} -> {fk['referred_table']}" 
                           for fk in table_info['foreign_keys']]
                    print(f"   🔗 FK: {', '.join(fks[:2])}")
        
        if self.sample_data:
            print(f"\n📊 DADOS ATUAIS:")
            for table_name, data_info in self.sample_data.items():
                print(f"   📋 {table_name}: {data_info['count']} registros")
        
        print("\n" + "="*60)


def main():
    """🚀 Função principal"""
    print("🗄️ GERADOR DE ESTRUTURA DO BANCO DE DADOS")
    print("="*50)
    
    generator = DatabaseStructureGenerator()
    
    # Analisar estrutura
    generator.analyze_database_structure()
    
    # Obter dados atuais
    generator.get_current_data_samples()
    
    # Salvar em arquivo
    output_file = generator.save_structure_to_file()
    
    # Relatório resumido
    generator.create_summary_report()
    
    print(f"\n✅ Processo concluído!")
    print(f"📁 Arquivo gerado: {output_file}")
    print(f"🎯 Pronto para executar testes!")


if __name__ == "__main__":
    main()
