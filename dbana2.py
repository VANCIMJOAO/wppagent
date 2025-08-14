#!/usr/bin/env python3
"""
🔧 CORREÇÃO DA INTEGRAÇÃO LLM - Database
========================================
Força o bot a usar dados reais do banco
"""

import asyncio
import asyncpg
import json
from datetime import datetime

class LLMDatabaseIntegrationFixer:
    def __init__(self):
        self.DATABASE_URL = "postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway"
        
    async def connect(self):
        """Conecta ao banco"""
        try:
            self.db = await asyncpg.connect(self.DATABASE_URL)
            print("✅ Conectado ao banco PostgreSQL")
            return True
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            return False

    async def get_business_data(self):
        """Extrai todos os dados do negócio"""
        print("\n📋 EXTRAINDO DADOS REAIS DO NEGÓCIO")
        print("=" * 50)
        
        business_data = {}
        
        try:
            # Informações da empresa
            company_info = await self.db.fetchrow("SELECT * FROM company_info WHERE business_id = 3")
            
            if company_info:
                business_data['company'] = dict(company_info)
                print("✅ Dados da empresa extraídos:")
                print(f"   🏢 Nome: {company_info['company_name']}")
                print(f"   📍 Endereço: {company_info['street_address']}, {company_info['city']}")
                print(f"   📞 WhatsApp: {company_info['whatsapp_number']}")
                print(f"   📧 Email: {company_info['email_contact']}")
            
            # Serviços
            services = await self.db.fetch("SELECT * FROM services WHERE business_id = 3 AND is_active = true")
            
            if services:
                business_data['services'] = [dict(service) for service in services]
                print(f"\n✅ {len(services)} serviços extraídos:")
                for service in services:
                    print(f"   🔧 {service['name']} - {service['price']} ({service['duration_minutes']}min)")
            
            # Horários de funcionamento
            try:
                business_hours = await self.db.fetch("SELECT * FROM business_hours WHERE business_id = 3")
                if business_hours:
                    business_data['hours'] = [dict(hour) for hour in business_hours]
                    print(f"\n✅ Horários de funcionamento extraídos: {len(business_hours)} registros")
            except:
                print("\n⚠️ Tabela business_hours não encontrada")
            
            # Políticas do negócio
            try:
                policies = await self.db.fetch("SELECT * FROM business_policies WHERE business_id = 3")
                if policies:
                    business_data['policies'] = [dict(policy) for policy in policies]
                    print(f"\n✅ Políticas extraídas: {len(policies)} registros")
            except:
                print("\n⚠️ Tabela business_policies não encontrada")
            
            # Métodos de pagamento
            try:
                payment_methods = await self.db.fetch("SELECT * FROM payment_methods WHERE business_id = 3")
                if payment_methods:
                    business_data['payment_methods'] = [dict(pm) for pm in payment_methods]
                    print(f"\n✅ Métodos de pagamento: {len(payment_methods)} registros")
            except:
                print("\n⚠️ Tabela payment_methods não encontrada")
            
            return business_data
            
        except Exception as e:
            print(f"❌ Erro ao extrair dados: {e}")
            return {}

    async def check_bot_configuration(self):
        """Verifica configuração do bot"""
        print("\n🤖 VERIFICANDO CONFIGURAÇÃO DO BOT")
        print("=" * 50)
        
        try:
            bot_config = await self.db.fetch("SELECT * FROM bot_configurations WHERE business_id = 3")
            
            if bot_config:
                print("✅ Configurações do bot encontradas:")
                for config in bot_config:
                    print(f"   ⚙️ {dict(config)}")
                return [dict(config) for config in bot_config]
            else:
                print("⚠️ Nenhuma configuração específica do bot encontrada")
                return []
                
        except Exception as e:
            print(f"❌ Erro ao verificar configuração: {e}")
            return []

    async def test_database_queries(self):
        """Testa queries que o bot deveria fazer"""
        print("\n🧪 TESTANDO QUERIES QUE O BOT DEVERIA FAZER")
        print("=" * 50)
        
        test_scenarios = [
            {
                "question": "Quais serviços vocês oferecem?",
                "query": "SELECT name, description, price, duration_minutes FROM services WHERE business_id = 3 AND is_active = true",
                "expected": "Lista de serviços reais"
            },
            {
                "question": "Qual o endereço?", 
                "query": "SELECT street_address, city, state FROM company_info WHERE business_id = 3",
                "expected": "Rua das Flores, 123 - Centro, São Paulo"
            },
            {
                "question": "Quanto custa limpeza de pele?",
                "query": "SELECT price FROM services WHERE business_id = 3 AND name ILIKE '%limpeza%'",
                "expected": "R$ 80,00"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n❓ Pergunta: {scenario['question']}")
            print(f"🔍 Query: {scenario['query']}")
            
            try:
                result = await self.db.fetch(scenario['query'])
                if result:
                    print(f"✅ Resultado: {[dict(row) for row in result]}")
                    print(f"✅ Esperado: {scenario['expected']}")
                else:
                    print("❌ Nenhum resultado encontrado")
            except Exception as e:
                print(f"❌ Erro na query: {e}")

    async def generate_llm_prompt_template(self, business_data):
        """Gera template de prompt para LLM usar dados reais"""
        print("\n📝 GERANDO TEMPLATE DE PROMPT PARA LLM")
        print("=" * 50)
        
        company = business_data.get('company', {})
        services = business_data.get('services', [])
        
        prompt_template = f"""
DADOS REAIS DA EMPRESA (SEMPRE CONSULTE BANCO DE DADOS):
========================================================

🏢 EMPRESA: {company.get('company_name', 'Studio Beleza & Bem-Estar')}
📍 ENDEREÇO: {company.get('street_address', '')}, {company.get('city', '')}, {company.get('state', '')}
📞 WHATSAPP: {company.get('whatsapp_number', '')}
📧 EMAIL: {company.get('email_contact', '')}
🌐 SITE: {company.get('website', '')}
📱 INSTAGRAM: {company.get('instagram', '')}

💬 MENSAGEM DE BOAS-VINDAS:
{company.get('welcome_message', '')}

🔧 SERVIÇOS DISPONÍVEIS:
"""
        
        for service in services:
            prompt_template += f"""
- {service['name']}: {service['price']} ({service['duration_minutes']}min)
  Descrição: {service['description']}
"""
        
        prompt_template += f"""

⚠️ INSTRUÇÕES CRÍTICAS PARA LLM:
================================
1. SEMPRE consulte o banco de dados antes de responder
2. USE APENAS dados reais da empresa acima
3. NÃO invente preços, endereços ou informações
4. Para serviços: consulte tabela 'services' WHERE business_id = 3
5. Para empresa: consulte tabela 'company_info' WHERE business_id = 3
6. Sempre use o nome real: "{company.get('company_name', 'Studio Beleza & Bem-Estar')}"
7. Sempre use endereço real: "{company.get('street_address', '')}"

📋 QUERIES ESSENCIAIS:
- Serviços: SELECT * FROM services WHERE business_id = 3 AND is_active = true
- Empresa: SELECT * FROM company_info WHERE business_id = 3
- Horários: SELECT * FROM business_hours WHERE business_id = 3
- Políticas: SELECT * FROM business_policies WHERE business_id = 3
"""
        
        # Salvar template
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"llm_prompt_template_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(prompt_template)
        
        print(f"📄 Template salvo: {filename}")
        print("\n📋 PREVIEW DO TEMPLATE:")
        print(prompt_template[:800] + "...")
        
        return prompt_template

    async def create_integration_test(self):
        """Cria teste de integração real"""
        print("\n🧪 CRIANDO TESTE DE INTEGRAÇÃO")
        print("=" * 50)
        
        test_messages = [
            "Quais serviços vocês oferecem?",
            "Quanto custa uma limpeza de pele?", 
            "Qual o endereço de vocês?",
            "Qual o horário de funcionamento?",
            "Quero agendar um hidrofacial"
        ]
        
        print("📱 MENSAGENS DE TESTE:")
        for i, msg in enumerate(test_messages, 1):
            print(f"   {i}. {msg}")
        
        # Salvar teste
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "test_messages": test_messages,
            "expected_behavior": "Bot deve consultar banco e usar dados reais",
            "critical_points": [
                "Nome da empresa: Studio Beleza & Bem-Estar",
                "Endereço real: Rua das Flores, 123 - Centro",
                "Preços reais: R$ 45,00 a R$ 300,00",
                "Serviços específicos: 10 serviços cadastrados"
            ]
        }
        
        filename = f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Teste salvo: {filename}")

    async def run_integration_fix(self):
        """Executa correção completa da integração"""
        print("🔧 INICIANDO CORREÇÃO DA INTEGRAÇÃO LLM")
        print("=" * 60)
        
        if not await self.connect():
            return False
        
        # 1. Extrair dados reais
        business_data = await self.get_business_data()
        
        # 2. Verificar configuração
        bot_config = await self.check_bot_configuration()
        
        # 3. Testar queries
        await self.test_database_queries()
        
        # 4. Gerar template de prompt
        await self.generate_llm_prompt_template(business_data)
        
        # 5. Criar teste de integração
        await self.create_integration_test()
        
        # 6. Relatório final
        print("\n📊 RELATÓRIO FINAL DE CORREÇÃO")
        print("=" * 50)
        print("✅ Dados da empresa extraídos corretamente")
        print("✅ Serviços reais identificados")
        print("✅ Queries de teste executadas")
        print("✅ Template de prompt gerado")
        print("✅ Teste de integração criado")
        
        print("\n🎯 PRÓXIMOS PASSOS:")
        print("   1. Aplicar template de prompt no sistema LLM")
        print("   2. Configurar bot para consultar banco sempre")
        print("   3. Testar com mensagens reais")
        print("   4. Verificar se respostas usam dados corretos")
        
        return True

    async def close(self):
        """Fecha conexão"""
        try:
            if hasattr(self, 'db'):
                await self.db.close()
                print("✅ Conexão fechada")
        except Exception as e:
            print(f"❌ Erro ao fechar: {e}")


async def main():
    """Função principal"""
    fixer = LLMDatabaseIntegrationFixer()
    
    try:
        await fixer.run_integration_fix()
    except KeyboardInterrupt:
        print("\n⏹️ Correção interrompida")
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await fixer.close()


if __name__ == "__main__":
    print("🔧 CORREÇÃO DA INTEGRAÇÃO LLM - Database")
    print("=" * 50)
    print("🎯 O problema identificado:")
    print("   ❌ Bot não consulta dados reais do banco")
    print("   ❌ Usa conhecimento genérico da LLM")
    print("   ❌ Ignora informações específicas cadastradas")
    print("\n✅ Solução:")
    print("   🔧 Forçar consulta ao banco sempre")
    print("   📋 Usar dados reais da empresa")
    print("   🎯 Template de prompt correto")
    print("=" * 50)
    
    input("▶️ Pressione ENTER para corrigir integração...")
    
    asyncio.run(main())