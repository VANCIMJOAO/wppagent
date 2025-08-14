#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO COMPLETO - Database WhatsApp LLM
==============================================
Verifica estrutura e dados do banco
"""

import asyncio
import asyncpg
import json
from datetime import datetime

class DatabaseDiagnostic:
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

    async def check_database_structure(self):
        """Verifica estrutura das tabelas"""
        print("\n🔍 VERIFICANDO ESTRUTURA DO BANCO")
        print("=" * 50)
        
        try:
            # Listar todas as tabelas
            tables = await self.db.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            print("📋 TABELAS ENCONTRADAS:")
            for table in tables:
                print(f"   📁 {table['table_name']}")
            
            # Verificar estrutura de cada tabela importante
            important_tables = ['users', 'conversations', 'messages', 'services', 'appointments', 'business_info']
            
            for table_name in important_tables:
                print(f"\n📊 ESTRUTURA DA TABELA: {table_name}")
                print("-" * 40)
                
                try:
                    columns = await self.db.fetch(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}'
                        ORDER BY ordinal_position
                    """)
                    
                    if columns:
                        for col in columns:
                            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                            print(f"   • {col['column_name']} ({col['data_type']}) {nullable}")
                    else:
                        print(f"   ⚠️ Tabela '{table_name}' não encontrada")
                        
                except Exception as e:
                    print(f"   ❌ Erro ao verificar {table_name}: {e}")
                    
        except Exception as e:
            print(f"❌ Erro ao verificar estrutura: {e}")

    async def check_business_data(self):
        """Verifica dados de negócio configurados"""
        print("\n🏢 VERIFICANDO DADOS DE NEGÓCIO")
        print("=" * 50)
        
        # Verificar se existe tabela de informações do negócio
        try:
            business_info = await self.db.fetch("SELECT * FROM business_info LIMIT 5")
            if business_info:
                print("✅ Dados de negócio encontrados:")
                for info in business_info:
                    print(f"   📋 {dict(info)}")
            else:
                print("⚠️ Nenhum dado de negócio encontrado na tabela business_info")
        except Exception as e:
            print(f"❌ Erro ao verificar business_info: {e}")
        
        # Verificar serviços
        try:
            services = await self.db.fetch("SELECT * FROM services LIMIT 10")
            if services:
                print("\n✅ Serviços cadastrados:")
                for service in services:
                    print(f"   🔧 {dict(service)}")
            else:
                print("\n⚠️ Nenhum serviço encontrado na tabela services")
        except Exception as e:
            print(f"\n❌ Erro ao verificar services: {e}")
        
        # Verificar outras tabelas de configuração
        config_tables = ['pricing', 'schedules', 'company_info', 'settings']
        for table in config_tables:
            try:
                data = await self.db.fetch(f"SELECT * FROM {table} LIMIT 3")
                if data:
                    print(f"\n✅ Dados em {table}:")
                    for row in data:
                        print(f"   📄 {dict(row)}")
            except:
                print(f"\n⚠️ Tabela '{table}' não encontrada ou vazia")

    async def check_recent_activity(self):
        """Verifica atividade recente"""
        print("\n📈 VERIFICANDO ATIVIDADE RECENTE")
        print("=" * 50)
        
        try:
            # Mensagens recentes
            recent_messages = await self.db.fetch("""
                SELECT 
                    m.direction, m.content, m.created_at, 
                    u.wa_id, u.nome
                FROM messages m
                JOIN users u ON m.user_id = u.id
                ORDER BY m.created_at DESC
                LIMIT 10
            """)
            
            print("📱 ÚLTIMAS 10 MENSAGENS:")
            for msg in recent_messages:
                direction = "📤" if msg['direction'] == 'in' else "📥"
                print(f"   {direction} {msg['wa_id']}: {msg['content'][:50]}...")
                print(f"      ⏰ {msg['created_at']}")
        
        except Exception as e:
            print(f"❌ Erro ao verificar atividade: {e}")

    async def check_llm_integration(self):
        """Verifica integração com LLM"""
        print("\n🤖 VERIFICANDO INTEGRAÇÃO LLM")
        print("=" * 50)
        
        try:
            # Verificar se há logs de LLM
            llm_logs = await self.db.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name LIKE '%llm%' OR table_name LIKE '%ai%'
            """)
            
            if llm_logs:
                print("✅ Tabelas relacionadas à LLM:")
                for table in llm_logs:
                    print(f"   🧠 {table['table_name']}")
            else:
                print("⚠️ Nenhuma tabela específica de LLM encontrada")
            
            # Verificar configurações
            try:
                config = await self.db.fetch("SELECT * FROM configurations WHERE key LIKE '%llm%' OR key LIKE '%openai%'")
                if config:
                    print("\n✅ Configurações LLM:")
                    for cfg in config:
                        print(f"   ⚙️ {cfg['key']}: {cfg['value'][:50]}...")
            except:
                print("\n⚠️ Tabela 'configurations' não encontrada")
                
        except Exception as e:
            print(f"❌ Erro ao verificar LLM: {e}")

    async def suggest_improvements(self):
        """Sugere melhorias baseadas na análise"""
        print("\n💡 SUGESTÕES DE MELHORIAS")
        print("=" * 50)
        
        suggestions = [
            "📋 Criar tabela 'business_info' com dados reais da empresa",
            "🔧 Popular tabela 'services' com serviços específicos",
            "💰 Configurar tabela 'pricing' com preços reais",
            "📍 Adicionar endereço e contatos reais",
            "⏰ Configurar horários de funcionamento específicos",
            "🤖 Verificar se LLM está consultando banco corretamente",
            "📊 Implementar métricas de qualidade de resposta",
            "🔄 Criar sistema de feedback das respostas"
        ]
        
        for suggestion in suggestions:
            print(f"   {suggestion}")

    async def generate_diagnosis_report(self):
        """Gera relatório completo de diagnóstico"""
        print("\n📋 GERANDO RELATÓRIO DE DIAGNÓSTICO")
        print("=" * 50)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Coletar dados para relatório
        diagnosis_data = {
            "timestamp": datetime.now().isoformat(),
            "database_connection": "successful",
            "tables_found": [],
            "business_data_status": "needs_investigation",
            "llm_integration_status": "needs_investigation",
            "recommendations": []
        }
        
        # Salvar relatório
        filename = f"database_diagnosis_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(diagnosis_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Diagnóstico salvo: {filename}")

    async def run_full_diagnosis(self):
        """Executa diagnóstico completo"""
        print("🔍 INICIANDO DIAGNÓSTICO COMPLETO DO BANCO")
        print("=" * 60)
        
        if not await self.connect():
            return False
        
        await self.check_database_structure()
        await self.check_business_data()
        await self.check_recent_activity()
        await self.check_llm_integration()
        await self.suggest_improvements()
        await self.generate_diagnosis_report()
        
        print("\n✅ DIAGNÓSTICO CONCLUÍDO!")
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
    diagnostic = DatabaseDiagnostic()
    
    try:
        await diagnostic.run_full_diagnosis()
    except KeyboardInterrupt:
        print("\n⏹️ Diagnóstico interrompido")
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await diagnostic.close()


if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO COMPLETO - Database WhatsApp LLM")
    print("=" * 60)
    print("🎯 Este script vai:")
    print("   ✅ Verificar estrutura do banco")
    print("   ✅ Analisar dados de negócio")
    print("   ✅ Verificar integração LLM")
    print("   ✅ Sugerir melhorias")
    print("=" * 60)
    
    input("▶️ Pressione ENTER para iniciar diagnóstico...")
    
    asyncio.run(main())